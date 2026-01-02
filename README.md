# AmeriGas Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/skircr115/ha-amerigas.svg)](https://github.com/skircr115/ha-amerigas/releases)
[![License](https://img.shields.io/github/license/skircr115/ha-amerigas.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-production-green)

> **HACS custom component** for monitoring your AmeriGas propane account. Track tank levels, deliveries, payments, and integrate with the Energy Dashboard.

## 🆕 What's New in v3.0.4

### 🎯 Future-Proof Architecture
**v3.0.4** - Entity ID Independent Design
- ✅ **Rename-safe sensors** - Sensors work regardless of entity naming
- ✅ **Helper methods** - Calculations use coordinator data directly
- ✅ **No entity lookups** - More efficient and reliable
- ✅ **Production ready** - All critical issues resolved

### 🔧 Recent Fixes (v3.0.1-v3.0.3)
- ✅ **Timezone handling** - All datetime sensors now timezone-aware
- ✅ **State restoration** - Lifetime sensors survive restarts
- ✅ **Entity ID corrections** - Fixed cross-sensor references

### 🏗️ Complete v3.0.0 Refactor
**Major architectural upgrade from pyscript to native custom component**

**✅ Native Home Assistant Integration**
- UI-only configuration (no YAML editing)
- Full HACS support with one-click installation
- DataUpdateCoordinator pattern for efficiency
- Zero dependencies (removed Pyscript requirement)

**✅ Enhanced Reliability**
- 98-99% accuracy (improved from 95-98%)
- Better unknown handling (shows "unavailable" vs "0" or "999")
- Improved overfill tracking (uses actual delivery amounts)
- Enhanced datetime parsing (multiple format support)
- State preservation backup (protects against DB corruption)

**✅ All v2.0.1 Critical Fixes Included**
- Noise filtering (0.5 gal threshold prevents drift)
- Bounds checking (0-100% tank level validation)
- Tank size validation
- Energy Dashboard spike fixes

## ✨ Features

- 🔥 **Real-time Tank Monitoring** - Current level, gallons remaining, days until empty
- 🚚 **Delivery Tracking** - Last/next delivery dates, gallons delivered
- 💰 **Payment Information** - Amount due, account balance, payment history
- 📊 **Usage Analytics** - Daily/monthly/yearly consumption and costs
- ⚡ **Energy Dashboard** - Full integration with Home Assistant Energy Dashboard
- 🔔 **Smart Alerts** - Low propane, high usage, payment due notifications
- 📈 **Cost Tracking** - Per-gallon pricing, estimated refill costs
- 📉 **Lifetime Tracking** - Permanent consumption tracking that never resets
- 🎯 **98-99% Accuracy** - Production-grade reliability
- 🔧 **Rename-safe** - Works regardless of entity naming (v3.0.4+)

## 📋 Prerequisites

- Home Assistant Core 2023.1 or later
- Active MyAmeriGas online account
- AmeriGas propane service

## 🚀 Installation

### HACS (Recommended)

1. **Open HACS**
   - Go to HACS → Integrations
   
2. **Add Repository**
   - Click "⋮" (three dots) → Custom repositories
   - Repository: `https://github.com/skircr115/ha-amerigas`
   - Category: Integration
   - Click "Add"

3. **Install Integration**
   - Search for "AmeriGas Propane"
   - Click "Download"
   - Restart Home Assistant

4. **Configure**
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "AmeriGas Propane"
   - Enter your MyAmeriGas credentials
   - Click "Submit"

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/skircr115/ha-amerigas/releases)
2. Extract and copy the `custom_components/amerigas` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Add integration via UI (Settings → Devices & Services)

## ⚙️ Configuration

Configuration is done entirely through the UI:

1. Settings → Devices & Services → Add Integration
2. Search: "AmeriGas Propane"
3. Enter credentials:
   - **Email**: Your MyAmeriGas account email
   - **Password**: Your MyAmeriGas password
4. Click Submit

**Update Interval**: 6 hours (automatic)

## 📊 Sensors

The integration creates 37 sensors:

### Base Sensors (15)

| Sensor | Description | Unit |
|--------|-------------|------|
| Tank Level | Current percentage | % |
| Tank Size | Capacity | gal |
| Days Remaining (AmeriGas) | AmeriGas estimate | days |
| Amount Due | Current bill | $ |
| Account Balance | Balance | $ |
| Last Payment Date | Date | timestamp |
| Last Payment Amount | Amount | $ |
| Last Tank Reading | Monitor timestamp | timestamp |
| Last Delivery Date | Date | timestamp |
| Last Delivery Gallons | Amount delivered | gal |
| Next Delivery Date | Scheduled date | timestamp |
| Auto Pay | Status | text |
| Paperless Billing | Status | text |
| Account Number | Number | text |
| Service Address | Address | text |

### Calculated Sensors (20)

| Sensor | Description | Unit |
|--------|-------------|------|
| Gallons Remaining | Tank gallons | gal |
| Used Since Delivery | Consumption | gal |
| Energy Consumption | Display only | ft³ |
| Daily Average Usage | Rate | gal/day |
| Days Until Empty | Your estimate | days |
| Cost Per Gallon | Price | $/gal |
| Cost Per Cubic Foot | Price | $/ft³ |
| Cost Since Delivery | Total cost | $ |
| Estimated Refill Cost | Estimate | $ |
| Days Since Delivery | Days | days |
| Days Remaining Difference | Comparison | days |

### Lifetime Tracking (2) ⭐

| Sensor | Description | Purpose |
|--------|-------------|---------|
| **Lifetime Gallons** | Total consumed | Tracking |
| **Lifetime Energy** | Total ft³ | **Energy Dashboard** |

**v3.0.4 Note**: All calculated sensors now work independently of entity naming. You can rename any sensor without breaking the integration!

## ⚡ Energy Dashboard Setup

### Quick Setup

1. Settings → Dashboards → Energy
2. Add Gas Source
3. Select: **Lifetime Energy** (sensor.propane_tank_lifetime_energy)
4. (Optional) Add Cost: **Cost Since Last Delivery**

### Result

- Tracks total propane consumption
- Historical usage graphs
- Cost tracking
- Comparison tools

## 🎨 Dashboard Examples

### Lovelace Card Example

```yaml
type: entities
title: Propane Tank
entities:
  - entity: sensor.propane_tank_tank_level
    name: Level
  - entity: sensor.propane_tank_gallons_remaining
    name: Remaining
  - entity: sensor.propane_tank_days_until_empty
    name: Days Until Empty
  - entity: sensor.propane_tank_daily_average_usage
    name: Daily Usage
  - entity: sensor.propane_tank_last_delivery_date
    name: Last Delivery
```

### Gauge Card

```yaml
type: gauge
entity: sensor.propane_tank_tank_level
min: 0
max: 100
severity:
  green: 40
  yellow: 20
  red: 0
```

## 🔔 Automation Examples

### Low Propane Alert

```yaml
automation:
  - alias: "Low Propane Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.propane_tank_tank_level
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Low Propane"
          message: "Tank is at {{ states('sensor.propane_tank_tank_level') }}%"
```

### High Usage Alert

```yaml
automation:
  - alias: "High Propane Usage"
    trigger:
      - platform: numeric_state
        entity_id: sensor.propane_tank_daily_average_usage
        above: 5
    action:
      - service: notify.mobile_app
        data:
          message: "Daily usage is {{ states('sensor.propane_tank_daily_average_usage') }} gal/day"
```

## 📝 Migration from v1.x/v2.x

If upgrading from pyscript version (v1.x or v2.x):

1. **Read Migration Guide**: See [MIGRATION.md](MIGRATION.md) for detailed instructions
2. **Remove old pyscript files**
3. **Install v3.0.4 via HACS**
4. **Configure via UI**
5. **Update Energy Dashboard** (entity IDs have changed)

## 🐛 Troubleshooting

### Integration Won't Load

**Check Home Assistant logs** for errors:
- Settings → System → Logs
- Search for "amerigas"

**Common issues:**
- Invalid credentials → Reconfigure integration
- Network connectivity → Check internet connection
- AmeriGas API down → Wait and retry

### Sensors Showing "Unavailable"

**Normal during:**
- Initial setup (first update takes ~5 minutes)
- AmeriGas API maintenance
- Network interruptions

**Check:**
1. Verify credentials are correct
2. Check Home Assistant logs
3. Manually reload integration

### "Unknown" Values

**Possible causes:**
- No delivery history yet → Wait for first delivery
- Tank level at 0% → Refill needed
- AmeriGas data incomplete → Contact AmeriGas

### Lifetime Sensors Reset

**Should not happen in v3.0.4**. If it does:
1. Check Home Assistant logs
2. Verify state restoration is working
3. File an issue on GitHub

## 🔧 Advanced Configuration

### Custom Update Interval

Not currently supported - fixed at 6 hours to respect AmeriGas API limits.

### Entity Customization

You can safely rename any entity in the UI:
- Settings → Devices & Services → AmeriGas
- Click on any entity
- Click the gear icon
- Change "Entity ID" or "Name"

**v3.0.4+**: All calculations will continue to work correctly after renaming!

## 📊 Accuracy & Reliability

### Calculation Methods

**Gallons Remaining**: `tank_size × (tank_level / 100)`
- Accuracy: 98-99%
- Updates: Every 6 hours

**Daily Average Usage**: `used_since_delivery / days_since_delivery`
- Accuracy: 98-99%
- Improves over time

**Days Until Empty**: `gallons_remaining / daily_average_usage`
- Accuracy: 85-95% (depends on usage consistency)
- More accurate after 7+ days of data

### Known Limitations

- AmeriGas updates tank levels 2-4x daily
- Thermal expansion can cause minor fluctuations
- Delivery estimates require usage history
- Cost calculations based on last delivery price

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