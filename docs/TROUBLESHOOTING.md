# Troubleshooting Guide

This guide helps you resolve common issues with the AmeriGas Home Assistant integration.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Installation Issues](#installation-issues)
- [Login & Authentication](#login--authentication)
- [Sensor Issues](#sensor-issues)
- [Template Sensor Errors](#template-sensor-errors)
- [Energy Dashboard Issues](#energy-dashboard-issues)
- [Performance Issues](#performance-issues)
- [Advanced Debugging](#advanced-debugging)

---

## Quick Diagnostics

### Step 1: Check Pyscript Status
```
Settings → Devices & Services → Integrations → Pyscript
```

**Status should be:** "Loaded"

If not loaded:
1. Verify Pyscript is installed via HACS
2. Check `configuration.yaml` has `pyscript:` section
3. Restart Home Assistant

### Step 2: Check Credentials
```yaml
# configuration.yaml
pyscript:
  allow_all_imports: true
  hass_is_global: true
  apps:
    amerigas:
      username: "your_email@example.com"  # ← Check this
      password: "your_password"            # ← And this
```

**Test credentials:**
- Login at https://www.myamerigas.com
- If login fails there, it will fail in HA

### Step 3: Check Logs
```
Settings → System → Logs
```

**Search for:** "AmeriGas"

**Look for:**
- ✅ "AmeriGas: Login successful"
- ✅ "AmeriGas: Successfully updated all sensors"
- ❌ "AmeriGas: Login failed"
- ❌ "AmeriGas: Could not find accountSummaryViewModel"

### Step 4: Manual Update Test
```
Developer Tools → Services
Service: pyscript.amerigas_update
[Call Service]
```

**Check logs immediately** after calling service.

### Step 5: Verify Sensors Exist
```
Developer Tools → States
```

**Search for:** "amerigas"

**You should see 15 sensors:**
- sensor.amerigas_tank_level
- sensor.amerigas_tank_size
- sensor.amerigas_days_remaining
- sensor.amerigas_amount_due
- sensor.amerigas_account_balance
- sensor.amerigas_last_payment_date
- sensor.amerigas_last_payment_amount
- sensor.amerigas_last_tank_reading
- sensor.amerigas_last_delivery_date
- sensor.amerigas_last_delivery_gallons
- sensor.amerigas_next_delivery_date
- sensor.amerigas_auto_pay
- sensor.amerigas_paperless
- sensor.amerigas_account_number
- sensor.amerigas_service_address

---

## Installation Issues

### Pyscript Not Found

**Problem:** Can't find Pyscript in HACS

**Solution:**
1. Go to HACS → Integrations
2. Click "⋮" (three dots) → Custom repositories
3. Add: `https://github.com/custom-components/pyscript`
4. Category: Integration
5. Click "Add"
6. Search for "Pyscript" and install

### Files Not Loading

**Problem:** Integration not working after installation

**Solution:**
```bash
# Verify file structure
ls -la config/pyscript/
# Should show: amerigas.py

ls -la config/
# Should show: template_sensors.yaml, utility_meter.yaml

# Check file permissions
chmod 644 config/pyscript/amerigas.py
chmod 644 config/template_sensors.yaml
chmod 644 config/utility_meter.yaml
```

### Configuration Not Applied

**Problem:** Changes to configuration.yaml not taking effect

**Solution:**
1. Check YAML syntax:
```
   Developer Tools → YAML → Check Configuration
```
2. Look for red errors
3. Fix any indentation issues (use spaces, not tabs)
4. Restart Home Assistant completely

---

## Login & Authentication

### Login Failed: Invalid Credentials

**Problem:** "AmeriGas: Login failed - Invalid credentials"

**Checklist:**
- [ ] Credentials work on https://www.myamerigas.com
- [ ] Username is email address
- [ ] Password has no special characters causing YAML issues
- [ ] No extra spaces in username/password
- [ ] Quotes around credentials in YAML

**Special Characters in Password:**

If password has quotes or special YAML characters:
```yaml
# Use single quotes if password has double quotes
password: 'my"pass"word'

# Use double quotes if password has single quotes
password: "my'pass'word"

# Escape backslashes
password: "my\\password"
```

### Login Failed: Timeout

**Problem:** "AmeriGas: Network error - timeout"

**Possible causes:**
1. **Internet connectivity issue**
   - Test: `ping www.myamerigas.com` from HA host
   
2. **DNS resolution problem**
   - Add to configuration.yaml:
```yaml
     # Under pyscript/apps/amerigas:
     timeout: 60  # Increase timeout
```

3. **Firewall blocking**
   - Check firewall logs
   - Allow outbound HTTPS (port 443) to myamerigas.com

### Login Failed: 2FA or Security Questions

**Problem:** AmeriGas requires additional authentication

**Current Status:** This integration does NOT support:
- Two-factor authentication (2FA)
- Security questions
- CAPTCHA challenges

**Workarounds:**
1. Disable 2FA on AmeriGas account (if possible)
2. Use account that doesn't require 2FA
3. Contact AmeriGas to remove 2FA requirement

### Account Locked

**Problem:** Too many login attempts

**Solution:**
1. Wait 30 minutes
2. Login manually at https://www.myamerigas.com
3. Reset password if needed
4. Update credentials in HA
5. Increase `scan_interval` in script:
```python
   # In amerigas.py, change cron schedule:
   @time_trigger("cron(0 */12 * * *)")  # Every 12 hours instead of 6
```

---

## Sensor Issues

### All Sensors Show "Unavailable"

**Problem:** All 15 AmeriGas sensors are "unavailable"

**Diagnosis:**
```
Developer Tools → States → sensor.amerigas_tank_level
```

If shows "unavailable":

**Steps:**
1. Check logs for errors
2. Call `pyscript.amerigas_update` manually
3. Check credentials are correct
4. Verify Pyscript is loaded
5. Restart Home Assistant

### Sensors Show "Unknown"

**Problem:** Sensors exist but state is "unknown"

**Causes:**
1. **Never updated** - Call `pyscript.amerigas_update`
2. **Data not in account** - Some fields may not apply to all accounts
3. **Parsing error** - Check logs for "Could not parse"

**Normal "unknown" sensors:**
- `sensor.amerigas_next_delivery_date` - If on automatic delivery
- Template sensors - If base sensor is unknown

### Tank Level Not Updating

**Problem:** `sensor.amerigas_tank_level` stuck at old value

**Causes:**
1. **Tank monitor offline** - Check AmeriGas website
2. **Update not running** - Call service manually
3. **AmeriGas website issue** - Wait and retry

**Check:**
```yaml
# Check last_monitor_reading attribute
Developer Tools → States → sensor.amerigas_tank_level
# Look at: last_monitor_reading
```

If > 48 hours old, tank monitor may be offline.

### Cost Sensors Show Zero

**Problem:** `sensor.propane_cost_per_gallon` shows 0

**Cause:** No delivery data yet

**Solution:**
1. Wait for first delivery after setup
2. Or manually set initial values:
```yaml
   # In template_sensors.yaml, add fallback:
   {{ (last_payment / last_delivery) | round(2) if last_delivery > 0 else 3.00 }}
```

### Next Delivery Always "Unknown"

**Problem:** `sensor.amerigas_next_delivery_date` always shows "unknown"

**Explanation:** This is **normal** for automatic delivery customers.

AmeriGas doesn't pre-schedule automatic deliveries - they deliver based on usage predictions.

**Only shows date when:**
- You have a will-call account
- You manually scheduled a delivery
- You have an open order

---

## Template Sensor Errors

### Template Error: NoneType

**Error:**
```
TemplateError('TypeError: unsupported operand type(s) for -: 'datetime.datetime' and 'NoneType'')
```

**Cause:** Base sensor is "unknown" or "unavailable"

**Solution:** Already fixed in provided template_sensors.yaml

If you modified templates, add null checks:
```yaml
state: >
  {% set last_delivery_date = states('sensor.amerigas_last_delivery_date') %}
  {% if last_delivery_date not in ['Unknown', 'unknown', 'unavailable', 'none', 'None'] %}
    {% set delivery_datetime = as_datetime(last_delivery_date) %}
    {% if delivery_datetime is not none %}
      # Your calculation here
    {% else %}
      {{ 0 }}
    {% endif %}
  {% else %}
    {{ 0 }}
  {% endif %}
```

### Template Sensors Not Loading

**Problem:** Template sensors don't appear

**Checklist:**
- [ ] `template_sensors.yaml` exists in config folder
- [ ] `configuration.yaml` has `template: !include template_sensors.yaml`
- [ ] YAML syntax is correct
- [ ] No duplicate unique_id values
- [ ] Reloaded template entities

**Reload:**
```
Developer Tools → YAML → Reload Template Entities
```

### Utility Meters Not Working

**Problem:** Utility meters show unavailable

**Cause:** Source sensor not available yet

**Solution:**
1. Ensure source sensor exists and has a value
2. Check source sensor state class:
```
   Developer Tools → States → sensor.propane_energy_consumption
```
   Must have: `state_class: total_increasing`

3. Restart Home Assistant after creating utility meters

---

## Energy Dashboard Issues

### Propane Not Showing in Gas Source Picker

**Problem:** Can't add propane to Energy Dashboard

**Requirements Check:**
```
Developer Tools → States → sensor.propane_energy_consumption
```

**Must have:**
- `device_class: gas` ✓
- `state_class: total_increasing` ✓
- `unit_of_measurement: ft³` ✓ (with superscript 3)

**Common Issues:**

1. **Wrong unit:** `ft3` instead of `ft³`
   - Must use Unicode superscript: ³
   - Copy from template_sensors.yaml

2. **Wrong state_class:** `measurement` instead of `total_increasing`
   - Check template_sensors.yaml

3. **Statistics errors:**
```
   Developer Tools → Statistics → Search "propane_energy_consumption"
```
   - Fix any listed issues
   - May need to delete and recreate sensor

### Cost Tracking Not Working

**Problem:** Energy Dashboard not showing costs

**Solution:**

**Option 1:** Use cost sensor
```
Energy Dashboard Settings → Gas Source → 
Use an entity tracking the total costs →
Select: sensor.propane_cost_since_last_delivery
```

**Option 2:** Use fixed price
```
Energy Dashboard Settings → Gas Source →
Enter fixed price: 0.0825  # Adjust to your $/ft³
```

**Calculate your price:**
```
Price per ft³ = (Price per gallon) / 36.3888

Example:
$3.00/gal ÷ 36.3888 = $0.0825/ft³
```

### Statistics Errors

**Problem:** "Fix issue" button in Statistics

**Common Errors:**

**1. Unit Change**
```
Error: Unit changed from 'gal' to 'ft³'
```
**Solution:** Click "Fix issue" and confirm

**2. State Class Change**
```
Error: State class changed from 'measurement' to 'total_increasing'
```
**Solution:** Click "Fix issue" and confirm

**3. Reset Statistics**

If statistics are corrupted:
```sql
# In Home Assistant database
DELETE FROM statistics WHERE metadata_id = 
  (SELECT id FROM statistics_meta WHERE statistic_id = 'sensor.propane_energy_consumption');
DELETE FROM statistics_short_term WHERE metadata_id = 
  (SELECT id FROM statistics_meta WHERE statistic_id = 'sensor.propane_energy_consumption');
```

**Easier way:**
```
Developer Tools → Statistics → 
sensor.propane_energy_consumption →
[Fix issue] → Delete statistics
```

Then restart HA to rebuild statistics.

---

## Performance Issues

### Home Assistant Slow After Installation

**Problem:** HA sluggish after adding integration

**Unlikely cause** - Integration is lightweight

**Check:**
1. Number of sensors (should be ~35 total)
2. Update frequency (default 6 hours)
3. Log file size

**Reduce load:**
```python
# In amerigas.py, increase interval:
@time_trigger("cron(0 */12 * * *)")  # Every 12 hours
```

### Update Takes Too Long

**Problem:** Manual update takes >30 seconds

**Normal:** 10-20 seconds is typical

**If > 60 seconds:**
1. Check internet speed
2. Increase timeout in code
3. Check AmeriGas website responsiveness

---

## Advanced Debugging

### Enable Debug Logging

**For Pyscript:**
```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.pyscript: debug
    custom_components.pyscript.file.amerigas: debug
```

**For Templates:**
```yaml
logger:
  logs:
    homeassistant.components.template: debug
```

Restart HA, then check logs.

### Inspect Raw Account Data

Add to `amerigas.py` after successful parse:
```python
log.info(f"Raw account data: {json.dumps(account_data, indent=2)}")
```

This will dump all available data to logs.

### Test Login Manually

Create test script:
```python
# test_login.py
import requests
import base64

username = "your_email@example.com"
password = "your_password"

encoded_email = base64.b64encode(username.encode()).decode()
encoded_password = base64.b64encode(password.encode()).decode()

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
})

login_data = {
    'loginViewModel[EmailAddress]': encoded_email,
    'loginViewModel[Password]': encoded_password,
}

response = session.post('https://www.myamerigas.com/Login/Login', data=login_data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")
```

Run outside HA to test.

### Check Network Connectivity

From HA host:
```bash
# Test DNS
nslookup www.myamerigas.com

# Test connectivity
curl -I https://www.myamerigas.com

# Test with timeout
curl --max-time 30 https://www.myamerigas.com/Login/SignIn
```

### Validate YAML Files
```bash
# Install yamllint
pip install yamllint

# Check files
yamllint config/template_sensors.yaml
yamllint config/utility_meter.yaml
yamllint config/configuration.yaml
```

### Reset Everything

**Nuclear option** - start fresh:
```bash
# Backup first!
cp config/pyscript/amerigas.py config/pyscript/amerigas.py.backup
cp config/template_sensors.yaml config/template_sensors.yaml.backup

# Remove sensors from HA
rm config/.storage/core.entity_registry

# Restart HA

# Reinstall files

# Restart again
```

---

## Common Error Messages

### "Could not find accountSummaryViewModel"

**Meaning:** Couldn't parse dashboard data

**Causes:**
1. AmeriGas changed website structure
2. Login failed but script continued
3. Account access issue

**Solution:**
1. Check if you can access dashboard manually
2. Check logs for login errors
3. Report issue on GitHub if persistent

### "Network error - Connection refused"

**Meaning:** Can't reach AmeriGas website

**Causes:**
1. Internet down
2. Firewall blocking
3. AmeriGas website down

**Test:**
```bash
curl https://www.myamerigas.com
```

### "JSON parsing error"

**Meaning:** Received invalid data from website

**Causes:**
1. AmeriGas website returned error page
2. Data format changed
3. Account access restricted

**Debug:**
Enable debug logging to see raw response.

---

## Still Need Help?

### Before Asking for Help

**Provide:**
1. ✅ Home Assistant version
2. ✅ Pyscript version
3. ✅ Full error message from logs
4. ✅ Sensor states (screenshot of Developer Tools → States)
5. ✅ What you already tried
6. ❌ Don't share passwords!

### Get Support

- 💬 [GitHub Discussions](https://github.com/skircr115/ha-amerigas/discussions) - General questions
- 🐛 [GitHub Issues](https://github.com/skircr115/ha-amerigas/issues) - Bug reports
- 🏠 [Home Assistant Forum](https://community.home-assistant.io/) - HA-specific questions

### Report a Bug

When opening an issue:
```markdown
**Version:** HA 2024.1.0, Pyscript 1.5.0
**Problem:** Sensors show unavailable
**Error:** [Paste error from logs]
**Steps to reproduce:**
1. Install integration
2. Configure credentials
3. Call amerigas_update
**Expected:** Sensors populate
**Actual:** All sensors unavailable
```

---

**[← Back to README](README.md)**
```

Save this as `docs/TROUBLESHOOTING.md` in your repository.

## Other Recommendations:

1. **Add `.gitignore`** to prevent committing secrets:
```
__pycache__/
*.pyc
.DS_Store
secrets.yaml
