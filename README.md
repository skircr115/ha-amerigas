# AmeriGas Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/skircr115/ha-amerigas.svg)](https://github.com/skircr115/ha-amerigas/releases)
[![License](https://img.shields.io/github/license/skircr115/ha-amerigas.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-production-green)

> **HACS custom component** for monitoring your AmeriGas propane account. Track tank levels, deliveries, payments, and integrate with the Energy Dashboard.

## ✨ What's New in v3.0.7

###🐛 Critical Sensor Fixes
**Fixed 3 sensors showing incorrect states!**

- ✅ **Energy Consumption (Display)** - No longer shows "unknown"
- ✅ **Days Until Empty** - Now calculates for ANY usage rate (even 0.05 gal/day!)
- ✅ **Days Remaining Difference** - Always shows comparison values
- ✅ **Lifetime Energy** - Better Energy Dashboard compatibility

**Key improvement**: Days Until Empty now does the math regardless of how low your usage is. Only unavailable if you've never had a delivery recorded.

---

### Previous in v3.0.6

#### 🕐 Cron-Based Refresh Schedule
**Predictable refresh times at 00:00, 06:00, 12:00, and 18:00!**

- ✅ Fixed schedule instead of relative intervals
- ✅ Always know when your data will update
- ✅ No drift after HA restarts
- ✅ Still refreshes on startup for immediate data

#### 🔧 Fixed Unclosed Connection Error
**Resolved the `Error doing job: Unclosed connection (None)` error!**

The aiohttp session is now properly closed after each API fetch.

---

### Previous in v3.0.5

#### 🎯 Automatic Pre-Delivery Detection
**The integration now automatically captures your exact tank level when a delivery happens!**

- **Zero configuration needed** - works automatically after installation
- **100% accurate tracking** regardless of delivery size (small top-offs or full deliveries)
- **No more manual entry** - the system detects new deliveries and calculates pre-delivery levels automatically

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

### Smart Calculations (v3.0.7)
- **Estimated Refill Cost** - Realistic cost estimates using 80% fill level
- **Days Until Empty** - Projected days remaining (works with ANY usage rate!)
- **Cost Analysis** - Price per gallon and per cubic foot
- **Days Remaining Difference** - Compare your calculation vs AmeriGas estimate

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
- Days Until Empty (works with ANY usage rate!)
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

**Real Example:**
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

---

## 🛠️ Manual Services (v3.0.5)

### Service: Set Pre-Delivery Level

For edge cases and historical deliveries:

- **A delivery happened BEFORE upgrading to v3.0.5** - Historic deliveries won't have auto-captured values
- **Automatic detection failed** - Rare cases where delivery detection didn't trigger
- **You want to correct a value** - Fix any inaccurate capture

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

---

### Service: Refresh Data

**Force an immediate update from the AmeriGas API**

The integration automatically updates at **00:00, 06:00, 12:00, 18:00** daily, but you can manually refresh anytime.

**When to use:**
- You want current data right now
- Checking if a delivery has been recorded
- Troubleshooting update issues

**Via Developer Tools:**
1. Go to **Developer Tools** → **Services**
2. Search for `AmeriGas: Refresh Data`
3. Click **Call Service**

**Example Service Call:**
```yaml
service: amerigas.refresh_data
```

---

## 🔧 Troubleshooting

### Days Until Empty Shows Large Number

**This is correct behavior!** 

v3.0.7 now does the math regardless of how low your usage is:

**Example**: Vacation home using 0.05 gal/day
```
400 gallons ÷ 0.05 gal/day = 8,000 days (~22 years)
Sensor shows: "8000 days" ✓
```

The sensor will only show "unavailable" if you've never had a delivery recorded (no baseline data).

### Days Until Empty Shows 9999

This means your usage is extremely low (< 0.001 gal/day). The sensor caps at 9999 days to prevent overflow, but you can see the real calculation in the sensor attributes.

**Check attributes:**
```yaml
sensor.propane_days_until_empty:
  calculation: "400.00 gal ÷ 0.00 gal/day = 800000.0 days (capped at 9999)"
  note: "Usage rate extremely low - showing 9999 days as practical maximum"
```

### Energy Consumption Shows Unknown

**Fixed in v3.0.7!** This sensor now calculates directly from coordinator data and should always show a value.

If still showing unknown:
1. Check that tank size sensor has a value
2. Restart Home Assistant
3. Check logs for errors

### Sensors Haven't Updated in 6+ Hours

v3.0.6 fixed connection leaks. Updates should occur at 00:00, 06:00, 12:00, 18:00.

**Quick Fix:**
1. Use manual refresh: `service: amerigas.refresh_data`
2. Check logs for errors
3. Verify AmeriGas website is accessible

### Finding Your Pre-Delivery Level Entity

**The entity ID is dynamic based on your device name!**

Common entity IDs:
- `number.amerigas_propane_pre_delivery_tank_level` (default)
- `number.propane_tank_pre_delivery_tank_level` (if renamed)

**To find yours:**
1. Go to **Developer Tools** → **States**
2. Search for: `pre_delivery`
3. Look for the number entity with "Pre-Delivery Tank Level"

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
    secondary_info: attribute:calculation
  - type: divider
  - entity: sensor.amerigas_estimated_refill_cost
    name: Est. Refill Cost
  - entity: sensor.amerigas_last_delivery_date
    name: Last Delivery
  - entity: sensor.amerigas_last_delivery_gallons
    name: Delivery Amount
```

---

## 🔄 Upgrading

### From v3.0.6

1. Update integration through HACS
2. Restart Home Assistant
3. Sensors will populate immediately
4. No configuration changes needed

**No breaking changes!**

### From v3.0.0 - v3.0.5

1. Update integration through HACS
2. Restart Home Assistant
3. All existing sensors continue working
4. New sensors appear automatically

### From v2.x (pyscript version)

This is a complete rewrite. See [MIGRATION.md](MIGRATION.md) for detailed instructions.

---

## 🐛 Known Issues

### Historical Small Deliveries

If you had small deliveries before v3.0.5:
- Historical calculations remain inaccurate (can't change the past)
- All future deliveries will be 100% accurate
- Optional: Manually set pre-delivery level for current period

### API Rate Limits

- Integration updates every 6 hours by default (00:00, 06:00, 12:00, 18:00)
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