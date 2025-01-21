"""Config flow for FriGem integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_FRIGATE_URL,
    CONF_MQTT_TOPIC,
    CONF_CAMERAS,
    CONF_PROMPT,
    DEFAULT_MQTT_TOPIC,
    DEFAULT_PROMPT,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_FRIGATE_URL): str,
        vol.Optional(CONF_MQTT_TOPIC, default=DEFAULT_MQTT_TOPIC): str,
    }
)

class FrigemConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FriGem."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.api_key: str | None = None
        self.frigate_url: str | None = None
        self.mqtt_topic: str | None = None
        self.available_cameras: dict[str, str] = {}
        self.selected_camera: str | None = None

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Handle import from configuration."""
        camera = import_data[CONF_CAMERAS][0]
        await self.async_set_unique_id(f"frigem_{camera}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"FriGem - {camera}",
            data=import_data,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self.api_key = user_input[CONF_API_KEY]
            self.frigate_url = user_input[CONF_FRIGATE_URL].rstrip("/")
            self.mqtt_topic = user_input.get(CONF_MQTT_TOPIC, DEFAULT_MQTT_TOPIC)

            try:
                session = async_get_clientsession(self.hass)
                async with session.get(f"{self.frigate_url}/api/config") as response:
                    if response.status == 200:
                        config = await response.json()
                        self.available_cameras = {
                            camera_name: camera.get("name", camera_name)
                            for camera_name, camera in config.get("cameras", {}).items()
                        }
                        return await self.async_step_cameras()
                    errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_cameras(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the camera selection step."""
        errors = {}

        if user_input is not None:
            self.selected_camera = user_input[CONF_CAMERAS]
            return await self.async_step_prompt()

        # Create a list of selectable cameras with proper formatting
        camera_options = [
            selector.SelectOptionDict(
                value=camera_id,
                label=f"{camera_name}",
            )
            for camera_id, camera_name in self.available_cameras.items()
        ]

        return self.async_show_form(
            step_id="cameras",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CAMERAS): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=camera_options,
                            multiple=False,  # Only allow one camera
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            translation_key="cameras",
                        )
                    ),
                }
            ),
            description_placeholders={
                "camera_count": str(len(self.available_cameras)),
            },
            errors=errors,
        )

    async def async_step_prompt(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the prompt configuration step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(f"frigem_{self.selected_camera}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"FriGem - {self.selected_camera}",
                data={
                    CONF_API_KEY: self.api_key,
                    CONF_FRIGATE_URL: self.frigate_url,
                    CONF_MQTT_TOPIC: self.mqtt_topic,
                    CONF_CAMERAS: [self.selected_camera],
                    CONF_PROMPT: user_input[CONF_PROMPT],
                },
            )

        return self.async_show_form(
            step_id="prompt",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PROMPT,
                        default=DEFAULT_PROMPT,
                    ): str,
                }
            ),
            description_placeholders={
                "camera": self.selected_camera,
                "label": "{label}"  # Pass through the {label} placeholder
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> FrigemOptionsFlow:
        """Create the options flow."""
        return FrigemOptionsFlow(config_entry.data, config_entry.entry_id)


class FrigemOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for FriGem."""

    def __init__(self, config_data: dict[str, Any], entry_id: str) -> None:
        """Initialize options flow."""
        self.config_data = config_data
        self.entry_id = entry_id
        self.available_cameras: dict[str, str] = {}
        self.selected_camera: str | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            self.selected_camera = user_input[CONF_CAMERAS]
            return await self.async_step_prompt()

        try:
            session = async_get_clientsession(self.hass)
            async with session.get(f"{self.config_data[CONF_FRIGATE_URL]}/api/config") as response:
                if response.status == 200:
                    config = await response.json()
                    self.available_cameras = {
                        camera_name: camera.get("name", camera_name)
                        for camera_name, camera in config.get("cameras", {}).items()
                    }
        except Exception as err:
            _LOGGER.error("Error connecting to Frigate: %s", str(err))
            return self.async_abort(reason="cannot_connect")

        # Create a list of selectable cameras with proper formatting
        camera_options = [
            selector.SelectOptionDict(
                value=camera_id,
                label=f"{camera_name}",
            )
            for camera_id, camera_name in self.available_cameras.items()
        ]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CAMERAS,
                        default=self.config_data[CONF_CAMERAS][0],  # Get first camera from list
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=camera_options,
                            multiple=False,  # Only allow one camera
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            translation_key="cameras",
                        )
                    ),
                }
            ),
            description_placeholders={
                "camera_count": str(len(self.available_cameras)),
            },
        )

    async def async_step_prompt(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the prompt configuration step."""
        if user_input is not None:
            # Update the config entry
            self.hass.config_entries.async_update_entry(
                self.hass.config_entries.async_get_entry(self.entry_id),
                title=f"FriGem - {self.selected_camera}",
                data={
                    **self.config_data,
                    CONF_CAMERAS: [self.selected_camera],
                    CONF_PROMPT: user_input[CONF_PROMPT],
                },
            )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="prompt",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PROMPT,
                        default=self.config_data.get(CONF_PROMPT, DEFAULT_PROMPT),
                    ): str,
                }
            ),
            description_placeholders={
                "camera": self.selected_camera,
                "label": "{label}"  # Pass through the {label} placeholder
            },
        )
