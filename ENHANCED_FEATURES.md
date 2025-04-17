# Enhanced AI Meeting Assistant Features

This document describes the new features added to the AI Meeting Assistant and how to use them.

## New Features

### 1. Real-time Speech Recognition

The assistant now includes real-time speech recognition to transcribe meeting conversations as they happen. This feature:

- Works offline using CMU Sphinx (no API key required)
- Can optionally use Google Cloud Speech-to-Text for better accuracy (requires API key)
- Adds transcribed text to the meeting transcript in real-time
- Processes audio chunks to detect speech

### 2. Command Recognition

The assistant can now recognize and respond to commands during meetings. Commands can be given by speaking or typing in the chat:

```
Augment [command]
```

Available commands:
- `help`: Show available commands
- `summarize`: Generate a summary of the meeting so far
- `take notes`: Confirm that the assistant is taking notes
- `list participants`: Show who's in the meeting
- `status`: Show the assistant's current status
- `mute/unmute`: Control the assistant's microphone
- `record/stop recording`: Control audio recording
- `transcribe/stop transcribing`: Control transcription
- `leave`: Make the assistant leave the meeting

### 3. Meeting Summarization

The assistant now generates summaries of meetings automatically when leaving a meeting. This feature:

- Works offline with a basic summarization algorithm
- Can use OpenAI for better summaries (requires API key)
- Includes action items and key decisions
- References important timestamps
- Saves summaries to the `recordings` folder

### 4. Enhanced Audio Recording

The audio recording functionality has been improved:

- Better audio quality with configurable parameters
- Integration with speech recognition
- Automatic saving of recordings
- Volume detection to identify when someone is speaking

### 5. Improved UI Interaction

The assistant now has more robust UI interaction with Google Meet:

- Better detection of UI elements
- Multiple fallback strategies for clicking buttons
- JavaScript execution for difficult-to-click elements
- More reliable joining and leaving of meetings

## How to Use the Enhanced Features

### Testing the Enhanced Bot

Use the new test script to try out the enhanced features:

```
python test_enhanced_bot.py --meeting-url "your-meeting-url"
```

Options:
- `--headless`: Run in headless mode (no visible browser window)
- `--no-transcribe`: Disable real-time transcription

### Configuration

The enhanced features can be configured in `config.yaml`:

```yaml
# Google Meet Configuration
google_meet:
  # ... existing settings ...
  record_audio: true
  auto_transcribe: true
  send_greeting: true
  enable_captions: true
  # Speech recognition settings
  speech_recognition:
    use_google: false  # Set to true to use Google Cloud Speech-to-Text
    energy_threshold: 300
    dynamic_energy_threshold: true

# Agent Configuration
agent:
  name: "Augment"
  trigger_word: "Augment"
  greeting_message: "Hello! I'm the AI Meeting Assistant..."

# OpenAI Configuration
openai:
  api_key: ""  # Add your OpenAI API key for better summarization

# Summarization Configuration
summarization:
  generate_action_items: true
  include_timestamps: true
  summary_length: "medium"  # "short", "medium", "long"
```

### Output Files

All output files are saved in the `recordings` folder:

- `meeting_[timestamp].wav`: Audio recording of the meeting
- `transcript_[timestamp].txt`: Transcript of the meeting
- `summary_[timestamp].txt`: Summary of the meeting

## Installation of New Dependencies

To install the new dependencies required for the enhanced features:

```
python install_requirements.py
```

This will install:
- `pyaudio`: For audio recording
- `numpy`: For audio processing
- `wave`: For saving audio files
- `SpeechRecognition`: For speech recognition
- `pocketsphinx`: For offline speech recognition
- `openai`: For summarization
- `requests`: For HTTP requests
- `python-dotenv`: For environment variables

## Troubleshooting

### Speech Recognition Issues

- **No transcription**: Make sure `pocketsphinx` is installed correctly
- **Poor transcription quality**: Consider using Google Cloud Speech-to-Text for better accuracy
- **High CPU usage**: Adjust the `energy_threshold` in the configuration

### Command Recognition Issues

- **Commands not recognized**: Make sure the trigger word is set correctly in `config.yaml`
- **Wrong command execution**: Check the command patterns in `command_recognition.py`

### Audio Recording Issues

- **No audio**: Check your system's audio settings and make sure PyAudio is installed correctly
- **Poor audio quality**: Adjust the audio parameters in `audio_handler.py`

### Meeting Summarization Issues

- **Basic summaries**: Add your OpenAI API key to `config.yaml` for better summaries
- **Missing action items**: Make sure `generate_action_items` is set to `true` in `config.yaml`
