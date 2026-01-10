# AmeriGas Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/skircr115/ha-amerigas.svg)](https://github.com/skircr115/ha-amerigas/releases)
[![License](https://img.shields.io/github/license/skircr115/ha-amerigas.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-production-green)

> **HACS custom component** for monitoring your AmeriGas propane account. Track tank levels, deliveries, payments, and integrate with the Energy Dashboard.

## ✨ What's New in v3.0.6

### 🕐 Cron-Based Refresh Schedule
**Predictable refresh times at 00:00, 06:00, 12:00, and 18:00!**

- ✅ Fixed schedule instead of relative intervals
- ✅ Always know when your data will update
- ✅ No drift after HA restarts
- ✅ Still refreshes on startup for immediate data

### 🔧 CRITICAL: Fixed Unclosed Connection Error
**Resolved the `Error doing job: Unclosed connection (None)` error!**

The aiohttp session is now properly closed after each API fetch:
- ✅ Session cleaned up in `api.py` after data fetch
- ✅ Session cleaned up in `config_flow.py` after validation
- ✅ No more connection resource leaks
- ✅ Proper cleanup on integration unload

### 📦 HACS Compliance Improvements
- ✅ Added recommended `hacs.json` fields
- ✅ Added service translations to `strings.json`

---

### Previous in v3.0.5

#### 🎯 Automatic Pre-Delivery Detection
**The integration now automatically captures your exact tank level when a delivery happens!**

- **Zero configuration needed** - works automatically after installation
- **100% accurate tracking** regardless of delivery size (small top-offs or full deliveries)
- **No more manual entry** - the system detects new deliveries and calculates pre-delivery levels automatically

#### 📊 Fixed: Estimated Refill Cost
Now uses realistic **80% maximum fill level** (industry standard) instead of assuming 100% fill.

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

## 🛠️ Manual Services (v3.0.5)

### Service: Set Pre-Delivery Level

For edge cases and historical deliveries:

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

### Service: Refresh Data

**Force an immediate update from the AmeriGas API**

The integration automatically updates every **6 hours**, but you can manually refresh anytime.

**When to use:**
- You want current data right now
- Checking if a delivery has been recorded
- Troubleshooting update issues
- Just installed and want fresh data

**Via Developer Tools:**
1. Go to **Developer Tools** → **Services**
2. Search for `AmeriGas: Refresh Data`
3. Click **Call Service** (no parameters needed)

**Example Service Call:**
```yaml
service: amerigas.refresh_data
```

**Via Automation:**
```yaml
# Example: Refresh data every morning at 6 AM
automation:
  - alias: "Daily Propane Update"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: amerigas.refresh_data
```

**What the Service Does:**
- Fetches latest data from AmeriGas API immediately
- Updates all 37 sensors with fresh data
- Triggers delivery detection if new delivery found
- Logs update status for troubleshooting

**Automatic Update Schedule:**
- **Schedule:** 00:00, 06:00, 12:00, 18:00 daily (cron-based)
- **On Startup:** Immediate refresh when HA starts
- **Manual:** Use this service to force update anytime

**Note:** If you notice sensors not updating automatically, check Home Assistant logs for errors and use this service to manually refresh.

---

## 🔧 Troubleshooting

### Sensors Haven't Updated in 6+ Hours

**Issue:** Sensors show stale data (last updated 6-14+ hours ago)

**v3.0.5 Fix:** This was caused by connection leaks and is now fixed! If you're on v3.0.5:

**Quick Fix:**
1. Use manual refresh: `service: amerigas.refresh_data`
2. Check logs for "Unclosed connection" errors
3. If you see connection errors, restart Home Assistant
4. After restart with v3.0.5, automatic updates should work

**If still having issues:**
- Enable debug logging (see COORDINATOR_UPDATE_GUIDE.md)
- Check for API errors in logs
- Verify AmeriGas website is accessible
- Try manual refresh to confirm credentials work

**Note:** Versions before v3.0.5 had connection leaks causing updates to stop. v3.0.5 fixes this completely.

### Finding Your Pre-Delivery Level Entity

**The entity ID is dynamic based on your device name!**

Common entity IDs:
- `number.amerigas_propane_pre_delivery_tank_level` (default device name)
- `number.propane_tank_pre_delivery_tank_level` (if you renamed device to "Propane Tank")
- `number.my_tank_pre_delivery_tank_level` (if you renamed device to "My Tank")

**To find yours:**
1. Go to **Developer Tools** → **States**
2. Search for: `pre_delivery`
3. Look for the number entity with "Pre-Delivery Tank Level" in the name

**Note:** The integration uses entity registry lookups by unique_id, so the service and automatic detection work regardless of what you name the device in the UI!

### Service Works But Still Shows Fallback Calculation

**Issue:** After running `amerigas.set_pre_delivery_level`, the sensor still shows fallback estimation.

**Check:**
1. Verify the number entity value is > 0 (not 0)
2. Restart Home Assistant after setting the value
3. Check Home Assistant logs for any errors

**If still not working:**
- Check logs for "Could not lookup pre-delivery level entity"
- Verify the number entity exists in Developer Tools → States
- Try manually setting the state in Developer Tools

### Pre-Delivery Level Shows 0

**First delivery after upgrade:**
- Normal! The auto-capture only works for NEW deliveries after v3.0.5 installation
- Wait for your next delivery and it will capture automatically
- Or use the service to manually set the value

**Using the service:**
```yaml
service: amerigas.set_pre_delivery_level
data:
  gallons: 391.9
```

**Or manually via Developer Tools:**
1. Go to **Developer Tools** → **States**
2. Search for `pre_delivery` to find your entity
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