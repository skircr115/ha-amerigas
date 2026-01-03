"""Delivery tracking and automatic pre-delivery level capture."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfVolume

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class DeliveryTracker:
    """Tracks deliveries and automatically captures pre-delivery tank levels.
    
    This class monitors the last_delivery_date sensor and when it changes,
    automatically calculates and stores the pre-delivery tank level.
    
    The calculation is simple: pre_delivery = current_level - delivery_amount
    This works because when the API updates, it provides the post-delivery level.
    """
    
    def __init__(
        self,
        hass: HomeAssistant,
        coordinator,
        entry_id: str,
    ):
        """Initialize the delivery tracker."""
        self.hass = hass
        self.coordinator = coordinator
        self.entry_id = entry_id
        self._last_known_delivery_date: str | None = None
        self._pre_delivery_level: float = 0.0
        
        # Register coordinator update callback
        self.coordinator.async_add_listener(self._handle_coordinator_update)
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator data updates to detect new deliveries."""
        if not self.coordinator.data:
            return
        
        delivery_date = self.coordinator.data.get("last_delivery_date")
        
        # Check if this is a new delivery
        if (delivery_date and 
            delivery_date != self._last_known_delivery_date and
            self._last_known_delivery_date is not None):
            
            _LOGGER.info(f"New delivery detected! Date changed from "
                        f"{self._last_known_delivery_date} to {delivery_date}")
            
            # Capture the pre-delivery level
            self._capture_pre_delivery_level()
        
        # Update last known date
        if delivery_date:
            self._last_known_delivery_date = delivery_date
    
    def _capture_pre_delivery_level(self) -> None:
        """Calculate and store the pre-delivery tank level.
        
        Logic:
        - Current level (from API) = Post-delivery level
        - Delivery amount (from API) = Gallons delivered
        - Pre-delivery level = Current - Delivery
        
        Example:
        - Current: 420 gallons (after delivery)
        - Delivery: 28.1 gallons
        - Pre-delivery: 420 - 28.1 = 391.9 gallons
        """
        try:
            # Get current tank level (post-delivery)
            tank_size = self.coordinator.data.get("tank_size", 500)
            tank_level_pct = self.coordinator.data.get("tank_level", 0)
            
            # Bounds check
            if tank_level_pct < 0:
                tank_level_pct = 0
            elif tank_level_pct > 100:
                tank_level_pct = 100
            
            current_level = tank_size * (tank_level_pct / 100)
            
            # Get delivery amount
            delivery_amount = self.coordinator.data.get("last_delivery_gallons", 0)
            
            # Calculate pre-delivery level
            pre_delivery_level = current_level - delivery_amount
            
            # Bounds check
            if pre_delivery_level < 0:
                pre_delivery_level = 0
            
            # Store the captured level
            self._pre_delivery_level = round(pre_delivery_level, 2)
            
            _LOGGER.info(
                f"Auto-captured pre-delivery level: {self._pre_delivery_level} gal "
                f"(Current: {current_level} gal, Delivery: {delivery_amount} gal)"
            )
            
            # Update the number entity
            entity_id = f"number.{DOMAIN}_pre_delivery_level"
            if state := self.hass.states.get(entity_id):
                # Trigger update by setting the value
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        "number",
                        "set_value",
                        {
                            "entity_id": entity_id,
                            "value": self._pre_delivery_level,
                        },
                    )
                )
            
        except Exception as e:
            _LOGGER.error(f"Error capturing pre-delivery level: {e}")
    
    @property
    def pre_delivery_level(self) -> float:
        """Return the captured pre-delivery level."""
        return self._pre_delivery_level


class PreDeliveryLevelNumber(NumberEntity, RestoreEntity):
    """Number entity that stores the automatically captured pre-delivery tank level.
    
    This entity is automatically updated by the DeliveryTracker when a new
    delivery is detected. Users can also manually adjust it if needed.
    
    The value is used by the "Used Since Last Delivery" sensor to provide
    accurate consumption tracking regardless of delivery size.
    """
    
    _attr_has_entity_name = False  # Use explicit name for predictable entity_id
    _attr_name = "AmeriGas Pre-Delivery Level"  # Generates: number.amerigas_pre_delivery_level
    _attr_icon = "mdi:gauge-empty"
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_mode = NumberMode.BOX
    _attr_native_step = 0.1
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def __init__(self, coordinator, entry):
        """Initialize the number entity."""
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_pre_delivery_level"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "AmeriGas Propane",
            "manufacturer": "AmeriGas",
            "model": "Propane Tank Monitor",
        }
        
        # Set min/max based on tank size when available
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 1000.0
        
        # Start at 0 (will be auto-populated on first delivery)
        self._attr_native_value = 0.0
    
    async def async_added_to_hass(self) -> None:
        """Restore last state when entity is added."""
        await super().async_added_to_hass()
        
        # Restore previous value
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in (None, "unknown", "unavailable"):
                try:
                    self._attr_native_value = float(last_state.state)
                    _LOGGER.info(f"Restored pre-delivery level: {self._attr_native_value} gal")
                except (ValueError, TypeError):
                    self._attr_native_value = 0.0
        
        # Update min/max based on tank size
        self._update_tank_limits()
        
        # Listen for coordinator updates to adjust limits
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_tank_limits()
        self.async_write_ha_state()
    
    def _update_tank_limits(self) -> None:
        """Update min/max based on current tank size."""
        if self.coordinator.data and (tank_size := self.coordinator.data.get("tank_size")):
            self._attr_native_max_value = float(tank_size)
    
    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._attr_native_value
    
    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        self._attr_native_value = value
        self.async_write_ha_state()
        _LOGGER.info(f"Pre-delivery level set to: {value} gal")
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        if not self.coordinator.data:
            return {}
        
        tank_size = self.coordinator.data.get("tank_size", 500)
        last_delivery = self.coordinator.data.get("last_delivery_gallons", 0)
        last_delivery_date = self.coordinator.data.get("last_delivery_date", "unknown")
        
        attrs = {
            "tank_size": tank_size,
            "last_delivery_date": last_delivery_date,
            "last_delivery_gallons": last_delivery,
            "auto_capture_enabled": True,
        }
        
        # Show calculated starting level if we have delivery data
        if self._attr_native_value > 0 and last_delivery > 0:
            starting_level = self._attr_native_value + last_delivery
            # Cap at tank capacity
            if starting_level > tank_size:
                starting_level = tank_size
            
            attrs["calculated_starting_level"] = round(starting_level, 2)
            attrs["calculation"] = f"{self._attr_native_value} + {last_delivery} = {starting_level}"
        
        return attrs
