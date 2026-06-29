# AmeriGas Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/skircr115/ha-amerigas.svg)](https://github.com/skircr115/ha-amerigas/releases)
[![License](https://img.shields.io/github/license/skircr115/ha-amerigas.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-production-green)

> **HACS custom component** for monitoring your AmeriGas propane account. Track tank levels, deliveries, payments, and integrate with the Energy Dashboard.

---

## ✨ What's New in v3.2.0

### 🐛 Delivery Address Sensor for Will-Call Customers

Will-call customers with a billing address separate from their tank location were seeing the local AmeriGas district office address in `sensor.amerigas_propane_service_address` rather than their actual tank address. This is a data limitation of `accountSummaryViewModel` — for will-call accounts, that JSON blob contains district billing fields, not the customer's delivery address.

A new `sensor.amerigas_propane_delivery_address` sensor is added. It parses the delivery address directly from the dashboard HTML, capturing the actual tank location regardless of account type. `sensor.amerigas_propane_service_address` is unchanged.

### ⚡ Entity Registry Lookup Optimization

Pre-delivery level entity lookups now use `async_get_entity_id()` instead of scanning the full entity registry on every call. No behavioral change — this is a performance and correctness improvement.

### 🧪 Initial Unit Test Coverage

Added `tests/` package with boundary condition tests for `_calculate_gallons_remaining` and API initialization.

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

**API sensors (16):** tank level, tank size, days remaining, amount due, account balance, last/next delivery date and gallons, last payment date/amount, last tank reading, auto-pay status, paperless billing, account number, service address, delivery address

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

The integration uses two independent triggers to detect a delivery:

**Trigger 1 — Level-jump (telemetry-first):** Fires immediately when the tank monitor reports an increase ≥ 10 gallons between consecutive coordinator polls. Captures both pre-fill and post-fill directly from the tank monitor — the most accurate baseline, independent of portal lag.

**Trigger 2 — Date-change (API confirmation):** Fires when `last_delivery_date` changes. If the level-jump trigger already captured the fill, this path confirms and skips re-capture. Otherwise it calculates `pre_delivery = current_level - last_delivery_gallons`. Capture is deferred if `last_delivery_gallons` hasn't updated yet in the same poll, firing on a subsequent poll once both values are current.

The captured pre-delivery level is stored in `number.amerigas_pre_delivery_level` and used by all consumption sensors. All sensors recalculate immediately when this value changes.

**Example (level-jump path):**
```
Pre-fill (tank monitor):  145 gal  ← captured at delivery time
Post-fill (tank monitor): 420 gal  ← captured at delivery time

Used since delivery:  420 - 395 (current) = 25 gal  ✅ (accuracy: 100%, tank monitor)
```

**Example (API fallback path):**
```
Post-delivery level:  420 gal
Delivery amount:      255.9 gal
Pre-delivery level:   164.1 gal  ← auto-captured once portal updates

Used since delivery:  420 - 395 (current) = 25 gal  ✅ (accuracy: ~95%, API)
```

---

## 🛠️ Manual Services

### `amerigas.set_pre_delivery_level`
Manually set the pre-delivery level — useful for deliveries that occurred before v3.0.5 or if auto-capture failed.

```yaml
service: amerigas.set_pre_delivery_level
data:
  gallons: 145.0
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

**Service address showing wrong address (Billing address instead of your tank location)** — Fixed in v3.2.0 for some customers. After updating, use `sensor.amerigas_propane_delivery_address` for your tank location. `sensor.amerigas_propane_service_address` reflects the `accountSummaryViewModel` JSON data and is unchanged.

**Sensors show wrong values right after a delivery** — If the integration was not running at delivery time (e.g. you just installed v3.1.1), the level-jump trigger could not fire. Set the pre-delivery level manually: `amerigas.set_pre_delivery_level` with the tank level in gallons immediately before the delivery. Sensors correct immediately.

**Cost per gallon looks wrong after a delivery** — Expected until the invoice is paid. v3.1.1 automatically uses `account_balance` or `amount_due` as the cost basis when `last_payment_date` predates `last_delivery_date`. Once payment is recorded, it reverts to the standard calculation.

**Need to update your password?** — Use Settings → Devices & Services → AmeriGas → Configure (v3.1.0+). No reinstall required.

**Daily Average Usage unit change prompt in Statistics** — Expected after upgrading to v3.1.0. Go to Developer Tools → Statistics, find `propane_daily_average_usage`, and accept the unit fix. Safe to confirm.

**Date sensors showing the wrong day (one day early)** — Fixed in v3.0.11. Update and restart.

**Next delivery date entity missing / HA prompting you to delete it** — Fixed in v3.0.11. Update and restart; the entity will be recreated automatically.

**Lifetime sensors reset to 0 on restart** — Fixed in v3.0.8. Update immediately. After updating, check logs for `State restoration complete. Lifetime total: XXX.XX gal`.

**Sensors not updating after setting pre-delivery level** — Fixed in v3.0.7. Verify you are on v3.0.7+ and restart.

**Daily Average Usage shows 0.0000 gal/day** — Fixed in v3.0.7. Check that the pre-delivery level entity has a non-zero value and that the `calculation_method` attribute shows `auto_captured` or `tank_monitor`.

**Days Until Empty shows a very large number** — Expected for low-usage installations (e.g. vacation homes). The sensor caps at 9,999 days for usage below 0.001 gal/day. Check the `calculation` attribute for the exact math.

**API timeouts / sensors unavailable** — Timeout is 45 seconds (raised in v3.0.8). If timeouts persist, use `amerigas.refresh_data` to retry manually.

**Finding the pre-delivery level entity** — Developer Tools → States → search `pre_delivery`.

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

### From any v3.0.x, v3.1.x, or v3.2.x
No breaking changes. Update via HACS and restart. All sensors, entities, and automations continue working without modification.

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