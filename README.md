PGAI Test Bot (Patient Simulator)

A small voice-bot project used to simulate patient calls and test conversational healthcare agent flows using Twilio, OpenAI Whisper/ChatGPT, and ElevenLabs TTS.

## Features
- Simulates patient voice calls
- Records and transcribes audio using Whisper
- Generates conversational responses using ChatGPT
- Produces TTS responses using ElevenLabs

## Prerequisites
- Python 3.10 or newer
- Virtual environment tool (venv, pipenv, or similar)
- Twilio account and phone number (for real call testing)
- OpenAI API key (for Whisper and ChatGPT)
- ElevenLabs API key (for TTS)
- ngrok (recommended for local webhook testing)

## Installation

1. Clone the repository and enter the folder:

```bash
git clone https://github.com/npatel0924/PGAI-Test-Bot.git
cd "PGAI Test Bot"
```

2. Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

3. Create a `.env` file (or set environment variables) with the required keys:

- `OPENAI_API_KEY`
- `ELEVENLABS_API_KEY`
- `TWILIO_ACCOUNT_SID` (optional for Twilio integration)
- `TWILIO_AUTH_TOKEN` (optional)

Example `.env` (do not commit this file):

```
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=eleven_...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=your_token
```

## Running the bot

There are two primary entry points in this project:

- `run.py` — starts the application for local development
- `app/webhook_server.py` — contains the webhook server that Twilio or other services call

Quick local run (recommended with ngrok for external webhook testing):

```bash
python run.py
# In another terminal, expose your local server to the public internet (example):
ngrok http 8000
```

Point your Twilio webhook at the ngrok URL (e.g., `https://<id>.ngrok.io/twilio-webhook`) so inbound calls reach `app/webhook_server.py`.

## Project structure

- `run.py` — app launcher used in development
- `app/`
  - `bot.py` — main bot logic & orchestration
  - `webhook_server.py` — Flask/FastAPI webhook endpoints (Twilio callbacks)
  - `__init__.py`
  - `static/`, `audio/` — assets and temporary audio
- `scenarios/` — predefined patient scenarios used to drive conversations
- `services/` — wrappers for external services
  - `llm_service.py` — ChatGPT integration
  - `transcribe_service.py` — Whisper integration
  - `tts_service.py` — ElevenLabs TTS integration
- `tests/` — simple test runner and helpers
- `transcripts/` — saved transcripts from runs

## Running tests

Run the provided simple test runner:

```bash
python -m tests.test_runner
```

Note: tests in this repo are lightweight and designed to exercise components rather than full external integrations.

## Development notes
- Use ngrok for Twilio webhooks during development.
- Keep API keys out of source control and use environment variables.
- Audio files are stored under `app/static/audio/` during runtime; clean up as needed.

## Troubleshooting
- If transcription fails, confirm `OPENAI_API_KEY` is set and has Whisper access.
- If TTS fails, confirm `ELEVENLABS_API_KEY` and check service limits.
- If Twilio webhooks don't arrive, verify your ngrok URL and webhook configuration.

## Contributing
- Open an issue or pull request with a clear description of the change.
- Include tests for non-trivial logic changes.
