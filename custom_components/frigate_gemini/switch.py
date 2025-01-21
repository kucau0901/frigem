"""Switch platform for frigate_gemini."""
from __future__ import annotations

import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the FriGem switches."""
    cameras = config_entry.data.get("cameras", [])
    _LOGGER.debug("[frigate_gemini] Setting up switches for cameras: %s", cameras)
    switches = [FrigateGeminiSwitch(camera) for camera in cameras]
    async_add_entities(switches)


class FrigateGeminiSwitch(SwitchEntity):
    """Switch to enable/disable Gemini analysis for a camera."""
    
    _attr_has_entity_name = True
    
    def __init__(self, camera: str) -> None:
        """Initialize the switch."""
        self._camera = camera
        self._attr_unique_id = f"frigem_switch_{camera}"
        self._attr_name = f"FriGem Analysis {camera}"
        self._attr_is_on = True  # Default to enabled
        _LOGGER.debug("[frigate_gemini] Initialized switch for camera %s (enabled by default)", camera)
        
    async def async_turn_on(self, **kwargs) -> None:
        """Turn on Gemini analysis."""
        self._attr_is_on = True
        self.async_write_ha_state()
        _LOGGER.debug("[frigate_gemini] Enabled analysis for camera %s", self._camera)
        
    async def async_turn_off(self, **kwargs) -> None:
        """Turn off Gemini analysis."""
        self._attr_is_on = False
        self.async_write_ha_state()
        _LOGGER.debug("[frigate_gemini] Disabled analysis for camera %s", self._camera)

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:video-check" if self.is_on else "mdi:video-off"
