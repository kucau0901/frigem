# Frigate Gemini Integration - FriGem

A Home Assistant custom component that enhances your Frigate NVR experience with Google's Gemini 2.0 AI model. This integration analyzes video clips from Frigate events and provides natural language descriptions of what's happening in the scene.

## Features

- 🎥 Automatic video clip analysis from Frigate events
- 🤖 Powered by Google's Gemini 2.0 AI model
- 📝 Customizable analysis prompts per camera
- 🔔 Real-time event processing via MQTT
- 🎯 Single camera focus for accurate analysis

## Installation

### HACS Installation (Recommended)

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

## Troubleshooting

### Common Issues

1. **Cannot connect to Frigate**
   - Verify your Frigate URL is correct and accessible
   - Check if Frigate is running and responding

2. **No events being processed**
   - Verify MQTT topic matches Frigate's configuration
   - Check MQTT broker connection in Home Assistant
   - Ensure camera is selected in integration settings

3. **Invalid API Key**
   - Verify your Google API key has access to Gemini 2.0
   - Check for any spaces or special characters in the key

### Debug Logging

To enable debug logging, add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.frigate_gemini: debug
```

Then restart Home Assistant.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- Report issues on [GitHub](https://github.com/kucau0901/frigem/issues)
- Join discussions in the [Home Assistant Community](https://community.home-assistant.io/)

## Sensors

For each configured camera, the integration creates a sensor named `sensor.frigem_[camera_name]`. These sensors provide a way to view the current state and history of detections in the Home Assistant UI.

### Sensor State
The sensor's state reflects the latest detection in a human-readable format:
```
Detected [object] ([confidence]%) at [timestamp]
```

For example:
```
Detected person (95.6%) at 2025-01-21T10:16:33+08:00
```

### Sensor Attributes
Each sensor provides detailed information through its attributes:

```yaml
camera: "front_door"         # Name of the camera
last_updated: "2025-01-21T10:16:33+08:00"  # ISO format timestamp
event_id: "1234567890"       # Frigate event ID
label: "person"              # Detected object type
confidence: 0.96             # Detection confidence (0-1)
full_analysis: "..."         # Complete Gemini analysis text
```

### Using Sensor Data

The sensors are best used for:
- Displaying current state in the Home Assistant UI
- Creating history graphs and statistics
- Reference in template conditions
- Creating template sensors for specific data points

For real-time automations, always use the `frigate_gemini_analysis_complete` event as your trigger (see Automation Examples section below).

### Template Sensor Examples
If you want to track specific aspects of the detections, you can create template sensors:

```yaml
template:
  - sensor:
      - name: "Front Door Last Detection Time"
        state: >
          {{ state_attr('sensor.frigem_front_door', 'last_updated') }}
      - name: "Front Door Detection Confidence"
        state: >
          {{ (state_attr('sensor.frigem_front_door', 'confidence') * 100) | round(1) }}
        unit_of_measurement: "%"
```

## Switches

For each configured camera, the integration creates a switch named `switch.frigem_analysis_[camera_name]`. These switches allow you to control when Gemini analysis should be performed.

### Switch Functionality

- **ON**: Video clips from this camera will be analyzed by Gemini
- **OFF**: Video clips from this camera will be ignored (no Gemini analysis)

### Switch Entity Details

Each switch provides:
```yaml
switch.frigem_analysis_front_door:
  state: on/off
  icon: mdi:video-check (when on) / mdi:video-off (when off)
  attributes:
    friendly_name: "FriGem Analysis front_door"
    camera: "front_door"
```

### Using Switches

You can control the switches in several ways:

1. **Home Assistant UI**:
   - Find the switch entity in your dashboard
   - Click to toggle analysis on/off

2. **Service Calls**:
```yaml
# Turn off analysis
service: switch.turn_off
target:
  entity_id: switch.frigem_analysis_front_door

# Turn on analysis
service: switch.turn_on
target:
  entity_id: switch.frigem_analysis_front_door
```

3. **Automation Example**:
```yaml
# Disable analysis at night
automation:
  - alias: "Disable front door analysis at night"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.frigem_analysis_front_door

  - alias: "Enable front door analysis in morning"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.frigem_analysis_front_door
```

### Debug Logging

To enable detailed debug logging for the component, add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.frigate_gemini: debug
```

This will show detailed logs including:
- Switch state changes
- Event processing decisions
- Analysis start/completion
- Error details

Example debug log output:
```log
[frigate_gemini] Setting up switches for cameras: ['front_door', 'backyard']
[frigate_gemini] Initialized switch for camera front_door (enabled by default)
[frigate_gemini] Processing event for camera front_door (switch state: on)
[frigate_gemini] Starting analysis for camera front_door (event_id: 123456, label: person)
[frigate_gemini] Sending video to Gemini for analysis: http://frigate:5000/clips/123456.mp4
[frigate_gemini] Analysis complete for camera front_door: A person walked up to the door and...
[frigate_gemini] Updated sensor state for camera front_door
```

These logs are particularly useful for:
- Debugging issues with the component
- Verifying when analysis is being skipped
- Tracking the processing flow for each event
- Monitoring switch state changes

## Automation Examples

For real-time response to detections, always use the event trigger. The integration fires the `frigate_gemini_analysis_complete` event that you should use in your automations.

### Text-to-Speech Announcements

The integration fires a `frigate_gemini_analysis_complete` event that you can use with TTS services to announce detections. Here are some examples:

#### Basic Announcement
```yaml
automation:
  alias: "Announce Gemini Analysis"
  trigger:
    platform: event
    event_type: frigate_gemini_analysis_complete
  action:
    - service: tts.cloud_say  # Replace with your TTS service (e.g., tts.google_translate_say)
      data:
        entity_id: media_player.living_room_speaker  # Replace with your media player
        message: "{{ trigger.event.data.analysis }}"
```

#### Smart Announcement with Confidence Check
```yaml
automation:
  alias: "Smart Detection Announcement"
  trigger:
    platform: event
    event_type: frigate_gemini_analysis_complete
  condition:
    - condition: template
      value_template: "{{ trigger.event.data.confidence_raw > 0.8 }}"  # 80% confidence threshold
    - condition: time
      after: "08:00:00"
      before: "22:00:00"
  action:
    - service: tts.cloud_say
      data:
        entity_id: media_player.living_room_speaker
        message: >-
          {{ trigger.event.data.camera | replace("_", " ") }} camera: 
          {{ trigger.event.data.analysis }}
```

#### Person-Only Announcements
```yaml
automation:
  alias: "Announce Person Detection"
  trigger:
    platform: event
    event_type: frigate_gemini_analysis_complete
    event_data:
      label: person
  action:
    - service: tts.cloud_say
      data:
        entity_id: media_player.living_room_speaker
        message: >-
          Person detected at {{ trigger.event.data.camera | replace("_", " ") }} camera. 
          {{ trigger.event.data.analysis }}
```

#### Custom Message Format
```yaml
automation:
  alias: "Detailed Detection Announcement"
  trigger:
    platform: event
    event_type: frigate_gemini_analysis_complete
  variables:
    confidence_pct: "{{ (trigger.event.data.confidence_raw * 100) | round(1) }}"
  condition:
    - condition: template
      value_template: "{{ trigger.event.data.confidence_raw > 0.6 }}"
  action:
    - service: tts.cloud_say
      data:
        entity_id: media_player.living_room_speaker
        message: >-
          {% set camera = trigger.event.data.camera | replace("_", " ") %}
          {% if confidence_pct > 90 %}
            High confidence detection at {{ camera }} camera: 
          {% else %}
            Possible detection at {{ camera }} camera: 
          {% endif %}
          {{ trigger.event.data.analysis }}
```

### Available Event Data

The `frigate_gemini_analysis_complete` event provides these fields:
- `camera`: Camera name
- `event_id`: Frigate event ID
- `label`: Detected object type (e.g., person, car)
- `confidence`: Confidence as percentage string (e.g., "82.4%")
- `confidence_raw`: Raw confidence value (0.0 to 1.0)
- `analysis`: The full Gemini analysis text
- `detection_time`: Event detection time in ISO format

You can use any of these fields in your automation's message template.

### TTS Service Options

Common TTS services you can use:
- `tts.google_translate_say`: Free Google Translate TTS
- `tts.cloud_say`: Cloud TTS providers
- `tts.amazon_polly_say`: Amazon Polly TTS

Replace `tts.cloud_say` in the examples with your preferred TTS service.

### Event Details

The event contains all necessary data for automations:
```yaml
event_type: frigate_gemini_analysis_complete
data:
  camera: "front_door"        # Camera name
  label: "person"            # Detected object type
  event_id: "1234567890"     # Frigate event ID
  analysis: "Full analysis text..."  # Complete Gemini analysis
  confidence: 0.965          # Confidence score (0-1)
```

### Example Automations

1. **Real-time Person Detection Alert**
```yaml
automation:
  alias: "Alert on Person Detection"
  trigger:
    platform: event
    event_type: frigate_gemini_analysis_complete
  condition:
    - condition: template
      value_template: >
        {{ trigger.event.data.label == 'person' and 
           trigger.event.data.confidence > 0.90 }}
    # Optionally use sensor attributes in conditions
    - condition: template
      value_template: >
        {% set last_alert = states('input_datetime.last_person_alert') %}
        {% set minutes_since = ((now() - last_alert) | as_timestamp / 60) | int %}
        {{ minutes_since > 5 }}
  action:
    - service: notify.mobile_app
      data:
        title: "Person Detected"
        message: "{{ trigger.event.data.analysis }}"
    # Update last alert time
    - service: input_datetime.set_datetime
      target:
        entity_id: input_datetime.last_person_alert
      data:
        timestamp: "{{ now().timestamp() | int }}"
```

2. **Event Logging with Sensor Reference**
```yaml
automation:
  alias: "Log High Confidence Detections"
  trigger:
    platform: event
    event_type: frigate_gemini_analysis_complete
  condition:
    - condition: template
      value_template: "{{ trigger.event.data.confidence > 0.95 }}"
  action:
    - service: local_file.write
      data:
        path: "/config/frigate_analysis.log"
        append: true
        content: |
          Camera: {{ trigger.event.data.camera }}
          Time: {{ now().strftime('%Y-%m-%d %H:%M:%S') }}
          Event: {{ trigger.event.data.event_id }}
          Analysis: {{ trigger.event.data.analysis }}
          Current Sensor State: {{ states('sensor.frigem_' + trigger.event.data.camera) }}
          ---
```

3. **Night Time Security**
```yaml
automation:
  alias: "Night Time Detection"
  trigger:
    platform: event
    event_type: frigate_gemini_analysis_complete
  condition:
    - condition: time
      after: '22:00:00'
      before: '06:00:00'
    - condition: template
      value_template: "{{ trigger.event.data.confidence > 0.85 }}"
  action:
    - service: light.turn_on
      target:
        entity_id: light.outdoor_lights
    - service: notify.mobile_app
      data:
        title: "Night Time Activity"
        message: "{{ trigger.event.data.analysis }}"
        data:
          push:
            sound: 
              name: default
              critical: 1
              volume: 1.0
```

These automations demonstrate:
- Using events for real-time triggers
- Combining event data with sensor attributes in conditions
- Integration with other Home Assistant services
- Proper timing and state tracking
- Advanced notification options

