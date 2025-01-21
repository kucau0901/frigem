"""The FriGem integration."""
from __future__ import annotations

import logging
import asyncio
import aiohttp
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_MQTT_TOPIC,
    CONF_FRIGATE_URL,
    CONF_CAMERAS,
    CONF_PROMPT,
    DEFAULT_MQTT_TOPIC,
    DEFAULT_PROMPT,
)
from .mqtt_handler import MQTTHandler
from .gemini_handler import GeminiHandler

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.SWITCH]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the FriGem component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FriGem from a config entry."""
    try:
        # Ensure we have the required configuration
        if not entry.data.get(CONF_API_KEY):
            raise ConfigEntryNotReady("Missing API key")
        if not entry.data.get(CONF_FRIGATE_URL):
            raise ConfigEntryNotReady("Missing Frigate URL")
        if not entry.data.get(CONF_CAMERAS):
            raise ConfigEntryNotReady("No cameras configured")

        # Initialize data store
        hass.data.setdefault(DOMAIN, {})
        
        # Set unique ID if not set
        if not entry.unique_id:
            hass.config_entries.async_update_entry(
                entry, unique_id=f"frigem_{entry.data[CONF_CAMERAS][0]}"
            )

        # Initialize handlers
        try:
            # Initialize Gemini handler first
            gemini_handler = GeminiHandler(entry.data[CONF_API_KEY])
            _LOGGER.debug("Gemini handler initialized successfully")

            # Initialize MQTT handler
            mqtt_handler = MQTTHandler(
                hass,
                entry.data[CONF_FRIGATE_URL],
                entry.data.get(CONF_MQTT_TOPIC, DEFAULT_MQTT_TOPIC),
                entry.data[CONF_CAMERAS],
                entry.data.get(CONF_PROMPT, DEFAULT_PROMPT),
                gemini_handler,
            )
            await mqtt_handler.async_setup()
            _LOGGER.debug("MQTT handler initialized successfully")

            # Store handlers
            hass.data[DOMAIN][entry.entry_id] = {
                "mqtt_handler": mqtt_handler,
                "gemini_handler": gemini_handler,
            }

            # Set up platforms
            await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
            _LOGGER.debug("Platforms setup completed")

            return True

        except Exception as err:
            _LOGGER.error("Error setting up FriGem: %s", str(err))
            # Clean up any partially initialized handlers
            if "mqtt_handler" in locals():
                await mqtt_handler.async_unload()
            if "gemini_handler" in locals():
                await gemini_handler.close()
            raise ConfigEntryNotReady(f"Failed to initialize: {str(err)}") from err

    except Exception as err:
        _LOGGER.error("Error during FriGem setup: %s", str(err))
        raise ConfigEntryNotReady(f"Setup failed: {str(err)}") from err


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading FriGem integration")

    # Unload platforms first
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Get the data store
        data = hass.data[DOMAIN].pop(entry.entry_id)
        
        # Clean up handlers
        if mqtt_handler := data.get("mqtt_handler"):
            await mqtt_handler.async_unload()
            _LOGGER.debug("MQTT handler unloaded")
            
        if gemini_handler := data.get("gemini_handler"):
            await gemini_handler.close()
            _LOGGER.debug("Gemini handler closed")

    return unload_ok
