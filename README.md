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
- ⚡ **Energy Dashboard** - Full integration with Home Assistant Energy Dashboard
- 🔔 **Smart Alerts** - Low propane, high usage, payment due notifications
- 📈 **Cost Tracking** - Per-gallon pricing, estimated refill costs

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Sensors](#sensors)
- [Energy Dashboard](#energy-dashboard)
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

| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.amerigas_tank_level` | Current tank percentage | % |
| `sensor.amerigas_tank_size` | Tank capacity | gal |
| `sensor.amerigas_days_remaining` | AmeriGas estimate | days |
| `sensor.amerigas_amount_due` | Current bill amount | $ |
| `sensor.amerigas_account_balance` | Account balance | $ |
| `sensor.amerigas_last_payment_date` | Last payment date | timestamp |
| `sensor.amerigas_last_payment_amount` | Last payment amount | $ |
| `sensor.amerigas_last_tank_reading` | Last monitor reading | timestamp |
| `sensor.amerigas_last_delivery_date` | Last delivery date | timestamp |
| `sensor.amerigas_last_delivery_gallons` | Gallons delivered | gal |
| `sensor.amerigas_next_delivery_date` | Next scheduled delivery | timestamp |
| `sensor.amerigas_auto_pay` | Auto pay status | text |
| `sensor.amerigas_paperless` | Paperless billing status | text |
| `sensor.amerigas_account_number` | Account number | text |
| `sensor.amerigas_service_address` | Service address | text |

### Calculated Sensors (11)

| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.propane_tank_gallons_remaining` | Gallons left in tank | gal |
| `sensor.propane_used_since_last_delivery` | Gallons consumed since last delivery | gal |
| `sensor.propane_energy_consumption` | Consumption in cubic feet (for Energy Dashboard) | ft³ |
| `sensor.propane_daily_average_usage` | Daily usage rate | gal/day |
| `sensor.propane_days_until_empty` | Your estimate based on usage | days |
| `sensor.propane_cost_per_gallon` | Price per gallon | $/gal |
| `sensor.propane_cost_per_cubic_foot` | Price per cubic foot | $/ft³ |
| `sensor.propane_cost_since_last_delivery` | Current period cost | $ |
| `sensor.propane_estimated_refill_cost` | Estimated next fill cost | $ |
| `sensor.propane_days_since_last_delivery` | Days since last fill | days |
| `sensor.propane_days_remaining_difference` | Comparison vs AmeriGas | days |

### Utility Meters (6)

**Gallons Tracking:**
- `sensor.daily_propane_gallons`
- `sensor.monthly_propane_gallons`
- `sensor.yearly_propane_gallons`

**Energy Dashboard (ft³):**
- `sensor.daily_propane_energy`
- `sensor.monthly_propane_energy`
- `sensor.yearly_propane_energy`

> **Note:** Cost tracking is now handled through the `sensor.propane_cost_since_last_delivery` sensor which automatically tracks costs based on your consumption and the cost per gallon from your last delivery. Utility meters for costs have been removed as they were incompatible with the resetting nature of the cost sensor after each delivery.

## ⚡ Energy Dashboard

### Setup

1. **Add Gas Source**
   - Go to Settings → Dashboards → Energy
   - Click "Add Gas Source"
   - Select: `Propane Energy Consumption`

2. **Add Cost Tracking**
   - Click on the gas source you added
   - Under "Use an entity tracking the total costs"
   - Select: `Propane Cost Since Last Delivery`

### Result

Your Energy Dashboard will show:
- 📊 Daily/Monthly/Yearly propane consumption
- 💰 Cost tracking and trends
- 📈 Comparison with electricity usage
- 🔥 Total BTU/energy consumption

### Important Notes

- **Energy consumption resets after each delivery** - The `sensor.propane_energy_consumption` sensor tracks consumption since your last delivery. When you get a new delivery, it will reset and start counting from zero again.
- **Partial refills are accounted for** - If you receive a partial refill (e.g., 29 gallons instead of a full tank), the calculations properly account for the starting amount based on what was delivered plus what remained.
- **Cost tracking** - The `sensor.propane_cost_since_last_delivery` uses `state_class: total` which is appropriate for monetary tracking that resets periodically.

![Energy Dashboard](https://via.placeholder.com/800x400?text=Energy+Dashboard+Screenshot)

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

### Login Fails

- Verify credentials work on MyAmeriGas website
- Check for special characters in password (may need quotes)
- Review error messages in logs

### Template Sensor Errors

- Ensure `template_sensors.yaml` is included in `configuration.yaml`
- Check YAML syntax with: `Developer Tools → YAML → Check Configuration`
- Reload templates: `Developer Tools → YAML → Reload Template Entities`

### Energy Dashboard Not Showing Propane

**Verify sensor attributes:**
```
Developer Tools → States → sensor.propane_energy_consumption
```

Should have:
- `device_class: gas`
- `state_class: total_increasing`
- `unit_of_measurement: ft³`

**Check for statistics errors:**
```
Developer Tools → Statistics
Search for: propane_energy_consumption
```

### Cost Tracking Issues

- Ensure you have received at least one delivery
- Verify `sensor.amerigas_last_payment_amount` has a value
- Check `sensor.propane_cost_per_gallon` is calculating correctly
- Note: Cost sensors use `state_class: total` which is correct for monetary device class

### Common Warnings and How to Fix Them

**Warning: "Entity sensor.propane_cost_since_last_delivery is using state class 'measurement' which is impossible considering device class ('monetary')"**
- This has been fixed in the latest version
- Cost sensors now use `state_class: total` which is correct for monetary tracking

**Error: "could not convert string to float: '0.0\n# Comment'"**
- This indicates a YAML formatting issue with comments in template sensors
- Ensure all comments are on their own lines and not inside template blocks

[Full troubleshooting guide →](docs/TROUBLESHOOTING.md)

## 📝 How It Works

1. **Pyscript** logs into your MyAmeriGas account every 6 hours
2. **Scrapes** the dashboard HTML for account data
3. **Parses** JavaScript variables containing account information
4. **Creates** 15 sensors with data from AmeriGas portal
5. **Template sensors** calculate usage, costs, and conversions
6. **Utility meters** track daily/monthly/yearly consumption
7. **Energy Dashboard** displays propane alongside electricity

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
  Utility Meters (tracking)
       ↓
  Energy Dashboard
```

### Consumption Calculation Logic

The integration calculates consumption since your last delivery using this logic:

1. **Starting Amount** = Remaining gallons + Delivered gallons
2. **Used Amount** = Starting Amount - Current Remaining
3. **Energy Consumption** = Used Amount × 36.3888 (converts gallons to ft³)

This properly handles:
- Full tank refills
- Partial refills (e.g., 29 gallons when 80% capacity is 400 gallons)
- Tank capacity limits (calculations cap at 80% of tank size by default)

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
- Thanks to all contributors and users! (@Ricket)

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
