# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2026-03-08

### 🔐 New Feature — In-Place Credential Updates

Users can now update their AmeriGas username or password without deleting and re-adding the integration. A **Configure** button now appears on the AmeriGas integration card under **Settings → Devices & Services**. The credentials are validated before saving; if validation fails the form stays open with an error. The update takes effect on the next coordinator refresh with no restart required and no loss of historical data or Energy Dashboard statistics.

**Implementation**: Added `OptionsFlow` class to `config_flow.py` and wired it via `async_get_options_flow()` on `ConfigFlow`. The username field is pre-filled with the current value so users only need to re-enter the password. Per HA 2025.12+ requirements, `config_entry` is accessed as a read-only injected property rather than being passed to `__init__` — passing it manually caused an `AttributeError` (500 Internal Server Error) in earlier implementations.

### 📊 Enhancement — Daily Average Usage: Proper Unit & Device Class

`sensor.propane_daily_average_usage` now declares `SensorDeviceClass.VOLUME_FLOW_RATE` and uses `UnitOfVolumeFlowRate.GALLONS_PER_DAY` (`gal/d`) instead of the previous bare string `gal/day`. This is the correct HA representation for a consumption rate and enables proper unit conversion in the UI and Lovelace cards.

**Migration note for existing installs**: Home Assistant will display a one-time unit-change prompt under **Developer Tools → Statistics** for `propane_daily_average_usage`. Accepting it corrects the historical unit metadata without altering the underlying recorded values.

### 💳 Enhancement — Last Payment Date Fully Timestamp-Aware

`sensor.amerigas_last_payment_date` previously received the raw string from the API layer and relied on HA to interpret it. The `api.py` `_parse_account_data()` method now parses `LastPaymentDate` through `parse_date()` and returns a timezone-aware `datetime`, consistent with every other date field. This ensures `SensorDeviceClass.TIMESTAMP` rendering is correct and prevents display inconsistencies for users with non-UTC timezones.

### 💳 Enhancement — Payment Terms Days Attribute

`sensor.amerigas_amount_due` now exposes a `payment_terms_days` integer attribute parsed from the `PaymentTermsUpDate` string (e.g. `"Due within 1 day"` → `1`, `"Due within 30 days"` → `30`). Falls back to `30` if the field is absent or unparseable. This value is used internally by cost-per-gallon correlation logic and is also available for automations (e.g. alert if payment is due within N days).

### 🔧 Technical Changes

**`config_flow.py`**
- Added `OptionsFlow` class implementing `async_step_init()` with credential pre-fill and full validation
- Added `async_get_options_flow()` static method to `ConfigFlow` returning `OptionsFlow()`
- `OptionsFlow` uses HA 2025.12+ pattern: no `__init__` override; `self.config_entry` accessed as injected property
- `async_update_entry()` called on successful validation to apply credential changes in place

**`api.py` — `_parse_account_data()`**
- `last_payment_date` now assigned via `parse_date()` instead of passing the raw string
- Added `payment_terms_days` field: integer extracted from `PaymentTermsUpDate` via `re.search(r'\d+', ...)`; defaults to `30`

**`sensor.py` — `PropaneDailyAverageUsageSensor`**
- `_attr_native_unit_of_measurement` changed from `"gal/day"` to `UnitOfVolumeFlowRate.GALLONS_PER_DAY`
- `_attr_device_class` added: `SensorDeviceClass.VOLUME_FLOW_RATE`

**`sensor.py` — `AmeriGasAmountDueSensor`**
- `extra_state_attributes` now includes `payment_terms_days` integer alongside the existing `payment_terms` raw string

**`manifest.json`**
- Version bumped to `3.1.0`

### 🔄 Migration Notes

No breaking changes. Update via HACS and restart. All existing sensors, entity IDs, automations, and Energy Dashboard configuration continue working without modification.

If Home Assistant shows a Statistics unit-change prompt for `propane_daily_average_usage`, accept it — this is expected and safe.

---

## [3.0.11] - 2026-02-28

### 🐛 Bug Fix — Date Timezone Handling

**Fixed: Date sensors rolling back one day for US timezones**

All date fields returned by the AmeriGas API — last delivery date, next delivery date, last tank reading, last payment date — can arrive as date-only strings with no time or timezone component (e.g., `01/15/2026`). The previous code attached `timezone.utc` to these naive datetimes, which caused Home Assistant to convert them to local time and display the date as the day before for any timezone behind UTC (all US timezones).

**Solution**: Naive datetimes are now treated as local time by attaching `dt_util.get_default_time_zone()` — the HA-configured timezone from Settings → System → General — instead of UTC. A date-only string like `01/15/2026` is now stored as midnight local time and displays correctly regardless of UTC offset.

**Fixed: Next delivery date sensor disappearing from Home Assistant**

The `replace(tzinfo=None)` workaround introduced in v3.0.8 stripped timezone info from the next delivery date after parsing, producing a naive datetime. `AmeriGasNextDeliveryDateSensor` uses `SensorDeviceClass.TIMESTAMP`, which requires a timezone-aware datetime. Home Assistant rejected the naive value, marking the entity unavailable and eventually prompting users to delete it.

**Solution**: Removed the `replace(tzinfo=None)` strip entirely. `parse_date()` now returns a timezone-aware datetime for all fields consistently, so no post-processing is needed.

### 🔧 Technical Changes

**`api.py` — `parse_date()`**
- Changed naive datetime handling from `replace(tzinfo=timezone.utc)` to `replace(tzinfo=dt_util.get_default_time_zone())`
- Affects all date fields: last delivery date, next delivery date, last tank reading, last payment date

**`api.py` — `_parse_account_data()`**
- Removed `replace(tzinfo=None)` post-processing strip on `next_delivery_date`
- Removed surrounding `if/else` block — `parse_date()` result now assigned directly
- Next delivery date fallback chain (`estDeliveryWindowTo` → `estDeliveryWindowFrom` → `orderDate` → `OneClickOrderViewModel.NextDeliveryDate` → `account_data.NextDeliveryDate`) preserved unchanged

**`manifest.json`**
- Version bumped to `3.0.11`

### 🔄 Migration Notes

No breaking changes. Update via HACS and restart. Date sensors will immediately reflect the corrected timezone handling. If the Next Delivery Date entity was deleted, it will be recreated automatically after restart — no manual action required beyond the update.

---

## [3.0.10] - 2026-02-28

### 🔧 API Fix — Next Delivery Date Lookup Simplified

**Fixed: Next delivery date showing incorrect or missing values**

The multi-stage fallback chain for resolving `next_delivery_date` introduced in v3.0.8 was over-engineered and caused incorrect results for some account configurations. The logic was attempting to read estimated delivery window fields (`estDeliveryWindowTo`, `estDeliveryWindowFrom`, `orderDate`, `EstimatedDelivery`) that do not reliably exist or contain useful data across all account types. Additionally, the old code applied a timezone strip (`replace(tzinfo=None)`) as a workaround to prevent Home Assistant from shifting the displayed date — an approach that introduced subtle inconsistencies with the rest of the date-handling pipeline.

**Solution**: Reverted to a clean, direct 3-level lookup chain and removed the timezone strip entirely, letting `parse_date()` handle the result consistently with all other date fields.

**New lookup order:**
1. `LstOpenOrders[0].DeliveryDate` (primary)
2. `OneClickOrderViewModel.NextDeliveryDate` (fallback)
3. `account_data.NextDeliveryDate` (final fallback)

### 🔧 Technical Changes

**`api.py` — `_parse_account_data()`**
- Replaced 5-level fallback chain with a clean 3-level lookup
- Changed primary open-orders key from `estDeliveryWindowTo` → `DeliveryDate`
- Removed intermediate fallbacks for `estDeliveryWindowFrom`, `orderDate`, and `EstimatedDelivery`
- Removed timezone strip (`parsed_result.replace(tzinfo=None)`) workaround
- `next_delivery_date` now assigned directly via `parse_date()`, consistent with all other date fields

**`manifest.json`**
- Version bumped to `3.0.10`

### 🔄 Migration Notes

No breaking changes. Update via HACS and restart. The next delivery date sensor will immediately reflect the corrected lookup logic.

---

## [3.0.9] - 2026-02-05

### 🔒 CI Security — Workflow Permissions Hardening

**Fixed: GitHub Actions workflow missing explicit permissions (CodeQL alert #1)**

The `hassfest.yml` validation workflow did not declare an explicit `permissions` block, meaning the `GITHUB_TOKEN` was granted broader default scopes than necessary for a read-only validation job.

**Solution**: Added `permissions: contents: read` to the `validate` job in `.github/workflows/hassfest.yml`. This scopes the token to the minimum required (fetching the repository to run hassfest) and resolves the GitHub code scanning alert.

No integration code was changed in this release.

### 🔧 Technical Changes

**`.github/workflows/hassfest.yml`**
- Added `permissions: contents: read` under the `validate` job

**`manifest.json`**
- Version bumped to `3.0.9`

### 🔄 Migration Notes

No changes to integration behavior. This is a CI/repository hygiene release only.

---

## [3.0.8] - 2026-01-25

### 🐛 Critical Bug Fix — Energy Dashboard Data Integrity

**Fixed: Lifetime sensors resetting to 0 on Home Assistant restart**

- **Root cause**: Race condition where the coordinator fired an update before `async_added_to_hass()` completed state restoration, writing `0.0` to the database and permanently corrupting Energy Dashboard historical data
- **Solution**: Added `_restoration_complete` flag to `PropaneLifetimeGallonsSensor`; coordinator updates are blocked until restoration finishes
- **Affected sensors**: Propane Lifetime Gallons, Propane Lifetime Energy

**Fixed: Lifetime sensors resetting when AmeriGas API is temporarily unreachable**
- Existing lifetime total is now preserved when the API returns errors or timeouts

**Fixed: API timeout causing "unavailable" sensor states**
- `API_TIMEOUT` increased from 30 → 45 seconds in `const.py` to accommodate AmeriGas server latency

### 🔧 Technical Changes

- `sensor.py` — `PropaneLifetimeGallonsSensor`: added `_restoration_complete` flag, coordinator update guard, API-outage value preservation, `restoration_complete` diagnostic attribute
- `const.py` — `API_TIMEOUT` changed from `30` to `45`
- `manifest.json` — version bumped to `3.0.8`

### 🔄 Migration Notes

Critical update for all users. No breaking changes. Update via HACS and restart. Verify restoration in logs:
```
State restoration complete. Lifetime total: XXX.XX gal
```

---

## [3.0.7] - 2026-01-24

### 🐛 Critical Bug Fixes — Race Condition in Sensor Updates

**Fixed: Sensors not updating when pre-delivery level changes**
- Moved pre-delivery level state-change listener from `PropaneUsedSinceDeliverySensor` to `AmeriGasSensorBase` so all dependent sensors recalculate immediately

**Fixed: Daily Average Usage showing 0.0000 gal/day**
- Refactored `PropaneDailyAverageUsageSensor` to use centralized `_calculate_daily_average()` helper

**Fixed: Energy Consumption (Display) showing "unknown"**
- Now calculates directly from coordinator data via centralized helper

**Fixed: Days Until Empty showing "unavailable" for low usage**
- Sensor now always calculates days regardless of usage rate; caps at 9,999 for extremely low usage (< 0.001 gal/day)

**Fixed: Days Remaining Difference showing "unknown"**
- Always calculates the difference; caps at 9,999 for extremely low usage

### ✨ Enhancements

- Added `_get_pre_delivery_level()` centralized helper to `AmeriGasSensorBase`
- Added `calculation_method`, `calculation`, and `note` attributes to usage-dependent sensors

---

## [3.0.6] - 2026-01-10

### 🕐 Cron-Based Refresh Schedule

- Replaced `timedelta(hours=6)` with `async_track_time_change()` firing at 00:00, 06:00, 12:00, 18:00 daily
- Immediate fetch on HA startup preserved

### 🐛 Bug Fixes

- Fixed `Error doing job: Unclosed connection (None)` — aiohttp session now closed in `finally` block after each fetch and after config flow validation

### 📦 HACS Compliance

- `hacs.json`: added `hacs`, `zip_release`, `filename` fields
- `strings.json`: added service translations for `set_pre_delivery_level` and `refresh_data`

---

## [3.0.5] - 2026-01-04

### 🎯 Major Features

- **Automatic pre-delivery level detection** — when `last_delivery_date` changes, calculates `pre_delivery = current - delivery_amount` automatically with 100% accuracy for any delivery size
- **`amerigas.set_pre_delivery_level` service** — manually set pre-delivery level for historical deliveries or corrections
- **`amerigas.refresh_data` service** — force immediate API refresh on demand
- **`number.amerigas_pre_delivery_level` entity** — persists auto-captured value across restarts; manually adjustable
- **Fixed estimated refill cost** — changed from 100% fill assumption to industry-standard 80%

### 🔧 New Files

- `delivery_tracker.py`, `number.py`, `services.yaml`

---

## [3.0.4] - 2025-01-02

### 🎯 Refactor — Eliminate Entity ID Dependencies

- All cross-sensor dependencies now use coordinator data or direct sensor references
- Sensors work correctly regardless of entity ID renaming in the UI

---

## [3.0.3] - 2025-01-02

### 🐛 Hotfix — Entity ID References

- Fixed incorrect `propane_tank_` prefix in cross-sensor entity ID lookups causing calculated sensors to show "unknown"

---

## [3.0.2] - 2025-01-02

### 🐛 Hotfix — Lifetime Sensor State Restoration

- Fixed `AttributeError: 'str' object has no attribute 'isoformat'` on restart in lifetime gallons sensor

---

## [3.0.1] - 2025-01-02

### 🐛 Hotfix — Timezone-Aware Datetimes

- All datetime values now return timezone-aware objects as required by Home Assistant; fixed 4 sensors that failed to load

---

## [3.0.0] - 2025-01-02

### 🎉 Major Refactor — Native Custom Component

Complete rewrite from pyscript to a native Home Assistant custom component with UI-based config flow, HACS support, `DataUpdateCoordinator` pattern, and state restoration for lifetime sensors.

---

## Links

- [GitHub Releases](https://github.com/skircr115/ha-amerigas/releases)
- [Documentation](https://github.com/skircr115/ha-amerigas)
- [Issues](https://github.com/skircr115/ha-amerigas/issues)
- [Discussions](https://github.com/skircr115/ha-amerigas/discussions)