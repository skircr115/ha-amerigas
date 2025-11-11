# AmeriGas Home Assistant Integration - Complete Package

A complete Home Assistant integration for monitoring your AmeriGas propane account, including tank level, delivery history, payments, and Energy Dashboard integration.

## 📋 Features

- **Real-time Tank Monitoring** - Current tank level, gallons remaining, days until empty
- **Delivery Tracking** - Last delivery date, gallons delivered, next scheduled delivery
- **Payment Information** - Amount due, account balance, last payment details
- **Cost Analysis** - Cost per gallon, estimated refill cost, usage rates
- **Energy Dashboard Integration** - Track propane consumption alongside electricity
- **Automated Updates** - Auto-refresh every 6 hours + on Home Assistant startup

## 📦 What's Included

- 15 sensors from AmeriGas portal
- 8 calculated template sensors for usage tracking
- 9 utility meters (daily/monthly/yearly for gallons, energy, and cost)
- Energy Dashboard ready with cost tracking
- Example automations and dashboard cards

---

## 🚀 Installation

### Prerequisites

1. **Pyscript** - Install via HACS
   - Go to HACS > Integrations
   - Search for "Pyscript Python scripting"
   - Install and restart Home Assistant

2. **AmeriGas Account** - Active MyAmeriGas online account credentials

### Step 1: Enable Pyscript

Add to `configuration.yaml`:

```yaml
pyscript:
  allow_all_imports: true
  hass_is_global: true
  apps:
    amerigas:
      username: "your_email@example.com"
      password: "your_password_here"
```

⚠️ **Important:** Credentials must be in `configuration.yaml` under `pyscript:`, NOT in `secrets.yaml`

### Step 2: Create Directory Structure

```
config/
├── pyscript/
│   └── amerigas.py
├── template_sensors.yaml
├── utility_meter.yaml
└── configuration.yaml
```

### Step 3: Install/Update Files provided in this repository

### Step 4: Restart Home Assistant

After all files are in place:
1. Go to **Settings > System > Restart**
2. Wait for restart to complete

---

## ✅ Verify Installation

### Check Sensors
Go to **Developer Tools > States** and search for "amerigas" - you should see 15 sensors:

**AmeriGas Portal Sensors:**
- `sensor.amerigas_tank_level` - Current tank percentage
- `sensor.amerigas_tank_size` - Tank capacity in gallons
- `sensor.amerigas_days_remaining` - AmeriGas's estimate
- `sensor.amerigas_amount_due` - Current bill amount
- `sensor.amerigas_account_balance` - Account balance
- `sensor.amerigas_last_payment_date` - Last payment date
- `sensor.amerigas_last_payment_amount` - Last payment amount
- `sensor.amerigas_last_tank_reading` - Last monitor reading timestamp
- `sensor.amerigas_last_delivery_date` - Last delivery date
- `sensor.amerigas_last_delivery_gallons` - Gallons delivered
- `sensor.amerigas_next_delivery_date` - Next scheduled delivery (if any)
- `sensor.amerigas_auto_pay` - Auto pay status
- `sensor.amerigas_paperless` - Paperless billing status
- `sensor.amerigas_account_number` - Your account number
- `sensor.amerigas_service_address` - Service address

**Calculated Sensors:**
- `sensor.propane_tank_gallons_remaining` - Gallons left in tank
- `sensor.propane_used_since_last_delivery` - Gallons consumed
- `sensor.propane_energy_consumption` - Consumption in ft³ (Energy Dashboard)
- `sensor.propane_daily_average_usage` - Usage rate (gal/day)
- `sensor.propane_days_until_empty` - Your estimate based on usage
- `sensor.propane_cost_per_gallon` - $/gallon from last delivery
- `sensor.propane_cost_per_cubic_foot` - $/ft³ for Energy Dashboard
- `sensor.propane_cost_since_last_delivery` - Current cost

### Manual Update
Call the service to fetch data:
1. Go to **Developer Tools > Services**
2. Select service: `pyscript.amerigas_update`
3. Click **Call Service**

Check logs at **Settings > System > Logs** - search for "AmeriGas"

---

## 📊 Energy Dashboard Setup

### Add Gas Source
1. Go to **Settings > Dashboards > Energy**
2. Click **"Add Gas Source"**
3. Select: **`Propane Energy Consumption`**
4. Optional: Add cost tracking
   - Select: **`Propane Cost Since Last Delivery`**
   - Or enter fixed price per ft³

### View in Energy Dashboard
Your propane consumption will now appear alongside electricity in the Energy Dashboard with:
- 📈 Consumption graphs
- 💰 Cost tracking
- 📊 Historical comparisons
- 🔥 Daily/Monthly/Yearly totals

---

## 🎨 Example Dashboard Cards

### Card 1: Tank Status

```yaml
type: vertical-stack
cards:
  - type: gauge
    entity: sensor.amerigas_tank_level
    min: 0
    max: 100
    name: Propane Tank
    severity:
      green: 40
      yellow: 20
      red: 0
  
  - type: entities
    title: Tank Details
    entities:
      - entity: sensor.propane_tank_gallons_remaining
        name: Gallons Remaining
      - entity: sensor.amerigas_tank_size
        name: Tank Capacity
      - entity: sensor.amerigas_days_remaining
        name: Days Left (AmeriGas)
      - entity: sensor.propane_days_until_empty
        name: Days Left (Your Usage)
      - entity: sensor.amerigas_last_tank_reading
        name: Last Reading
```

### Card 2: Usage & Costs

```yaml
type: entities
title: Propane Usage & Costs
entities:
  - entity: sensor.propane_used_since_last_delivery
    name: Used Since Last Fill
  - entity: sensor.propane_daily_average_usage
    name: Daily Usage Rate
  - entity: sensor.propane_days_since_last_delivery
    name: Days Since Last Fill
  - type: divider
  - entity: sensor.propane_cost_per_gallon
    name: Current Price
  - entity: sensor.propane_cost_since_last_delivery
    name: Cost This Period
  - entity: sensor.propane_estimated_refill_cost
    name: Est. Refill Cost
```

### Card 3: Account Info

```yaml
type: entities
title: AmeriGas Account
entities:
  - entity: sensor.amerigas_amount_due
    name: Amount Due
  - entity: sensor.amerigas_account_balance
    name: Account Balance
  - entity: sensor.amerigas_last_payment_date
    name: Last Payment
  - entity: sensor.amerigas_last_payment_amount
    name: Payment Amount
  - type: divider
  - entity: sensor.amerigas_last_delivery_date
    name: Last Delivery
  - entity: sensor.amerigas_last_delivery_gallons
    name: Gallons Delivered
  - entity: sensor.amerigas_next_delivery_date
    name: Next Delivery
  - type: divider
  - entity: sensor.amerigas_auto_pay
    name: Auto Pay
  - entity: sensor.amerigas_paperless
    name: Paperless Billing
  - entity: sensor.amerigas_account_number
    name: Account Number
```

### Card 4: Quick Update Button

```yaml
type: button
name: Update AmeriGas Data
icon: mdi:refresh
tap_action:
  action: call-service
  service: pyscript.amerigas_update
```

---

## 🔔 Example Automations

### Low Propane Alert

```yaml
alias: "Low Propane Alert"
description: "Alert when tank drops below 30%"
trigger:
  - platform: numeric_state
    entity_id: sensor.amerigas_tank_level
    below: 30
condition:
  - condition: template
    value_template: "{{ states('sensor.amerigas_tank_level') | int > 0 }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Low Propane Level"
      message: >
        Tank is at {{ states('sensor.amerigas_tank_level') }}%.
        {{ states('sensor.propane_tank_gallons_remaining') }} gallons remaining.
        Estimated {{ states('sensor.propane_days_until_empty') }} days left.
      data:
        importance: high
        tag: low_propane
```

### Payment Due Notification

```yaml
alias: "Payment Due Notification"
description: "Alert when payment is due and auto-pay is off"
trigger:
  - platform: numeric_state
    entity_id: sensor.amerigas_amount_due
    above: 0
condition:
  - condition: template
    value_template: "{{ states('sensor.amerigas_auto_pay') != 'On' }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "AmeriGas Payment Due"
      message: "${{ states('sensor.amerigas_amount_due') }} is due"
      data:
        actions:
          - action: URI
            title: Make Payment
            uri: https://www.myamerigas.com
```

### Propane Running Low

```yaml
alias: "Propane Running Low"
description: "Alert when less than 14 days of propane remaining"
trigger:
  - platform: numeric_state
    entity_id: sensor.propane_days_until_empty
    below: 14
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Propane Running Low"
      message: >
        Only {{ states('sensor.propane_days_until_empty') }} days remaining
        ({{ states('sensor.amerigas_tank_level') }}% / 
        {{ states('sensor.propane_tank_gallons_remaining') }} gallons).
        Daily usage: {{ states('sensor.propane_daily_average_usage') }} gal/day
      data:
        importance: high
```

### High Usage Alert

```yaml
alias: "High Propane Usage Alert"
description: "Alert when daily usage is unusually high"
trigger:
  - platform: numeric_state
    entity_id: sensor.propane_daily_average_usage
    above: 10  # Adjust threshold as needed
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "High Propane Usage Detected"
      message: >
        Daily usage is {{ states('sensor.propane_daily_average_usage') }} gal/day,
        which is higher than normal. Check for leaks or unusual consumption.
```

### Weekly Report

```yaml
alias: "Weekly Propane Report"
description: "Send weekly propane usage report"
trigger:
  - platform: time
    at: "08:00:00"
  - platform: time
    weekday: sun
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Weekly Propane Report"
      message: >
        Tank: {{ states('sensor.amerigas_tank_level') }}%
        ({{ states('sensor.propane_tank_gallons_remaining') }} gal)
        
        This week: {{ states('sensor.daily_propane_gallons') }} gallons used
        Avg usage: {{ states('sensor.propane_daily_average_usage') }} gal/day
        Days remaining: {{ states('sensor.propane_days_until_empty') }}
        
        Cost this period: ${{ states('sensor.propane_cost_since_last_delivery') }}
```

---

## 🔧 Troubleshooting

### Sensors Show "Unavailable"
1. Check Pyscript is loaded: **Settings > Devices & Services > Pyscript**
2. Check credentials in `configuration.yaml` under `pyscript: > apps: > amerigas:`
3. Check logs: **Settings > System > Logs** - search for "AmeriGas"
4. Manually run: `pyscript.amerigas_update` service

### Login Fails
- Verify credentials work on https://www.myamerigas.com
- Check for special characters in password (may need escaping in YAML)
- Look for error messages in logs

### Template Errors
- Ensure `template_sensors.yaml` is included in `configuration.yaml`
- Check for YAML syntax errors
- Reload templates: **Developer Tools > YAML > Reload Template Entities**

### Energy Dashboard Not Showing Propane
- Verify `sensor.propane_energy_consumption` has:
  - `device_class: gas`
  - `state_class: total_increasing`
  - `unit_of_measurement: ft³` (with superscript 3)
- Check **Developer Tools > Statistics** for errors

### Cost Tracking Not Working
- Ensure last payment and delivery data exists
- Check `sensor.propane_cost_per_gallon` has a value
- Verify `sensor.propane_cost_since_last_delivery` is updating

---

## 📝 Notes

- **Update Frequency:** Data updates every 6 hours automatically (configurable in script)
- **Manual Updates:** Call `pyscript.amerigas_update` service anytime
- **Tank Size:** Default is 500 gallons - adjust in templates if different
- **Conversion Factor:** 1 gallon propane = 36.3888 cubic feet
- **Next Delivery:** May show "unknown" for automatic delivery customers
- **Credentials:** Stored in `configuration.yaml` (Pyscript can't access secrets.yaml)

---

## 🔐 Security Notes

⚠️ Your AmeriGas credentials are stored in plain text in `configuration.yaml`

**To improve security:**
1. Set appropriate file permissions: `chmod 600 configuration.yaml`
2. Ensure Home Assistant is not exposed to the internet without proper authentication
3. Consider using a dedicated AmeriGas account with limited permissions
4. Regularly rotate your password

---

## 📚 Additional Resources

- **Home Assistant Pyscript Docs:** https://hacs-pyscript.readthedocs.io/
- **Home Assistant Energy Dashboard:** https://www.home-assistant.io/docs/energy/
- **Template Sensors:** https://www.home-assistant.io/integrations/template/
- **Utility Meters:** https://www.home-assistant.io/integrations/utility_meter/

---

## 🤝 Contributing

Found a bug or want to improve this integration?
- Report issues with detailed logs
- Share your dashboard cards and automations
- Suggest new features or sensors

---

## 📜 License

This integration is provided as-is for personal use. 

**Disclaimer:** This is an unofficial integration and is not affiliated with or endorsed by AmeriGas. Use at your own risk. Always verify propane levels manually and follow AmeriGas safety guidelines.

---

## 🎉 Credits

Created for the Home Assistant community. Special thanks to:
- Pyscript developers for the amazing integration
- Home Assistant community for templates and ideas
- AmeriGas customers who needed better monitoring

---

## ✨ Enjoy Your Smart Propane Monitoring!

You now have complete visibility into your propane usage, costs, and account status right in Home Assistant. Stay safe and never run out of propane again! 🔥
