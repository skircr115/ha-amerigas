# AmeriGas Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/skircr115/ha-amerigas.svg)](https://github.com/skircr115/ha-amerigas/releases)
[![License](https://img.shields.io/github/license/skircr115/ha-amerigas.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-production-green)

> **HACS custom component** for monitoring your AmeriGas propane account. Track tank levels, deliveries, payments, and integrate with the Energy Dashboard.

---

## ✨ What's New in v3.1.0

### 🔐 Update Credentials Without Reinstalling

You can now update your AmeriGas username or password directly from the integration's Configure dialog — no need to delete and re-add the integration. Go to **Settings → Devices & Services → AmeriGas → Configure** and enter your updated credentials. The change takes effect on the next data refresh with no restart required and no loss of historical data.

### 📊 Daily Average Usage — Proper Unit & Device Class

`sensor.propane_daily_average_usage` now uses `gal/d` (gallons per day) with `SensorDeviceClass.VOLUME_FLOW_RATE`, the correct HA representation for a flow rate. Previously the sensor used a plain `gal/day` string unit with no device class, which caused inconsistent display and prevented unit conversion in the UI.

**Migration note:** If you had this sensor tracked in the Statistics database before v3.1.0, Home Assistant will show a one-time unit-change prompt under **Developer Tools → Statistics**. Accepting it is safe and expected — it corrects the historical unit metadata without affecting the underlying values.

### 💳 Payment Date & Terms Improvements

`sensor.amerigas_last_payment_date` now correctly uses `SensorDeviceClass.TIMESTAMP` end-to-end: the API layer returns a timezone-aware `datetime` object instead of the raw string it previously passed through. This prevents subtle display issues and makes the sensor consistent with all other date sensors.

`sensor.amerigas_amount_due` gains a new `payment_terms_days` attribute (integer) parsed from the `PaymentTermsUpDate` field (e.g. `"Due within 1 day"` → `1`). This is used internally to improve cost-per-gallon accuracy but is also available for automations.

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
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=skircr115&repository=ha-amerigas&category=Integration)
 
 -OR-
1. Open HACS → Integrations
2. Search for "AmeriGas Propane"
4. Install and restart Home Assistant

### Manual

1. Download the latest release from [GitHub Releases](https://github.com/skircr115/ha-amerigas/releases)
2. Copy `custom_components/amerigas` to your `config/custom_components/` directory
3. Restart Home Assistant

---

## ⚙️ Configuration

1. **Settings** → **Devices & Services** → **+ Add Integration**
2. Search "AmeriGas" and select it
3. Enter your MyAmeriGas account credentials and click **Submit**

### Updating Credentials (v3.1.0+)

If your password changes, go to **Settings → Devices & Services → AmeriGas → Configure** and re-enter your credentials. No restart needed and no historical data is lost.

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

**Need to update your password?** — Use Settings → Devices & Services → AmeriGas → Configure (v3.1.0+). No reinstall required.

**Daily Average Usage unit change prompt in Statistics** — Expected after upgrading to v3.1.0. Go to Developer Tools → Statistics, find `propane_daily_average_usage`, and accept the unit fix. Safe to confirm.

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
No breaking changes. Update via HACS and restart. All sensors, entities, and automations continue working without modification. If upgrading from a version prior to v3.1.0, see the Daily Average Usage note in the Troubleshooting section above.

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