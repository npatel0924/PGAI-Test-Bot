# PGAI Test Bot

A voice-based patient simulator for testing conversational healthcare agents. It places or receives phone calls, transcribes the live audio, generates patient-style responses with an LLM, and speaks them back over the line — letting you exercise call-handling agents end-to-end against scripted clinical scenarios.

## How it works

1. A call connects through **Twilio**, which forwards audio to a webhook server.
2. Caller audio is transcribed in near real time using **OpenAI Whisper**.
3. The transcript and the active scenario are passed to **ChatGPT**, which generates the simulated patient's reply.
4. The reply is synthesized to speech with **ElevenLabs** and streamed back to the caller.

## Features

- Drives realistic patient calls from predefined scenarios in `scenarios/`
- Whisper-based speech-to-text
- ChatGPT-generated, scenario-aware responses
- Natural-sounding ElevenLabs TTS
- Saves transcripts of every run for review

## Requirements

- Python 3.10+
- A virtual environment tool (`venv`, `pipenv`, etc.)
- API keys for OpenAI and ElevenLabs
- A Twilio account and number (for live call testing)
- ngrok (recommended, for exposing local webhooks to Twilio)

## Setup

Clone and install:

```bash
git clone https://github.com/npatel0924/PGAI-Test-Bot.git
cd PGAI-Test-Bot

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS / Linux

pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=eleven_...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=your_token
```

Do not commit this file.

## Running

Start the app:

```bash
python run.py
```

In a second terminal, expose the webhook server publicly:

```bash
ngrok http 8000
```

Then point your Twilio number's voice webhook at the ngrok URL, e.g.:

```
https://<your-id>.ngrok.io/twilio-webhook
```

Inbound calls will be routed into `app/webhook_server.py`.

## Project structure

```
PGAI-Test-Bot/
├── run.py                    # Dev entry point
├── requirements.txt
├── app/
│   ├── bot.py                # Core bot orchestration
│   ├── webhook_server.py     # Twilio webhook endpoints
│   └── static/audio/         # Runtime audio files
├── scenarios/                # Patient scenario definitions
├── services/
│   ├── llm_service.py        # ChatGPT wrapper
│   ├── transcribe_service.py # Whisper wrapper
│   └── tts_service.py        # ElevenLabs wrapper
├── tests/                    # Lightweight component tests
└── transcripts/              # Saved call transcripts
```

## Testing

```bash
python -m tests.test_runner
```

Tests in this repo are designed to exercise individual components rather than full external integrations, so they don't hit live APIs.

## Troubleshooting

- **Transcription failing** — confirm `OPENAI_API_KEY` is set and has Whisper access.
- **TTS failing** — confirm `ELEVENLABS_API_KEY` and check your account's character limits.
- **Webhooks not arriving** — verify the ngrok URL in your Twilio console matches the running tunnel.

## Development notes

- Keep API keys out of source control; use environment variables.
- Audio under `app/static/audio/` accumulates during runs — clean it up periodically.
- Use ngrok (or a similar tunnel) for local Twilio webhook testing.

## Contributing

Issues and pull requests are welcome. For non-trivial changes, please include tests and a clear description of what's changing and why.
