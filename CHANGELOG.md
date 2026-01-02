# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Improved "used since delivery" calculation (uses actual delivery amounts)
- Better "unknown" handling (shows "unavailable" instead of "0" or "999")
- Lifetime sensors now use RestoreEntity pattern

### Fixed
- All v2.0.1 critical fixes included:
  - Noise filtering (0.5 gal threshold)
  - Bounds checking (0-100% tank level)
  - Tank size validation
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

### Migration Required
- See [MIGRATION.md](MIGRATION.md) for complete guide
- Lifetime sensors will reset (fresh start)
- Energy Dashboard sensor change required
- All entity IDs remain the same

---

## [2.1.0] - (Planned, skipped to 3.0.0)

### Added (Incorporated into 3.0.0)
- Better unknown handling
- Improved overfill logic
- Enhanced datetime parsing
- State preservation backup
- Diagnostic attributes

---

## [2.0.1] - (Never Released)

### Fixed (Incorporated into 3.0.0)
- Noise filtering (0.5 gal threshold)
- Bounds checking on tank level
- Tank size availability validation

---

## [2.0.0]

### Added
- Lifetime tracking sensors (ratchet mechanism)
- Energy Dashboard integration (fixed spikes)
- State-triggered updates instead of time-triggered
- Proper state_class attributes

### Changed
- Energy Dashboard sensor: Use `propane_lifetime_energy` instead of `propane_energy_consumption`

### Fixed
- Energy Dashboard spikes from time-triggered updates
- Statistics errors from incorrect state_class
- Datetime parsing with timezone support
- Negative consumption from thermal expansion

### Removed
- Cost utility meters (incompatible with delivery reset)

---

## [1.x]

### Initial Release
- Pyscript-based integration
- 15 base sensors from AmeriGas API
- Template sensors for calculations
- Utility meters for tracking
- Basic Energy Dashboard support

---

## Version Comparison

| Feature | v1.x | v2.0.0 | v3.0.0 |
|---------|------|--------|--------|
| Architecture | Pyscript | Pyscript | Native Component |
| Installation | Manual | Manual | HACS |
| Configuration | YAML | YAML | UI |
| Dependencies | Pyscript | Pyscript | None |
| Accuracy | 85% | 95% | 98-99% |
| Energy Dashboard | Basic | Fixed | Optimized |
| Error Handling | Basic | Good | Advanced |

---

## Upgrade Paths

### From v1.x → v3.0.0
1. Read [MIGRATION.md](MIGRATION.md)
2. Remove old pyscript configuration
3. Install v3.0.0 via HACS
4. Configure via UI
5. Update Energy Dashboard

### From v2.0.0 → v3.0.0
Same as v1.x → v3.0.0 (both used pyscript)

---

## Links

- [GitHub Releases](https://github.com/skircr115/ha-amerigas/releases)
- [Documentation](https://github.com/skircr115/ha-amerigas)
- [Issues](https://github.com/skircr115/ha-amerigas/issues)
- [Discussions](https://github.com/skircr115/ha-amerigas/discussions)
