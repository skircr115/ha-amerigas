# AmeriGas Propane - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

Monitor your AmeriGas propane account directly in Home Assistant!

## Features

🔥 **Real-time Tank Monitoring**
- Current tank level percentage
- Gallons remaining
- Days until empty estimate

🚚 **Delivery Tracking**
- Last delivery date and amount
- Next scheduled delivery
- Delivery history

💰 **Financial Tracking**
- Current account balance
- Amount due
- Cost per gallon
- Payment history

📊 **Usage Analytics**
- Daily average usage
- Consumption trends
- Cost analysis

⚡ **Energy Dashboard**
- Full Home Assistant Energy Dashboard integration
- Clean, spike-free data
- Lifetime consumption tracking

🎯 **98-99% Accuracy**
- Advanced noise filtering
- Thermal expansion handling
- Bounds checking

## Quick Install

1. **HACS** → **Integrations** → Search **"AmeriGas"** → **Install**
2. **Restart** Home Assistant
3. **Settings** → **Devices & Services** → **Add Integration** → **AmeriGas Propane**
4. Enter your MyAmeriGas credentials
5. Done! ✅

## What You Get

### 37 Sensors
- 15 base sensors from AmeriGas
- 11 calculated sensors
- 2 lifetime tracking sensors
- Full Energy Dashboard support

### Zero Dependencies
- No Pyscript required
- No YAML editing
- Pure custom component

### Easy Updates
- Automatic via HACS
- One-click install
- No manual file management

## Configuration

**All configuration via UI - No YAML editing!**

Settings → Devices & Services → Add Integration → AmeriGas Propane

Enter:
- Email: your MyAmeriGas email
- Password: your MyAmeriGas password

That's it!

## Energy Dashboard

1. Settings → Energy → Add Gas Source
2. Select: **Lifetime Energy** sensor
3. (Optional) Add cost tracking
4. Enjoy clean propane data!

## Documentation

- [README](https://github.com/skircr115/ha-amerigas)
- [Migration Guide](https://github.com/skircr115/ha-amerigas/blob/main/MIGRATION.md)
- [Troubleshooting](https://github.com/skircr115/ha-amerigas#troubleshooting)

## Support

- [Issues](https://github.com/skircr115/ha-amerigas/issues)
- [Discussions](https://github.com/skircr115/ha-amerigas/discussions)
- [Community Forum](https://community.home-assistant.io/)

---

**Version:** 3.0.0  
**Author:** [@skircr115](https://github.com/skircr115)  
**License:** MIT

*This is an unofficial integration. Not affiliated with AmeriGas.*
