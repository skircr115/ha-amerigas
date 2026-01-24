# AmeriGas Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/skircr115/ha-amerigas.svg)](https://github.com/skircr115/ha-amerigas/releases)
[![License](https://img.shields.io/github/license/skircr115/ha-amerigas.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-production-green)

> **HACS custom component** for monitoring your AmeriGas propane account. Track tank levels, deliveries, payments, and integrate with the Energy Dashboard.

## ✨ What's New in v3.0.7

### 🐛 Critical Race Condition Fix
**Fixed sensors not updating when pre-delivery level changes!**

Previously, only the "Used Since Delivery" sensor responded to pre-delivery level changes. Other sensors (Cost Since Delivery, Energy Consumption, Daily Average Usage, Days Until Empty) continued using stale estimated values until the next 6-hour coordinator refresh.

**Now fixed:** All dependent sensors immediately recalculate when you set the pre-delivery level.

### 🔧 Fixed Sensors
- ✅ **Daily Average Usage** - No longer shows 0.0000 gal/day
- ✅ **Cost Since Last Delivery** - Now uses correct usage value
- ✅ **Energy Consumption (Display)** - Now uses correct usage value
- ✅ **Days Until Empty** - Now calculates correctly for any usage rate
- ✅ **Days Remaining Difference** - Always shows comparison values

### 📊 Before vs After

**Scenario**: 500 gal tank, pre-delivery 391.9 gal, delivery 28.1 gal, current 270 gal

| Sensor | Before (Broken) | After (Fixed) |
|--------|-----------------|---------------|
| Used Since Delivery | 150 gal ✓ | 150 gal ✓ |
| Daily Average Usage | 0.0000 gal/day ✗ | 4.69 gal/day ✓ |
| Cost Since Delivery | $0.00 ✗ | $526.50 ✓ |
| Energy Consumption | 0 ft³ ✗ | 5,458 ft³ ✓ |
| Days Until Empty | 9999 days ✗ | 58 days ✓ |

---

## 🚀 Features

### Real-Time Monitoring
- **Tank Level** - Current percentage and gallons remaining
- **Days Remaining** - Estimated days until tank empty based on your usage
- **Delivery History** - Track all deliveries with dates and amounts
- **Cost Tracking** - Monitor cost per gallon and total spend

### Accurate Consumption Tracking (v3.0.5+)
- **Automatic Pre-Delivery Capture** - 100% accurate for any delivery size
- **Lifetime Consumption** - Total propane used since installation
- **Daily Average** - Your average usage per day
- **Used Since Delivery** - Gallons consumed since last fill
- **Energy Dashboard Integration** - Track propane consumption alongside other utilities

### Smart Calculations (v3.0.7)
- **Centralized Calculations** - All sensors use same pre-delivery level
- **Instant Updates** - Change pre-delivery level, all sensors update immediately
- **Estimated Refill Cost** - Realistic cost estimates using 80% fill level
- **Days Until Empty** - Works with ANY usage rate (even vacation homes!)
- **Calculation Transparency** - See exactly how each value is computed

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

#### Diagnostic Entity (v3.0.5+)
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

### The Magic Behind v3.0.5+

When AmeriGas delivers propane:
1. Their API updates with new delivery date and amount
2. Your tank level sensor updates to post-delivery level
3. Integration detects the delivery date changed
4. Automatically calculates: **Pre-delivery = Current - Delivery**
5. Stores this exact value permanently
6. **v3.0.7**: All dependent sensors immediately recalculate

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

## 🛠️ Manual Services

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
5. **v3.0.7**: All dependent sensors update immediately!

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

### Sensors Not Updating After Setting Pre-Delivery Level

**Fixed in v3.0.7!** All sensors now have a state change listener that triggers recalculation when the pre-delivery level changes.

If you're still seeing issues:
1. Check you're running v3.0.7 or later
2. Restart Home Assistant after updating
3. Check logs for any errors

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

### Daily Average Shows 0.0000 gal/day

**Fixed in v3.0.7!** This was caused by the sensor using a fallback 20% estimation instead of the actual pre-delivery level.

If still showing 0:
1. Verify pre-delivery level is set (check the number entity)
2. Verify you're on v3.0.7 or later
3. Check the `calculation_method` attribute - should show `auto_captured`

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
  - entity: sensor.amerigas_cost_since_last_delivery
    name: Cost Since Delivery
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
3. All sensors will immediately use correct pre-delivery level
4. No configuration changes needed

**No breaking changes!**

### From v3.0.0 - v3.0.5

1. Update integration through HACS
2. Restart Home Assistant
3. All existing sensors continue working
4. New sensors appear automatically
5. If pre-delivery level was set, all sensors now use it correctly

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