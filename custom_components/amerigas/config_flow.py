"""Config flow for AmeriGas integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .api import AmeriGasAPI, AmeriGasAPIError, AmeriGasAuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Called from both the initial setup flow and the options flow so that
    credential validation logic only lives in one place.
    """
    api = AmeriGasAPI(data[CONF_USERNAME], data[CONF_PASSWORD])

    try:
        # Attempt to fetch data to validate credentials
        await api.async_get_data()
    except AmeriGasAuthError as err:
        raise InvalidAuth from err
    except AmeriGasAPIError as err:
        raise CannotConnect from err
    finally:
        # Ensure API session is closed after validation
        await api.close()
    
    # Return info that you want to store in the config entry.
    return {"title": "AmeriGas Propane"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AmeriGas."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlow:
        """Return the options flow handler.

        v3.0.12: Enables credential updates via Settings → Devices & Services →
        AmeriGas → Configure without requiring the integration to be deleted
        and re-added.

        Note: config_entry is NOT passed to OptionsFlow() — as of HA 2025.12,
        config_entry is a read-only property injected by HA automatically.
        Passing it manually and assigning self.config_entry raises AttributeError,
        which caused the 500 Internal Server Error when opening the options flow.
        """
        return OptionsFlow()


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options for AmeriGas.

    v3.0.12: Allows credentials to be updated in place. The username field is
    pre-filled with the current value; the password field is always blank so
    the user must deliberately re-enter it (avoids storing it in form state).

    HA 2025.12+: No __init__ override — config_entry is a read-only property
    that HA injects after instantiation. Access it via self.config_entry in
    async_step_init directly.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception in options flow")
                errors["base"] = "unknown"
            else:
                # Update the config entry data with the new credentials.
                # This takes effect on the next coordinator refresh without
                # requiring a full HA restart.
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=user_input
                )
                return self.async_create_entry(title="", data={})

        # Pre-fill username so the user only needs to re-enter the password
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_USERNAME,
                    default=self.config_entry.data.get(CONF_USERNAME, ""),
                ): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""