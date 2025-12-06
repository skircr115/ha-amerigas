# AmeriGas Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/skircr115/ha-amerigas.svg)](https://github.com/skircr115/ha-amerigas/releases)
[![License](https://img.shields.io/github/license/skircr115/ha-amerigas.svg)](LICENSE)

> **Unofficial** Home Assistant integration for monitoring your AmeriGas propane account. Track tank levels, deliveries, payments, and integrate with the Energy Dashboard.

## ✨ Features

- 🔥 **Real-time Tank Monitoring** - Current level, gallons remaining, days until empty
- 🚚 **Delivery Tracking** - Last/next delivery dates, gallons delivered
- 💰 **Payment Information** - Amount due, account balance, payment history
- 📊 **Usage Analytics** - Daily/monthly/yearly consumption and costs
- ⚡ **Energy Dashboard** - Full integration with Home Assistant Energy Dashboard (v2.0.0+ fixes spikes and statistics errors)
- 🔔 **Smart Alerts** - Low propane, high usage, payment due notifications
- 📈 **Cost Tracking** - Per-gallon pricing, estimated refill costs
- 📉 **Lifetime Tracking** - NEW in v2.0.0: Permanent consumption tracking that never resets

## 🆕 What's New in v2.0.0

### Major Energy Dashboard Improvements

**Problem Solved:** Previous versions had issues with Energy Dashboard integration:
- Time-triggered updates caused data spikes
- Statistics errors from incorrect `state_class` values
- Data corruption on long-term energy tracking

**Solution in v2.0.0:**
- **State-triggered "ratchet" mechanism** - Updates only when tank level actually changes
- **Lifetime tracking sensors** - Never reset, only increase
- **Proper `state_class` attributes** - Fixes Home Assistant validation warnings

### New Lifetime Tracking Sensors (2)

| Sensor | Description | Purpose |
|--------|-------------|---------|
| `sensor.propane_lifetime_gallons` | Total gallons consumed (lifetime) | Tracks all consumption since installation |
| `sensor.propane_lifetime_energy` | Total ft³ consumed (lifetime) | **PRIMARY sensor for Energy Dashboard** |

**How it works:**
- Monitors `sensor.propane_tank_gallons_remaining` for changes
- When tank level drops (consumption): adds the difference to lifetime total
- When tank level rises (delivery/thermal expansion): keeps lifetime total unchanged
- Result: Clean, spike-free data perfect for Energy Dashboard

### Energy Dashboard Migration Required

⚠️ **IMPORTANT:** If upgrading from v1.x, you MUST update your Energy Dashboard configuration:

**Old (v1.x):** 
- Gas Source: `sensor.propane_energy_consumption` (resets after each delivery, causes issues)

**New (v2.0.0):**
- Gas Source: `sensor.propane_lifetime_energy` (never resets, reliable long-term tracking)

### Bug Fixes & Improvements

✅ **Fixed:**
1. Energy Dashboard spikes from time-triggered updates
2. Statistics errors from incorrect `state_class` values
3. Datetime parsing errors (proper timezone handling)
4. Negative usage values from thermal expansion
5. Template sensor YAML errors from inline comments
6. Monetary device class warnings
7. Missing `state_class` on static sensors

✅ **Improved:**
- Added `state_class: measurement` to `amerigas_tank_size`, `last_payment_amount`, `last_delivery_gallons`
- Better null/unknown value handling in all template sensors
- Proper availability conditions on all sensors
- ISO format datetime parsing with timezone support
- Thermal expansion logic (prevents negative consumption)

### Breaking Changes

⚠️ **Energy Dashboard Source Change Required**
- You MUST change your Energy Dashboard gas source from `sensor.propane_energy_consumption` to `sensor.propane_lifetime_energy`
- The old sensor still exists for display purposes but should NOT be used for Energy Dashboard

⚠️ **Cost Utility Meters Removed**
- Removed: `daily_propane_cost`, `monthly_propane_cost`, `yearly_propane_cost`
- Reason: Incompatible with delivery reset behavior
- Replacement: Use `sensor.propane_cost_since_last_delivery` for cost tracking

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Sensors](#sensors)
- [Energy Dashboard](#energy-dashboard)
- [Migration Guide (v1.x to v2.0.0)](#migration-guide-v1x-to-v200)
- [Dashboard Cards](#dashboard-cards)
- [Automations](#automations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Prerequisites

- Home Assistant Core 2023.1 or later
- [Pyscript](https://github.com/custom-components/pyscript) installed via HACS
- Active MyAmeriGas online account
- AmeriGas propane service with tank monitoring (optional, but recommended)

## 🚀 Installation

### Method 1: Manual Installation

1. **Install Pyscript via HACS**
   - Go to HACS → Integrations
   - Click "Explore & Download Repositories"
   - Search for "Pyscript Python scripting"
   - Install and restart Home Assistant

2. **Create Directory Structure**
   ```bash
   mkdir -p config/pyscript
   ```

3. **Download Files**
   - Download [`amerigas.py`](pyscript/amerigas.py) to `config/pyscript/`
   - Download [`template_sensors.yaml`](template_sensors.yaml) to `config/`
   - Download [`utility_meter.yaml`](utility_meter.yaml) to `config/`

4. **Update `configuration.yaml`**
   ```yaml
   pyscript:
     allow_all_imports: true
     hass_is_global: true
     apps:
       amerigas:
         username: "your_email@example.com"
         password: "your_password"
   
   template: !include template_sensors.yaml
   utility_meter: !include utility_meter.yaml
   ```

5. **Restart Home Assistant**

### Method 2: Git Clone

```bash
cd config
git clone https://github.com/skircr115/ha-amerigas.git
cp ha-amerigas/pyscript/amerigas.py pyscript/
cp ha-amerigas/template_sensors.yaml .
cp ha-amerigas/utility_meter.yaml .
```

Then update `configuration.yaml` as shown above.

## ⚙️ Configuration

### Basic Configuration

Add to your `configuration.yaml`:

```yaml
pyscript:
  allow_all_imports: true
  hass_is_global: true
  apps:
    amerigas:
      username: "your_email@example.com"
      password: "your_password"

template: !include template_sensors.yaml
utility_meter: !include utility_meter.yaml
```

⚠️ **Security Note:** Credentials must be in `configuration.yaml` under `pyscript:`. Pyscript cannot access `secrets.yaml` directly.

### Optional: Disable Auto-Updates

To disable automatic updates, comment out in `pyscript/amerigas.py`:

```python
# @time_trigger("cron(0 */6 * * *)")
# async def amerigas_scheduled():
#     """Run update every 6 hours"""
#     ...
```

## 📊 Sensors

### AmeriGas Portal Sensors (15)

| Sensor | Description | Unit | State Class |
|--------|-------------|------|-------------|
| `sensor.amerigas_tank_level` | Current tank percentage | % | measurement |
| `sensor.amerigas_tank_size` | Tank capacity | gal | measurement |
| `sensor.amerigas_days_remaining` | AmeriGas estimate | days | measurement |
| `sensor.amerigas_amount_due` | Current bill amount | $ | total |
| `sensor.amerigas_account_balance` | Account balance | $ | total |
| `sensor.amerigas_last_payment_date` | Last payment date | timestamp | - |
| `sensor.amerigas_last_payment_amount` | Last payment amount | $ | measurement |
| `sensor.amerigas_last_tank_reading` | Last monitor reading | timestamp | - |
| `sensor.amerigas_last_delivery_date` | Last delivery date | timestamp | - |
| `sensor.amerigas_last_delivery_gallons` | Gallons delivered | gal | measurement |
| `sensor.amerigas_next_delivery_date` | Next scheduled delivery | timestamp | - |
| `sensor.amerigas_auto_pay` | Auto pay status | text | - |
| `sensor.amerigas_paperless` | Paperless billing status | text | - |
| `sensor.amerigas_account_number` | Account number | text | - |
| `sensor.amerigas_service_address` | Service address | text | - |

### Calculated Sensors (11 + 2 New)

| Sensor | Description | Unit | State Class |
|--------|-------------|------|-------------|
| `sensor.propane_tank_gallons_remaining` | Gallons left in tank | gal | measurement |
| `sensor.propane_used_since_last_delivery` | Gallons consumed since last delivery | gal | total |
| `sensor.propane_energy_consumption` | Consumption in ft³ (display only) | ft³ | total |
| `sensor.propane_daily_average_usage` | Daily usage rate | gal/day | measurement |
| `sensor.propane_days_until_empty` | Your estimate based on usage | days | measurement |
| `sensor.propane_cost_per_gallon` | Price per gallon | $/gal | measurement |
| `sensor.propane_cost_per_cubic_foot` | Price per cubic foot | $/ft³ | measurement |
| `sensor.propane_cost_since_last_delivery` | Current period cost | $ | total |
| `sensor.propane_estimated_refill_cost` | Estimated next fill cost | $ | measurement |
| `sensor.propane_days_since_last_delivery` | Days since last fill | days | - |
| `sensor.propane_days_remaining_difference` | Comparison vs AmeriGas | days | - |
| **NEW: `sensor.propane_lifetime_gallons`** | **Total gallons consumed (lifetime)** | **gal** | **total_increasing** |
| **NEW: `sensor.propane_lifetime_energy`** | **Total ft³ consumed (for Energy Dashboard)** | **ft³** | **total_increasing** |

### Utility Meters (6)

**Gallons Tracking:**
- `sensor.daily_propane_gallons`
- `sensor.monthly_propane_gallons`
- `sensor.yearly_propane_gallons`

**Energy Dashboard (ft³):**
- `sensor.daily_propane_energy`
- `sensor.monthly_propane_energy`
- `sensor.yearly_propane_energy`

> **Note:** Cost utility meters have been removed in v2.0.0. Use `sensor.propane_cost_since_last_delivery` for cost tracking instead.

## ⚡ Energy Dashboard

### Setup (v2.0.0+)

1. **Add Gas Source**
   - Go to Settings → Dashboards → Energy
   - Click "Add Gas Source"
   - Select: **`Propane Lifetime Energy`** (NOT `Propane Energy Consumption`)

2. **Add Cost Tracking**
   - Click on the gas source you added
   - Under "Use an entity tracking the total costs"
   - Select: `Propane Cost Since Last Delivery`

### Result

Your Energy Dashboard will show:
- 📊 Daily/Monthly/Yearly propane consumption (no spikes!)
- 💰 Cost tracking and trends
- 📈 Comparison with electricity usage
- 🔥 Total BTU/energy consumption
- ✅ Clean, reliable long-term statistics

### Important Notes

**v2.0.0 Changes:**
- ✅ **Use `sensor.propane_lifetime_energy`** for Energy Dashboard (never resets, reliable)
- ⚠️ **DO NOT use `sensor.propane_energy_consumption`** for Energy Dashboard (resets after delivery, for display only)
- ✅ The "ratchet" mechanism ensures only actual consumption is tracked
- ✅ Deliveries and thermal expansion don't create false consumption spikes
- ✅ Proper `state_class: total_increasing` prevents statistics errors

**How Lifetime Tracking Works:**
```
Tank level drops (consumption) → Add to lifetime total
Tank level rises (delivery/heat) → Keep lifetime total unchanged
Result: Monotonically increasing value perfect for Energy Dashboard
```

![Energy Dashboard](https://via.placeholder.com/800x400?text=Energy+Dashboard+Screenshot)

## 🔄 Migration Guide (v1.x to v2.0.0)

### Step 1: Backup Your Configuration
```bash
cp config/pyscript/amerigas.py config/pyscript/amerigas.py.backup
cp config/template_sensors.yaml config/template_sensors.yaml.backup
```

### Step 2: Update Files
1. Replace `pyscript/amerigas.py` with new version
2. Replace `template_sensors.yaml` with new version
3. Update `utility_meter.yaml` (cost meters removed)

### Step 3: Update Energy Dashboard
1. Go to Settings → Dashboards → Energy
2. Click on your existing propane gas source
3. Change source sensor from `sensor.propane_energy_consumption` to `sensor.propane_lifetime_energy`
4. Save changes

### Step 4: Reload & Restart
```
Developer Tools → YAML → Reload "Pyscript Python scripting"
Developer Tools → YAML → Reload "Template Entities"
Settings → System → Restart Home Assistant
```

### Step 5: Verify
1. Check all sensors are available
2. Verify `sensor.propane_lifetime_gallons` and `sensor.propane_lifetime_energy` exist
3. Monitor Energy Dashboard for clean data (no spikes)
4. Check logs for any errors

### What to Expect
- Lifetime sensors start at 0 and build up over time
- Energy Dashboard will show clean, monotonically increasing data
- No more statistics errors or unit change warnings
- Historical data from v1.x remains intact

### Rollback (if needed)
```bash
cp config/pyscript/amerigas.py.backup config/pyscript/amerigas.py
cp config/template_sensors.yaml.backup config/template_sensors.yaml
# Restart Home Assistant
# Change Energy Dashboard back to sensor.propane_energy_consumption
```

## 🎨 Dashboard Cards

### Tank Status Gauge

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
      - entity: sensor.amerigas_days_remaining
        name: Days Left (AmeriGas)
      - entity: sensor.propane_days_until_empty
        name: Days Left (Your Usage)
      - entity: sensor.amerigas_last_tank_reading
        name: Last Reading
```

### Usage & Costs Card

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

### NEW: Lifetime Tracking Card (v2.0.0+)

```yaml
type: entities
title: Lifetime Propane Consumption
entities:
  - entity: sensor.propane_lifetime_gallons
    name: Total Gallons Consumed
    icon: mdi:gas-station
  - entity: sensor.propane_lifetime_energy
    name: Total Energy (ft³)
    icon: mdi:fire
  - type: divider
  - entity: sensor.yearly_propane_gallons
    name: This Year
  - entity: sensor.monthly_propane_gallons
    name: This Month
  - entity: sensor.daily_propane_gallons
    name: Today
```

### Account Information Card

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
```

### Quick Update Button

```yaml
type: button
name: Update AmeriGas Data
icon: mdi:refresh
tap_action:
  action: call-service
  service: pyscript.amerigas_update
```

## 🔔 Automations

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

[More automation examples →](docs/AUTOMATIONS.md)

## 🔧 Troubleshooting

### Sensors Show "Unavailable"

**Check Pyscript Status:**
```
Settings → Devices & Services → Pyscript
```

**Verify Credentials:**
- Check `configuration.yaml` has correct username/password under `pyscript: > apps: > amerigas:`
- Test login at https://www.myamerigas.com

**Check Logs:**
```
Settings → System → Logs
Search for: "AmeriGas"
```

**Manual Update:**
```
Developer Tools → Services
Service: pyscript.amerigas_update
Call Service
```

### Lifetime Sensors Not Updating (v2.0.0+)

**Problem:** `sensor.propane_lifetime_gallons` or `sensor.propane_lifetime_energy` stuck at 0 or not changing

**Causes:**
1. Tank level hasn't actually changed (sensors only update on consumption)
2. Tank level sensor is unavailable
3. Template sensors haven't reloaded

**Solution:**
```
Developer Tools → YAML → Reload "Template Entities"
Wait for actual consumption (tank level to drop)
Check: Developer Tools → States → sensor.propane_tank_gallons_remaining
```

### Energy Dashboard Not Showing Propane (v2.0.0+)

**Verify you're using the correct sensor:**
```
Developer Tools → States → sensor.propane_lifetime_energy
```

Should have:
- `device_class: gas` ✓
- `state_class: total_increasing` ✓ (NOT `total`)
- `unit_of_measurement: ft³` ✓

**Check for statistics errors:**
```
Developer Tools → Statistics
Search for: propane_lifetime_energy
```

### Common v2.0.0 Warnings

**Warning: "Entity sensor.daily_propane_gallons is using native unit of measurement 'gal' which is not a valid unit for the device class ('gas')"**

**Solution:** This is expected. Gallon utility meters are for display only and don't have `device_class: gas`. Only the ft³ sensors need that device class. You can safely ignore this warning or remove the `device_class` from the utility meter configuration if it bothers you.

**Warning: Unit changed from 'gal' to 'ft³'** (during migration)

**Solution:** This happens when switching Energy Dashboard from the old sensor to new sensor. Click "Fix issue" in Developer Tools → Statistics and confirm the change.

### Login Fails

- Verify credentials work on MyAmeriGas website
- Check for special characters in password (may need quotes)
- Review error messages in logs

### Template Sensor Errors

- Ensure `template_sensors.yaml` is included in `configuration.yaml`
- Check YAML syntax with: `Developer Tools → YAML → Check Configuration`
- Reload templates: `Developer Tools → YAML → Reload Template Entities`

[Full troubleshooting guide →](docs/TROUBLESHOOTING.md)

## 📝 How It Works

### v2.0.0 Architecture

1. **Pyscript** logs into your MyAmeriGas account every 6 hours
2. **Scrapes** the dashboard HTML for account data
3. **Parses** JavaScript variables containing account information
4. **Creates** 15 base sensors with data from AmeriGas portal
5. **Template sensors** calculate usage, costs, and conversions
6. **State-triggered sensors** maintain lifetime tracking (THE RATCHET)
7. **Utility meters** track daily/monthly/yearly consumption
8. **Energy Dashboard** displays clean, spike-free propane data

### Data Flow

```
MyAmeriGas Portal
       ↓
  Pyscript (amerigas.py)
       ↓
  15 Base Sensors
       ↓
  Template Sensors (calculations)
       ↓
  State-Triggered Sensors (lifetime tracking)
       ↓
  Utility Meters (time-based tracking)
       ↓
  Energy Dashboard (clean, reliable data)
```

### The "Ratchet" Mechanism (v2.0.0+)

**Problem:** Time-triggered updates caused spikes in Energy Dashboard

**Solution:** State-triggered updates that only track actual consumption

```python
Trigger: sensor.propane_tank_gallons_remaining changes

If current_level < previous_level:
    # Consumption occurred
    lifetime_total += (previous - current)
    
Else if current_level >= previous_level:
    # Delivery or thermal expansion
    lifetime_total stays the same (no change)

Result: Monotonically increasing value, perfect for Energy Dashboard
```

### Consumption Calculation Logic

**Since Last Delivery (Resets):**
```
Assumes tank filled to 80% capacity
Used = (Tank_Size × 0.8) - Current_Remaining
If negative (overfill/heat expansion): Show 0
```

**Lifetime Tracking (Never Resets):**
```
Only adds when tank level drops
Ignores deliveries and thermal expansion
Builds permanent consumption record
```

This properly handles:
- Full tank refills
- Partial refills
- Thermal expansion (hot days)
- Tank overfills
- Multiple deliveries

## 🔐 Security & Privacy

⚠️ **Important Security Notes:**

- Credentials are stored in plain text in `configuration.yaml`
- This integration scrapes the MyAmeriGas website (no official API)
- Data is processed locally on your Home Assistant instance
- No data is sent to third parties

**Recommendations:**
- Set appropriate file permissions: `chmod 600 configuration.yaml`
- Ensure Home Assistant is not exposed without authentication
- Use strong, unique credentials
- Consider a dedicated AmeriGas account for monitoring
- Regularly rotate your password

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

### Ways to Contribute

- 🐛 Report bugs via [GitHub Issues](https://github.com/skircr115/ha-amerigas/issues)
- 💡 Suggest features or improvements
- 📖 Improve documentation
- 🎨 Share your dashboard cards
- 🔔 Submit automation examples
- 🔧 Submit pull requests

### Development Setup

```bash
git clone https://github.com/skircr115/ha-amerigas.git
cd ha-amerigas
# Make your changes
# Test thoroughly
# Submit PR
```

## 📚 Additional Resources

- [Home Assistant Pyscript Documentation](https://hacs-pyscript.readthedocs.io/)
- [Home Assistant Energy Dashboard](https://www.home-assistant.io/docs/energy/)
- [Template Sensor Documentation](https://www.home-assistant.io/integrations/template/)
- [Utility Meter Documentation](https://www.home-assistant.io/integrations/utility_meter/)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=skircr115/ha-amerigas&type=Date)](https://star-history.com/#skircr115/ha-amerigas&Date)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**This is an unofficial integration and is not affiliated with, endorsed by, or connected to AmeriGas.**

- Use at your own risk
- Always verify propane levels manually
- Follow AmeriGas safety guidelines
- This integration relies on web scraping and may break if AmeriGas changes their website
- The developers are not responsible for any issues arising from use of this integration

## 🙏 Acknowledgments

- Built for the [Home Assistant](https://www.home-assistant.io/) community
- Powered by [Pyscript](https://github.com/custom-components/pyscript)
- Inspired by the need for better propane monitoring
- Thanks to all contributors and users! (@Ricket and others)
- Special thanks to the community for reporting Energy Dashboard issues that led to v2.0.0 improvements

## 💬 Support

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/skircr115/ha-amerigas/issues)
- 💡 **Feature Requests:** [GitHub Discussions](https://github.com/skircr115/ha-amerigas/discussions)
- 💬 **Community:** [Home Assistant Forum](https://community.home-assistant.io/)

---

<div align="center">

**If this integration helped you, please ⭐ star the repo!**

Made with ❤️ for the Home Assistant community

[Report Bug](https://github.com/skircr115/ha-amerigas/issues) · [Request Feature](https://github.com/skircr115/ha-amerigas/issues) · [Discussions](https://github.com/skircr115/ha-amerigas/discussions)

</div>