# Frigate Gemini - FriGem
[![hacs_badge](https://img.shields.io/badge/HACS-Integration-41BDF5.svg)](https://github.com/hacs/integration)
![GitHub all releases](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=Download%20Count&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.frigate_gemini.total)
![GitHub manifest version (path)](https://img.shields.io/github/manifest-json/v/kucau0901/frigem?filename=custom_components%2Ffrigate_gemini%2Fmanifest.json)

A Home Assistant custom component that enhances your Frigate NVR experience with Google's Gemini 2.0 AI model. This integration analyzes video clips from Frigate events and provides natural language descriptions of what's happening in the scene.

## Features

- 🎥 Automatic video clip analysis from Frigate events
- 🤖 Powered by Google's Gemini 2.0 AI model
- 📝 Customizable analysis prompts per camera
- 🔔 Real-time event processing via MQTT
- 🎯 Single camera focus for accurate analysis

## Installation

### HACS Installation (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kucau0901&repository=frigem&category=integration)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Add this repository as a custom repository in HACS:
   - Click on HACS in the sidebar
   - Click on Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add `https://github.com/kucau0901/frigem` as a custom repository
   - Select "Integration" as the category
3. Click Install
4. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/frigate_gemini` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### Prerequisites

1. A working [Frigate NVR](https://frigate.video/) installation. Minimum version 0.9.1
2. A Google API key with access to Gemini 2.0
3. MQTT broker configured in Home Assistant

### Setup Process

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Frigate Gemini"
4. Fill in the required information:
   - Gemini API Key
   - Frigate URL (e.g., http://frigate:5000)
   - MQTT Topic (default: frigate/events)
5. Select a camera to monitor
6. Configure the analysis prompt

### Prompt Configuration

Each camera can have its own custom prompt for video analysis. The prompt supports the `{label}` placeholder, which will be replaced with the detected object type (e.g., person, car, dog).

Example prompts:
- `"What is the {label} doing in the video? Describe their actions and behavior."`
- `"Focus on the {label}'s movement patterns and any interactions with the environment."`
- `"Analyze the {label}'s appearance, actions, and any notable events in the scene."`

You can update the prompt at any time through the integration's options in the Home Assistant UI.

## Usage

Once configured, the integration will:
1. Listen for Frigate event notifications on the configured MQTT topic
2. Download the event video clip
3. Send the clip to Gemini 2.0 for analysis with your custom prompt
4. Create a sensor with the analysis result

The sensor entity will be named `sensor.frigem_[camera_name]` and will contain:
- State: Latest analysis result
- Attributes:
  - Camera name
  - Event timestamp
  - Detected label
  - Custom prompt used

Head over to our [WIKI](https://github.com/kucau0901/frigem/wiki) for more.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- Report issues on [GitHub](https://github.com/kucau0901/frigem/issues)
- Join discussions in the [Home Assistant Community](https://community.home-assistant.io/)
- Join [Home Assistant Malaysia](https://www.facebook.com/groups/homeassistantmalaysia)
