"""Constants for the AmeriGas integration."""
from typing import Final

DOMAIN: Final = "amerigas"

# Configuration
CONF_SCAN_INTERVAL: Final = "scan_interval"
DEFAULT_SCAN_INTERVAL: Final = 6  # hours

# API Constants
API_LOGIN_URL: Final = "https://www.myamerigas.com/Login/Login"
API_DASHBOARD_URL: Final = "https://www.myamerigas.com/Dashboard/Dashboard"
API_TIMEOUT: Final = 45 #seconds; increase if you have a slow connection (or AmeriGas is slow)

# Sensor Keys
TANK_LEVEL: Final = "tank_level"
TANK_SIZE: Final = "tank_size"
DAYS_REMAINING: Final = "days_remaining"
AMOUNT_DUE: Final = "amount_due"
ACCOUNT_BALANCE: Final = "account_balance"
LAST_PAYMENT_DATE: Final = "last_payment_date"
LAST_PAYMENT_AMOUNT: Final = "last_payment_amount"
LAST_TANK_READING: Final = "last_tank_reading"
LAST_DELIVERY_DATE: Final = "last_delivery_date"
LAST_DELIVERY_GALLONS: Final = "last_delivery_gallons"
NEXT_DELIVERY_DATE: Final = "next_delivery_date"
AUTO_PAY: Final = "auto_pay"
PAPERLESS: Final = "paperless"
ACCOUNT_NUMBER: Final = "account_number"
SERVICE_ADDRESS: Final = "service_address"

# Calculated Sensor Keys
GALLONS_REMAINING: Final = "gallons_remaining"
USED_SINCE_DELIVERY: Final = "used_since_delivery"
ENERGY_CONSUMPTION: Final = "energy_consumption"
DAILY_AVERAGE_USAGE: Final = "daily_average_usage"
DAYS_UNTIL_EMPTY: Final = "days_until_empty"
COST_PER_GALLON: Final = "cost_per_gallon"
COST_PER_CUBIC_FOOT: Final = "cost_per_cubic_foot"
COST_SINCE_DELIVERY: Final = "cost_since_delivery"
ESTIMATED_REFILL_COST: Final = "estimated_refill_cost"
DAYS_SINCE_DELIVERY: Final = "days_since_delivery"
DAYS_REMAINING_DIFFERENCE: Final = "days_remaining_difference"

# Lifetime Tracking
LIFETIME_GALLONS: Final = "lifetime_gallons"
LIFETIME_ENERGY: Final = "lifetime_energy"

# Conversion Constants
GALLONS_TO_CUBIC_FEET: Final = 36.3888
DEFAULT_FILL_PERCENTAGE: Final = 0.8
DEFAULT_TANK_SIZE: Final = 500
NOISE_THRESHOLD_GALLONS: Final = 0.5
