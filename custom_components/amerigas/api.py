"""API client for AmeriGas."""
from __future__ import annotations

import aiohttp
import base64
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from homeassistant.util import dt as dt_util

from .const import API_LOGIN_URL, API_DASHBOARD_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class AmeriGasAPIError(Exception):
    """Base exception for AmeriGas API errors."""


class AmeriGasAuthError(AmeriGasAPIError):
    """Authentication error."""


class AmeriGasAPI:
    """API client for AmeriGas customer portal."""
    
    def __init__(self, username: str, password: str) -> None:
        """Initialize the API client."""
        self.username = username
        self.password = password
        self._session: aiohttp.ClientSession | None = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            _LOGGER.debug("Created new aiohttp session")
        return self._session
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            _LOGGER.debug("Closed aiohttp session")
            self._session = None
    
    async def async_get_data(self) -> dict[str, Any]:
        """Fetch data from AmeriGas portal."""
        try:
            # Login and get dashboard data
            account_data = await self._async_fetch_dashboard()
            
            # Parse and return clean data
            return self._parse_account_data(account_data)
            
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Network error: {err}")
            raise AmeriGasAPIError(f"Network error: {err}") from err
        except json.JSONDecodeError as err:
            _LOGGER.error(f"JSON parsing error: {err}")
            raise AmeriGasAPIError(f"JSON parsing error: {err}") from err
        finally:
            # Close session after each fetch to prevent unclosed connection warnings
            await self.close()
    
    async def _async_fetch_dashboard(self) -> dict[str, Any]:
        """Login and fetch dashboard data."""
        session = await self._get_session()
        
        # Base64 encode credentials
        encoded_email = base64.b64encode(self.username.encode()).decode()
        encoded_password = base64.b64encode(self.password.encode()).decode()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        login_data = {
            'loginViewModel[EmailAddress]': encoded_email,
            'loginViewModel[Password]': encoded_password,
            'loginViewModel[SAPErrorMessage]': ''
        }
        
        # Login
        async with session.post(
            API_LOGIN_URL,
            data=login_data,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
        ) as response:
            if response.status != 200:
                raise AmeriGasAuthError(f"Login failed with status {response.status}")
            
            login_result = await response.json()
            if not login_result.get('success'):
                error_msg = login_result.get('message', 'Unknown error')
                raise AmeriGasAuthError(f"Login failed: {error_msg}")
        
        # Get dashboard
        async with session.get(
            API_DASHBOARD_URL,
            timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
        ) as response:
            if response.status != 200:
                raise AmeriGasAPIError(f"Dashboard fetch failed with status {response.status}")
            
            dashboard_text = await response.text()
        
        # Parse accountSummaryViewModel from JavaScript
        pattern = r'accountSummaryViewModel\s*=\s*({.*?});'
        match = re.search(pattern, dashboard_text, re.DOTALL)
        
        if not match:
            raise AmeriGasAPIError("Could not find accountSummaryViewModel in page")
        
        return json.loads(match.group(1))
    
    def _parse_account_data(self, account_data: dict[str, Any]) -> dict[str, Any]:
        """Parse raw account data into clean format."""
        # Helper functions
        def safe_float(value, default=0.0):
            if value is None or value == '':
                return default
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').strip()
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        def safe_int(value, default=0):
            try:
                return int(value) if value else default
            except (ValueError, TypeError):
                return default
        
        def parse_date(date_str):
            """Parse AmeriGas date in multiple formats, always returns timezone-aware datetime.
            
            Naive datetimes (date-only strings like MM/DD/YYYY) are treated as local time
            using the HA-configured timezone, so dates never roll back a day due to UTC offset.
            Datetimes that already carry timezone info are left unchanged.
            """
            if not date_str or date_str in ['', 'N/A', 'Unknown', 'None']:
                return None
            
            try:
                dt_obj = None
                
                # ISO format with T
                if 'T' in str(date_str):
                    if date_str.endswith('Z'):
                        dt_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        dt_obj = datetime.fromisoformat(date_str)
                
                # US date format
                elif '/' in str(date_str):
                    parts = str(date_str).split('/')
                    if len(parts) == 3:
                        if len(parts[2]) == 2:
                            dt_obj = datetime.strptime(str(date_str), '%m/%d/%y')
                        else:
                            dt_obj = datetime.strptime(str(date_str), '%m/%d/%Y')
                
                # Fallback
                else:
                    dt_obj = datetime.fromisoformat(str(date_str))
                
                if dt_obj:
                    if dt_obj.tzinfo is None:
                        # Treat as local time — date-only strings have no timezone context,
                        # so attaching UTC would cause them to roll back a day for US timezones.
                        dt_obj = dt_obj.replace(tzinfo=dt_util.get_default_time_zone())
                    return dt_obj
                
                return None
                
            except (ValueError, AttributeError, TypeError) as e:
                _LOGGER.warning(f"Could not parse date '{date_str}': {e}")
                return None
        
        # Extract delivery data
        my_orders = account_data.get('myOrdersViewModel', {})
        one_click = my_orders.get('OneClickOrderViewModel', {}) if my_orders else {}
        
        last_delivery_date_raw = one_click.get('LastDeliveryDate', '') if one_click else ''
        last_delivery_gallons = safe_float(one_click.get('LastDeliveredGallons'), 0.0) if one_click else 0.0
        
        # Parse dates
        last_tank_reading = parse_date(account_data.get('TMReadDate', ''))
        last_delivery_date = parse_date(last_delivery_date_raw)
        
        # Next delivery date - check open orders first, then fall back
        next_delivery_date_raw = None
        if my_orders:
            open_orders = my_orders.get('LstOpenOrders', [])
            if open_orders and len(open_orders) > 0:
                # 1. Primary: firm end of delivery window
                next_delivery_date_raw = open_orders[0].get('estDeliveryWindowTo')
                # 2. Start of delivery window
                if not next_delivery_date_raw:
                    next_delivery_date_raw = open_orders[0].get('estDeliveryWindowFrom')
                # 3. General order date if window not set
                if not next_delivery_date_raw:
                    next_delivery_date_raw = open_orders[0].get('orderDate')
        
        # 4. OneClick fallback
        if not next_delivery_date_raw and one_click:
            next_delivery_date_raw = one_click.get('NextDeliveryDate')
        
        # 5. Account level final fallback
        if not next_delivery_date_raw and account_data:
            next_delivery_date_raw = account_data.get('NextDeliveryDate', '')
        
        next_delivery_date = parse_date(next_delivery_date_raw)
        
        # Build service address
        street = account_data.get('Street', '')
        city = account_data.get('City', '')
        state_code = account_data.get('State', '')
        zip_code = account_data.get('Zip', '')
        service_address = f"{street}, {city}, {state_code} {zip_code}" if all([street, city, state_code, zip_code]) else None
        
        return {
            # Tank Info
            'tank_level': safe_int(account_data.get('ForecastTankLevel'), 0),
            'tank_size': safe_int(account_data.get('TankSize'), 0),
            'days_remaining': safe_int(account_data.get('RunOutDays'), 0),
            
            # Financial
            'amount_due': safe_float(account_data.get('AmounDue'), 0.0),
            'account_balance': safe_float(account_data.get('AccountBalance'), 0.0),
            'last_payment_date': account_data.get('LastPaymentDate'),
            'last_payment_amount': safe_float(account_data.get('LastPaymentAmount'), 0.0),
            
            # Tank Monitor
            'last_tank_reading': last_tank_reading,
            'tank_monitor': 'Yes' if account_data.get('TankMonitor') == '1' else 'No',
            
            # Delivery
            'last_delivery_date': last_delivery_date,
            'last_delivery_gallons': last_delivery_gallons,
            'next_delivery_date': next_delivery_date,
            
            # Account Settings
            'auto_pay': account_data.get('AutoPayment', 'Unknown'),
            'paperless': account_data.get('Paperless', 'Unknown'),
            'account_number': account_data.get('ShipToAccount', 'Unknown'),
            
            # Address
            'service_address': service_address,
            'street': street,
            'city': city,
            'state': state_code,
            'zip': zip_code,
            
            # Metadata
            'delivery_type': account_data.get('ForecastLongName', 'Unknown'),
            'payment_terms': account_data.get('PaymentTermsUpDate', 'Unknown'),
        }
