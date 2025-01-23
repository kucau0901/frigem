# Frigem
[![hacs_badge](https://img.shields.io/badge/HACS-Integration-41BDF5.svg)](https://github.com/hacs/integration)
![GitHub all releases](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=Download%20Count&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.frigate_gemini.total)
![GitHub manifest version (path)](https://img.shields.io/github/manifest-json/v/kucau0901/frigem?filename=custom_components%2Ffrigate_gemini%2Fmanifest.json)

Frigem is a Home Assistant custom component that integrates Frigate NVR with Google's Gemini 2.0 AI model to provide intelligent video analysis.

## Features
- Automatically analyzes Frigate event videos using Gemini 2.0
- Configurable cameras and custom prompts
- Real-time event processing through MQTT
- Easy setup through Home Assistant UI

## Requirements
- Home Assistant 2023.8.0 or newer
- Frigate NVR
- Google Cloud API key for Gemini access

## Support
- [Documentation](https://github.com/kucau0901/frigem)
- [Issues](https://github.com/kucau0901/frigem/issues)
