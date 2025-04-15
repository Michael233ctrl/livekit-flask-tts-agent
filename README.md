# LiveKit Voice Pipeline with Audio Length Validation

## Project Description

This project implements a voice assistant using LiveKit's Voice Pipeline Agent. A key feature is the validation of the estimated length of generated audio before it is sent to the Text-to-Speech (TTS) engine. This validation is handled by a Flask backend server, which trims the text if the estimated audio length exceeds 60 seconds.

## Features

- LiveKit Voice Pipeline Agent integration.
- Audio length validation using a Flask backend.
- Text trimming for audio exceeding 60 seconds.
- Communication between LiveKit agent and Flask server.
- User interface for voice agent interaction.

## Architecture

### Components

1. **LiveKit Voice Pipeline Agent:** Handles voice input, sends text to the Flask server for validation, receives processed text, and sends text to the TTS engine.
2. **Flask Backend Server:** Provides the `/validate_audio_length` endpoint for text validation and trimming.
3. **User Interface:** A React-based web application for user interaction.

### Communication Flow

1. User interacts with the UI (speaks).
2. UI sends audio to LiveKit.
3. LiveKit agent receives the audio, performs STT, and obtains the text.
4. LiveKit agent estimates audio length and sends a POST request to the Flask server's `/validate_audio_length` endpoint with the length and text.
5. Flask server processes the request:
   - If length > 60s, trim the text and return it.
   - If length <= 60s, return the original text.
6. LiveKit agent receives the processed text from the Flask server.
7. LiveKit agent sends the text to the TTS engine.
8. TTS engine generates audio.
9. LiveKit agent sends the audio to the UI.
10. UI plays the audio to the user.

---

## Installation and Setup

### Prerequisites

- Python 3.11
- Node.js
- Docker
- An [ngrok](https://ngrok.com) account and authtoken

### 1. Clone the repository

```bash
git clone https://github.com/your-repo/your-project.git
cd your-project
```

### 2. Set up environment variables

- Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

- Fill in the required API keys and configuration in `.env.local`.

### 3. Start the application using Docker Compose

```bash
make build
```

This will build and start all the services using Docker Compose.

### 4. Access the application

- Frontend: [http://localhost:3000](http://localhost:3000)
- ngrok (if enabled): [http://localhost:4040](http://localhost:4040) — view public URL and inspect requests

---

## Makefile Commands

| Command         | Description                               |
|-----------------|-------------------------------------------|
| `make build`    | Build and start all services              |
| `make up`       | Start services in detached mode           |
| `make down`     | Stop and remove all running services      |
| `make restart`  | Restart all services                      |
| `make logs`     | View logs for all services                |
| `make prune`    | Remove all unused Docker containers       |

---

## Environment Configuration

The `.env.example` file provides a template for required environment variables:

```dotenv
# LiveKit agent configuration
LIVEKIT_URL=wss://<myproject>.livekit.cloud
LIVEKIT_API_KEY=<api-key>
LIVEKIT_API_SECRET=<api-secret>
OPENAI_API_KEY=<openai-api-key>
DEEPGRAM_API_KEY=<deepgram-api-key>
CARTESIA_API_KEY=<cartesia-api-key>
GOOGLE_API_KEY=

# Frontend public configuration
NEXT_PUBLIC_LIVEKIT_URL=wss://<myproject>.livekit.cloud

# Audio server configuration
AUDIO_SERVER_URL=http://audio_server:5000
MAX_AUDIO_LENGTH=60.0
DEFAULT_VOICE_WPM=150

# NGROK configuration
NGROK_AUTHTOKEN=
NGROK_URL=
```

---

## Code Structure

```
├── agent/            # LiveKit agent (main.py, Dockerfile)
├── audio_server/     # Flask server (app.py, requirements.txt, Dockerfile)
├── frontend/         # React frontend
├── ngrok/            # ngrok configuration (ngrok.yml)
├── docker-compose.yml
├── .env.example
└── Makefile
```
---

## Flask Server Endpoints

### `/health` (GET)

**Purpose:** Simple health check to confirm the server is running.

**Response:**
```json
{
  "status": "ok"
}
```

---

### `/validate_audio_length` (POST)

**Purpose:** Validates a block of text based on the estimated audio duration. If the estimated duration exceeds the maximum allowed time (default is 60 seconds), the text is trimmed to a middle segment that fits within the limit.

**Input:**

```json
{
  "text": "Your long input text here...",
  "estimated_length": 75.5,
  "max_length": 60.0  // optional, defaults to 60 if not provided
}
```

- `text`: The input string to be validated.
- `estimated_length`: Estimated duration in seconds for the input text.
- `max_length`: (Optional) Maximum allowed duration in seconds (default is 60).

**Successful Response (when trimming is NOT needed):**

```json
{
  "text": "Your original input text...",
  "modified": false,
  "estimated_duration": 55.0
}
```

**Successful Response (when trimming is applied):**

```json
{
  "text": "...trimmed middle segment of the text...",
  "modified": true,
  "original_length": 512,
  "trimmed_length": 260,
  "estimated_original_duration": 75.5,
  "estimated_new_duration": 60.0
}
```

**Error Responses:**

- Missing fields:
```json
{
  "error": "Missing required fields"
}
```

- Invalid types or values:
```json
{
  "error": "estimated_length must be a positive number"
}
```

- Server error:
```json
{
  "error": "Internal error message here"
}
```

---

## Text Trimming Logic

1. Split the input text into words.
2. Calculate the estimated audio duration.
3. If the estimated duration exceeds 60 seconds:
   - Trim the text to fit within the limit, centered around the middle of the text.
4. Return the processed (original or trimmed) text.

