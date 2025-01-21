"""Sensor platform for FriGem integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    CONF_CAMERAS,
    STATE_NO_DETECTION,
    ATTR_CAMERA,
    ATTR_LAST_UPDATED,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the FriGem sensors."""
    cameras = config_entry.data.get(CONF_CAMERAS, [])
    _LOGGER.debug("[SENSOR] Setting up sensors for cameras: %s", cameras)
    
    entities = []
    for camera in cameras:
        _LOGGER.debug("[SENSOR] Creating sensor for camera: %s", camera)
        entities.append(FrigateGeminiSensor(hass, config_entry, camera))

    if entities:
        async_add_entities(entities)
        _LOGGER.debug("[SENSOR] Added %d sensors", len(entities))
    else:
        _LOGGER.warning("[SENSOR] No cameras configured, no sensors added")


class FrigateGeminiSensor(SensorEntity):
    """FriGem Sensor class."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, camera: str
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self.config_entry = config_entry
        self.camera = camera
        
        # Set unique ID
        self._attr_unique_id = f"frigem_{camera}"
        
        # Set entity ID
        self.entity_id = f"sensor.frigem_{camera}"
        
        # Set name and device info
        self._attr_name = f"FriGem {camera}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"frigem_{camera}")},
            name=f"FriGem {camera}",
            manufacturer="Frigate Gemini",
            model="Video Analysis Sensor",
            sw_version="1.0.0",
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        state = self.hass.states.get(self.entity_id)
        if state is None:
            return STATE_NO_DETECTION
        return state.state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        state = self.hass.states.get(self.entity_id)
        if state is None:
            return {
                ATTR_CAMERA: self.camera,
                ATTR_LAST_UPDATED: datetime.utcnow().isoformat(),
            }
        return dict(state.attributes)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("[SENSOR] Added sensor for camera %s with ID: %s", self.camera, self.entity_id)
        # Initialize with no detection state
        self.hass.states.async_set(
            self.entity_id,
            STATE_NO_DETECTION,
            {
                ATTR_CAMERA: self.camera,
                ATTR_LAST_UPDATED: datetime.utcnow().isoformat(),
            },
        )
