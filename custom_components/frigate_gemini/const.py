"""Constants for the FriGem integration."""

DOMAIN = "frigate_gemini"

# Configuration
CONF_API_KEY = "api_key"
CONF_FRIGATE_URL = "frigate_url"
CONF_MQTT_TOPIC = "mqtt_topic"
CONF_CAMERAS = "cameras"
CONF_PROMPT = "prompt"

# Defaults
DEFAULT_MQTT_TOPIC = "frigate/events"
DEFAULT_PROMPT = "Provide a summary of the events in the video. Focus more on the {label}."

# Attributes
ATTR_CAMERA = "camera"
ATTR_LABEL = "label"
ATTR_FULL_ANALYSIS = "full_analysis"
ATTR_PROMPT = "prompt"
ATTR_EVENT_ID = "event_id"
ATTR_CONFIDENCE = "confidence"
ATTR_CONFIDENCE_RAW = "confidence_raw"
ATTR_DETECTION_TIME = "detection_time"
ATTR_LAST_UPDATED = "last_updated"

# Sensor States
STATE_NO_DETECTION = "No detection"
STATE_DETECTION_FORMAT = "{label} detected at {time} ({confidence}% confidence)"

# Gemini API
MODEL_ID = "gemini-2.0-flash-exp"  # Model for video analysis

# Frigate API
FRIGATE_HOST = "localhost:5000"  # Frigate runs on port 5000
FRIGATE_CLIP_URL = "http://{host}/api/events/{event_id}/clip.mp4"

# Services
SERVICE_ANALYZE_VIDEO = "analyze_video"

# Error messages
ERROR_GEMINI_API = "Error communicating with Gemini API"
ERROR_INVALID_PATH = "Invalid file path"
ERROR_INVALID_API_KEY = "Invalid API key. Please check your API key and try again."
ERROR_API_QUOTA = "API quota exceeded. Please try again later."
ERROR_FILE_UPLOAD = "Failed to upload video file"
ERROR_FILE_PROCESSING = "Error processing video file"
