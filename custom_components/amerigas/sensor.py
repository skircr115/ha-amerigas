"""Sensor platform for AmeriGas integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    GALLONS_TO_CUBIC_FEET,
    DEFAULT_FILL_PERCENTAGE,
    DEFAULT_TANK_SIZE,
    NOISE_THRESHOLD_GALLONS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AmeriGas sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Base sensors from API
    sensors: list[SensorEntity] = [
        AmeriGasTankLevelSensor(coordinator, entry.entry_id),
        AmeriGasTankSizeSensor(coordinator, entry.entry_id),
        AmeriGasDaysRemainingSensor(coordinator, entry.entry_id),
        AmeriGasAmountDueSensor(coordinator, entry.entry_id),
        AmeriGasAccountBalanceSensor(coordinator, entry.entry_id),
        AmeriGasLastPaymentDateSensor(coordinator, entry.entry_id),
        AmeriGasLastPaymentAmountSensor(coordinator, entry.entry_id),
        AmeriGasLastTankReadingSensor(coordinator, entry.entry_id),
        AmeriGasLastDeliveryDateSensor(coordinator, entry.entry_id),
        AmeriGasLastDeliveryGallonsSensor(coordinator, entry.entry_id),
        AmeriGasNextDeliveryDateSensor(coordinator, entry.entry_id),
        AmeriGasAutoPaySensor(coordinator, entry.entry_id),
        AmeriGasPaperlessSensor(coordinator, entry.entry_id),
        AmeriGasAccountNumberSensor(coordinator, entry.entry_id),
        AmeriGasServiceAddressSensor(coordinator, entry.entry_id),
    ]
    
    # Calculated sensors
    sensors.extend([
        PropaneGallonsRemainingSensor(coordinator, entry.entry_id),
        PropaneUsedSinceDeliverySensor(coordinator, entry.entry_id),
        PropaneEnergyConsumptionSensor(coordinator, entry.entry_id),
        PropaneDailyAverageUsageSensor(coordinator, entry.entry_id),
        PropaneDaysUntilEmptySensor(coordinator, entry.entry_id),
        PropaneCostPerGallonSensor(coordinator, entry.entry_id),
        PropaneCostPerCubicFootSensor(coordinator, entry.entry_id),
        PropaneCostSinceDeliverySensor(coordinator, entry.entry_id),
        PropaneEstimatedRefillCostSensor(coordinator, entry.entry_id),
        PropaneDaysSinceDeliverySensor(coordinator, entry.entry_id),
        PropaneDaysRemainingDifferenceSensor(coordinator, entry.entry_id),
    ])
    
    # Lifetime tracking sensors (v2.0.0+)
    lifetime_gallons_sensor = PropaneLifetimeGallonsSensor(coordinator, hass, entry.entry_id)
    lifetime_energy_sensor = PropaneLifetimeEnergySensor(coordinator, hass, lifetime_gallons_sensor, entry.entry_id)
    
    sensors.extend([
        lifetime_gallons_sensor,
        lifetime_energy_sensor,
    ])
    
    async_add_entities(sensors)


class AmeriGasSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for AmeriGas sensors."""
    
    _attr_has_entity_name = True
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "AmeriGas Propane",
            "manufacturer": "AmeriGas",
            "model": "AmeriGas Account",
        }
        self._pre_delivery_entity_id: str | None = None
    
    async def async_added_to_hass(self) -> None:
        """Set up listener for pre-delivery level changes.
        
        v3.0.8: All sensors that depend on usage calculations need to
        recalculate when the pre-delivery level changes, not just when
        the coordinator updates.
        """
        await super().async_added_to_hass()
        
        # Find and cache the pre-delivery level entity ID
        try:
            from homeassistant.helpers import entity_registry as er
            
            entity_reg = er.async_get(self.hass)
            
            for entity in entity_reg.entities.values():
                if entity.unique_id and entity.unique_id.endswith("_pre_delivery_level"):
                    if entity.platform == DOMAIN:
                        self._pre_delivery_entity_id = entity.entity_id
                        break
            
            # Set up listener for pre-delivery level changes
            if self._pre_delivery_entity_id:
                @callback
                def _handle_pre_delivery_change(event):
                    """Handle pre-delivery level state change."""
                    if event.data.get("entity_id") != self._pre_delivery_entity_id:
                        return
                    
                    new_state = event.data.get("new_state")
                    if new_state and new_state.state not in ("unknown", "unavailable"):
                        # Force recalculation of this sensor
                        self.async_write_ha_state()
                
                self.async_on_remove(
                    self.hass.bus.async_listen("state_changed", _handle_pre_delivery_change)
                )
        except Exception as e:
            _LOGGER.debug(f"Could not set up pre-delivery level listener: {e}")
    
    def _get_pre_delivery_level(self) -> float | None:
        """Get the pre-delivery level from the number entity.
        
        v3.0.8: Centralized helper method for all sensors to use.
        Returns the auto-captured pre-delivery level if available,
        or None if not found or not set.
        """
        if not hasattr(self, 'hass') or self.hass is None:
            return None
        
        # Use cached entity ID if available (set in async_added_to_hass)
        if hasattr(self, '_pre_delivery_entity_id') and self._pre_delivery_entity_id:
            if state := self.hass.states.get(self._pre_delivery_entity_id):
                try:
                    value = float(state.state)
                    if value > 0:
                        return value
                except (ValueError, TypeError):
                    pass
            return None
        
        # Fallback: search entity registry (for sensors that haven't been added to hass yet)
        try:
            from homeassistant.helpers import entity_registry as er
            
            entity_reg = er.async_get(self.hass)
            
            for entity in entity_reg.entities.values():
                if entity.unique_id and entity.unique_id.endswith("_pre_delivery_level"):
                    if entity.platform == DOMAIN:
                        if state := self.hass.states.get(entity.entity_id):
                            try:
                                value = float(state.state)
                                if value > 0:
                                    return value
                            except (ValueError, TypeError):
                                pass
                        break
        except Exception as e:
            _LOGGER.debug(f"Could not get pre-delivery level: {e}")
        
        return None
    
    def _calculate_gallons_remaining(self) -> float | None:
        """Calculate gallons remaining from coordinator data."""
        tank_size = self.coordinator.data.get("tank_size") or DEFAULT_TANK_SIZE
        percent = self.coordinator.data.get("tank_level") or 0
        
        # Bounds check
        if percent < 0:
            percent = 0
        elif percent > 100:
            percent = 100
        
        if tank_size <= 0:
            return None
        
        return round(tank_size * (percent / 100), 2)
    
    def _calculate_used_since_delivery(self) -> tuple[float | None, str]:
        """Calculate gallons used since delivery from coordinator data.
        
        v3.0.8: Now uses auto-captured pre-delivery level if available.
        Returns tuple of (gallons_used, calculation_method).
        """
        tank_size = self.coordinator.data.get("tank_size") or DEFAULT_TANK_SIZE
        tank_level = self.coordinator.data.get("tank_level") or 0
        
        # Bounds check
        if tank_level < 0:
            tank_level = 0
        elif tank_level > 100:
            tank_level = 100
        
        current = tank_size * (tank_level / 100)
        last_delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        
        # v3.0.8: Check for auto-captured pre-delivery level
        pre_delivery_level = self._get_pre_delivery_level()
        
        if pre_delivery_level and pre_delivery_level > 0:
            # Use auto-captured level (100% accurate)
            starting_level = pre_delivery_level + last_delivery
            calculation_method = "auto_captured"
        elif last_delivery > 0:
            # Fallback: Smart estimation based on delivery size
            if last_delivery < 50:
                estimated_before = tank_size * 0.65
                calculation_method = "small_delivery_estimate"
            else:
                estimated_before = tank_size * 0.20
                calculation_method = "large_delivery_estimate"
            starting_level = estimated_before + last_delivery
        else:
            # Fallback: assume 80% fill
            starting_level = tank_size * DEFAULT_FILL_PERCENTAGE
            calculation_method = "assumed_80_percent"
        
        # Cap at tank capacity
        if starting_level > tank_size:
            starting_level = tank_size
        
        used = starting_level - current
        
        return (max(0, round(used, 2)), calculation_method)
    
    def _calculate_daily_average(self) -> float | None:
        """Calculate daily average usage from coordinator data.
        
        v3.0.8: Now uses _calculate_used_since_delivery which includes pre-delivery level.
        """
        last_date = self.coordinator.data.get("last_delivery_date")
        if not last_date:
            return None
        
        used, _ = self._calculate_used_since_delivery()
        if used is None:
            return None
        
        now = dt_util.now()
        days = (now - last_date).days
        
        if days <= 0:
            return None
        
        return round(used / days, 2)
    
    def _calculate_cost_per_gallon(self) -> float | None:
        """Calculate cost per gallon from coordinator data."""
        payment = self.coordinator.data.get("last_payment_amount") or 0
        delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        
        if delivery <= 0:
            return None
        
        return round(payment / delivery, 2)


# =============================================================================
# BASE SENSORS FROM API
# =============================================================================

class AmeriGasTankLevelSensor(AmeriGasSensorBase):
    """Tank level percentage sensor."""
    
    _attr_name = "Tank Level"
    _attr_unique_id = "amerigas_tank_level"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:propane-tank"
    
    @property
    def native_value(self) -> int | None:
        """Return tank level percentage."""
        return self.coordinator.data.get("tank_level")
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        return {
            "tank_monitor": self.coordinator.data.get("tank_monitor"),
            "delivery_type": self.coordinator.data.get("delivery_type"),
        }


class AmeriGasTankSizeSensor(AmeriGasSensorBase):
    """Tank size sensor."""
    
    _attr_name = "Tank Size"
    _attr_unique_id = "amerigas_tank_size"
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_device_class = SensorDeviceClass.VOLUME_STORAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:propane-tank-outline"
    
    @property
    def native_value(self) -> int | None:
        """Return tank size."""
        return self.coordinator.data.get("tank_size")


class AmeriGasDaysRemainingSensor(AmeriGasSensorBase):
    """Days remaining sensor (AmeriGas estimate)."""
    
    _attr_name = "Days Remaining (AmeriGas)"
    _attr_unique_id = "amerigas_days_remaining"
    _attr_native_unit_of_measurement = "days"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calendar-clock"
    
    @property
    def native_value(self) -> int | None:
        """Return days remaining."""
        return self.coordinator.data.get("days_remaining")


class AmeriGasAmountDueSensor(AmeriGasSensorBase):
    """Amount due sensor."""
    
    _attr_name = "Amount Due"
    _attr_unique_id = "amerigas_amount_due"
    _attr_native_unit_of_measurement = "USD"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:currency-usd"
    
    @property
    def native_value(self) -> float | None:
        """Return amount due."""
        return self.coordinator.data.get("amount_due")
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        return {
            "payment_terms": self.coordinator.data.get("payment_terms"),
        }


class AmeriGasAccountBalanceSensor(AmeriGasSensorBase):
    """Account balance sensor."""
    
    _attr_name = "Account Balance"
    _attr_unique_id = "amerigas_account_balance"
    _attr_native_unit_of_measurement = "USD"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:cash"
    
    @property
    def native_value(self) -> float | None:
        """Return account balance."""
        return self.coordinator.data.get("account_balance")


class AmeriGasLastPaymentDateSensor(AmeriGasSensorBase):
    """Last payment date sensor."""
    
    _attr_name = "Last Payment Date"
    _attr_unique_id = "amerigas_last_payment_date"
    _attr_icon = "mdi:calendar-check"
    
    @property
    def native_value(self) -> str | None:
        """Return last payment date."""
        return self.coordinator.data.get("last_payment_date")


class AmeriGasLastPaymentAmountSensor(AmeriGasSensorBase):
    """Last payment amount sensor."""
    
    _attr_name = "Last Payment Amount"
    _attr_unique_id = "amerigas_last_payment_amount"
    _attr_native_unit_of_measurement = "USD"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:credit-card"
    
    @property
    def native_value(self) -> float | None:
        """Return last payment amount."""
        return self.coordinator.data.get("last_payment_amount")


class AmeriGasLastTankReadingSensor(AmeriGasSensorBase):
    """Last tank reading timestamp sensor."""
    
    _attr_name = "Last Tank Reading"
    _attr_unique_id = "amerigas_last_tank_reading"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"
    
    @property
    def native_value(self) -> datetime | None:
        """Return last tank reading timestamp."""
        return self.coordinator.data.get("last_tank_reading")


class AmeriGasLastDeliveryDateSensor(AmeriGasSensorBase):
    """Last delivery date sensor."""
    
    _attr_name = "Last Delivery Date"
    _attr_unique_id = "amerigas_last_delivery_date"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:truck-delivery"
    
    @property
    def native_value(self) -> datetime | None:
        """Return last delivery date."""
        return self.coordinator.data.get("last_delivery_date")


class AmeriGasLastDeliveryGallonsSensor(AmeriGasSensorBase):
    """Last delivery gallons sensor."""
    
    _attr_name = "Last Delivery Gallons"
    _attr_unique_id = "amerigas_last_delivery_gallons"
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:gas-station"
    
    @property
    def native_value(self) -> float | None:
        """Return last delivery gallons."""
        return self.coordinator.data.get("last_delivery_gallons")


class AmeriGasNextDeliveryDateSensor(AmeriGasSensorBase):
    """Next delivery date sensor."""
    
    _attr_name = "Next Delivery Date"
    _attr_unique_id = "amerigas_next_delivery_date"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:truck-delivery"
    
    @property
    def native_value(self) -> datetime | None:
        """Return next delivery date."""
        return self.coordinator.data.get("next_delivery_date")
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        next_date = self.coordinator.data.get("next_delivery_date")
        return {
            "has_scheduled_delivery": next_date is not None,
        }


class AmeriGasAutoPaySensor(AmeriGasSensorBase):
    """Auto pay status sensor."""
    
    _attr_name = "Auto Pay"
    _attr_unique_id = "amerigas_auto_pay"
    _attr_icon = "mdi:credit-card-check"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> str | None:
        """Return auto pay status."""
        return self.coordinator.data.get("auto_pay")


class AmeriGasPaperlessSensor(AmeriGasSensorBase):
    """Paperless billing status sensor."""
    
    _attr_name = "Paperless Billing"
    _attr_unique_id = "amerigas_paperless"
    _attr_icon = "mdi:file-document"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> str | None:
        """Return paperless billing status."""
        return self.coordinator.data.get("paperless")


class AmeriGasAccountNumberSensor(AmeriGasSensorBase):
    """Account number sensor."""
    
    _attr_name = "Account Number"
    _attr_unique_id = "amerigas_account_number"
    _attr_icon = "mdi:account"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> str | None:
        """Return account number."""
        return self.coordinator.data.get("account_number")


class AmeriGasServiceAddressSensor(AmeriGasSensorBase):
    """Service address sensor."""
    
    _attr_name = "Service Address"
    _attr_unique_id = "amerigas_service_address"
    _attr_icon = "mdi:home-map-marker"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> str | None:
        """Return service address."""
        return self.coordinator.data.get("service_address")
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        return {
            "street": self.coordinator.data.get("street"),
            "city": self.coordinator.data.get("city"),
            "state": self.coordinator.data.get("state"),
            "zip": self.coordinator.data.get("zip"),
        }


# =============================================================================
# CALCULATED SENSORS
# =============================================================================

class PropaneGallonsRemainingSensor(AmeriGasSensorBase):
    """Gallons remaining sensor with v2.0.1 bounds checking."""
    
    _attr_name = "Gallons Remaining"
    _attr_unique_id = "propane_tank_gallons_remaining"
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_device_class = SensorDeviceClass.VOLUME_STORAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> float | None:
        """Return gallons remaining with bounds checking."""
        return self._calculate_gallons_remaining()
    
    @property
    def available(self) -> bool:
        """Return if sensor is available."""
        tank_size = self.coordinator.data.get("tank_size")
        return tank_size is not None and tank_size > 0


class PropaneUsedSinceDeliverySensor(AmeriGasSensorBase):
    """Used since delivery sensor with v3.0.8 improvements.
    
    v3.0.8: Now uses the centralized _calculate_used_since_delivery() helper
    which properly looks up the pre-delivery level.
    """
    
    _attr_name = "Used Since Last Delivery"
    _attr_unique_id = "propane_used_since_last_delivery"
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:gas-station"
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id)
        self._calculation_method = "unknown"
        self._starting_level = 0.0
    
    @property
    def native_value(self) -> float | None:
        """Return gallons used with auto-captured pre-delivery level."""
        used, method = self._calculate_used_since_delivery()
        self._calculation_method = method
        
        # Calculate starting level for attributes
        pre_delivery = self._get_pre_delivery_level()
        last_delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        tank_size = self.coordinator.data.get("tank_size") or DEFAULT_TANK_SIZE
        
        if pre_delivery and pre_delivery > 0:
            self._starting_level = min(pre_delivery + last_delivery, tank_size)
        elif last_delivery > 0:
            if last_delivery < 50:
                estimated_before = tank_size * 0.65
            else:
                estimated_before = tank_size * 0.20
            self._starting_level = min(estimated_before + last_delivery, tank_size)
        else:
            self._starting_level = tank_size * DEFAULT_FILL_PERCENTAGE
        
        return used
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        last_delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        pre_delivery = self._get_pre_delivery_level()
        
        attrs = {
            "calculation_method": self._calculation_method,
            "last_delivery_gallons": last_delivery,
            "calculated_starting_level": round(self._starting_level, 2),
        }
        
        if pre_delivery and pre_delivery > 0:
            attrs["pre_delivery_level"] = round(pre_delivery, 2)
            attrs["accuracy"] = "100% (auto-captured)"
        elif self._calculation_method == "small_delivery_estimate":
            attrs["accuracy"] = "~75% (estimated)"
        elif self._calculation_method == "large_delivery_estimate":
            attrs["accuracy"] = "~95% (estimated)"
        else:
            attrs["accuracy"] = "~90% (estimated)"
        
        return attrs


class PropaneEnergyConsumptionSensor(AmeriGasSensorBase):
    """Energy consumption sensor (display only, not for Energy Dashboard).
    
    v3.0.8: Now uses _calculate_used_since_delivery() which includes pre-delivery level.
    """
    
    _attr_name = "Energy Consumption (Display)"
    _attr_unique_id = "propane_energy_consumption"
    _attr_native_unit_of_measurement = "ft³"
    _attr_device_class = SensorDeviceClass.GAS
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:fire"
    
    @property
    def native_value(self) -> float | None:
        """Return energy in cubic feet.
        
        v3.0.8: Uses centralized helper that includes pre-delivery level.
        """
        used, _ = self._calculate_used_since_delivery()
        
        if used is None:
            return None
        
        return round(used * GALLONS_TO_CUBIC_FEET, 2)
    
    @property
    def available(self) -> bool:
        """Return availability."""
        tank_size = self.coordinator.data.get("tank_size")
        return tank_size is not None and tank_size > 0


class PropaneDailyAverageUsageSensor(AmeriGasSensorBase):
    """Daily average usage sensor.
    
    v3.0.8: Now uses _calculate_daily_average() which internally uses
    _calculate_used_since_delivery() with pre-delivery level support.
    """
    
    _attr_name = "Daily Average Usage"
    _attr_unique_id = "propane_daily_average_usage"
    _attr_native_unit_of_measurement = "gal/day"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-line"
    
    @property
    def native_value(self) -> float | None:
        """Return daily average usage.
        
        v3.0.8: Uses centralized helper that includes pre-delivery level.
        """
        return self._calculate_daily_average()
    
    @property
    def available(self) -> bool:
        """Return availability."""
        last_date = self.coordinator.data.get("last_delivery_date")
        if not last_date:
            return False
        
        now = dt_util.now()
        days = (now - last_date).days
        tank_size = self.coordinator.data.get("tank_size")
        return days > 0 and tank_size and tank_size > 0
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        last_date = self.coordinator.data.get("last_delivery_date")
        used, method = self._calculate_used_since_delivery()
        
        attrs = {
            "calculation_method": method,
            "gallons_used": used,
        }
        
        if last_date:
            now = dt_util.now()
            days = (now - last_date).days
            attrs["days_since_delivery"] = days
            if used and days > 0:
                attrs["calculation"] = f"{used:.2f} gal ÷ {days} days = {used/days:.4f} gal/day"
        
        return attrs


class PropaneDaysUntilEmptySensor(AmeriGasSensorBase):
    """Days until empty sensor.
    
    v3.0.8: Uses _calculate_daily_average() which now includes pre-delivery level.
    """
    
    _attr_name = "Days Until Empty"
    _attr_unique_id = "propane_days_until_empty"
    _attr_native_unit_of_measurement = "days"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calendar-clock"
    
    @property
    def native_value(self) -> int | None:
        """Return days until empty."""
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        
        if remaining is None or avg_usage is None:
            return None
        
        if remaining <= 0:
            return 0
        
        if avg_usage < 0.001:
            return 9999
        
        days = remaining / avg_usage
        
        if days > 9999:
            return 9999
        
        return round(days)
    
    @property
    def available(self) -> bool:
        """Sensor is available if we have the data needed to calculate."""
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        return remaining is not None and avg_usage is not None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        _, method = self._calculate_used_since_delivery()
        
        attrs = {
            "gallons_remaining": remaining,
            "daily_average_usage": avg_usage,
            "calculation_method": method,
        }
        
        if avg_usage is not None:
            if avg_usage < 0.001:
                attrs["note"] = "Usage rate extremely low - showing 9999 days as practical maximum"
            elif avg_usage < 0.1:
                attrs["note"] = f"Low usage rate: {avg_usage:.3f} gal/day"
        
        if remaining is not None and avg_usage is not None and avg_usage > 0:
            days_raw = remaining / avg_usage
            attrs["calculation"] = f"{remaining:.2f} gal ÷ {avg_usage:.2f} gal/day = {days_raw:.1f} days"
            if days_raw > 9999:
                attrs["calculation"] += " (capped at 9999)"
        
        return attrs


class PropaneCostPerGallonSensor(AmeriGasSensorBase):
    """Cost per gallon sensor with v2.1.0 improvements."""
    
    _attr_name = "Cost Per Gallon"
    _attr_unique_id = "propane_cost_per_gallon"
    _attr_native_unit_of_measurement = "USD/gal"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:currency-usd"
    
    @property
    def native_value(self) -> float | None:
        """Return cost per gallon."""
        return self._calculate_cost_per_gallon()
    
    @property
    def available(self) -> bool:
        """Return availability."""
        delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        return delivery > 0


class PropaneCostPerCubicFootSensor(AmeriGasSensorBase):
    """Cost per cubic foot sensor."""
    
    _attr_name = "Cost Per Cubic Foot"
    _attr_unique_id = "propane_cost_per_cubic_foot"
    _attr_native_unit_of_measurement = "USD/ft³"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:currency-usd"
    
    @property
    def native_value(self) -> float | None:
        """Return cost per cubic foot."""
        cost_per_gallon = self._calculate_cost_per_gallon()
        
        if cost_per_gallon is None:
            return None
        
        return round(cost_per_gallon / GALLONS_TO_CUBIC_FEET, 4)
    
    @property
    def available(self) -> bool:
        """Return availability."""
        delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        return delivery > 0


class PropaneCostSinceDeliverySensor(AmeriGasSensorBase):
    """Cost since delivery sensor.
    
    v3.0.8: Uses centralized _calculate_used_since_delivery() helper.
    """
    
    _attr_name = "Cost Since Last Delivery"
    _attr_unique_id = "propane_cost_since_last_delivery"
    _attr_native_unit_of_measurement = "USD"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:cash"
    
    @property
    def native_value(self) -> float | None:
        """Return cost since delivery."""
        used, _ = self._calculate_used_since_delivery()
        cost = self._calculate_cost_per_gallon()
        
        if used is None or cost is None or cost == 0:
            return None
        
        return round(used * cost, 2)
    
    @property
    def available(self) -> bool:
        """Return availability."""
        used, _ = self._calculate_used_since_delivery()
        cost = self._calculate_cost_per_gallon()
        return used is not None and cost is not None and cost > 0
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        used, method = self._calculate_used_since_delivery()
        cost = self._calculate_cost_per_gallon()
        
        attrs = {
            "gallons_used": used,
            "cost_per_gallon": cost,
            "calculation_method": method,
        }
        
        if used and cost:
            attrs["calculation"] = f"{used:.2f} gal × ${cost:.2f}/gal = ${used * cost:.2f}"
        
        return attrs


class PropaneEstimatedRefillCostSensor(AmeriGasSensorBase):
    """Estimated refill cost sensor.
    
    v3.0.8: Uses centralized helpers for consistent calculations.
    """
    
    _attr_name = "Estimated Refill Cost"
    _attr_unique_id = "propane_estimated_refill_cost"
    _attr_native_unit_of_measurement = "USD"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:cash-multiple"
    
    @property
    def native_value(self) -> float | None:
        """Return estimated refill cost."""
        tank_size = self.coordinator.data.get("tank_size") or DEFAULT_TANK_SIZE
        remaining = self._calculate_gallons_remaining()
        cost = self._calculate_cost_per_gallon()
        
        if remaining is None or cost is None:
            return None
        
        max_fill_level = tank_size * 0.80
        needed = max_fill_level - remaining
        
        if needed < 0:
            needed = 0
        elif needed > tank_size:
            needed = tank_size
        
        return round(needed * cost, 2)
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        tank_size = self.coordinator.data.get("tank_size") or DEFAULT_TANK_SIZE
        remaining = self._calculate_gallons_remaining()
        
        max_fill_level = tank_size * 0.80
        needed = max_fill_level - remaining if remaining else 0
        if needed < 0:
            needed = 0
        
        return {
            "max_fill_level": round(max_fill_level, 2),
            "gallons_needed": round(needed, 2),
            "fill_percentage": "80%",
            "note": "Most companies fill to 80% for safety",
        }


class PropaneDaysSinceDeliverySensor(AmeriGasSensorBase):
    """Days since delivery sensor."""
    
    _attr_name = "Days Since Last Delivery"
    _attr_unique_id = "propane_days_since_last_delivery"
    _attr_native_unit_of_measurement = "days"
    _attr_icon = "mdi:calendar"
    
    @property
    def native_value(self) -> int | None:
        """Return days since delivery."""
        last_date = self.coordinator.data.get("last_delivery_date")
        
        if not last_date:
            return None
        
        now = dt_util.now()
        return (now - last_date).days
    
    @property
    def available(self) -> bool:
        """Return availability."""
        return self.coordinator.data.get("last_delivery_date") is not None


class PropaneDaysRemainingDifferenceSensor(AmeriGasSensorBase):
    """Days remaining difference sensor.
    
    v3.0.8: Uses centralized helpers for consistent calculations.
    """
    
    _attr_name = "Days Remaining Difference"
    _attr_unique_id = "propane_days_remaining_difference"
    _attr_native_unit_of_measurement = "days"
    _attr_icon = "mdi:compare"
    
    @property
    def native_value(self) -> int | None:
        """Return difference in estimates."""
        amerigas = self.coordinator.data.get("days_remaining") or 0
        
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        
        if remaining is None or avg_usage is None:
            return None
        
        if remaining <= 0:
            mine = 0
        elif avg_usage < 0.001:
            mine = 9999
        else:
            days = remaining / avg_usage
            mine = min(round(days), 9999)
        
        return mine - amerigas
    
    @property
    def available(self) -> bool:
        """Available if we have data to calculate."""
        amerigas = self.coordinator.data.get("days_remaining")
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        return amerigas is not None and remaining is not None and avg_usage is not None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        _, method = self._calculate_used_since_delivery()
        
        mine = None
        if remaining is not None and avg_usage is not None:
            if remaining <= 0:
                mine = 0
            elif avg_usage < 0.001:
                mine = 9999
            else:
                days = remaining / avg_usage
                mine = min(round(days), 9999)
        
        attrs = {
            "amerigas_estimate": self.coordinator.data.get("days_remaining"),
            "your_estimate": mine,
            "gallons_remaining": remaining,
            "daily_average_usage": avg_usage,
            "calculation_method": method,
        }
        
        if remaining is not None and avg_usage is not None and avg_usage > 0:
            days_raw = remaining / avg_usage
            attrs["calculation"] = f"{remaining:.2f} gal ÷ {avg_usage:.2f} gal/day = {days_raw:.1f} days"
            if days_raw > 9999:
                attrs["calculation"] += " (capped at 9999)"
        
        if avg_usage is not None and avg_usage < 0.001:
            attrs["note"] = "Usage rate extremely low - estimate capped at 9999 days"
        
        return attrs


# =============================================================================
# LIFETIME TRACKING SENSORS (v2.0.0+ with v2.1.0 enhancements)
# =============================================================================

class PropaneLifetimeGallonsSensor(AmeriGasSensorBase, RestoreEntity):
    """Lifetime gallons sensor with robust state restoration."""
    
    _attr_name = "Lifetime Gallons"
    _attr_unique_id = "propane_lifetime_gallons"
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:gas-station"
    
    def __init__(self, coordinator: DataUpdateCoordinator, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id)
        self._previous_gallons: float | None = None
        self._lifetime_total: float = 0.0
        self._last_consumption_event: datetime | None = None
        self._total_triggers: int = 0
        self._ignored_triggers: int = 0
        self._largest_consumption: float = 0.0
    
    async def async_added_to_hass(self) -> None:
        """Restore state when added to hass."""
        await super().async_added_to_hass()
        
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in (None, "", "unknown", "unavailable"):
                try:
                    restored_value = float(last_state.state)
                    if restored_value >= 0:
                        self._lifetime_total = restored_value
                        _LOGGER.info(f"Restored lifetime gallons: {self._lifetime_total}")
                except (ValueError, TypeError) as e:
                    _LOGGER.warning(f"Could not restore lifetime gallons: {e}")
            
            if last_state.attributes:
                try:
                    if "previous_gallons" in last_state.attributes:
                        self._previous_gallons = float(last_state.attributes["previous_gallons"])
                    
                    last_event = last_state.attributes.get("last_consumption_event")
                    if last_event and last_event != "never":
                        try:
                            self._last_consumption_event = datetime.fromisoformat(last_event)
                        except (ValueError, TypeError):
                            self._last_consumption_event = None
                    
                    self._total_triggers = last_state.attributes.get("total_triggers", 0)
                    self._ignored_triggers = last_state.attributes.get("ignored_triggers", 0)
                    self._largest_consumption = last_state.attributes.get("largest_consumption", 0.0)
                    
                    if self._lifetime_total == 0.0 and "last_valid_state" in last_state.attributes:
                        backup = last_state.attributes.get("last_valid_state")
                        if backup and backup > 0:
                            self._lifetime_total = float(backup)
                            _LOGGER.warning(f"Main state was 0, restored from backup: {self._lifetime_total}")
                
                except Exception as e:
                    _LOGGER.error(f"Error restoring lifetime sensor attributes: {e}")
        
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )
        
        if self.coordinator.last_update_success and self.coordinator.data:
            self._handle_coordinator_update()
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        current_gallons = self._calculate_gallons_remaining()
        if current_gallons is None:
            self.async_write_ha_state()
            return
        
        if self._previous_gallons is None:
            self._previous_gallons = current_gallons
            self.async_write_ha_state()
            return
        
        diff = self._previous_gallons - current_gallons
        self._total_triggers += 1
        
        if diff > NOISE_THRESHOLD_GALLONS:
            self._lifetime_total += diff
            self._previous_gallons = current_gallons
            self._last_consumption_event = dt_util.now()
            if diff > self._largest_consumption:
                self._largest_consumption = diff
            _LOGGER.info(f"Lifetime consumption: +{diff:.2f} gal, total now {self._lifetime_total:.2f} gal")
        elif diff > 0:
            self._ignored_triggers += 1
        else:
            if diff < -1.0:
                _LOGGER.info(f"Delivery detected: +{abs(diff):.2f} gal")
            self._previous_gallons = current_gallons
        
        self.async_write_ha_state()
    
    @property
    def native_value(self) -> float:
        """Return lifetime gallons."""
        return round(self._lifetime_total, 2)
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        if self._last_consumption_event is None:
            last_event = "never"
        elif isinstance(self._last_consumption_event, str):
            last_event = self._last_consumption_event
        else:
            last_event = self._last_consumption_event.isoformat()
        
        return {
            "last_valid_state": self._lifetime_total,
            "previous_gallons": self._previous_gallons if self._previous_gallons is not None else 0.0,
            "last_consumption_event": last_event,
            "total_triggers": self._total_triggers,
            "ignored_triggers": self._ignored_triggers,
            "largest_consumption": round(self._largest_consumption, 2),
            "threshold_gallons": NOISE_THRESHOLD_GALLONS,
            "version": "3.0.8",
        }


class PropaneLifetimeEnergySensor(AmeriGasSensorBase):
    """Lifetime energy sensor for Energy Dashboard."""
    
    _attr_name = "Lifetime Energy"
    _attr_unique_id = "propane_lifetime_energy"
    _attr_native_unit_of_measurement = "ft³"
    _attr_device_class = SensorDeviceClass.GAS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:fire"
    
    def __init__(self, coordinator: DataUpdateCoordinator, hass: HomeAssistant, lifetime_gallons_sensor: PropaneLifetimeGallonsSensor, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id)
        self._hass = hass
        self._lifetime_gallons_sensor = lifetime_gallons_sensor
    
    @property
    def native_value(self) -> float:
        """Return lifetime energy in cubic feet."""
        gallons = self._lifetime_gallons_sensor.native_value
        
        if gallons is None or gallons == 0:
            return 0.0
        
        return round(gallons * GALLONS_TO_CUBIC_FEET, 2)
    
    @property
    def available(self) -> bool:
        """Always available, even if value is 0."""
        return True
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        gallons = self._lifetime_gallons_sensor.native_value
        
        return {
            "source_sensor": "sensor.propane_tank_lifetime_gallons",
            "conversion_factor": GALLONS_TO_CUBIC_FEET,
            "lifetime_gallons": gallons if gallons is not None else 0.0,
            "formula": f"{gallons if gallons else 0.0} gal × {GALLONS_TO_CUBIC_FEET} ft³/gal",
            "version": "3.0.8",
        }