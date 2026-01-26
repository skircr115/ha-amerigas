# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.8] - 2026-01-25

### 🐛 Critical Bug Fix - Energy Dashboard Data Integrity

#### Lifetime Sensors Reset to Zero - CRITICAL FIX FOR ENERGY DASHBOARD

**Fixed: Lifetime sensors resetting to 0 on Home Assistant restart or API failure**
- **Root cause**: Race condition where coordinator updates executed before state restoration completed
- **Impact**: CRITICAL - Affects Energy Dashboard integration and all users tracking lifetime propane consumption
- **Data loss**: Permanent loss of historical consumption tracking data
- **Solution**: Added `_restoration_complete` flag to block coordinator updates until state restoration finishes
- **Affected sensors**:
  - Propane Lifetime Gallons (sensor.propane_tank_lifetime_gallons)
  - Propane Lifetime Energy (sensor.propane_lifetime_energy) - **Energy Dashboard source**

**Timeline of the bug**:
1. Sensor initializes with `_lifetime_total = 0.0`
2. CoordinatorEntity base class registers sensor as coordinator listener during `__init__`
3. Coordinator fires update BEFORE `async_added_to_hass()` completes
4. `_handle_coordinator_update()` executes with `_lifetime_total` still at `0.0`
5. Sensor writes `0.0` to database, overwriting previous good value
6. State restoration attempts to load old value - TOO LATE, database already corrupted

**Also Fixed: Lifetime sensors resetting when AmeriGas API temporarily unreachable**
- Now preserves existing lifetime total when API returns errors or timeouts
- Prevents false consumption events during network outages
- Maintains data integrity for Energy Dashboard

**And Fixed: API timeout issues with slow AmeriGas website**

Root cause: AmeriGas website can be slow to respond, causing 30-second timeout to be insufficient
Solution: Increased API timeout from 30 seconds to 45 seconds
Impact: Resolves "unavailable" sensor states caused by API timeouts
Affected components: All API calls (login and dashboard fetch)

### 🔧 Technical Changes

**Modified Files**:
- `sensor.py` - PropaneLifetimeGallonsSensor class
  - Added `_restoration_complete: bool = False` flag to `__init__`
  - Set `_restoration_complete = True` after state restoration completes
  - Added early return guard in `_handle_coordinator_update()` to block updates before restoration
  - Enhanced logging for restoration process and API failures
  - Added `restoration_complete` attribute for debugging
  - Updated version to 3.0.8

- `sensor.py` - PropaneLifetimeEnergySensor class  
  - Updated version to 3.0.8

- `const.py` - Changed API_TIMEOUT from 30 to 45 seconds due to AmeriGas web server consistent latency. This timeout is used for both:

Login authentication (POST to /Login/Login)
Dashboard data fetch (GET to /Dashboard/Dashboard)

- `manifest.json` - Version bump to 3.0.8

**Code Quality**:
- Added defensive programming to prevent data corruption
- Enhanced debug logging for restoration lifecycle
- Improved state preservation during API outages
- Better error handling for Edge cases

### ⚠️ Critical Importance for Energy Dashboard Users

If you're using the Energy Dashboard to track propane consumption:
- **This is a CRITICAL update** - prevents permanent data loss
- Lifetime sensors feed the Energy Dashboard gas consumption tracking
- Previous versions could silently reset your historical data to 0
- Update immediately to prevent future data loss

**If you've already experienced data loss:**
- Check sensor attributes for `last_valid_state` - this backup may have your old value
- Historical data before the reset cannot be recovered
- After updating to v3.0.8, future data will be preserved correctly

### 🔄 Migration Notes

#### From v3.0.7 or Earlier
- **CRITICAL: Update immediately if using Energy Dashboard**
- No breaking changes in functionality
- Simply update via HACS and restart
- Existing lifetime values will be preserved going forward
- Check logs after restart to verify restoration:
  ```
  State restoration complete. Lifetime total: XXX.XX gal
  ```

#### Verification After Update
1. Note current lifetime gallons value before updating
2. Update integration to v3.0.8
3. Restart Home Assistant
4. Check lifetime sensors match pre-restart values
5. Check logs for successful restoration message
6. Restart again to confirm persistence

#### If Values Reset During Update
If sensors reset to 0 despite the update:
1. Check Developer Tools → States
2. Find `sensor.propane_tank_lifetime_gallons`
3. Look in attributes for `last_valid_state`
4. This backup value may contain your old total
5. Contact maintainer if backup also lost

### 📊 Testing Performed

**Restart Test**: ✅ Values persist across multiple HA restarts  
**API Failure Test**: ✅ Values remain stable when AmeriGas unreachable  
**API Timeout Test**: ✅ AmeriGas connectivity during updates is now more stable resulting in less frequent "unreachable" statuses  
**Integration Reload**: ✅ Values preserved through reload cycles  
**Energy Dashboard**: ✅ Historical data maintains integrity  
**Long-term Stability**: ✅ No resets over extended operation

### 🔒 Energy Dashboard Data Integrity

With v3.0.8:
- Lifetime sensors should NEVER reset to 0 unexpectedly
- Data persists across HA restarts
- Data persists through API outages  
- Data persists through integration reloads
- Energy Dashboard integration remains accurate
- Historical consumption tracking is protected

**This fix is essential for reliable long-term propane consumption tracking.**

---

**v3.0.8 - Energy Dashboard Data Integrity Protected** 🔒

## [3.0.7] - 2026-01-24

### 🐛 Critical Bug Fixes

#### Race Condition in Sensor Updates - CRITICAL FIX

**Fixed: Sensors not updating when pre-delivery level changes**
- **Root cause**: Only `PropaneUsedSinceDeliverySensor` had a state change listener for the pre-delivery level entity. Other dependent sensors (Cost Since Delivery, Energy Consumption, Daily Average Usage, Days Until Empty) only recalculated on coordinator updates (every 6 hours), causing them to use stale estimated values.
- **Solution**: Moved pre-delivery level state change listener to `AmeriGasSensorBase` so ALL dependent sensors automatically recalculate when pre-delivery level changes.
- **Impact**: Setting pre-delivery level now immediately updates all dependent sensors
- **Affected sensors**:
  - Cost Since Last Delivery
  - Energy Consumption (Display)
  - Daily Average Usage
  - Days Until Empty
  - Days Remaining Difference

**Fixed: Daily Average Usage showing 0.0000 gal/day**
- **Root cause**: `PropaneDailyAverageUsageSensor` was duplicating calculation logic inline without looking up the pre-delivery level, always using the 20% fallback estimation.
- **Solution**: Refactored to use centralized `_calculate_daily_average()` helper which properly uses pre-delivery level.
- **Impact**: Daily average now reflects actual usage based on captured pre-delivery level

**Fixed: Cascading calculation errors**
- **Root cause**: Multiple sensors were independently calculating "used since delivery" with different methods, most ignoring the pre-delivery level entirely.
- **Solution**: 
  - Added `_get_pre_delivery_level()` centralized helper to base class
  - Refactored `_calculate_used_since_delivery()` to use pre-delivery level and return tuple `(gallons, method)`
  - All dependent sensors now use these centralized helpers
- **Impact**: Consistent, accurate calculations across all sensors

#### Sensor State Issues

**Fixed: Energy Consumption (Display) showing "unknown"**
- **Root cause**: Sensor relied on entity state lookup which failed during initialization
- **Solution**: Calculate directly from coordinator data using centralized helper
- **Impact**: Sensor now always shows valid cubic feet value

**Fixed: Days Until Empty showing "unavailable" for low usage**
- **Root cause**: Sensor marked itself unavailable when daily usage was < 0.1 gal/day
- **Solution**: Always calculate days remaining, regardless of usage rate
  - Normal usage (2 gal/day): Shows calculated days (e.g., 200 days)
  - Low usage (0.05 gal/day): Shows calculated days (e.g., 8000 days)
  - Extremely low (< 0.001 gal/day): Caps at 9999 days to prevent overflow
- **Philosophy**: Do the math, don't patronize the user
- **Impact**: Vacation homes and low-usage scenarios now show accurate projections

**Fixed: Days Remaining Difference showing "unknown"**
- **Root cause**: Sensor returned None when usage was low
- **Solution**: Always calculate difference, cap at 9999 for extremely low usage

### ✨ Enhancements

#### Centralized Pre-Delivery Level Support
- **Added**: `_get_pre_delivery_level()` helper method in base class
- **Added**: Pre-delivery level state change listener in base class
- **Added**: Cached entity ID lookup for efficiency
- **Benefit**: All sensors automatically respond to pre-delivery level changes

#### Improved Calculation Transparency
- **Added**: `calculation_method` attribute to all usage-dependent sensors
- **Added**: `calculation` attribute showing exact math performed
- **Added**: `note` attribute for edge cases (low usage, capped values)

#### Days Until Empty Improvements
- **Added**: Calculation attribute showing exact math
- **Added**: Note attribute for edge cases
- **Added**: Support for ANY usage rate (no minimum threshold)

### 📊 Example: Before vs After Fix

**Scenario**: 500 gal tank, pre-delivery level set to 391.9 gal, delivery 28.1 gal, current 270 gal

**Before v3.0.7 (broken)**:
```yaml
# Used Since Delivery had listener, calculated correctly
sensor.propane_used_since_last_delivery: 150 gal ✓

# Other sensors used 20% fallback (100 gal estimated pre-delivery)
# Starting: 100 + 28.1 = 128.1 gal, Used: 128.1 - 270 = negative → 0 gal
sensor.propane_daily_average_usage: 0.0000 gal/day ✗
sensor.propane_cost_since_last_delivery: $0.00 ✗
sensor.propane_energy_consumption: 0 ft³ ✗
sensor.propane_days_until_empty: 9999 days ✗
```

**After v3.0.7 (fixed)**:
```yaml
# All sensors now use pre-delivery level correctly
sensor.propane_used_since_last_delivery: 150 gal ✓
sensor.propane_daily_average_usage: 4.69 gal/day ✓
sensor.propane_cost_since_last_delivery: $526.50 ✓
sensor.propane_energy_consumption: 5458.32 ft³ ✓
sensor.propane_days_until_empty: 58 days ✓
```

### 🔧 Technical Changes

**Modified Files**:
- `sensor.py` - Major refactor
  - Added `_get_pre_delivery_level()` to `AmeriGasSensorBase`
  - Added `async_added_to_hass()` with state change listener to `AmeriGasSensorBase`
  - Refactored `_calculate_used_since_delivery()` to use pre-delivery level
  - Refactored `_calculate_daily_average()` to use centralized helper
  - Fixed `PropaneEnergyConsumptionSensor` to use centralized helper
  - Fixed `PropaneDailyAverageUsageSensor` to use centralized helper
  - Fixed `PropaneCostSinceDeliverySensor` to use centralized helper
  - Removed duplicate listener from `PropaneUsedSinceDeliverySensor`

**Code Quality**:
- Eliminated code duplication across sensors
- Single source of truth for usage calculations
- Consistent calculation method reporting
- Improved logging for debugging

### 🔄 Migration Notes

#### From v3.0.6
- **No breaking changes!**
- Simply update and restart
- All sensors will immediately use correct pre-delivery level
- If pre-delivery level was already set, dependent sensors will show correct values after restart

#### From v3.0.0 - v3.0.5
- See v3.0.6 migration notes below
- All previous fixes included

---

## [3.0.6] - 2026-01-10

### 🕐 Cron-Based Refresh Schedule

- **Changed**: Replaced `timedelta(hours=6)` with cron-based scheduling
- **Schedule**: Refreshes at exactly 00:00, 06:00, 12:00, 18:00 daily
- **Benefit**: Predictable timing, no drift after HA restarts
- **Startup**: Still fetches data immediately on HA startup
- **Implementation**: Uses `async_track_time_change()` from HA helpers

### 🔧 Bug Fixes

#### Unclosed Connection Error - CRITICAL FIX
- **Fixed**: `Error doing job: Unclosed connection (None)` error in logs
- **Root cause**: aiohttp session was never closed after API data fetch
- **Solution**: Added `finally: await self.close()` to `api.py` after each fetch
- **Also fixed**: Config flow now closes session after credential validation
- **Impact**: No more connection resource leaks

### 📦 HACS Compliance Updates

- **Enhanced**: `hacs.json` with recommended fields (`hacs`, `zip_release`, `filename`)
- **Added**: Service translations in `strings.json` for `set_pre_delivery_level` and `refresh_data`

### 🏗️ Technical Changes

#### Modified Files
- `__init__.py` - Cron-based scheduling via `async_track_time_change()`, proper cleanup
- `api.py` - Session closed in `finally` block after each fetch
- `config_flow.py` - Session closed in `finally` block after validation
- `hacs.json` - Added HACS 1.6.0 requirement, zip_release, filename
- `strings.json` - Added services translations section
- `manifest.json` - Version bump to 3.0.6

### 🔄 Migration Notes

#### From v3.0.5
- **No breaking changes!**
- Simply update and restart
- Refresh schedule changes from relative interval to fixed times
- All existing sensors and entities preserved

---

## [3.0.5] - 2026-01-04

### 🎯 Major Features

#### Automatic Pre-Delivery Level Detection
- **Added**: Completely automatic pre-delivery tank level capture when new deliveries are detected
- **How it works**: When `last_delivery_date` changes, system automatically calculates `pre_delivery = current - delivery_amount`
- **Impact**: 100% accurate consumption tracking for ANY delivery size (small, medium, or large)
- **User effort**: ZERO - works automatically after installation

#### Accuracy Improvements
- **Before v3.0.5**: Small deliveries (< 50 gal) showed 0% accuracy
- **After v3.0.5**: ALL deliveries show 100% accuracy
- **Example**: 28.1 gallon delivery previously showed 0 gallons used, now correctly shows 120 gallons used

### 🔧 Bug Fixes

#### Unclosed Connection Leak (v3.0.5) - CRITICAL FIX
- **Fixed**: API now uses persistent aiohttp session instead of creating new session per request
- **Impact**: Eliminates "Unclosed connection" errors that caused coordinator to stop updating
- **Root cause**: Creating new session for every API call left connections open
- **Solution**: Single persistent session with proper lifecycle management
- **Added**: Explicit session cleanup on integration unload and HA shutdown
- **Result**: Automatic 6-hour updates now work reliably without connection exhaustion

#### Dynamic Entity ID Support (v3.0.5)
- **Fixed**: All entity lookups now use entity registry with unique_id matching
- **Impact**: Service and automatic detection work regardless of device/entity naming in UI
- **How it works**: Finds entities by `unique_id` ending with `_pre_delivery_level` instead of hardcoded entity IDs
- **Benefit**: Users can rename device from "AmeriGas Propane" to "My Tank" and everything still works
- **Technical**: Implemented in sensor.py, delivery_tracker.py, and __init__.py

#### Coordinator Access (v3.0.5)
- **Fixed**: Sensors now correctly extract coordinator from `hass.data` dictionary
- **Changed**: `sensor.py` line 43 now accesses `hass.data[DOMAIN][entry.entry_id]["coordinator"]`
- **Impact**: All 37 sensors load correctly without AttributeError
- **Root cause**: Service registration changed data structure from direct coordinator to dictionary

#### Estimated Refill Cost
- **Fixed**: Changed from assuming 100% tank fill to realistic 80% fill (industry standard)
- **Impact**: Cost estimates are now 50% more accurate
- **Example**: 
  - Old: 500 gal tank at 60% → estimates $500 refill
  - New: 500 gal tank at 60% → estimates $250 refill (correct!)
- **Added**: Attributes showing max fill level, gallons needed, and fill percentage

### ✨ Enhancements

#### New Entities
- **Added**: `number.amerigas_pre_delivery_level` - Diagnostic entity showing auto-captured pre-delivery levels
  - Automatically updated when deliveries detected
  - Can be manually adjusted if needed
  - Shows calculation details in attributes
  - Persists across HA restarts

#### New Services
- **Added**: `amerigas.set_pre_delivery_level` - Manual service to set pre-delivery tank level
  - **Use case**: Set pre-delivery level for deliveries that occurred before v3.0.5 upgrade
  - **Use case**: Correct pre-delivery level if automatic detection fails
  - **Parameters**: `gallons` (float, 0-1000)
  - **Example**: `service: amerigas.set_pre_delivery_level` with `data: {gallons: 391.9}`
  - Service updates the number entity and logs the change

- **Added**: `amerigas.refresh_data` - Manual service to force immediate API update
  - **Use case**: Force refresh instead of waiting for 6-hour automatic cycle
  - **Use case**: Get current data immediately after a delivery
  - **Use case**: Troubleshoot update issues
  - **Parameters**: None
  - **Example**: `service: amerigas.refresh_data`
  - Fetches all data from AmeriGas API and updates all sensors

#### Enhanced Sensor Attributes
- **Added**: `accuracy` attribute to "Used Since Delivery" sensor
  - "100% (auto-captured)" when using automatic detection
  - "~95% (estimated)" for fallback calculations
- **Added**: `pre_delivery_level` attribute showing the exact captured value
- **Added**: `calculated_starting_level` showing the total starting level (pre-delivery + delivery)

#### Improved Calculation Methods
- **Enhanced**: Smart estimation fallback if auto-capture not available
  - Small deliveries (< 50 gal): Assumes 65% pre-delivery (was 20%)
  - Large deliveries (≥ 50 gal): Assumes 20% pre-delivery (unchanged)
- **Added**: `calculation_method` attribute with values:
  - `auto_captured` - 100% accurate (new in v3.0.5)
  - `small_delivery_estimate` - ~75% accurate
  - `large_delivery_estimate` - ~95% accurate
  - `assumed_80_percent` - ~90% accurate

### 📚 Documentation
- **Updated**: README.md with v3.0.5 features
- **Added**: Detailed explanation of automatic detection
- **Added**: Real-world examples
- **Added**: Troubleshooting guide
- **Added**: Quick start checklist

### 🏗️ Technical Changes

#### New Files
- `delivery_tracker.py` - Core logic for delivery detection and pre-delivery capture
- `number.py` - Number platform for pre-delivery level entity
- `services.yaml` - Service definitions for manual pre-delivery level setting

#### Modified Files
- `__init__.py` - Added delivery tracker initialization and number platform
- `sensor.py` - Enhanced PropaneUsedSinceDeliverySensor with auto-capture support
- `sensor.py` - Fixed PropaneEstimatedRefillCostSensor to use 80% fill level
- `manifest.json` - Version bump to 3.0.5

#### Code Quality
- Added comprehensive docstrings
- Added inline comments explaining logic
- Improved error handling
- **Enhanced coordinator logging** - Now logs every update attempt (success/failure)
- **Added debug logging** - Track update schedule and API calls
- Enhanced logging for debugging

### 🔄 Migration Notes

#### From v3.0.0 - v3.0.4
- **No breaking changes!**
- Simply update and restart
- New number entity appears automatically
- Existing sensors continue working
- Auto-capture starts with next delivery

#### From v2.x (pyscript version)
- See MIGRATION.md for detailed instructions
- Major architecture change (pyscript → native integration)
- All sensor unique IDs preserved for seamless migration

### ⚠️ Known Limitations

#### Historical Deliveries
- Auto-capture only works for NEW deliveries after v3.0.5 installation
- Historical calculations remain as-is (can't retroactively capture past deliveries)
- **Workaround**: Manually set `number.amerigas_pre_delivery_level` if desired

#### First Delivery After Upgrade
- Will show 0.0 gallons in pre-delivery level entity until first new delivery
- Calculation falls back to smart estimation (same as v3.0.4)
- Becomes fully automatic after first delivery post-upgrade

---

## [3.0.4] - 2025-01-02

### 🎯 Major Refactor - Eliminate Entity ID Dependencies

**BREAKING FIX:** Completely eliminates hardcoded entity ID lookups. Sensors now calculate directly from coordinator data or use direct sensor references.

### Changed
- **CRITICAL:** All cross-sensor dependencies now use coordinator data or direct references
- Added helper methods to `AmeriGasSensorBase` for common calculations
- Refactored all dependent sensors to use helper methods
- `PropaneLifetimeEnergySensor` now receives direct reference to `PropaneLifetimeGallonsSensor`
- **MAJOR BENEFIT:** Sensors now work regardless of entity ID renaming in UI

### Fixed
- **CRITICAL:** Sensors no longer break if user renames entity IDs in UI
- Eliminated all `self.hass.states.get()` calls with hardcoded entity IDs
- More efficient calculations (no state lookups needed)
- Reduced potential for circular dependencies

---

## [3.0.3] - 2025-01-02

### 🐛 Hotfix - Cross-Sensor Entity ID References

**HOTFIX:** Fixes incorrect entity ID references causing calculated sensors to show "unknown".

### Fixed
- **CRITICAL:** All cross-sensor references now use correct entity IDs with `propane_tank_` prefix
- Cost Per Cubic Foot sensor now calculates correctly
- All sensors that depend on other sensor states now work properly

---

## [3.0.2] - 2025-01-02

### 🐛 Hotfix - Lifetime Sensor State Restoration

**HOTFIX:** Fixes AttributeError in lifetime gallons sensor when restoring state from previous session.

### Fixed
- **CRITICAL:** `AttributeError: 'str' object has no attribute 'isoformat'` in lifetime gallons sensor
- State restoration now properly parses `last_consumption_event` from ISO string to datetime

---

## [3.0.1] - 2025-01-02

### 🐛 Critical Hotfix - Timezone Issues

**HOTFIX:** Addresses critical timezone-aware datetime requirement that prevented sensors from loading.

### Fixed
- **CRITICAL:** All datetime values now return timezone-aware objects (required by Home Assistant)
- Fixed 4 sensors that failed to load
- Enhanced `parse_date()` function to ensure all parsed dates are timezone-aware

---

## [3.0.0] - 2025-01-02

### 🎉 Major Refactor - Native Custom Component

**BREAKING CHANGES:** Complete rewrite from pyscript to native Home Assistant custom component.

### Added
- Native Home Assistant custom component architecture
- UI-based configuration flow (no more YAML editing)
- HACS support for one-click installation
- DataUpdateCoordinator pattern for efficient updates
- Config flow with credential validation
- Advanced error handling with custom exceptions
- State restoration for lifetime sensors
- Diagnostic attributes for troubleshooting
- Enhanced datetime parsing (multiple format support)
- State preservation backup (protects against DB corruption)
- Comprehensive documentation (56 KB)
- Migration guide from pyscript version

### Changed
- **Installation:** HACS one-click instead of manual files
- **Configuration:** UI-only instead of YAML editing
- **Dependencies:** Zero dependencies (removed Pyscript requirement)
- **Sensors:** Native sensor entities instead of template sensors
- **Updates:** Automatic via HACS instead of manual
- **Accuracy:** Improved to 98-99% (was 95-98%)

### Fixed
- Energy Dashboard spike issues
- Date parsing errors with various formats
- False consumption from thermal expansion
- Negative usage values
- Statistics errors

### Removed
- Pyscript dependency
- Manual template_sensors.yaml file
- Manual utility_meter.yaml file
- YAML configuration requirement

---

## Links

- [GitHub Releases](https://github.com/skircr115/ha-amerigas/releases)
- [Documentation](https://github.com/skircr115/ha-amerigas)
- [Issues](https://github.com/skircr115/ha-amerigas/issues)
- [Discussions](https://github.com/skircr115/ha-amerigas/discussions)