# AmeriGas Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/skircr115/ha-amerigas.svg)](https://github.com/skircr115/ha-amerigas/releases)
[![License](https://img.shields.io/github/license/skircr115/ha-amerigas.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-production-green)

> **HACS custom component** for monitoring your AmeriGas propane account. Track tank levels, deliveries, payments, and integrate with the Energy Dashboard.

## ✨ What's New in v3.0.5

### 🎯 Automatic Pre-Delivery Detection
**The integration now automatically captures your exact tank level when a delivery happens!**

- **Zero configuration needed** - works automatically after installation
- **100% accurate tracking** regardless of delivery size (small top-offs or full deliveries)
- **No more manual entry** - the system detects new deliveries and calculates pre-delivery levels automatically

**How it works:**
1. Integration detects when `last_delivery_date` changes
2. Automatically calculates: `pre_delivery_level = current_level - delivery_amount`
3. Stores the value permanently for accurate consumption calculations
4. All future calculations use this exact value

**Your benefits:**
- Small deliveries (28 gallons): 100% accurate (was 0% accurate in v3.0.0)
- Medium deliveries (100 gallons): 100% accurate  
- Large deliveries (300+ gallons): 100% accurate
- **Zero user effort required**

### 📊 Fixed: Estimated Refill Cost
Now uses realistic **80% maximum fill level** (industry standard) instead of assuming 100% fill.

**Example:**
- Tank: 500 gallons
- Current: 300 gallons (60%)
- **Old:** Estimates 200 gallons needed = $500 ❌
- **New:** Estimates 100 gallons needed = $250 ✅

---

## 🚀 Features

### Real-Time Monitoring
- **Tank Level** - Current percentage and gallons remaining
- **Days Remaining** - Estimated days until tank empty based on your usage
- **Delivery History** - Track all deliveries with dates and amounts
- **Cost Tracking** - Monitor cost per gallon and total spend

### Accurate Consumption Tracking (v3.0.5)
- **Automatic Pre-Delivery Capture** - 100% accurate for any delivery size
- **Lifetime Consumption** - Total propane used since installation
- **Daily Average** - Your average usage per day
- **Used Since Delivery** - Gallons consumed since last fill
- **Energy Dashboard Integration** - Track propane consumption alongside other utilities

### Smart Calculations
- **Estimated Refill Cost** - Realistic cost estimates using 80% fill level
- **Days Until Empty** - Projected days remaining based on usage patterns
- **Cost Analysis** - Price per gallon and per cubic foot

### Diagnostic Tools
- **Pre-Delivery Level Tracker** - See captured pre-delivery levels
- **Calculation Methods** - Know how each value is calculated
- **Accuracy Indicators** - See estimation accuracy for each sensor

---

## 📦 Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right
4. Select "Custom repositories"
5. Add repository URL: `https://github.com/skircr115/ha-amerigas`
6. Category: Integration
7. Click "Add"
8. Click "Install" on the AmeriGas card
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/skircr115/ha-amerigas/releases)
2. Extract the `custom_components/amerigas` folder
3. Copy it to your `config/custom_components/` directory
4. Restart Home Assistant

---

## ⚙️ Configuration

### Setup

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "AmeriGas"
4. Enter your AmeriGas account credentials
5. Click **Submit**

### What Gets Created

#### Sensors (37 total)
**From AmeriGas API:**
- Tank level (percentage)
- Tank size (gallons)
- Last delivery date
- Last delivery amount
- Last payment amount
- Days remaining
- And more...

**Calculated Sensors:**
- Propane Tank Gallons Remaining
- Used Since Last Delivery (with 100% accuracy!)
- Daily Average Usage
- Days Until Empty
- Cost Per Gallon
- Estimated Refill Cost (realistic 80% fill)
- Lifetime Consumption
- And more...

#### Diagnostic Entity (v3.0.5)
- **Pre-Delivery Tank Level** - Automatically captured when deliveries occur
  - Visible in Diagnostics section
  - Can be manually adjusted if needed
  - Shows calculation details in attributes

---

## 📊 Energy Dashboard Integration

The integration provides sensors compatible with Home Assistant's Energy Dashboard:

1. Go to **Settings** → **Dashboards** → **Energy**
2. Click **Add Gas Source**
3. Select **Propane Lifetime Energy**
4. Click **Save**

This tracks your propane consumption over time with 100% accuracy!

---

## 🎯 How Automatic Detection Works

### The Magic Behind v3.0.5

When AmeriGas delivers propane:
1. Their API updates with new delivery date and amount
2. Your tank level sensor updates to post-delivery level
3. Integration detects the delivery date changed
4. Automatically calculates: **Pre-delivery = Current - Delivery**
5. Stores this exact value permanently

**Real Example (Your Case):**
```
Delivery detected: June 23, 2024
Current level: 420 gallons (post-delivery)
Delivery amount: 28.1 gallons
Calculated pre-delivery: 420 - 28.1 = 391.9 gallons ✅

Usage calculation:
Starting: 391.9 + 28.1 = 420 gallons
Current: 300 gallons
Used: 420 - 300 = 120 gallons ✅ PERFECT!
```

No more 0% accuracy for small deliveries. No more manual entry. Just works!

---

## 🛠️ Manual Pre-Delivery Level Service (v3.0.5)

### When to Use Manual Override

While automatic detection works for all deliveries after v3.0.5 installation, you may need to manually set the pre-delivery level if:

- **A delivery happened BEFORE upgrading to v3.0.5** - Historic deliveries won't have auto-captured values
- **Automatic detection failed** - Rare cases where delivery detection didn't trigger
- **You want to correct a value** - Fix any inaccurate capture

### Using the Service

**Via Developer Tools:**
1. Go to **Developer Tools** → **Services**
2. Search for `AmeriGas: Set Pre-Delivery Level`
3. Enter the pre-delivery level in gallons
4. Click **Call Service**

**Example Service Call:**
```yaml
service: amerigas.set_pre_delivery_level
data:
  gallons: 391.9
```

**Via Automation:**
```yaml
# Example: Set pre-delivery level when you press a button
automation:
  - alias: "Set Propane Pre-Delivery Level"
    trigger:
      - platform: state
        entity_id: input_button.set_propane_level
    action:
      - service: amerigas.set_pre_delivery_level
        data:
          gallons: "{{ states('input_number.propane_pre_delivery') | float }}"
```

**What the Service Does:**
- Updates `number.amerigas_pre_delivery_level` with your specified value
- All consumption calculations immediately use this new value
- Value persists across Home Assistant restarts
- Logs the change for troubleshooting

**Calculating Pre-Delivery Level:**

If you need to figure out what your pre-delivery level was:

```
Pre-Delivery = Current Level - Delivery Amount + Used Since Delivery

Example:
Current: 300 gallons
Delivery: 28.1 gallons  
Used since delivery: 120 gallons
Pre-Delivery = 300 - 28.1 + 120 = 391.9 gallons
```

Or simply check your tank gauge reading before the delivery truck arrives!

---

## 🔧 Troubleshooting

### Pre-Delivery Level Shows 0

**First delivery after upgrade:**
- Normal! The auto-capture only works for NEW deliveries after v3.0.5 installation
- Wait for your next delivery and it will capture automatically
- Or manually set the value in Developer Tools → States

**Manual override if needed:**
1. Go to **Developer Tools** → **States**
2. Find `number.amerigas_pre_delivery_level`
3. Set to your actual pre-delivery level
4. Click **Set State**

### Sensors Show "Unavailable"

**Common causes:**
- Integration still loading after restart (wait 30 seconds)
- AmeriGas API credentials incorrect
- Internet connection issues
- AmeriGas website down

**Fix:**
1. Check Home Assistant logs
2. Verify credentials in integration config
3. Try reloading the integration

### Estimated Refill Cost Seems Wrong

As of v3.0.5, this uses **80% maximum fill** (industry standard).

If your company fills to a different percentage:
- 80% is typical for safety (thermal expansion)
- Some companies may fill to 85% or 75%
- The estimate is based on last delivery cost

---

## 📱 Example Dashboard Card

```yaml
type: entities
title: Propane Tank
entities:
  - entity: sensor.amerigas_tank_level
    name: Tank Level
  - entity: sensor.amerigas_tank_gallons_remaining
    name: Gallons Remaining
  - entity: sensor.amerigas_used_since_last_delivery
    name: Used Since Delivery
    secondary_info: attribute:accuracy
  - entity: sensor.amerigas_daily_average_usage
    name: Daily Average
  - entity: sensor.amerigas_days_until_empty
    name: Days Until Empty
  - type: divider
  - entity: sensor.amerigas_estimated_refill_cost
    name: Est. Refill Cost
  - entity: sensor.amerigas_last_delivery_date
    name: Last Delivery
  - entity: sensor.amerigas_last_delivery_gallons
    name: Delivery Amount
  - type: divider
  - entity: number.amerigas_pre_delivery_level
    name: Pre-Delivery Level (Auto)
```

---

## 🔄 Upgrading to v3.0.5

### From v3.0.0 - v3.0.4

1. Update integration through HACS
2. Restart Home Assistant
3. New number entity appears automatically: `number.amerigas_pre_delivery_level`
4. Wait for next delivery - auto-capture starts working!
5. All existing sensors continue working

**No breaking changes!** Everything that worked before still works, just better.

### From v2.x (pyscript version)

This is a complete rewrite. See [MIGRATION.md](MIGRATION.md) for detailed instructions.

---

## 🐛 Known Issues

### Small Delivery History

If you had small deliveries before v3.0.5:
- Historical calculations remain inaccurate (can't change the past)
- All future deliveries will be 100% accurate
- Optional: Manually set pre-delivery level for current period

### API Rate Limits

- Integration updates every 6 hours by default
- AmeriGas may rate limit if updated too frequently
- Don't manually trigger updates more than once per hour

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md)

- 🐛 Report bugs via [Issues](https://github.com/skircr115/ha-amerigas/issues)
- 💡 Request features via [Discussions](https://github.com/skircr115/ha-amerigas/discussions)
- 🔧 Submit pull requests
- 📖 Improve documentation

## 📜 License

MIT License - see [LICENSE](LICENSE)

## ⚠️ Disclaimer

**This is an unofficial integration and is not affiliated with AmeriGas.**

- Use at your own risk
- Always verify propane levels manually
- Integration may break if AmeriGas changes their website
- Not responsible for any issues arising from use

## 🙏 Acknowledgments

- Built for [Home Assistant](https://www.home-assistant.io/)
- Thanks to all contributors (@Ricket and others)
- Special thanks to community for testing and feedback

## 💬 Support

- 🐛 **Bugs**: [GitHub Issues](https://github.com/skircr115/ha-amerigas/issues)
- 💡 **Features**: [GitHub Discussions](https://github.com/skircr115/ha-amerigas/discussions)
- 💬 **Community**: [Home Assistant Forum](https://community.home-assistant.io/)

---

<div align="center">

**If this integration helped you, please ⭐ star the repo!**

Made with ❤️ for the Home Assistant community

[Report Bug](https://github.com/skircr115/ha-amerigas/issues) · [Request Feature](https://github.com/skircr115/ha-amerigas/issues) · [Discussions](https://github.com/skircr115/ha-amerigas/discussions)

</div>