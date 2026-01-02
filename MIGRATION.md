# Migration Guide: Pyscript → Custom Component

## Overview

This guide helps you migrate from the pyscript-based AmeriGas integration to the new HACS custom component.

**Benefits of migrating:**
- ✅ No Pyscript dependency
- ✅ UI configuration (no YAML editing)
- ✅ Native Home Assistant integration
- ✅ Easier updates via HACS
- ✅ All v2.1.0 improvements included
- ✅ Better error handling and diagnostics

**Migration time:** ~15 minutes

---

## Before You Start

### Backup Your Data

```bash
# Backup configuration
cd /config
cp configuration.yaml configuration.yaml.backup
cp -r pyscript pyscript.backup
cp template_sensors.yaml template_sensors.yaml.backup
cp utility_meter.yaml utility_meter.yaml.backup

# Optional: Backup database
cp home-assistant_v2.db home-assistant_v2.db.backup
```

### Note Current Values

Record these for comparison after migration:
- Tank level: `sensor.amerigas_tank_level`
- Lifetime gallons: `sensor.propane_lifetime_gallons`
- Lifetime energy: `sensor.propane_lifetime_energy`

**Important:** Lifetime values will reset to 0 (fresh start)

---

## Step 1: Remove Old Integration

### 1.1 Stop Home Assistant

```bash
# If using supervised/docker
ha core stop

# If using venv
sudo systemctl stop home-assistant@homeassistant
```

### 1.2 Remove Configuration

Edit `configuration.yaml` and remove:

```yaml
# REMOVE THESE SECTIONS:
pyscript:
  allow_all_imports: true
  hass_is_global: true
  apps:
    amerigas:
      username: "your_email@example.com"
      password: "your_password"

template: !include template_sensors.yaml

utility_meter: !include utility_meter.yaml
```

Save the file.

### 1.3 Remove Files

```bash
cd /config

# Remove pyscript integration
rm pyscript/amerigas.py

# Remove template files
rm template_sensors.yaml
rm utility_meter.yaml

# Optional: Remove Pyscript entirely if not used elsewhere
# Only do this if AmeriGas was your only pyscript!
# rm -rf pyscript
```

---

## Step 2: Install Custom Component

### Option A: Install via HACS (Recommended)

1. **Open HACS**
   - Go to HACS → Integrations

2. **Add Custom Repository**
   - Click "⋮" (three dots) → Custom repositories
   - Repository: `https://github.com/skircr115/ha-amerigas`
   - Category: Integration
   - Click "Add"

3. **Install**
   - Search for "AmeriGas Propane"
   - Click "Download"
   - Click "Download" again to confirm

4. **Restart Home Assistant**
   ```bash
   # Supervised/docker
   ha core restart
   
   # Venv
   sudo systemctl restart home-assistant@homeassistant
   ```

### Option B: Manual Installation

1. **Download Integration**
   ```bash
   cd /config
   git clone https://github.com/skircr115/ha-amerigas.git temp
   ```

2. **Copy Files**
   ```bash
   mkdir -p custom_components
   cp -r temp/custom_components/amerigas custom_components/
   rm -rf temp
   ```

3. **Verify Structure**
   ```bash
   ls -la custom_components/amerigas/
   # Should show:
   # __init__.py
   # api.py
   # config_flow.py
   # const.py
   # manifest.json
   # sensor.py
   # strings.json
   ```

4. **Restart Home Assistant**

---

## Step 3: Configure New Integration

### 3.1 Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"** (bottom right)
3. Search: **"AmeriGas Propane"**
4. Select it

### 3.2 Enter Credentials

1. **Email Address**: your_email@example.com
2. **Password**: your_password
3. Click **"Submit"**

### 3.3 Verify Setup

You should see:
- ✅ "Success!" message
- ✅ "AmeriGas Propane" device with 37 sensors
- ✅ All sensors showing values (not "unavailable")

Check: **Developer Tools** → **States** → Search "amerigas"

Expected sensors:
- sensor.amerigas_tank_level
- sensor.propane_gallons_remaining
- sensor.propane_lifetime_gallons
- sensor.propane_lifetime_energy
- ...and 33 more

---

## Step 4: Update Energy Dashboard

### 4.1 Remove Old Sensor

1. Settings → Dashboards → Energy
2. Find your propane gas source
3. Click the trash icon to remove it

### 4.2 Add New Sensor

1. Click **"Add Gas Source"**
2. Select: **Lifetime Energy** (sensor.propane_lifetime_energy)
3. (Optional) Add cost sensor: **Cost Since Last Delivery**
4. Click **"Save"**

### 4.3 Fix Statistics (if needed)

You may see warnings about unit changes:

1. Developer Tools → Statistics
2. Search: "propane"
3. Click **"Fix issue"** on any warnings
4. Confirm changes

---

## Step 5: Update Automations & Dashboards

### 5.1 Check Automations

Review automations that reference AmeriGas sensors:

**Old entity IDs** → **New entity IDs** (mostly the same)

| Old | New | Change? |
|-----|-----|---------|
| sensor.amerigas_tank_level | sensor.amerigas_tank_level | ✅ No change |
| sensor.propane_lifetime_gallons | sensor.propane_lifetime_gallons | ✅ No change |
| sensor.propane_lifetime_energy | sensor.propane_lifetime_energy | ✅ No change |

Most entity IDs are the same! Just verify they're working.

### 5.2 Update Dashboard Cards

Test all dashboard cards using AmeriGas sensors:

1. Go to each dashboard
2. Click Edit
3. Verify cards load properly
4. Update any broken references

### 5.3 Update Scripts

If you have scripts calling services:

**Old (pyscript):**
```yaml
service: pyscript.amerigas_update
```

**New (native):**
```yaml
service: homeassistant.update_entity
data:
  entity_id: sensor.amerigas_tank_level
```

---

## Step 6: Verify Everything Works

### 6.1 Check Sensors

Developer Tools → States → Search "amerigas"

Verify:
- [ ] All 37 sensors present
- [ ] No sensors show "unavailable"
- [ ] Values look correct
- [ ] Tank level matches MyAmeriGas website

### 6.2 Test Manual Update

1. Developer Tools → Services
2. Service: `homeassistant.update_entity`
3. Entity: `sensor.amerigas_tank_level`
4. Click **"Call Service"**
5. Check logs for success message

### 6.3 Check Logs

Settings → System → Logs → Search "amerigas"

Expected:
```
AmeriGas: Successfully updated all sensors
Tank: 65%, Days: 45
```

No errors expected.

### 6.4 Wait 24 Hours

Monitor for:
- Lifetime sensors incrementing properly
- No "unavailable" sensors
- Energy Dashboard showing data
- No errors in logs

---

## Troubleshooting

### Sensors Show "Unavailable"

**Check:**
1. Settings → Devices & Services → AmeriGas → Configure
2. Re-enter credentials if needed
3. Check logs for authentication errors

**Fix:**
```yaml
# Settings → Devices & Services → AmeriGas
# Click "..." → Delete
# Re-add integration with correct credentials
```

### Energy Dashboard Not Working

**Verify sensor:**
```
Developer Tools → States → sensor.propane_lifetime_energy

Must have:
- state_class: total_increasing ✓
- device_class: gas ✓
- unit: ft³ ✓
```

**Fix statistics:**
```
Developer Tools → Statistics
Search: propane_lifetime_energy
Fix any issues listed
```

### Lifetime Values Reset to 0

**Expected behavior.** The new integration starts fresh.

**To track:**
- Note old lifetime value before migration
- Add to new value after migration
- Or accept fresh start (recommended)

### Old Sensors Still Showing

**Remove orphaned entities:**
```
Settings → Devices & Services → Entities
Search: "amerigas" or "propane"
Select old entities → Delete
```

### Automations Not Triggering

**Update entity IDs:**
```yaml
# Check automation uses new entity names
# Most are the same, but verify in:
# Settings → Automations & Scenes
```

---

## Rollback (If Needed)

If you need to go back to pyscript version:

### 1. Remove Custom Component

```bash
cd /config
rm -rf custom_components/amerigas
```

### 2. Delete Integration

Settings → Devices & Services → AmeriGas → Delete

### 3. Restore Backups

```bash
cd /config
cp configuration.yaml.backup configuration.yaml
cp -r pyscript.backup/* pyscript/
cp template_sensors.yaml.backup template_sensors.yaml
cp utility_meter.yaml.backup utility_meter.yaml
```

### 4. Restart Home Assistant

```bash
ha core restart
```

### 5. Restore Energy Dashboard

Settings → Dashboards → Energy
Add back: sensor.propane_energy_consumption (old sensor)

---

## Post-Migration Checklist

- [ ] Pyscript configuration removed
- [ ] Old files deleted
- [ ] Custom component installed
- [ ] Integration configured via UI
- [ ] All 37 sensors working
- [ ] Energy Dashboard updated
- [ ] Automations updated
- [ ] Dashboard cards working
- [ ] No errors in logs
- [ ] Lifetime tracking working
- [ ] Manual update tested
- [ ] Backups created

---

## FAQ

**Q: Will I lose historical data?**
A: Historical data in the database remains. Lifetime sensors start fresh at 0.

**Q: Can I run both versions?**
A: No. Remove pyscript version before installing custom component.

**Q: Do I need to reconfigure automations?**
A: Mostly no. Entity IDs are the same. Just verify they work.

**Q: How long does migration take?**
A: 10-15 minutes for most users.

**Q: Can I migrate back?**
A: Yes, if you have backups. See Rollback section above.

**Q: Why are lifetime sensors reset?**
A: Different integration = fresh start. This is normal and expected.

**Q: Will Energy Dashboard break?**
A: No, but you need to update the gas source sensor.

**Q: What if I have problems?**
A: Check Troubleshooting section or open an issue on GitHub.

---

## Need Help?

- 🐛 **Issues**: [GitHub Issues](https://github.com/skircr115/ha-amerigas/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/skircr115/ha-amerigas/discussions)
- 📖 **Docs**: [README](README.md)

---

## Benefits Summary

| Feature | Pyscript | Custom Component |
|---------|----------|------------------|
| **Installation** | Manual YAML | HACS + UI |
| **Configuration** | Edit YAML | UI only |
| **Updates** | Manual | HACS automatic |
| **Dependencies** | Pyscript required | None |
| **Error Messages** | Basic | Detailed |
| **Diagnostics** | Limited | Full |
| **Version** | v2.0.0 | v3.0.4 |
| **Accuracy** | 95-98% | 98-99% |

**Migration is worth it!** ✅

---

**Ready to migrate? Start with Step 1!**
