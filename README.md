# AmeriGas Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/skircr115/ha-amerigas.svg)](https://github.com/skircr115/ha-amerigas/releases)
[![License](https://img.shields.io/github/license/skircr115/ha-amerigas.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-production-green)

> **HACS custom component** for monitoring your AmeriGas propane account. Track tank levels, deliveries, payments, and integrate with the Energy Dashboard.

---

## ✨ What's New in v3.0.11

### 🐛 Date Timezone Fix

All date sensors (last delivery date, next delivery date, last tank reading, last payment date) were displaying one day early for users in US timezones. Date-only strings returned by the AmeriGas API have no timezone context, and the previous code attached UTC to them — causing Home Assistant to shift them back when converting to local time. Dates are now treated as local time using the HA-configured timezone, so they display correctly regardless of UTC offset.

The next delivery date entity was also disappearing for some users after the v3.0.8 timezone strip workaround (`replace(tzinfo=None)`) produced a naive datetime that Home Assistant rejected for `SensorDeviceClass.TIMESTAMP` sensors. That workaround is now removed entirely. If the entity was deleted, it will be recreated automatically on restart after updating.

---

## 🚀 Features

### Real-Time Monitoring
- **Tank Level** — current percentage and gallons remaining
- **Days Remaining** — estimated days until empty based on your actual usage
- **Delivery Tracking** — last and next delivery dates and amounts
- **Cost Tracking** — cost per gallon, cost since last delivery, estimated refill cost

### Accurate Consumption Tracking (v3.0.5+)
- **Automatic Pre-Delivery Capture** — 100% accurate for any delivery size, zero configuration
- **Lifetime Consumption** — total propane used since installation, protected against data loss
- **Daily Average Usage** — your average consumption per day
- **Energy Dashboard Integration** — track propane alongside electricity and other utilities

### Robust Data Integrity (v3.0.8+)
- Lifetime sensors **never reset to 0** on HA restart (race condition fixed)
- Data persists through API outages and integration reloads
- Energy Dashboard historical data permanently protected

### Smart Calculations (v3.0.7+)
- All sensors share the same pre-delivery level; changing it updates everything instantly
- Days Until Empty works correctly for any usage rate, including vacation homes
- Calculation transparency via sensor attributes

---

## 📦 Installation

### HACS (Recommended)

1. Open HACS → Integrations
2. Click ⋮ → Custom repositories
3. Add `https://github.com/skircr115/ha-amerigas` (Category: Integration)
4. Install "AmeriGas Propane" and restart Home Assistant

### Manual

1. Download the latest release from [GitHub Releases](https://github.com/skircr115/ha-amerigas/releases)
2. Copy `custom_components/amerigas` to your `config/custom_components/` directory
3. Restart Home Assistant

---

## ⚙️ Configuration

1. **Settings** → **Devices & Services** → **+ Add Integration**
2. Search "AmeriGas" and select it
3. Enter your MyAmeriGas account credentials and click **Submit**

### What Gets Created

**API sensors (15):** tank level, tank size, days remaining, amount due, account balance, last/next delivery date and gallons, last payment date/amount, last tank reading, auto-pay status, paperless billing, account number, service address

**Calculated sensors (11):** gallons remaining, used since last delivery, energy consumption (display), daily average usage, days until empty, days since last delivery, cost per gallon, cost per cubic foot, cost since last delivery, estimated refill cost, days remaining difference

**Lifetime sensors (2):** Propane Lifetime Gallons, Propane Lifetime Energy (for Energy Dashboard)

**Diagnostic entity (1):** Pre-Delivery Tank Level number entity — auto-captured on each delivery, manually adjustable

---

## 📊 Energy Dashboard Integration

1. **Settings** → **Dashboards** → **Energy** → **Add Gas Source**
2. Select **Propane Lifetime Energy** (`sensor.propane_lifetime_energy`)
3. Click **Save**

> Update to v3.0.8 or later before using the Energy Dashboard to ensure historical data is never lost to the startup race condition.

---

## 🎯 How Automatic Pre-Delivery Detection Works

When AmeriGas records a delivery, the integration detects that `last_delivery_date` changed and automatically calculates:

```
pre_delivery = post_delivery_level - delivery_amount
```

This value is stored in `number.amerigas_pre_delivery_level` and used by all consumption sensors. All sensors recalculate immediately when this value changes.

**Example:**
```
Post-delivery level:  420 gal
Delivery amount:       28.1 gal
Pre-delivery level:   391.9 gal  ← auto-captured

Used since delivery:  420 - 300 (current) = 120 gal  ✅
```

---

## 🛠️ Manual Services

### `amerigas.set_pre_delivery_level`
Manually set the pre-delivery level — useful for deliveries that occurred before v3.0.5 or if auto-capture failed.

```yaml
service: amerigas.set_pre_delivery_level
data:
  gallons: 391.9
```

### `amerigas.refresh_data`
Force an immediate API fetch instead of waiting for the next scheduled refresh.

```yaml
service: amerigas.refresh_data
```

---

## 🔄 Update Schedule

Data refreshes automatically at **00:00, 06:00, 12:00, and 18:00** daily, plus immediately on HA startup. Use `amerigas.refresh_data` to trigger an on-demand update.

---

## 🔧 Troubleshooting

**Date sensors showing the wrong day (one day early)** — Fixed in v3.0.11. Update and restart.

**Next delivery date entity missing / HA prompting you to delete it** — Fixed in v3.0.11. Update and restart; the entity will be recreated automatically.

**Next delivery date is wrong or missing** — Fixed in v3.0.10/v3.0.11. Update and restart.

**Lifetime sensors reset to 0 on restart** — Fixed in v3.0.8. Update immediately if you see this. After updating, check logs for `State restoration complete. Lifetime total: XXX.XX gal`.

**Sensors not updating after setting pre-delivery level** — Fixed in v3.0.7. Verify you are on v3.0.7+ and restart.

**Daily Average Usage shows 0.0000 gal/day** — Fixed in v3.0.7. Check that the pre-delivery level entity has a non-zero value and that `calculation_method` attribute shows `auto_captured`.

**Days Until Empty shows a very large number** — Expected for low-usage installations (e.g., vacation homes). The sensor caps at 9,999 days for usage below 0.001 gal/day. Check the `calculation` attribute for the exact math.

**API timeouts / sensors unavailable** — Timeout was raised to 45 seconds in v3.0.8. If timeouts persist, use `amerigas.refresh_data` to retry manually.

**Finding the pre-delivery level entity** — Developer Tools → States → search `pre_delivery`. The entity ID is dynamic based on device name.

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
  - entity: sensor.amerigas_next_delivery_date
    name: Next Delivery
```

---

## 🔄 Upgrading

### From any v3.0.x
No breaking changes across the v3.0.x series. Update via HACS and restart. All sensors, entities, and automations continue working without modification.

### From v2.x (pyscript)
See [MIGRATION.md](MIGRATION.md) for detailed instructions.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and PRs welcome via [GitHub Issues](https://github.com/skircr115/ha-amerigas/issues) and [Discussions](https://github.com/skircr115/ha-amerigas/discussions).

## 📜 License

MIT License — see [LICENSE](LICENSE)

## ⚠️ Disclaimer

**Unofficial integration, not affiliated with AmeriGas.** Use at your own risk. Always verify propane levels manually. May break if AmeriGas changes their website.

## 🙏 Acknowledgments

Built for [Home Assistant](https://www.home-assistant.io/). Thanks to all contributors (@Ricket and others) and to the community for testing and feedback.

---

<div align="center">

**If this integration helped you, please ⭐ star the repo!**

Made with ❤️ for the Home Assistant community

[Report Bug](https://github.com/skircr115/ha-amerigas/issues) · [Request Feature](https://github.com/skircr115/ha-amerigas/issues) · [Discussions](https://github.com/skircr115/ha-amerigas/discussions)

</div>
