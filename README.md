# Amerigas-Home-Assistant-Integration
A complete Home Assistant integration for monitoring your AmeriGas propane account, including tank level, delivery history, payments, and Energy Dashboard integration.

📋 Features

Real-time Tank Monitoring - Current tank level, gallons remaining, days until empty
Delivery Tracking - Last delivery date, gallons delivered, next scheduled delivery
Payment Information - Amount due, account balance, last payment details
Cost Analysis - Cost per gallon, estimated refill cost, usage rates
Energy Dashboard Integration - Track propane consumption alongside electricity
Automated Updates - Auto-refresh every 6 hours + on Home Assistant startup

📦 What's Included

15 sensors from AmeriGas portal
8 calculated template sensors for usage tracking
9 utility meters (daily/monthly/yearly for gallons, energy, and cost)
Energy Dashboard ready with cost tracking
Example automations and dashboard cards


🚀 Installation
Prerequisites

Pyscript - Install via HACS

Go to HACS > Integrations
Search for "Pyscript Python scripting"
Install and restart Home Assistant


AmeriGas Account - Active MyAmeriGas online account credentials

Step 1: Enable Pyscript
Add to configuration.yaml:
yamlpyscript:
  allow_all_imports: true
  hass_is_global: true
  apps:
    amerigas:
      username: "your_email@example.com"
      password: "your_password_here"
⚠️ Important: Credentials must be in configuration.yaml under pyscript:, NOT in secrets.yaml
Step 2: Create Directory Structure
config/
├── pyscript/
│   └── amerigas.py
├── template_sensors.yaml
├── utility_meter.yaml
└── configuration.yaml
Step 3: Install Files
