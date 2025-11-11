# Automation Examples

This document contains ready-to-use automation examples for the AmeriGas Home Assistant integration.

## Table of Contents

- [Alert Automations](#alert-automations)
- [Notification Automations](#notification-automations)
- [Reporting Automations](#reporting-automations)
- [Advanced Automations](#advanced-automations)

---

## Alert Automations

### Low Propane Alert (Critical)

Alert when tank drops below 30% with detailed information.

```yaml
alias: "Low Propane Alert"
description: "Alert when tank drops below 30%"
trigger:
  - platform: numeric_state
    entity_id: sensor.amerigas_tank_level
    below: 30
condition:
  - condition: template
    value_template: "{{ states('sensor.amerigas_tank_level') | int > 0 }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "⚠️ Low Propane Level"
      message: >
        Tank is at {{ states('sensor.amerigas_tank_level') }}%.
        {{ states('sensor.propane_tank_gallons_remaining') }} gallons remaining.
        Estimated {{ states('sensor.propane_days_until_empty') }} days left.
        
        Daily usage: {{ states('sensor.propane_daily_average_usage') }} gal/day
      data:
        importance: high
        tag: low_propane
        channel: Alerts
        actions:
          - action: URI
            title: "Order Delivery"
            uri: https://www.myamerigas.com
```

### Critical Low (Emergency)

Alert when tank drops below 20% - immediate action needed.

```yaml
alias: "Critical Low Propane Alert"
description: "Emergency alert when tank below 20%"
trigger:
  - platform: numeric_state
    entity_id: sensor.amerigas_tank_level
    below: 20
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "🚨 CRITICAL: Propane Emergency"
      message: >
        URGENT: Tank at {{ states('sensor.amerigas_tank_level') }}%!
        Only {{ states('sensor.propane_tank_gallons_remaining') }} gallons left.
        Contact AmeriGas immediately: 800-263-7442
      data:
        importance: max
        tag: critical_propane
        channel: Emergency
        ttl: 0
        priority: high
  - service: persistent_notification.create
    data:
      title: "🚨 Critical Propane Level"
      message: >
        Tank at {{ states('sensor.amerigas_tank_level') }}%!
        Call AmeriGas: 800-263-7442
      notification_id: critical_propane
```

### High Usage Alert

Alert when daily usage is unusually high.

```yaml
alias: "High Propane Usage Alert"
description: "Alert when daily usage exceeds normal threshold"
trigger:
  - platform: numeric_state
    entity_id: sensor.propane_daily_average_usage
    above: 10  # Adjust based on your typical usage
    for:
      hours: 2
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "📈 High Propane Usage Detected"
      message: >
        Daily usage is {{ states('sensor.propane_daily_average_usage') }} gal/day,
        which is higher than normal.
        
        Possible causes:
        - Cold weather
        - Gas leak
        - Equipment malfunction
        - Guest usage
        
        Check your system and monitor usage.
      data:
        tag: high_usage
        channel: Alerts
```

### Tank Monitor Offline

Alert if tank monitor hasn't reported in 48 hours.

```yaml
alias: "Tank Monitor Offline Alert"
description: "Alert when tank monitor stops reporting"
trigger:
  - platform: template
    value_template: >
      {% set last_reading = state_attr('sensor.amerigas_tank_level', 'last_monitor_reading') %}
      {% if last_reading and last_reading != 'Unknown' %}
        {{ (now() - as_datetime(last_reading)).days > 2 }}
      {% else %}
        false
      {% endif %}
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "📡 Tank Monitor Offline"
      message: >
        Your tank monitor hasn't reported in over 48 hours.
        Last reading: {{ state_attr('sensor.amerigas_tank_level', 'last_monitor_reading') }}
        
        Contact AmeriGas if issue persists.
      data:
        tag: monitor_offline
```

---

## Notification Automations

### Payment Due Reminder

Remind when payment is due (for non-auto-pay customers).

```yaml
alias: "Payment Due Notification"
description: "Remind when payment is due and auto-pay is off"
trigger:
  - platform: numeric_state
    entity_id: sensor.amerigas_amount_due
    above: 0
condition:
  - condition: template
    value_template: "{{ states('sensor.amerigas_auto_pay') != 'On' }}"
  - condition: template
    value_template: "{{ states('sensor.amerigas_amount_due') | float > 0 }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "💳 AmeriGas Payment Due"
      message: >
        Payment of ${{ states('sensor.amerigas_amount_due') }} is due.
        Payment terms: {{ state_attr('sensor.amerigas_amount_due', 'payment_terms') }}
      data:
        tag: payment_due
        actions:
          - action: URI
            title: "Make Payment"
            uri: https://www.myamerigas.com
          - action: dismiss
            title: "Dismiss"
```

### Delivery Reminder

Notify when delivery is scheduled within 24 hours.

```yaml
alias: "Delivery Reminder"
description: "Notify when delivery is tomorrow"
trigger:
  - platform: time
    at: "18:00:00"
condition:
  - condition: template
    value_template: >
      {% set next_delivery = states('sensor.amerigas_next_delivery_date') %}
      {% if next_delivery not in ['unknown', 'unavailable', 'Unknown'] %}
        {% set delivery_date = as_datetime(next_delivery) %}
        {% if delivery_date %}
          {{ (delivery_date - now()).days == 1 }}
        {% else %}
          false
        {% endif %}
      {% else %}
        false
      {% endif %}
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "🚚 Propane Delivery Tomorrow"
      message: >
        Your AmeriGas delivery is scheduled for tomorrow.
        
        Ensure:
        - Driveway is clear
        - Path to tank is accessible
        - Gates/doors are unlocked
      data:
        tag: delivery_reminder
```

### Delivery Complete

Notify when delivery has been completed.

```yaml
alias: "Delivery Complete Notification"
description: "Notify when delivery is completed"
trigger:
  - platform: state
    entity_id: sensor.amerigas_last_delivery_date
condition:
  - condition: template
    value_template: >
      {{ trigger.to_state.state != trigger.from_state.state }}
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "✅ Propane Delivery Complete"
      message: >
        Delivery completed on {{ states('sensor.amerigas_last_delivery_date') | as_timestamp | timestamp_custom('%B %d, %Y') }}
        
        {{ states('sensor.amerigas_last_delivery_gallons') }} gallons delivered
        Tank now at {{ states('sensor.amerigas_tank_level') }}%
        Cost: ${{ states('sensor.amerigas_last_payment_amount') }}
        Price: ${{ states('sensor.propane_cost_per_gallon') }}/gal
      data:
        tag: delivery_complete
```

---

## Reporting Automations

### Daily Summary

Send daily propane status summary.

```yaml
alias: "Daily Propane Summary"
description: "Send daily propane status report"
trigger:
  - platform: time
    at: "08:00:00"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "📊 Daily Propane Report"
      message: >
        Tank Level: {{ states('sensor.amerigas_tank_level') }}%
        ({{ states('sensor.propane_tank_gallons_remaining') }} gallons)
        
        Days Remaining: {{ states('sensor.propane_days_until_empty') }} days
        Daily Usage: {{ states('sensor.propane_daily_average_usage') }} gal/day
        
        Yesterday's Cost: ${{ states('sensor.daily_propane_cost') }}
      data:
        tag: daily_report
```

### Weekly Detailed Report

Send comprehensive weekly report on Sunday morning.

```yaml
alias: "Weekly Propane Report"
description: "Send detailed weekly propane report"
trigger:
  - platform: time
    at: "09:00:00"
condition:
  - condition: time
    weekday:
      - sun
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "📈 Weekly Propane Report"
      message: >
        **Current Status**
        Tank: {{ states('sensor.amerigas_tank_level') }}% ({{ states('sensor.propane_tank_gallons_remaining') }} gal)
        Days Remaining: {{ states('sensor.propane_days_until_empty') }}
        
        **This Week**
        Usage: {{ states('sensor.daily_propane_gallons') }} gallons
        Cost: ${{ states('sensor.daily_propane_cost') }}
        Avg Daily: {{ states('sensor.propane_daily_average_usage') }} gal/day
        
        **This Month**
        Usage: {{ states('sensor.monthly_propane_gallons') }} gallons
        Cost: ${{ states('sensor.monthly_propane_cost') }}
        
        **Since Last Fill** ({{ states('sensor.propane_days_since_last_delivery') }} days ago)
        Used: {{ states('sensor.propane_used_since_last_delivery') }} gallons
        Cost: ${{ states('sensor.propane_cost_since_last_delivery') }}
        
        **Account**
        Balance: ${{ states('sensor.amerigas_account_balance') }}
        Amount Due: ${{ states('sensor.amerigas_amount_due') }}
      data:
        tag: weekly_report
```

### Monthly Cost Summary

Send monthly cost summary on the first of each month.

```yaml
alias: "Monthly Propane Cost Summary"
description: "Send monthly cost report"
trigger:
  - platform: time
    at: "10:00:00"
condition:
  - condition: template
    value_template: "{{ now().day == 1 }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "💰 Monthly Propane Cost Summary"
      message: >
        **Last Month's Propane Costs**
        
        Total Usage: {{ states('sensor.monthly_propane_gallons') }} gallons
        Total Cost: ${{ states('sensor.monthly_propane_cost') }}
        
        Average Daily: {{ states('sensor.propane_daily_average_usage') }} gal/day
        Average Cost/Day: ${{ (states('sensor.monthly_propane_cost') | float / 30) | round(2) }}
        
        Price/Gallon: ${{ states('sensor.propane_cost_per_gallon') }}
        
        **Year to Date**
        Total Usage: {{ states('sensor.yearly_propane_gallons') }} gallons
        Total Cost: ${{ states('sensor.yearly_propane_cost') }}
      data:
        tag: monthly_cost
```

### Low Tank Approaching

Predictive alert when tank will be low soon.

```yaml
alias: "Low Tank Approaching"
description: "Alert when tank will be low in 7 days"
trigger:
  - platform: numeric_state
    entity_id: sensor.propane_days_until_empty
    below: 7
condition:
  - condition: numeric_state
    entity_id: sensor.amerigas_tank_level
    above: 20
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "⚠️ Plan for Propane Delivery"
      message: >
        Based on current usage, your tank will be low in {{ states('sensor.propane_days_until_empty') }} days.
        
        Current: {{ states('sensor.amerigas_tank_level') }}% ({{ states('sensor.propane_tank_gallons_remaining') }} gal)
        Daily usage: {{ states('sensor.propane_daily_average_usage') }} gal/day
        
        Consider scheduling a delivery soon.
      data:
        tag: low_approaching
```

---

## Advanced Automations

### Smart Refill Reminder

Intelligent reminder based on usage patterns and weather.

```yaml
alias: "Smart Refill Reminder"
description: "Intelligent refill suggestion based on multiple factors"
trigger:
  - platform: numeric_state
    entity_id: sensor.amerigas_tank_level
    below: 35
condition:
  - condition: or
    conditions:
      # Winter (higher usage expected)
      - condition: template
        value_template: "{{ now().month in [11, 12, 1, 2, 3] }}"
      # High current usage
      - condition: numeric_state
        entity_id: sensor.propane_daily_average_usage
        above: 5
      # Days remaining less than 14
      - condition: numeric_state
        entity_id: sensor.propane_days_until_empty
        below: 14
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "🧠 Smart Refill Recommendation"
      message: >
        {% if now().month in [11, 12, 1, 2, 3] %}
        It's winter and your usage is higher.
        {% elif states('sensor.propane_daily_average_usage') | float > 5 %}
        Your usage is above average.
        {% else %}
        Your tank is getting low.
        {% endif %}
        
        Current: {{ states('sensor.amerigas_tank_level') }}%
        Estimated days: {{ states('sensor.propane_days_until_empty') }}
        Daily usage: {{ states('sensor.propane_daily_average_usage') }} gal/day
        
        Est. refill cost: ${{ states('sensor.propane_estimated_refill_cost') }}
        
        {% if states('sensor.amerigas_next_delivery_date') not in ['unknown', 'Unknown'] %}
        Next scheduled: {{ states('sensor.amerigas_next_delivery_date') | as_timestamp | timestamp_custom('%B %d') }}
        {% else %}
        No delivery scheduled yet.
        {% endif %}
      data:
        actions:
          - action: URI
            title: "Schedule Delivery"
            uri: https://www.myamerigas.com
```

### Usage Anomaly Detection

Detect unusual usage patterns.

```yaml
alias: "Propane Usage Anomaly Detection"
description: "Alert on unusual usage patterns"
trigger:
  - platform: state
    entity_id: sensor.propane_daily_average_usage
    for:
      hours: 6
condition:
  - condition: template
    value_template: >
      {% set current = states('sensor.propane_daily_average_usage') | float %}
      {% set history = state_attr('sensor.propane_daily_average_usage', 'history') | default([]) %}
      {% if history | length > 7 %}
        {% set avg = (history | sum / history | length) %}
        {% set threshold = avg * 1.5 %}
        {{ current > threshold }}
      {% else %}
        false
      {% endif %}
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "⚠️ Unusual Propane Usage Detected"
      message: >
        Current usage ({{ states('sensor.propane_daily_average_usage') }} gal/day) 
        is significantly higher than your average.
        
        Possible causes:
        - Cold weather
        - Guests or increased occupancy
        - Equipment issue
        - Possible leak
        
        Monitor usage and inspect equipment if pattern continues.
      data:
        tag: usage_anomaly
```

### Auto-Update on Low Battery (for Tank Monitor)

Trigger manual update if monitor battery is low.

```yaml
alias: "Update AmeriGas Data on Low Monitor Battery"
description: "Force update when tank monitor battery is low"
trigger:
  - platform: state
    entity_id: sensor.amerigas_tank_level
    attribute: tank_monitor
    to: "Low Battery"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "🔋 Tank Monitor Battery Low"
      message: "Your tank monitor battery is low. Contact AmeriGas for service."
  - service: pyscript.amerigas_update
    data: {}
```

### Cost Spike Alert

Alert if cost per gallon increases significantly.

```yaml
alias: "Propane Price Spike Alert"
description: "Alert when propane price increases significantly"
trigger:
  - platform: state
    entity_id: sensor.propane_cost_per_gallon
variables:
  old_price: "{{ trigger.from_state.state | float(0) }}"
  new_price: "{{ trigger.to_state.state | float(0) }}"
  increase_percent: "{{ ((new_price - old_price) / old_price * 100) | round(1) if old_price > 0 else 0 }}"
condition:
  - condition: template
    value_template: "{{ increase_percent > 15 }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "💸 Propane Price Increase Alert"
      message: >
        Propane price increased by {{ increase_percent }}%!
        
        Previous: ${{ old_price }}/gal
        New: ${{ new_price }}/gal
        Increase: ${{ (new_price - old_price) | round(2) }}/gal
        
        Consider filling tank before further increases.
      data:
        tag: price_spike
```

### Seasonal Usage Comparison

Compare current season usage to last year.

```yaml
alias: "Seasonal Usage Comparison"
description: "Compare winter usage year-over-year"
trigger:
  - platform: time
    at: "09:00:00"
condition:
  - condition: template
    value_template: "{{ now().day == 1 and now().month == 4 }}"  # April 1st
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "❄️ Winter Propane Usage Summary"
      message: >
        **This Winter** (Nov-Mar)
        Total Usage: {{ states('sensor.yearly_propane_gallons') }} gallons
        Total Cost: ${{ states('sensor.yearly_propane_cost') }}
        Avg Daily: {{ states('sensor.propane_daily_average_usage') }} gal/day
        
        Your data can help predict next winter's needs!
      data:
        tag: seasonal_summary
```

---

## Tips for Creating Your Own Automations

### Using Template Conditions

Check multiple conditions:
```yaml
condition:
  - condition: template
    value_template: >
      {{ states('sensor.amerigas_tank_level') | int < 30 
         and states('sensor.propane_days_until_empty') | int < 10 }}
```

### Rate Limiting Notifications

Prevent spam with `for` clause:
```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.amerigas_tank_level
    below: 30
    for:
      hours: 1  # Only trigger if condition persists for 1 hour
```

### Using Wait Template

Wait for a condition before continuing:
```yaml
action:
  - wait_template: "{{ states('sensor.amerigas_tank_level') | int > 50 }}"
    timeout: "24:00:00"
```

### Actionable Notifications

Add buttons to notifications:
```yaml
data:
  actions:
    - action: "SCHEDULE_DELIVERY"
      title: "Schedule Delivery"
    - action: "REMIND_LATER"
      title: "Remind in 3 Days"
```

Then create automation to handle the action:
```yaml
trigger:
  - platform: event
    event_type: mobile_app_notification_action
    event_data:
      action: SCHEDULE_DELIVERY
```

---

## Debugging Automations

### Check if automation is triggering

```yaml
action:
  - service: persistent_notification.create
    data:
      title: "Debug: Automation Triggered"
      message: "Tank level: {{ states('sensor.amerigas_tank_level') }}"
```

### Log sensor values

```yaml
action:
  - service: system_log.write
    data:
      message: >
        Tank: {{ states('sensor.amerigas_tank_level') }}%
        Days: {{ states('sensor.propane_days_until_empty') }}
      level: info
```

---

## Need Help?

- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Visit [Home Assistant Forum](https://community.home-assistant.io/)
- Open an [Issue on GitHub](https://github.com/skircr115/ha-amerigas/issues)

---

**[← Back to README](README.md)**
