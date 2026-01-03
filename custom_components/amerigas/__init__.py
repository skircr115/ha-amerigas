"""The AmeriGas Propane integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AmeriGasAPI
from .const import DOMAIN
from .delivery_tracker import DeliveryTracker

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_PRE_DELIVERY_LEVEL = "set_pre_delivery_level"
ATTR_GALLONS = "gallons"

SERVICE_SET_PRE_DELIVERY_LEVEL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_GALLONS): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=1000)
        ),
    }
)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AmeriGas from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    
    api = AmeriGasAPI(username, password)
    
    async def async_update_data():
        """Fetch data from AmeriGas."""
        try:
            return await api.async_get_data()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with AmeriGas: {err}") from err
    
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(hours=6),
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Set up delivery tracker for automatic pre-delivery level capture
    tracker = DeliveryTracker(hass, coordinator, entry.entry_id)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "tracker": tracker,
    }
    
    # Register service for manual pre-delivery level setting
    async def async_handle_set_pre_delivery_level(call: ServiceCall) -> None:
        """Handle the set_pre_delivery_level service call."""
        gallons = call.data[ATTR_GALLONS]
        
        # Update the number entity
        number_entity_id = f"number.{DOMAIN}_pre_delivery_level"
        
        await hass.services.async_call(
            "number",
            "set_value",
            {
                "entity_id": number_entity_id,
                "value": gallons,
            },
            blocking=True,
        )
        
        _LOGGER.info(
            "Manual pre-delivery level set to %.1f gallons via service call",
            gallons,
        )
    
    # Register the service (only once for the domain)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_PRE_DELIVERY_LEVEL):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_PRE_DELIVERY_LEVEL,
            async_handle_set_pre_delivery_level,
            schema=SERVICE_SET_PRE_DELIVERY_LEVEL_SCHEMA,
        )
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Unregister service if no other instances are running
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SET_PRE_DELIVERY_LEVEL)
    
    return unload_ok
