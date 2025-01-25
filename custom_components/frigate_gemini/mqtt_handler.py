"""MQTT Handler for Frigate events."""
from __future__ import annotations

import json
import logging
import os
import tempfile
import aiofiles
import aiohttp
import asyncio
from datetime import datetime
from typing import Any

from homeassistant.components.mqtt import async_subscribe
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import (
    ERROR_GEMINI_API,
    DEFAULT_PROMPT,
    STATE_DETECTION_FORMAT,
    ATTR_CAMERA,
    ATTR_EVENT_ID,
    ATTR_LABEL,
    ATTR_CONFIDENCE,
    ATTR_CONFIDENCE_RAW,
    ATTR_FULL_ANALYSIS,
    ATTR_LAST_UPDATED,
    ATTR_DETECTION_TIME,
)

from .gemini_handler import GeminiHandler

_LOGGER = logging.getLogger(__name__)

class MQTTHandler:
    """Handler for MQTT messages."""

    def __init__(
        self,
        hass: HomeAssistant,
        frigate_url: str,
        mqtt_topic: str,
        cameras: list[str],
        prompt: str,
        gemini_handler: GeminiHandler,
    ) -> None:
        """Initialize the MQTT handler."""
        self.hass = hass
        # Ensure URL ends with correct port and no trailing slash
        self.frigate_url = frigate_url.rstrip("/")
        if not ":5000" in self.frigate_url:
            self.frigate_url = f"{self.frigate_url}:5000"
        self.mqtt_topic = mqtt_topic
        self.cameras = cameras
        self.prompt = prompt
        self.gemini_handler = gemini_handler
        self._unsubscribe_events = None
        self._temp_dir = tempfile.mkdtemp(prefix="frigem_")
        _LOGGER.debug("[MQTT] Created temporary directory: %s", self._temp_dir)

    async def async_setup(self) -> None:
        """Set up the MQTT handler."""
        _LOGGER.debug("[MQTT] Setting up MQTT handler with topic: %s", self.mqtt_topic)
        
        # Subscribe to MQTT events
        self._unsubscribe_events = await async_subscribe(
            self.hass,
            self.mqtt_topic,
            self._handle_event,
        )
        _LOGGER.debug("[MQTT] Successfully subscribed to MQTT topic")

    async def async_unload(self) -> None:
        """Unload the MQTT handler."""
        if self._unsubscribe_events:
            self._unsubscribe_events()
            self._unsubscribe_events = None
            _LOGGER.debug("[MQTT] Unsubscribed from MQTT topic")
            
        # Clean up temporary directory
        if os.path.exists(self._temp_dir):
            try:
                # Run blocking operations in executor
                def cleanup_temp():
                    for file in os.listdir(self._temp_dir):
                        file_path = os.path.join(self._temp_dir, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    os.rmdir(self._temp_dir)
                
                await self.hass.async_add_executor_job(cleanup_temp)
                _LOGGER.debug("[MQTT] Cleaned up temporary directory")
            except Exception as err:
                _LOGGER.error("[MQTT] Error cleaning up temporary directory: %s", str(err))

    async def _download_video(self, video_url: str) -> str | None:
        """Download video from URL to temporary file."""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Create a temporary file path
                temp_path = os.path.join(self._temp_dir, f"{hash(video_url)}.mp4")
                
                _LOGGER.debug("[MQTT] Downloading video from %s to %s (attempt %d/%d)", 
                            video_url, temp_path, attempt + 1, max_retries)
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(video_url, timeout=30) as response:
                        if response.status == 200:
                            # Use aiofiles for non-blocking file operations
                            async with aiofiles.open(temp_path, 'wb') as f:
                                await f.write(await response.read())
                            _LOGGER.debug("[MQTT] Successfully downloaded video to %s", temp_path)
                            return temp_path
                        elif response.status == 404:
                            _LOGGER.error(
                                "[MQTT] Video not found (404). URL: %s",
                                video_url
                            )
                            return None  # Don't retry on 404
                        elif response.status == 500:
                            error_content = await response.text()
                            _LOGGER.warning(
                                "[MQTT] Server error (500) on attempt %d. URL: %s. Error: %s",
                                attempt + 1,
                                video_url,
                                error_content
                            )
                        else:
                            error_content = await response.text()
                            _LOGGER.error(
                                "[MQTT] Failed to download video, status: %d, URL: %s, Error: %s",
                                response.status,
                                video_url,
                                error_content
                            )
                
                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                
            except asyncio.TimeoutError:
                _LOGGER.warning(
                    "[MQTT] Timeout downloading video on attempt %d. URL: %s",
                    attempt + 1,
                    video_url
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    
            except Exception as err:
                _LOGGER.error(
                    "[MQTT] Error downloading video on attempt %d: %s. URL: %s",
                    attempt + 1,
                    str(err),
                    video_url
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
        
        _LOGGER.error(
            "[MQTT] Failed to download video after %d attempts. URL: %s",
            max_retries,
            video_url
        )
        return None

    async def _handle_event(self, message) -> None:
        """Handle an MQTT message."""
        try:
            payload = json.loads(message.payload)
            
            # Check if this is an end event
            if not payload.get("type") == "end":
                _LOGGER.debug("[frigate_gemini] Ignoring non-end event")
                return
                
            # Log full payload for debugging
            _LOGGER.debug("[frigate_gemini] Received end event payload: %s", payload)
            
            camera = payload.get("after", {}).get("camera")
            
            # Check if this is a camera we're monitoring
            if camera not in self.cameras:
                _LOGGER.debug("[frigate_gemini] Ignoring event for non-monitored camera: %s", camera)
                return
                
            # Check if analysis is enabled for this camera
            switch_entity_id = f"switch.frigem_analysis_{camera}"
            switch_state = self.hass.states.get(switch_entity_id)
            
            if not switch_state or switch_state.state == "off":
                _LOGGER.debug("[frigate_gemini] Analysis disabled for camera %s, skipping processing", camera)
                return
            
            # Get event details
            event_id = payload.get("after", {}).get("id")
            label = payload.get("after", {}).get("label")
            confidence = payload.get("after", {}).get("top_score", 0)
            
            if not event_id or not label:
                _LOGGER.debug("[frigate_gemini] Missing event_id or label for camera %s", camera)
                return
                
            _LOGGER.debug(
                "[frigate_gemini] Processing end event for camera %s (event_id: %s, label: %s, confidence: %.2f)",
                camera,
                event_id,
                label,
                confidence
            )

            # Construct the video URL using Frigate HTTP API
            video_url = f"{self.frigate_url}/api/events/{event_id}/clip.mp4"
            _LOGGER.debug("[frigate_gemini] Constructed video URL: %s", video_url)
            _LOGGER.debug("[frigate_gemini] Frigate base URL: %s", self.frigate_url)
            _LOGGER.debug("[frigate_gemini] Event ID: %s", event_id)

            # Download video
            temp_path = await self._download_video(video_url)
            if not temp_path:
                _LOGGER.error("[frigate_gemini] Failed to download video from %s", video_url)
                return

            try:
                analysis = await self.gemini_handler.analyze_video(
                    video_path=temp_path,
                    prompt=self.prompt,
                    label=label
                )
                
                _LOGGER.info("[frigate_gemini] Successfully analyzed video for camera %s", camera)
                _LOGGER.debug("[frigate_gemini] Analysis result: %s", analysis)

                # Get event end time in local timezone
                event_time = dt_util.as_local(
                    dt_util.utc_from_timestamp(
                        payload.get("after", {}).get("end_time", 0)
                    )
                )
                formatted_time = event_time.strftime("%I:%M:%S %p")  # e.g., "02:30:45 PM"

                # Update the sensor state
                sensor_entity_id = f"sensor.frigem_{camera}"
                self.hass.states.async_set(
                    sensor_entity_id,
                    f"{label} detected at {formatted_time} ({confidence:.1%} confidence)",
                    {
                        ATTR_CAMERA: camera,
                        ATTR_EVENT_ID: event_id,
                        ATTR_LABEL: label,
                        ATTR_CONFIDENCE: f"{confidence:.1%}",
                        ATTR_CONFIDENCE_RAW: confidence,
                        ATTR_FULL_ANALYSIS: analysis,
                        ATTR_LAST_UPDATED: dt_util.now().isoformat(),
                        ATTR_DETECTION_TIME: event_time.isoformat(),
                    },
                )

                # Fire event for automations
                self.hass.bus.async_fire(
                    "frigate_gemini_analysis_complete",
                    {
                        "camera": camera,
                        "event_id": event_id,
                        "label": label,
                        "confidence": f"{confidence:.1%}",
                        "confidence_raw": confidence,
                        "analysis": analysis,
                        "detection_time": event_time.isoformat(),
                    },
                )
                
                _LOGGER.debug("[frigate_gemini] Updated sensor state for camera %s: %s", camera, f"{label} detected at {formatted_time} ({confidence:.1%} confidence)")
                _LOGGER.debug("[frigate_gemini] Fired analysis complete event for camera %s", camera)
                
            except Exception as err:
                _LOGGER.error(
                    "[frigate_gemini] Error analyzing video for camera %s: %s",
                    camera,
                    str(err),
                )
            finally:
                # Clean up temporary file
                try:
                    # Run blocking operations in executor
                    await self.hass.async_add_executor_job(os.remove, temp_path)
                    _LOGGER.debug("[MQTT] Cleaned up temporary file: %s", temp_path)
                except Exception as err:
                    _LOGGER.error("[MQTT] Error cleaning up temporary file: %s", str(err))
                
        except json.JSONDecodeError as err:
            _LOGGER.error("[frigate_gemini] Error decoding MQTT message: %s", str(err))
        except Exception as err:
            _LOGGER.error("[frigate_gemini] Error handling MQTT message: %s", str(err))

