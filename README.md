# AI Meeting Assistant

An AI assistant that joins Google Meet meetings, transcribes conversations, responds to questions, searches the web, and generates meeting summaries.

## Features

- **Google Meet Integration**: Joins meetings as a participant using headless browser automation
- **Real-time Transcription**: Transcribes meeting audio using OpenAI Whisper or Google STT
- **Voice Responses**: Responds to queries with synthesized speech
- **Web Search**: Searches the web to answer questions during meetings
- **Data Queries**: Retrieves information from company databases or APIs
- **Email Summaries**: Sends meeting summaries and action items via email
- **LangChain Integration**: Uses LangChain for agent orchestration and tool usage

## Architecture

The AI Meeting Assistant is built with a modular architecture:

- **Meeting Interface**: Handles Google Meet integration, browser automation, and audio routing
- **Audio Streaming**: Manages speech-to-text, text-to-speech, and audio processing
- **Agent Core**: Provides LLM integration, LangChain agent setup, and conversation memory
- **Tools**: Implements web search, email sending, and data querying capabilities
- **Summarizer**: Processes transcripts and generates meeting summaries
- **Utils**: Provides configuration, logging, and security utilities

## Requirements

- Python 3.8+
- Chrome browser
- PulseAudio (for Linux audio routing)
- OpenAI API key
- Google API credentials (for Gmail integration)
- AWS credentials (optional, for Amazon Polly TTS)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-meeting-assistant.git
   cd ai-meeting-assistant
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up configuration:
   - Copy `config.yaml` to `config.local.yaml`
   - Edit `config.local.yaml` to add your API keys and preferences
   - Or set environment variables (see Configuration section)

## Configuration

The assistant can be configured through the `config.yaml` file or environment variables:

- **API Keys**:
  - `OPENAI_API_KEY`: OpenAI API key
  - `GOOGLE_CLIENT_ID`: Google API client ID
  - `GOOGLE_CLIENT_SECRET`: Google API client secret
  - `AWS_ACCESS_KEY_ID`: AWS access key ID (for Amazon Polly)
  - `AWS_SECRET_ACCESS_KEY`: AWS secret access key

- **LLM Configuration**:
  - `LLM_MODEL`: OpenAI model to use (default: gpt-4)

## Usage

### Join a Meeting

```
python main.py --meeting-url "https://meet.google.com/abc-defg-hij"
```

### Join a Meeting and Send Summary

```
python main.py --meeting-url "https://meet.google.com/abc-defg-hij" --email "user@example.com"
```

### Use Custom Configuration

```
python main.py --meeting-url "https://meet.google.com/abc-defg-hij" --config "config.local.yaml"
```

## Interacting with the Assistant

During a meeting, you can interact with the assistant by saying its name followed by a query:

- "Augment, what's the weather today?"
- "Augment, search for the latest news about AI."
- "Augment, what was our revenue last quarter?"

## Development

### Project Structure

```
ai-meeting-assistant/
├── meeting_interface/       # Google Meet integration
│   ├── browser_automation.py
│   ├── audio_routing.py
│   └── meet_client.py
├── audio_streaming/         # Audio processing
│   ├── speech_to_text.py
│   ├── text_to_speech.py
│   └── audio_processor.py
├── agent_core/              # LLM and agent logic
│   ├── llm_manager.py
│   ├── agent.py
│   └── memory.py
├── tools/                   # Agent tools
│   ├── web_search.py
│   ├── email_sender.py
│   └── data_query.py
├── summarizer/              # Meeting summarization
│   ├── transcript_processor.py
│   └── summary_generator.py
├── utils/                   # Utilities
│   ├── config.py
│   ├── logging_utils.py
│   └── security.py
├── main.py                  # Entry point
├── config.yaml              # Configuration
└── requirements.txt         # Dependencies
```

### Running Tests

```
pytest
```

## Security and Privacy

The assistant includes several security and privacy features:

- **Transcript Encryption**: Encrypts meeting transcripts
- **PII Filtering**: Filters personally identifiable information from transcripts
- **Consent Management**: Tracks user consent for recording and processing
- **Data Retention**: Configurable data retention policies

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [LangChain](https://github.com/hwchase17/langchain) for agent orchestration
- [OpenAI](https://openai.com/) for LLM and Whisper API
- [Selenium](https://www.selenium.dev/) and [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) for browser automation
