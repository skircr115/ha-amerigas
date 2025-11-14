# ============================================================================
# SAVE THIS AS: config/pyscript/amerigas.py
# ============================================================================

"""
AmeriGas Home Assistant Pyscript Integration
Scrapes data from AmeriGas customer portal
"""

import aiohttp
import base64
import json
import re
from datetime import datetime

# Get configuration from pyscript apps config
USERNAME = pyscript.config.get('apps', {}).get('amerigas', {}).get('username')
PASSWORD = pyscript.config.get('apps', {}).get('amerigas', {}).get('password')

# Validate configuration
if not USERNAME or not PASSWORD:
    log.error("AmeriGas: Username or password not configured in pyscript config")
    log.error("Add to configuration.yaml under pyscript: > apps: > amerigas:")


@service
async def amerigas_update():
    """
    Update all AmeriGas sensors by scraping the customer portal.
    This service can be called from automations or manually.
    """
    
    if not USERNAME or not PASSWORD:
        log.error("AmeriGas: Cannot update - credentials not configured")
        return
    
    try:
        log.info("AmeriGas: Starting update...")
        
        # Base64 encode credentials (as required by AmeriGas)
        encoded_email = base64.b64encode(USERNAME.encode()).decode()
        encoded_password = base64.b64encode(PASSWORD.encode()).decode()
        
        # Create async session
        async with aiohttp.ClientSession() as session:
            
            # Set headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # Login data
            login_data = {
                'loginViewModel[EmailAddress]': encoded_email,
                'loginViewModel[Password]': encoded_password,
                'loginViewModel[SAPErrorMessage]': ''
            }
            
            log.info("AmeriGas: Attempting login...")
            
            # Login request
            async with session.post(
                'https://www.myamerigas.com/Login/Login',
                data=login_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as login_response:
                
                if login_response.status != 200:
                    log.error(f"AmeriGas: Login failed with status {login_response.status}")
                    return
                
                # Check if login was successful
                login_result = await login_response.json()
                if not login_result.get('success'):
                    error_msg = login_result.get('message', 'Unknown error')
                    log.error(f"AmeriGas: Login failed - {error_msg}")
                    return
            
            log.info("AmeriGas: Login successful, fetching dashboard...")
            
            # Get dashboard
            async with session.get(
                'https://www.myamerigas.com/Dashboard/Dashboard',
                timeout=aiohttp.ClientTimeout(total=30)
            ) as dashboard_response:
                
                if dashboard_response.status != 200:
                    log.error(f"AmeriGas: Dashboard fetch failed with status {dashboard_response.status}")
                    return
                
                dashboard_text = await dashboard_response.text()
        
        # Parse accountSummaryViewModel from JavaScript
        pattern = r'accountSummaryViewModel\s*=\s*({.*?});'
        match = re.search(pattern, dashboard_text, re.DOTALL)
        
        if not match:
            log.error("AmeriGas: Could not find accountSummaryViewModel in page")
            return
        
        account_data = json.loads(match.group(1))
        log.info("AmeriGas: Successfully parsed account data")
        
        # Helper function to safely get and convert values
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
        
        # Extract and set sensor states
        current_time = datetime.now().isoformat()
        
        # Tank Level
        tank_level = safe_int(account_data.get('ForecastTankLevel'), 0)
        state.set(
            'sensor.amerigas_tank_level',
            tank_level,
            {
                'unit_of_measurement': '%',
                'state_class': 'measurement',
                'icon': 'mdi:propane-tank',
                'friendly_name': 'AmeriGas Tank Level',
                'tank_monitor': 'Yes' if account_data.get('TankMonitor') == '1' else 'No',
                'last_monitor_reading': account_data.get('TMReadDate', 'Unknown'),
                'delivery_type': account_data.get('ForecastLongName', 'Unknown'),
                'last_update': current_time
            }
        )
        
        # Tank Size (static value - ADDED state_class: 'measurement')
        tank_size = safe_int(account_data.get('TankSize'), 0)
        state.set(
            'sensor.amerigas_tank_size',
            tank_size,
            {
                'unit_of_measurement': 'gal',
                'icon': 'mdi:propane-tank-outline',
                'friendly_name': 'AmeriGas Tank Size',
                'device_class': 'volume_storage',
                'state_class': 'measurement', # FIXED: Added state_class
                'last_update': current_time
            }
        )
        
        # Days Remaining
        days_remaining = safe_int(account_data.get('RunOutDays'), 0)
        state.set(
            'sensor.amerigas_days_remaining',
            days_remaining,
            {
                'unit_of_measurement': 'days',
                'state_class': 'measurement',
                'icon': 'mdi:calendar-clock',
                'friendly_name': 'AmeriGas Days Remaining',
                'last_update': current_time
            }
        )
        
        # Amount Due
        amount_due = safe_float(account_data.get('AmounDue'), 0.0)
        state.set(
            'sensor.amerigas_amount_due',
            amount_due,
            {
                'unit_of_measurement': 'USD',
                'device_class': 'monetary',
                'state_class': 'total',
                'icon': 'mdi:currency-usd',
                'friendly_name': 'AmeriGas Amount Due',
                'payment_terms': account_data.get('PaymentTermsUpDate', 'Unknown'),
                'last_update': current_time
            }
        )
        
        # Account Balance
        account_balance = safe_float(account_data.get('AccountBalance'), 0.0)
        state.set(
            'sensor.amerigas_account_balance',
            account_balance,
            {
                'unit_of_measurement': 'USD',
                'device_class': 'monetary',
                'state_class': 'total',
                'icon': 'mdi:cash',
                'friendly_name': 'AmeriGas Account Balance',
                'last_update': current_time
            }
        )
        
        # Last Payment Date (no state_class for dates)
        last_payment_date = account_data.get('LastPaymentDate', 'Unknown')
        state.set(
            'sensor.amerigas_last_payment_date',
            last_payment_date,
            {
                'icon': 'mdi:calendar-check',
                'friendly_name': 'AmeriGas Last Payment Date',
                'last_update': current_time
            }
        )
        
        # Last Payment Amount (ADDED state_class: 'measurement')
        last_payment_amount = safe_float(account_data.get('LastPaymentAmount'), 0.0)
        state.set(
            'sensor.amerigas_last_payment_amount',
            last_payment_amount,
            {
                'unit_of_measurement': 'USD',
                'state_class': 'measurement', # FIXED: Added state_class
                'icon': 'mdi:credit-card',
                'friendly_name': 'AmeriGas Last Payment Amount',
                'last_update': current_time
            }
        )
        
        # Last Tank Reading (timestamp from tank monitor)
        tm_read_date = account_data.get('TMReadDate', '')
        if tm_read_date:
            # Convert from format like "2025-11-07T05:45:00" to ISO timestamp
            try:
                from datetime import datetime as dt
                # Added replace('Z', '+00:00') to handle Z-suffix for correct ISO parsing
                parsed_date = dt.fromisoformat(tm_read_date.replace('Z', '+00:00'))
                tank_reading_iso = parsed_date.isoformat()
            except:
                tank_reading_iso = tm_read_date
        else:
            tank_reading_iso = None
        
        state.set(
            'sensor.amerigas_last_tank_reading',
            tank_reading_iso,
            {
                'device_class': 'timestamp',
                'icon': 'mdi:clock-outline',
                'friendly_name': 'AmeriGas Last Tank Reading',
                'last_update': current_time
            }
        )
        
        # Last Delivery Date and Gallons
        last_delivery_date_raw = 'Unknown'
        last_delivery_gallons = 0.0
        
        my_orders = account_data.get('myOrdersViewModel', {})
        if my_orders:
            one_click = my_orders.get('OneClickOrderViewModel', {})
            if one_click:
                last_delivery_date_raw = one_click.get('LastDeliveryDate', 'Unknown')
                last_delivery_gallons = safe_float(one_click.get('LastDeliveredGallons'), 0.0)
        
        # Convert last delivery date to timestamp
        last_delivery_iso = None
        if last_delivery_date_raw and last_delivery_date_raw not in ['Unknown', '']:
            try:
                from datetime import datetime as dt
                # Try parsing common date formats
                if '/' in str(last_delivery_date_raw):
                    # Format like "06/24/25" or "06/24/2025"
                    date_parts = str(last_delivery_date_raw).split('/')
                    if len(date_parts[-1]) == 2:
                        parsed_date = dt.strptime(str(last_delivery_date_raw), '%m/%d/%y')
                    else:
                        parsed_date = dt.strptime(str(last_delivery_date_raw), '%m/%d/%Y')
                    last_delivery_iso = parsed_date.isoformat()
                else:
                    # Assume it's an ISO format date string without time
                    last_delivery_iso = str(last_delivery_date_raw)
                
                log.debug(f"AmeriGas: Last delivery date: {last_delivery_iso}")
            except Exception as e:
                log.warning(f"AmeriGas: Could not parse last delivery date '{last_delivery_date_raw}': {e}")
                last_delivery_iso = None
        
        state.set(
            'sensor.amerigas_last_delivery_date',
            # Use 'unknown' if no valid date, otherwise use the ISO timestamp
            last_delivery_iso if last_delivery_iso else 'unknown',
            {
                # device_class timestamp only if we have a valid ISO timestamp
                'device_class': 'timestamp' if last_delivery_iso else None,
                'icon': 'mdi:truck-delivery',
                'friendly_name': 'AmeriGas Last Delivery Date',
                'raw_value': last_delivery_date_raw,
                'last_update': current_time
            }
        )
        
        # Last delivery gallons (ADDED state_class: 'measurement')
        state.set(
            'sensor.amerigas_last_delivery_gallons',
            last_delivery_gallons,
            {
                'unit_of_measurement': 'gal',
                'state_class': 'measurement', # FIXED: Added state_class
                'icon': 'mdi:gas-station',
                'friendly_name': 'AmeriGas Last Delivery Gallons',
                'last_update': current_time
            }
        )
        
        # Next Delivery Date (if scheduled)
        # Check multiple possible locations in the data
        next_delivery_date = None
        
        # Try myOrdersViewModel location
        my_orders_vm = account_data.get('myOrdersViewModel', {})
        if my_orders_vm:
            # Check for open orders
            open_orders = my_orders_vm.get('LstOpenOrders', [])
            if open_orders and len(open_orders) > 0:
                # Get the first scheduled delivery
                next_delivery_date = open_orders[0].get('DeliveryDate', '')
            
            # Try OneClickOrderViewModel
            if not next_delivery_date:
                one_click = my_orders_vm.get('OneClickOrderViewModel', {})
                if one_click:
                    next_delivery_date = one_click.get('NextDeliveryDate', '')
        
        # Try top-level NextDeliveryDate
        if not next_delivery_date:
            next_delivery_date = account_data.get('NextDeliveryDate', '')
        
        # Log what we found for debugging
        log.debug(f"AmeriGas: Next delivery date raw value: {next_delivery_date}")
        log.debug(f"AmeriGas: Open orders count: {account_data.get('OpenOrdersCount', 0)}")
        
        # Convert to timestamp if available, otherwise use "None" state
        next_delivery_iso = None
        if next_delivery_date and next_delivery_date not in ['', 'Unknown', None]:
            try:
                from datetime import datetime as dt
                # Try parsing common date formats
                if '/' in str(next_delivery_date):
                    # Format like "06/24/25" or "06/24/2025"
                    date_parts = str(next_delivery_date).split('/')
                    if len(date_parts[-1]) == 2:
                        parsed_date = dt.strptime(str(next_delivery_date), '%m/%d/%y')
                    else:
                        parsed_date = dt.strptime(str(next_delivery_date), '%m/%d/%Y')
                elif 'T' in str(next_delivery_date):
                    # ISO format - Added replace('Z', '+00:00') for safety
                    parsed_date = dt.fromisoformat(str(next_delivery_date).replace('Z', '+00:00'))
                else:
                    # Try as-is (assuming YYYY-MM-DD or similar)
                    parsed_date = dt.fromisoformat(str(next_delivery_date))
                
                next_delivery_iso = parsed_date.isoformat()
                log.info(f"AmeriGas: Next delivery scheduled for {next_delivery_iso}")
            except Exception as e:
                log.warning(f"AmeriGas: Could not parse next delivery date '{next_delivery_date}': {e}")
                next_delivery_iso = None
        
        # Set sensor - will show as "unknown" if no delivery scheduled
        state.set(
            'sensor.amerigas_next_delivery_date',
            next_delivery_iso if next_delivery_iso else 'unknown',
            {
                'device_class': 'timestamp' if next_delivery_iso else None,
                'icon': 'mdi:truck-delivery',
                'friendly_name': 'AmeriGas Next Delivery Date',
                'has_scheduled_delivery': True if next_delivery_iso else False,
                'last_update': current_time
            }
        )
        
        # Auto Pay Status
        auto_pay = account_data.get('AutoPayment', 'Unknown')
        state.set(
            'sensor.amerigas_auto_pay',
            auto_pay,
            {
                'icon': 'mdi:credit-card-check',
                'friendly_name': 'AmeriGas Auto Pay',
                'last_update': current_time
            }
        )
        
        # Paperless Billing Status
        paperless = account_data.get('Paperless', 'Unknown')
        state.set(
            'sensor.amerigas_paperless',
            paperless,
            {
                'icon': 'mdi:file-document',
                'friendly_name': 'AmeriGas Paperless Billing',
                'last_update': current_time
            }
        )
        
        # Account Number
        account_number = account_data.get('ShipToAccount', 'Unknown')
        state.set(
            'sensor.amerigas_account_number',
            account_number,
            {
                'icon': 'mdi:account',
                'friendly_name': 'AmeriGas Account Number',
                'last_update': current_time
            }
        )
        
        # Service Address
        street = account_data.get('Street', '')
        city = account_data.get('City', '')
        state_code = account_data.get('State', '')
        zip_code = account_data.get('Zip', '')
        
        service_address = f"{street}, {city}, {state_code} {zip_code}" if all([street, city, state_code, zip_code]) else 'Unknown'
        state.set(
            'sensor.amerigas_service_address',
            service_address,
            {
                'icon': 'mdi:home-map-marker',
                'friendly_name': 'AmeriGas Service Address',
                'street': street,
                'city': city,
                'state': state_code,
                'zip': zip_code,
                'last_update': current_time
            }
        )
        
        log.info(f"AmeriGas: Successfully updated all sensors - Tank: {tank_level}%, Days: {days_remaining}")
        
        # Fire event for successful update
        task.executor(
            hass.bus.fire,
            'amerigas_update_complete',
            {
                'tank_level': tank_level,
                'days_remaining': days_remaining,
                'amount_due': amount_due
            }
        )

    except aiohttp.ClientError as e:
        log.error(f"AmeriGas: Network error - {str(e)}")
    except json.JSONDecodeError as e:
        log.error(f"AmeriGas: JSON parsing error - {str(e)}")
    except Exception as e:
        log.error(f"AmeriGas: Unexpected error - {str(e)}")


# Auto-run on startup (optional)
@time_trigger("startup")
async def amerigas_startup():
    """Run update when Home Assistant starts"""
    log.info("AmeriGas: Running initial update on startup")
    await task.sleep(30)  # Wait 30 seconds for HA to fully start
    await amerigas_update()


# Auto-run every 6 hours (optional - comment out if using automation instead)
@time_trigger("cron(0 */6 * * *)")
async def amerigas_scheduled():
    """Run update every 6 hours"""
    log.info("AmeriGas: Running scheduled update")
    await amerigas_update()