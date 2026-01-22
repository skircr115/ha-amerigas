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
    
    def _calculate_used_since_delivery(self) -> float | None:
        """Calculate gallons used since delivery from coordinator data."""
        tank_size = self.coordinator.data.get("tank_size") or DEFAULT_TANK_SIZE
        tank_level = self.coordinator.data.get("tank_level") or 0
        
        # Bounds check
        if tank_level < 0:
            tank_level = 0
        elif tank_level > 100:
            tank_level = 100
        
        current = tank_size * (tank_level / 100)
        last_delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        
        # Calculate used amount
        if last_delivery > 0:
            estimated_before = tank_size * 0.20
            starting_level = estimated_before + last_delivery
            if starting_level > tank_size:
                starting_level = tank_size
            used = starting_level - current
        else:
            full_fill_level = tank_size * DEFAULT_FILL_PERCENTAGE
            used = full_fill_level - current
        
        return max(0, round(used, 2))
    
    def _calculate_daily_average(self) -> float | None:
        """Calculate daily average usage from coordinator data."""
        last_date = self.coordinator.data.get("last_delivery_date")
        if not last_date:
            return None
        
        used = self._calculate_used_since_delivery()
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
        tank_size = self.coordinator.data.get("tank_size") or DEFAULT_TANK_SIZE
        percent = self.coordinator.data.get("tank_level") or 0
        
        # v2.0.1: Bounds check - clamp to 0-100%
        if percent < 0:
            percent = 0
        elif percent > 100:
            percent = 100
        
        return round(tank_size * (percent / 100), 2)
    
    @property
    def available(self) -> bool:
        """Return if sensor is available."""
        # v2.0.1: Require valid tank size
        tank_size = self.coordinator.data.get("tank_size")
        return tank_size is not None and tank_size > 0


class PropaneUsedSinceDeliverySensor(AmeriGasSensorBase):
    """Used since delivery sensor with v2.1.0 improvements."""
    
    _attr_name = "Used Since Last Delivery"
    _attr_unique_id = "propane_used_since_last_delivery"
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:gas-station"
    
    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()
        
        # Initialize storage for pre-delivery entity ID
        self._pre_delivery_entity_id = None
        
        # Find and listen to the pre-delivery level number entity
        try:
            from homeassistant.helpers import entity_registry as er
            from homeassistant.core import callback
            
            entity_reg = er.async_get(self.hass)
            
            # Find the pre-delivery level number entity
            for entity in entity_reg.entities.values():
                if entity.unique_id and entity.unique_id.endswith("_pre_delivery_level"):
                    if entity.platform == DOMAIN:
                        self._pre_delivery_entity_id = entity.entity_id
                        _LOGGER.debug(
                            f"Found pre-delivery entity: {self._pre_delivery_entity_id}, "
                            "setting up state listener"
                        )
                        break
            
            # Set up listener for pre-delivery level changes
            if self._pre_delivery_entity_id:
                @callback
                def _handle_pre_delivery_change(event):
                    """Handle pre-delivery level state change."""
                    # Check if this event is for our entity
                    if event.data.get("entity_id") != self._pre_delivery_entity_id:
                        return
                    
                    new_state = event.data.get("new_state")
                    if new_state and new_state.state not in ("unknown", "unavailable"):
                        _LOGGER.debug(
                            f"Pre-delivery level changed to {new_state.state}, "
                            "triggering sensor update"
                        )
                        self.async_write_ha_state()
                
                self.async_on_remove(
                    self.hass.bus.async_listen(
                        "state_changed",
                        _handle_pre_delivery_change,
                    )
                )
        except Exception as e:
            _LOGGER.warning(f"Could not set up pre-delivery level listener: {e}")
    
    @property
    def native_value(self) -> float | None:
        """Return gallons used with auto-captured pre-delivery level.
        
        v3.0.5: Uses automatically captured pre-delivery level from DeliveryTracker.
        When a new delivery is detected, the system automatically calculates:
        pre_delivery = current_level - delivery_amount
        
        This provides 100% accurate tracking regardless of delivery size.
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
        
        # v3.0.5: Check for AUTO-CAPTURED pre-delivery level using entity registry
        auto_captured_level = 0.0
        
        if self.hass:
            try:
                from homeassistant.helpers import entity_registry as er
                
                # Get entity registry
                entity_reg = er.async_get(self.hass)
                
                # Find the pre-delivery level number entity by unique_id pattern
                # The unique_id is {entry_id}_pre_delivery_level
                for entity in entity_reg.entities.values():
                    if entity.unique_id and entity.unique_id.endswith("_pre_delivery_level"):
                        if entity.platform == DOMAIN:
                            # Found it! Now get its state
                            if state := self.hass.states.get(entity.entity_id):
                                try:
                                    auto_captured_level = float(state.state)
                                    break
                                except (ValueError, TypeError):
                                    pass
            except Exception as e:
                _LOGGER.debug(f"Could not lookup pre-delivery level entity: {e}")
        
        # Calculate starting level based on available data
        if auto_captured_level > 0:
            # v3.0.5: AUTO-CAPTURED level (100% accurate!)
            starting_level = auto_captured_level + last_delivery
            calculation_method = "auto_captured"
        elif last_delivery > 0:
            # Fallback: Smart estimation based on delivery size
            if last_delivery < 50:
                # Small delivery = likely a top-off
                estimated_before = tank_size * 0.65
                calculation_method = "small_delivery_estimate"
            else:
                # Large delivery = likely a fill from low
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
        
        # Store calculation method for attributes
        self._calculation_method = calculation_method
        self._starting_level = starting_level
        self._pre_delivery_level = auto_captured_level if auto_captured_level > 0 else None
        
        # If negative (overfill/heat), show 0
        return max(0, round(used, 2))
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        last_delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        
        attrs = {
            "calculation_method": getattr(self, '_calculation_method', 'unknown'),
            "last_delivery_gallons": last_delivery,
            "calculated_starting_level": round(getattr(self, '_starting_level', 0), 2),
        }
        
        # Add pre-delivery level if auto-captured
        if hasattr(self, '_pre_delivery_level') and self._pre_delivery_level:
            attrs["pre_delivery_level"] = round(self._pre_delivery_level, 2)
            attrs["accuracy"] = "100% (auto-captured)"
        elif attrs["calculation_method"] == "small_delivery_estimate":
            attrs["accuracy"] = "~75% (estimated)"
        elif attrs["calculation_method"] == "large_delivery_estimate":
            attrs["accuracy"] = "~95% (estimated)"
        else:
            attrs["accuracy"] = "~90% (estimated)"
        
        return attrs


class PropaneEnergyConsumptionSensor(AmeriGasSensorBase):
    """Energy consumption sensor (display only, not for Energy Dashboard).
    
    v3.0.7: Calculate directly from coordinator data instead of entity lookup.
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
        
        Calculate directly from coordinator data using same logic as UsedSinceDeliverySensor.
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
        
        # Calculate used amount (same logic as UsedSinceDeliverySensor)
        if last_delivery > 0:
            if last_delivery < 50:
                estimated_before = tank_size * 0.65
            else:
                estimated_before = tank_size * 0.20
            starting_level = estimated_before + last_delivery
            if starting_level > tank_size:
                starting_level = tank_size
            used = starting_level - current
        else:
            full_fill_level = tank_size * DEFAULT_FILL_PERCENTAGE
            used = full_fill_level - current
        
        used = max(0, used)
        
        # Convert to cubic feet
        return round(used * GALLONS_TO_CUBIC_FEET, 2)
    
    @property
    def available(self) -> bool:
        """Return availability."""
        tank_size = self.coordinator.data.get("tank_size")
        return tank_size is not None and tank_size > 0


class PropaneDailyAverageUsageSensor(AmeriGasSensorBase):
    """Daily average usage sensor with v2.1.0 improvements."""
    
    _attr_name = "Daily Average Usage"
    _attr_unique_id = "propane_daily_average_usage"
    _attr_native_unit_of_measurement = "gal/day"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-line"
    
    @property
    def native_value(self) -> float | None:
        """Return daily average usage."""
        last_date = self.coordinator.data.get("last_delivery_date")
        
        if not last_date:
            return None
        
        # Calculate used amount directly
        tank_size = self.coordinator.data.get("tank_size") or DEFAULT_TANK_SIZE
        tank_level = self.coordinator.data.get("tank_level") or 0
        
        # Bounds check
        if tank_level < 0:
            tank_level = 0
        elif tank_level > 100:
            tank_level = 100
        
        current = tank_size * (tank_level / 100)
        last_delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        
        # Calculate used amount (same logic as UsedSinceDeliverySensor)
        if last_delivery > 0:
            estimated_before = tank_size * 0.20
            starting_level = estimated_before + last_delivery
            if starting_level > tank_size:
                starting_level = tank_size
            used = starting_level - current
        else:
            full_fill_level = tank_size * DEFAULT_FILL_PERCENTAGE
            used = full_fill_level - current
        
        used = max(0, used)
        
        # Calculate days since delivery
        now = dt_util.now()
        days = (now - last_date).days
        
        # v2.1.0: Return None instead of 0 on same day as delivery
        if days <= 0:
            return None
        
        return round(used / days, 2)
    
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


class PropaneDaysUntilEmptySensor(AmeriGasSensorBase):
    """Days until empty sensor.
    
    v3.0.7: Always calculate days remaining regardless of usage rate.
    Only unavailable if no usage data exists at all (no delivery ever recorded).
    """
    
    _attr_name = "Days Until Empty"
    _attr_unique_id = "propane_days_until_empty"
    _attr_native_unit_of_measurement = "days"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calendar-clock"
    
    @property
    def native_value(self) -> int | None:
        """Return days until empty.
        
        Calculate days remaining based on current usage rate, no matter how small.
        Only return None if we truly cannot calculate (no delivery data).
        """
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        
        # Return None only if we can't calculate at all
        # (avg_usage is None means no delivery has ever been recorded)
        if remaining is None or avg_usage is None:
            return None
        
        # If tank is empty, return 0
        if remaining <= 0:
            return 0
        
        # If usage is effectively zero (< 0.001 gal/day), cap at 9999 days
        # This prevents overflow while being honest about extremely low usage
        if avg_usage < 0.001:
            return 9999
        
        # Always do the math - divide remaining by usage rate
        days = remaining / avg_usage
        
        # Cap at reasonable maximum to prevent integer overflow
        if days > 9999:
            return 9999
        
        return round(days)
    
    @property
    def available(self) -> bool:
        """Sensor is available if we have the data needed to calculate.
        
        Only unavailable if:
        - No delivery has ever occurred (no avg_usage data)
        - Tank size is unknown
        - Current level is unknown
        """
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        
        # Available as long as we can calculate something
        # avg_usage being None means no delivery date exists (no usage data ever)
        return remaining is not None and avg_usage is not None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        
        attrs = {
            "gallons_remaining": remaining,
            "daily_average_usage": avg_usage,
        }
        
        # Add helpful notes for edge cases
        if avg_usage is not None:
            if avg_usage < 0.001:
                attrs["note"] = "Usage rate extremely low - showing 9999 days as practical maximum"
            elif avg_usage < 0.1:
                attrs["note"] = f"Low usage rate: {avg_usage:.3f} gal/day"
        
        # Show the calculation for transparency
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
        payment = self.coordinator.data.get("last_payment_amount") or 0
        delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        
        # v2.1.0: Return None instead of 0
        if delivery <= 0:
            return None
        
        return round(payment / delivery, 2)
    
    @property
    def available(self) -> bool:
        """Return availability."""
        payment = self.coordinator.data.get("last_payment_amount") or 0
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
        payment = self.coordinator.data.get("last_payment_amount") or 0
        delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        
        if delivery <= 0:
            return None
        
        cost_per_gallon = payment / delivery
        return round(cost_per_gallon / GALLONS_TO_CUBIC_FEET, 4)
    
    @property
    def available(self) -> bool:
        """Return availability."""
        payment = self.coordinator.data.get("last_payment_amount") or 0
        delivery = self.coordinator.data.get("last_delivery_gallons") or 0
        return delivery > 0


class PropaneCostSinceDeliverySensor(AmeriGasSensorBase):
    """Cost since delivery sensor."""
    
    _attr_name = "Cost Since Last Delivery"
    _attr_unique_id = "propane_cost_since_last_delivery"
    _attr_native_unit_of_measurement = "USD"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:cash"
    
    @property
    def native_value(self) -> float | None:
        """Return cost since delivery."""
        used = self._calculate_used_since_delivery()
        cost = self._calculate_cost_per_gallon()
        
        if used is None or cost is None:
            return None
        
        return round(used * cost, 2)


class PropaneEstimatedRefillCostSensor(AmeriGasSensorBase):
    """Estimated refill cost sensor."""
    
    _attr_name = "Estimated Refill Cost"
    _attr_unique_id = "propane_estimated_refill_cost"
    _attr_native_unit_of_measurement = "USD"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:cash-multiple"
    
    @property
    def native_value(self) -> float | None:
        """Return estimated refill cost.
        
        v3.0.5: Uses realistic 80% maximum fill level instead of 100%.
        Most propane companies fill to 80% for safety (thermal expansion).
        """
        tank_size = self.coordinator.data.get("tank_size") or DEFAULT_TANK_SIZE
        remaining = self._calculate_gallons_remaining()
        cost = self._calculate_cost_per_gallon()
        
        if remaining is None or cost is None:
            return None
        
        # v3.0.5: Use 80% maximum fill level (industry standard)
        max_fill_level = tank_size * 0.80
        
        needed = max_fill_level - remaining
        
        # Bounds check
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
    
    v3.0.7: Calculate difference regardless of usage rate.
    Only unavailable if no usage data exists.
    """
    
    _attr_name = "Days Remaining Difference"
    _attr_unique_id = "propane_days_remaining_difference"
    _attr_native_unit_of_measurement = "days"
    _attr_icon = "mdi:compare"
    
    @property
    def native_value(self) -> int | None:
        """Return difference in estimates.
        
        Calculates the difference between your calculated estimate and AmeriGas's estimate.
        Always does the math, regardless of usage rate.
        """
        amerigas = self.coordinator.data.get("days_remaining") or 0
        
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        
        # Can't calculate without data
        if remaining is None or avg_usage is None:
            return None
        
        # Calculate our estimate (same logic as Days Until Empty)
        if remaining <= 0:
            mine = 0
        elif avg_usage < 0.001:
            mine = 9999  # Cap at same maximum as Days Until Empty
        else:
            days = remaining / avg_usage
            mine = min(round(days), 9999)  # Cap at 9999
        
        return mine - amerigas
    
    @property
    def available(self) -> bool:
        """Available if we have data to calculate.
        
        Only unavailable if no delivery has ever occurred or AmeriGas data missing.
        """
        amerigas = self.coordinator.data.get("days_remaining")
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        
        return amerigas is not None and remaining is not None and avg_usage is not None
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        remaining = self._calculate_gallons_remaining()
        avg_usage = self._calculate_daily_average()
        
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
        }
        
        # Show calculation for transparency
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
    """Lifetime gallons sensor with v2.1.0 enhancements."""
    
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
        
        # Restore previous state
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._lifetime_total = float(last_state.state)
                
                # v2.1.0: Restore diagnostic attributes
                if last_state.attributes:
                    # Parse last_consumption_event back to datetime if it's a string
                    last_event = last_state.attributes.get("last_consumption_event")
                    if last_event and last_event != "never":
                        try:
                            # Parse ISO format string back to datetime
                            self._last_consumption_event = datetime.fromisoformat(last_event)
                        except (ValueError, TypeError):
                            self._last_consumption_event = None
                    else:
                        self._last_consumption_event = None
                    
                    self._total_triggers = last_state.attributes.get("total_triggers", 0)
                    self._ignored_triggers = last_state.attributes.get("ignored_triggers", 0)
                    self._largest_consumption = last_state.attributes.get("largest_consumption", 0.0)
                    # v2.1.0: State preservation backup
                    if "last_valid_state" in last_state.attributes:
                        backup = last_state.attributes.get("last_valid_state")
                        if backup and self._lifetime_total == 0:
                            self._lifetime_total = float(backup)
            except (ValueError, TypeError):
                self._lifetime_total = 0.0
        
        # Set up listener for gallons remaining changes
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Get current gallons remaining using helper method
        current_gallons = self._calculate_gallons_remaining()
        if current_gallons is None:
            self.async_write_ha_state()
            return
        
        # First run - just store current value
        if self._previous_gallons is None:
            self._previous_gallons = current_gallons
            self.async_write_ha_state()
            return
        
        # Calculate difference
        diff = self._previous_gallons - current_gallons
        
        # v2.1.0: Increment total triggers
        self._total_triggers += 1
        
        # v2.0.1: Noise filter - only track if > threshold
        if diff > NOISE_THRESHOLD_GALLONS:
            # Consumption occurred
            self._lifetime_total += diff
            self._previous_gallons = current_gallons
            
            # v2.1.0: Update diagnostic attributes
            self._last_consumption_event = dt_util.now()
            if diff > self._largest_consumption:
                self._largest_consumption = diff
        elif diff > 0:
            # v2.1.0: Small change filtered as noise
            self._ignored_triggers += 1
            # Don't update previous_gallons - wait for larger change
        else:
            # Level went up (delivery or thermal expansion)
            # Update previous but don't add to lifetime
            self._previous_gallons = current_gallons
        
        self.async_write_ha_state()
    
    @property
    def native_value(self) -> float:
        """Return lifetime gallons."""
        return round(self._lifetime_total, 2)
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes (v2.1.0 enhancements)."""
        # Handle last_consumption_event - could be datetime or string
        if self._last_consumption_event is None:
            last_event = "never"
        elif isinstance(self._last_consumption_event, str):
            last_event = self._last_consumption_event
        else:
            # It's a datetime object
            last_event = self._last_consumption_event.isoformat()
        
        return {
            # v2.1.0: State preservation backup
            "last_valid_state": self._lifetime_total,
            # v2.1.0: Diagnostic attributes
            "last_consumption_event": last_event,
            "total_triggers": self._total_triggers,
            "ignored_triggers": self._ignored_triggers,
            "largest_consumption": round(self._largest_consumption, 2),
            "threshold_gallons": NOISE_THRESHOLD_GALLONS,
            "version": "3.0.7",
        }


class PropaneLifetimeEnergySensor(AmeriGasSensorBase):
    """Lifetime energy sensor for Energy Dashboard.
    
    v3.0.7: Return 0.0 instead of None for better Energy Dashboard compatibility.
    """
    
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
        """Return lifetime energy in cubic feet.
        
        Math: gallons × 36.3888 = cubic feet
        Returns 0.0 instead of None for better Energy Dashboard compatibility.
        """
        # Get directly from the lifetime gallons sensor instance
        gallons = self._lifetime_gallons_sensor.native_value
        
        # Return 0.0 instead of None for Energy Dashboard
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
            "version": "3.0.7",
        }