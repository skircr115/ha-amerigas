# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.2.1] - 2026-08-18

### 🧪 Tests — Expanded Coverage for Used Since Delivery

Added comprehensive unit tests for `_calculate_used_since_delivery` in `tests/test_sensor.py`, covering the method's boundary conditions and normal operation.

**Fix:** Added a guard (`if not self.coordinator.data:`) to `_calculate_used_since_delivery` that returns early instead of raising an `AttributeError` when the coordinator has no data yet (e.g. before the first successful refresh).

### 🔧 Technical Changes

**`sensor.py` — `_calculate_used_since_delivery()`**
- Added `if not self.coordinator.data:` check to prevent `AttributeError` on missing coordinator data

**`tests/test_sensor.py`**
- Added `test_calculate_used_since_delivery` covering boundary and normal-operation cases

**`manifest.json`**
- Version bumped to `3.2.1`

### 🔄 Migration Notes

No breaking changes. Update via HACS and restart. No sensor behavior changes for accounts with normal data — this only affects the (rare) window before the coordinator's first successful poll.

---

## [3.2.0] - 2026-06-29

### 🐛 Bug Fix — Service Address Sensor Showing Billing Address for Some Customers (Fixes #26)

Customers with a billing address separate from their tank location saw the billing address in `sensor.amerigas_propane_service_address` instead of their actual service address. This is because `accountSummaryViewModel` — the only data source previously parsed — stores the customer billing address rather than the customer's tank address for some accounts. The customer's actual delivery address may only appear in the dashboard HTML markup for these customers.

**Fix:** A new `sensor.amerigas_propane_delivery_address` sensor is added. It parses the delivery address directly from the dashboard HTML using two strategies in priority order:

1. **"Delivery Address:" span** — extracts the pre-formatted full address from the `<span>` inside the delivery confirmation modal (e.g. `STREET, CITY STATE ZIP`). Most reliable for accounts with separate billing and delivery addresses.
2. **`aria-label` label cluster** — assembles the address from the four `<label aria-label="Street/City/State/Zipcode">` elements in the address detail header. Secondary fallback.

`sensor.amerigas_propane_service_address` is unchanged — it continues to reflect `Street`/`City`/`State`/`Zip` from `accountSummaryViewModel`, which is correct for auto-delivery customers. The new delivery address sensor will be `None`/unavailable on accounts where neither HTML pattern is present.

### ⚡ Performance — Entity Registry Lookup Optimization

Replaced full entity registry iteration (`for entity in entity_reg.entities.values()`) with direct `async_get_entity_id()` lookups in three locations. The old approach scanned every registered entity on every pre-delivery level lookup; the new approach resolves the target entity ID in O(1) using the known domain, platform, and unique ID.

**Affected files:** `__init__.py`, `sensor.py` (`_setup_pre_delivery_listener` and `_get_pre_delivery_level`), `delivery_tracker.py` (`_capture_pre_delivery_level_from_api`).

### 🧪 Tests — Initial Test Suite

Added `tests/` package with initial unit test coverage:

- **`test_api.py`** — `AmeriGasAPI` initialization (username, password, session state)
- **`test_sensor.py`** — `_calculate_gallons_remaining` boundary conditions: `tank_level` at 0, negative, 100, over 100, `None`; `tank_size` at `None` (falls back to `DEFAULT_TANK_SIZE`), 0 (falsy → `DEFAULT_TANK_SIZE`), negative (explicit guard returns `None`); normal operation at 50%

### 🔧 Technical Changes

**`api.py` — `_async_fetch_dashboard()`**
- Return type changed from `dict[str, Any]` to `tuple[dict[str, Any], str]`
- Now returns `(account_data, dashboard_html)` — raw HTML preserved for downstream parsing

**`api.py` — `async_get_data()`**
- Unpacks the tuple from `_async_fetch_dashboard()`
- Passes `dashboard_html` to `_parse_account_data()`

**`api.py` — `_parse_account_data()`**
- Signature gains `dashboard_html: str | None = None`
- Adds two-strategy HTML delivery address extraction
- `service_address` build logic unchanged
- `delivery_address` added to return dict

**`sensor.py` — `AmeriGasDeliveryAddressSensor`**
- New class: name `"Delivery Address"`, unique ID `amerigas_delivery_address`, icon `mdi:map-marker`, `EntityCategory.DIAGNOSTIC`
- Reads `delivery_address` key from coordinator data
- Registered in `async_setup_entry`

**`sensor.py` / `__init__.py` / `delivery_tracker.py`**
- `entity_reg.async_get_entity_id("number", DOMAIN, f"{entry_id}_pre_delivery_level")` replaces all three full-scan loops

### 🔄 Migration Notes

No breaking changes. Update via HACS and restart. `sensor.amerigas_propane_service_address` is unchanged.

Customers with separate delivery location: after updating, `sensor.amerigas_propane_delivery_address` will appear with your tank's address. Other customers: the sensor will show the same address as `service_address` if the HTML patterns match, or be unavailable if they don't — this is expected and does not affect any other sensors.

---

## [3.1.1] - 2026-03-10

### 🐛 Bug Fix — Stale Gallons Captured on Date-Change Trigger

**Fixed: Pre-delivery level captured against wrong delivery amount when portal updates date and gallons in separate API responses**

The date-change trigger in `DeliveryTracker` fired as soon as `last_delivery_date` changed, immediately calling `_capture_pre_delivery_level_from_api()`. If the portal had not yet updated `last_delivery_gallons` to reflect the new delivery, the calculation used the prior delivery's gallons figure — e.g. `420 - 28.1 = 391.9` instead of the correct `420 - 255.9 = 164.1`. The wrong pre-delivery level then cascaded into incorrect values for Used Since Delivery, Daily Average Usage, Days Until Empty, Cost Since Delivery, and Days Remaining Difference.

**Fix:** `DeliveryTracker` now tracks `last_delivery_gallons` across polls alongside `last_delivery_date`. When the date changes but gallons is unchanged, capture is deferred (`_pending_api_capture = True`) and fires on the subsequent poll when gallons updates. If both change in the same poll (normal case), capture fires immediately as before. A new level-jump trigger (Trigger 1) fires immediately when the tank monitor reports an increase ≥ 10 gallons between polls, capturing both `pre_fill` and `post_fill` directly from the tank monitor — the most accurate baseline, entirely independent of portal lag.

### 🐛 Bug Fix — Cost Per Gallon Incorrect Immediately After Delivery

**Fixed: Cost per gallon using previous delivery's payment until new invoice is paid**

`_calculate_cost_per_gallon()` unconditionally used `last_payment_amount / last_delivery_gallons`. Immediately after a delivery, `last_payment_amount` reflects a prior payment, producing a wrong cost per gallon (e.g. `$230.50 / 255.9 gal = $0.90/gal` instead of the actual `~$3.44/gal`).

**Fix:** If `last_payment_date < last_delivery_date`, the sensor uses `account_balance` (preferred) or `amount_due` as the numerator, since those fields reflect the outstanding charge for the current delivery. The sensor reverts to `last_payment_amount` automatically once payment is recorded and `last_payment_date` advances past `last_delivery_date`.

### 🔧 Technical Changes

**`delivery_tracker.py` — `DeliveryTracker.__init__()`**
- Added `_last_known_delivery_gallons: float = 0.0`
- Added `_pending_api_capture: bool = False`

**`delivery_tracker.py` — `DeliveryTracker._handle_coordinator_update()`**
- Trigger 2 split into three paths: immediate capture, deferred capture, and deferred-capture resolution
- `_last_known_delivery_gallons` updated every poll

**`sensor.py` — `AmeriGasSensorBase._calculate_cost_per_gallon()`**
- Added `last_payment_date` / `last_delivery_date` comparison
- Uses `account_balance` → `amount_due` fallback when payment predates delivery
- Existing `last_payment_amount` path unchanged for current-payment case

**`manifest.json`**
- Version bumped to `3.1.1`

### 🔄 Migration Notes

No breaking changes. Update via HACS and restart.

If you installed v3.1.1 after a recent delivery (level-jump trigger was not running at delivery time), set the pre-delivery level manually:

```yaml
service: amerigas.set_pre_delivery_level
data:
  gallons: 145.0  # your actual pre-delivery level in gallons
```

Cost per gallon self-corrects automatically once the delivery invoice is paid.

---

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

All date fields returned by the AmeriGas API can arrive as date-only strings with no time or timezone component (e.g., `01/15/2026`). The previous code attached `timezone.utc` to these naive datetimes, which caused Home Assistant to convert them to local time and display the date as the day before for any timezone behind UTC (all US timezones).

**Solution**: Naive datetimes are now treated as local time by attaching `dt_util.get_default_time_zone()` instead of UTC.

**Fixed: Next delivery date sensor disappearing from Home Assistant**

The `replace(tzinfo=None)` workaround stripped timezone info after parsing, producing a naive datetime that HA rejected for `SensorDeviceClass.TIMESTAMP`, marking the entity unavailable.

**Solution**: Removed the `replace(tzinfo=None)` strip entirely.

### 🔧 Technical Changes

**`api.py` — `parse_date()`**
- Changed naive datetime handling from `replace(tzinfo=timezone.utc)` to `replace(tzinfo=dt_util.get_default_time_zone())`

**`api.py` — `_parse_account_data()`**
- Removed `replace(tzinfo=None)` post-processing strip on `next_delivery_date`

**`manifest.json`**
- Version bumped to `3.0.11`

---

## [3.0.10] - 2026-02-28

### 🔧 API Fix — Next Delivery Date Lookup Simplified

Reverted to a clean 3-level lookup chain and removed the timezone strip entirely.

**New lookup order:**
1. `LstOpenOrders[0].DeliveryDate` (primary)
2. `OneClickOrderViewModel.NextDeliveryDate` (fallback)
3. `account_data.NextDeliveryDate` (final fallback)

**`manifest.json`** — version bumped to `3.0.10`

---

## [3.0.9] - 2026-02-05

### 🔒 CI Security — Workflow Permissions Hardening

Added `permissions: contents: read` to `hassfest.yml`. No integration code changed.

**`manifest.json`** — version bumped to `3.0.9`

---

## [3.0.8] - 2026-01-25

### 🐛 Critical Bug Fix — Energy Dashboard Data Integrity

- Fixed race condition where coordinator updated before state restoration, writing `0.0` to the database and corrupting Energy Dashboard historical data
- Fixed lifetime sensors resetting when AmeriGas API is temporarily unreachable
- Fixed API timeouts — `API_TIMEOUT` increased from 30 → 45 seconds

**`manifest.json`** — version bumped to `3.0.8`

---

## [3.0.7] - 2026-01-24

### 🐛 Critical Bug Fixes — Race Condition in Sensor Updates

- Fixed sensors not updating when pre-delivery level changes
- Fixed Daily Average Usage showing 0.0000 gal/day
- Fixed Energy Consumption (Display) showing "unknown"
- Fixed Days Until Empty and Days Remaining Difference showing "unavailable"

---

## [3.0.6] - 2026-01-10

### 🕐 Cron-Based Refresh Schedule

Replaced `timedelta(hours=6)` with `async_track_time_change()` firing at 00:00, 06:00, 12:00, 18:00 daily. Fixed unclosed aiohttp connection warning.

---

## [3.0.5] - 2026-01-04

### 🎯 Major Features

- Automatic pre-delivery level detection
- `amerigas.set_pre_delivery_level` service
- `amerigas.refresh_data` service
- `number.amerigas_pre_delivery_level` entity
- Fixed estimated refill cost to use 80% fill assumption

---

## [3.0.4] - 2025-01-02

Eliminated entity ID dependencies — all cross-sensor references now use coordinator data or direct sensor references.

---

## [3.0.3] - 2025-01-02

Hotfix — fixed incorrect `propane_tank_` prefix in cross-sensor entity ID lookups.

---

## [3.0.2] - 2025-01-02

Hotfix — fixed `AttributeError: 'str' object has no attribute 'isoformat'` on restart in lifetime gallons sensor.

---

## [3.0.1] - 2025-01-02

Hotfix — all datetime values now return timezone-aware objects as required by Home Assistant.

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
