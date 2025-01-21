"""Handle interactions with Google's Gemini API."""
from __future__ import annotations

import logging
import asyncio
import time
from typing import Any
from functools import partial
from concurrent.futures import ThreadPoolExecutor

from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

from .const import (
    DEFAULT_PROMPT,
    ERROR_GEMINI_API,
    MODEL_ID,
)

_LOGGER = logging.getLogger(__name__)

# Constants for retry mechanism
MAX_RETRIES = 5
RETRY_DELAY = 10  # seconds
MAX_PROCESSING_TIME = 120  # seconds

# Gemini File States
FILE_STATE_PROCESSING = "PROCESSING"
FILE_STATE_ACTIVE = "ACTIVE"
FILE_STATE_FAILED = "FAILED"


class GeminiAPIError(Exception):
    """Gemini API Error."""


class GeminiHandler:
    """Handle interactions with Gemini API."""

    def __init__(self, api_key: str) -> None:
        """Initialize the handler."""
        if not api_key or len(api_key.strip()) < 10:
            raise ValueError("Invalid API key format")

        _LOGGER.debug("[GEMINI] Initializing Gemini handler with API key")
        try:
            self.client = genai.Client(api_key=api_key)
            self._executor = ThreadPoolExecutor(max_workers=2)
            _LOGGER.debug("[GEMINI] Successfully initialized Gemini")
        except Exception as err:
            _LOGGER.error("[GEMINI] Error initializing Gemini: %s", str(err))
            if "permission" in str(err).lower() or "unauthorized" in str(err).lower():
                raise ValueError(
                    "Invalid Gemini API key. Please check your API key and try again."
                ) from err
            raise

    async def _run_in_executor(self, func, *args, **kwargs):
        """Run blocking function in executor."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                self._executor, 
                partial(func, *args, **kwargs)
            )
        except Exception as err:
            error_msg = str(err).lower()
            if "permission" in error_msg or "unauthorized" in error_msg:
                _LOGGER.error("[GEMINI] API key error: %s", str(err))
                raise GeminiAPIError(
                    "Invalid API key or insufficient permissions"
                ) from err
            elif "quota" in error_msg or "rate limit" in error_msg:
                _LOGGER.error("[GEMINI] API quota exceeded: %s", str(err))
                raise GeminiAPIError(
                    "API quota exceeded. Please try again later."
                ) from err
            else:
                _LOGGER.error("[GEMINI] API error: %s", str(err))
                raise GeminiAPIError(str(err)) from err

    async def analyze_video(
        self, video_path: str, prompt: str | None, label: str
    ) -> str:
        """Analyze a video using Gemini."""
        try:
            _LOGGER.debug(
                "[GEMINI] Preparing to analyze video: %s with label: %s",
                video_path,
                label,
            )

            # Format the prompt
            if not prompt:
                _LOGGER.debug("[GEMINI] No custom prompt provided, using default")
                prompt = DEFAULT_PROMPT
            formatted_prompt = prompt.format(label=label)
            _LOGGER.debug("[GEMINI] Using prompt: %s", formatted_prompt)

            # Upload video file
            _LOGGER.debug("[GEMINI] Uploading video file")
            video_file = await self._run_in_executor(
                self.client.files.upload,
                path=video_path
            )
            _LOGGER.debug("[GEMINI] Video uploaded: %s", video_file.uri)

            # Wait for video processing
            while True:
                video_file = await self._run_in_executor(
                    self.client.files.get,
                    name=video_file.name
                )
                _LOGGER.debug("[GEMINI] File state: %s", video_file.state)

                if video_file.state == FILE_STATE_FAILED:
                    error_msg = "Video processing failed"
                    _LOGGER.error("[GEMINI] %s", error_msg)
                    raise GeminiAPIError(error_msg)
                elif video_file.state == FILE_STATE_ACTIVE:
                    _LOGGER.debug("[GEMINI] Video processing complete")
                    break
                elif video_file.state == FILE_STATE_PROCESSING:
                    _LOGGER.debug("[GEMINI] File still processing...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    _LOGGER.warning("[GEMINI] Unknown file state: %s", video_file.state)
                    await asyncio.sleep(RETRY_DELAY)

            # Generate content
            _LOGGER.debug("[GEMINI] Generating content with model: %s", MODEL_ID)
            response = await self._run_in_executor(
                self.client.models.generate_content,
                model=MODEL_ID,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_uri(
                                file_uri=video_file.uri,
                                mime_type=video_file.mime_type
                            )
                        ]
                    ),
                    formatted_prompt
                ]
            )

            if not response or not response.text:
                _LOGGER.error("[GEMINI] Empty response from Gemini API")
                raise GeminiAPIError("Empty response from Gemini API")

            _LOGGER.info("[GEMINI] Successfully analyzed video")
            _LOGGER.debug("[GEMINI] Full analysis result: %s", response.text)
            _LOGGER.debug("[GEMINI] Response metadata: %s", {
                "model": MODEL_ID,
                "prompt": formatted_prompt,
                "video_uri": video_file.uri,
                "mime_type": video_file.mime_type,
                "response_length": len(response.text) if response.text else 0
            })
            
            return response.text

        except Exception as err:
            _LOGGER.error("[GEMINI] Error analyzing video: %s", str(err))
            raise GeminiAPIError(f"Video analysis failed: {str(err)}")

    async def close(self):
        """Close the executor."""
        self._executor.shutdown(wait=True)
