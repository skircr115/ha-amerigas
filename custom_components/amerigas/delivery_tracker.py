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

# Minimum gallon increase between coordinator polls to be treated as a delivery.
# Sized to be well above normal noise (tank monitor accuracy ~1–2%) but safely
# below any real delivery (smallest realistic fill ~10 gal).
DELIVERY_LEVEL_JUMP_THRESHOLD: float = 10.0


class DeliveryTracker:
    """Tracks deliveries and automatically captures pre-delivery tank levels.

    Two independent trigger paths detect a delivery:

    1. **Level-jump trigger** (telemetry-first): fires as soon as the tank
       monitor reports an increase ≥ DELIVERY_LEVEL_JUMP_THRESHOLD gallons
       between consecutive coordinator polls. Captures both pre_fill_gallons
       and post_fill_gallons directly from the tank monitor — the only values
       guaranteed to be accurate regardless of what the delivery slip or API say.

    2. **Date-change trigger** (API confirmation): fires when last_delivery_date
       changes. If the level-jump trigger already captured post_fill_gallons,
       this path confirms and skips re-capture. Otherwise falls back to
       API-derived pre_delivery_level only (no post_fill available).

    The two paths are de-duplicated via _pending_date_confirmation.
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
        self._last_known_delivery_gallons: float = 0.0
        self._previous_tank_gallons: float | None = None
        self._pre_delivery_level: float = 0.0
        self._post_fill_gallons: float = 0.0
        self._pending_date_confirmation: bool = False
        self._pending_api_capture: bool = False  # Date changed but gallons not yet updated

        # Register coordinator update callback
        self.coordinator.async_add_listener(self._handle_coordinator_update)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator data updates to detect new deliveries."""
        if not self.coordinator.data:
            return

        tank_size = self.coordinator.data.get("tank_size", 500)
        tank_level_pct = self.coordinator.data.get("tank_level", 0)
        tank_level_pct = max(0, min(100, tank_level_pct))
        current_gallons = round(tank_size * (tank_level_pct / 100), 2)

        # ------------------------------------------------------------------
        # Trigger 1: Level-jump (telemetry-first, portal-lag immune)
        # ------------------------------------------------------------------
        if self._previous_tank_gallons is not None:
            jump = current_gallons - self._previous_tank_gallons
            if jump >= DELIVERY_LEVEL_JUMP_THRESHOLD:
                _LOGGER.info(
                    "Delivery detected via level-jump trigger: %.1f → %.1f gal "
                    "(+%.1f gal). Capturing pre/post fill from tank monitor.",
                    self._previous_tank_gallons,
                    current_gallons,
                    jump,
                )
                # Both values sourced directly from the tank monitor.
                # The delivery slip and API last_delivery_gallons routinely
                # differ from the monitor reading — only the monitor is trusted.
                self._store_delivery_levels(
                    pre_fill=self._previous_tank_gallons,
                    post_fill=current_gallons,
                    trigger="level_jump",
                )
                self._pending_date_confirmation = True

        self._previous_tank_gallons = current_gallons

        # ------------------------------------------------------------------
        # Trigger 2: Date-change (API confirmation)
        # ------------------------------------------------------------------
        delivery_date = self.coordinator.data.get("last_delivery_date")
        delivery_gallons = self.coordinator.data.get("last_delivery_gallons", 0.0)

        if (
            delivery_date
            and delivery_date != self._last_known_delivery_date
            and self._last_known_delivery_date is not None
        ):
            if self._pending_date_confirmation:
                _LOGGER.info(
                    "Delivery confirmed by API date change (%s → %s). "
                    "Pre/post fill already captured by level-jump — skipping re-capture.",
                    self._last_known_delivery_date,
                    delivery_date,
                )
                self._pending_date_confirmation = False
            elif delivery_gallons != self._last_known_delivery_gallons:
                # Date and gallons both updated in the same poll — capture immediately.
                _LOGGER.info(
                    "Delivery detected via date-change trigger: %s → %s. "
                    "No level-jump captured; using API data (no post_fill available).",
                    self._last_known_delivery_date,
                    delivery_date,
                )
                self._capture_pre_delivery_level_from_api()
                self._pending_api_capture = False
            else:
                # Date changed but gallons not yet updated — portal lag between responses.
                # Defer capture until gallons catches up on a subsequent poll.
                _LOGGER.info(
                    "Delivery date changed (%s → %s) but gallons unchanged (%.1f gal) — "
                    "deferring capture until portal updates last_delivery_gallons.",
                    self._last_known_delivery_date,
                    delivery_date,
                    delivery_gallons,
                )
                self._pending_api_capture = True

        elif self._pending_api_capture and delivery_gallons != self._last_known_delivery_gallons:
            # Deferred capture: gallons has now updated on a subsequent poll.
            _LOGGER.info(
                "Deferred API capture firing: last_delivery_gallons updated to %.1f gal.",
                delivery_gallons,
            )
            self._capture_pre_delivery_level_from_api()
            self._pending_api_capture = False

        if delivery_date:
            self._last_known_delivery_date = delivery_date
        self._last_known_delivery_gallons = delivery_gallons

    # ------------------------------------------------------------------
    # Capture helpers
    # ------------------------------------------------------------------

    def _store_delivery_levels(self, pre_fill: float, post_fill: float, trigger: str) -> None:
        """Persist both pre-fill and post-fill tank monitor readings."""
        pre_fill = max(0.0, round(pre_fill, 2))
        post_fill = max(0.0, round(post_fill, 2))

        self._pre_delivery_level = pre_fill
        self._post_fill_gallons = post_fill

        _LOGGER.info(
            "Delivery levels captured (trigger=%s): pre=%.2f gal, post=%.2f gal, "
            "monitor-derived delivery=%.2f gal",
            trigger,
            pre_fill,
            post_fill,
            post_fill - pre_fill,
        )
        self._update_number_entity(pre_fill, post_fill)

    def _capture_pre_delivery_level_from_api(self) -> None:
        """Calculate pre-delivery level from API post-delivery data.

        Used only by the date-change path when no level-jump was detected.
        post_fill_gallons is NOT set — sensor.py will fall back to
        pre_delivery_level + last_delivery_gallons for this path.

        Logic:
        - Current level (from API) = Post-delivery level
        - Delivery amount (from API) = Gallons delivered
        - Pre-delivery level = Current - Delivery

        Example:
        - Current: 420 gallons (after delivery, from API)
        - Delivery: 255.9 gallons (from API, may lag 24-48 h)
        - Pre-delivery: 420 - 255.9 = 164.1 gallons
        """
        try:
            # Get current tank level (post-delivery)
            tank_size = self.coordinator.data.get("tank_size", 500)
            tank_level_pct = self.coordinator.data.get("tank_level", 0)

            # Bounds check
            tank_level_pct = max(0, min(100, tank_level_pct))
            current_level = tank_size * (tank_level_pct / 100)

            # Get delivery amount and calculate pre-delivery level
            delivery_amount = self.coordinator.data.get("last_delivery_gallons", 0)
            pre_delivery_level = max(0.0, current_level - delivery_amount)

            self._pre_delivery_level = round(pre_delivery_level, 2)
            self._post_fill_gallons = 0.0  # Not available on this path

            _LOGGER.info(
                "Pre-delivery level captured (trigger=date_change): %.2f gal. "
                "post_fill not available — sensor will use API fallback.",
                self._pre_delivery_level,
            )
            self._update_number_entity(self._pre_delivery_level, 0.0)

        except Exception as e:
            _LOGGER.error("Error computing pre-delivery level from API data: %s", e)

    def _update_number_entity(self, pre_fill: float, post_fill: float) -> None:
        """Push pre-fill and post-fill values to the number entity."""
        try:
            from homeassistant.helpers import entity_registry as er

            entity_reg = er.async_get(self.hass)

            target_entity_id = entity_reg.async_get_entity_id(
                "number", DOMAIN, f"{self.entry_id}_pre_delivery_level"
            )

            if not target_entity_id:
                _LOGGER.error("Could not find pre-delivery level number entity to update.")
                return

            # Store post_fill in hass.data so sensors can read it without
            # needing a second entity. Persisted via PreDeliveryLevelNumber
            # extra_state_attributes across restarts.
            self.hass.data[DOMAIN]["post_fill_gallons"] = post_fill

            self.hass.async_create_task(
                self.hass.services.async_call(
                    "number",
                    "set_value",
                    {"entity_id": target_entity_id, "value": pre_fill},
                )
            )
            _LOGGER.debug(
                "Queued update of %s: pre_fill=%.2f gal, post_fill=%.2f gal",
                target_entity_id,
                pre_fill,
                post_fill,
            )

        except Exception as e:
            _LOGGER.error("Error updating pre-delivery level entity: %s", e)

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def pre_delivery_level(self) -> float:
        """Return the most recently captured pre-delivery level."""
        return self._pre_delivery_level

    @property
    def post_fill_gallons(self) -> float:
        """Return the most recently captured post-fill tank monitor reading."""
        return self._post_fill_gallons


class PreDeliveryLevelNumber(NumberEntity, RestoreEntity):
    """Number entity storing the auto-captured pre-delivery tank level.

    Automatically updated by DeliveryTracker on each delivery.
    Manually adjustable via the amerigas.set_pre_delivery_level service.

    Also persists post_fill_gallons (from the level-jump trigger) as an
    attribute so sensors can use the tank-monitor-derived post-fill baseline
    across restarts.
    """

    _attr_has_entity_name = True  # Creates name based on device (e.g., "AmeriGas Propane Pre-Delivery Tank Level")
    _attr_name = "Pre-Delivery Tank Level"
    _attr_icon = "mdi:gauge-empty"
    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_mode = NumberMode.BOX
    _attr_native_step = 0.1
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry):
        """Initialize the number entity."""
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_pre_delivery_level"  # Stable unique_id for entity registry lookups
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "AmeriGas Propane",
            "manufacturer": "AmeriGas",
            "model": "AmeriGas Account",
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
        restored = False
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in (None, "unknown", "unavailable"):
                try:
                    self._attr_native_value = float(last_state.state)
                    restored = True
                    _LOGGER.info(f"Restored pre-delivery level: {self._attr_native_value} gal")
                except (ValueError, TypeError):
                    self._attr_native_value = 0.0

            # Restore post_fill_gallons from persisted attributes
            if last_state.attributes and "post_fill_gallons" in last_state.attributes:
                try:
                    post_fill = float(last_state.attributes["post_fill_gallons"])
                    if post_fill > 0:
                        self.hass.data[DOMAIN]["post_fill_gallons"] = post_fill
                        _LOGGER.info(f"Restored post-fill gallons: {post_fill} gal")
                except (ValueError, TypeError):
                    pass

        self._update_tank_limits()

        if restored:
            self.async_write_ha_state()
            _LOGGER.debug("Pre-delivery level state published after restoration")

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
        # Manual set clears post_fill — sensor.py will fall back to
        # pre_delivery + last_delivery_gallons (best available without monitor)
        self.hass.data[DOMAIN]["post_fill_gallons"] = 0.0
        self.async_write_ha_state()
        _LOGGER.info(f"Pre-delivery level manually set to: {value} gal")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        if not self.coordinator.data:
            return {}

        tank_size = self.coordinator.data.get("tank_size", 500)
        last_delivery = self.coordinator.data.get("last_delivery_gallons", 0)
        last_delivery_date = self.coordinator.data.get("last_delivery_date", "unknown")
        post_fill = self.hass.data.get(DOMAIN, {}).get("post_fill_gallons", 0.0)

        attrs = {
            "tank_size": tank_size,
            "last_delivery_date": last_delivery_date,
            "last_delivery_gallons": last_delivery,
            "auto_capture_enabled": True,
            "post_fill_gallons": post_fill,  # Persisted for restore across restarts
        }

        if post_fill > 0:
            attrs["delivered_gallons_monitor"] = round(post_fill - self._attr_native_value, 2)
            attrs["capture_method"] = "tank_monitor"
        elif self._attr_native_value > 0 and last_delivery > 0:
            attrs["capture_method"] = "api_fallback"
            # Show calculated starting level for transparency
            attrs["calculated_starting_level"] = round(
                min(self._attr_native_value + last_delivery, tank_size), 2
            )

        return attrs