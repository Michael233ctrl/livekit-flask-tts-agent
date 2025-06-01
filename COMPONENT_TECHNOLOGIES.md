# Component Technologies and Complexity

This document details the technologies, complexity, and relative size of the main components in the LiveKit Voice Pipeline project.

## 1. Frontend

*   **Role:** Provides the user interface for voice interaction, sends audio to the LiveKit Agent, and plays back audio received from the Agent.
*   **Primary Technologies:**
    *   **Language:** TypeScript
    *   **Framework:** React, Next.js
    *   **Key Libraries:**
        *   `@livekit/components-react`: For LiveKit room connection and UI components.
        *   `livekit-client`: Core LiveKit client SDK.
        *   `tailwindcss`: For styling.
        *   `framer-motion`: For animations.
        *   `@radix-ui/react-dropdown-menu`, `@radix-ui/react-select`: UI components.
*   **Complexity Assessment:** **Moderate**
    *   Manages real-time audio input and output.
    *   Integrates with the LiveKit SDK for session management and media streams.
    *   Handles dynamic UI updates based on connection state, agent state, and user interactions.
    *   State management for UI elements like voice selection and visualizers.
*   **Relative Size:** **Medium**
    *   Based on the file structure (`ls frontend/`), there are numerous components (`src/components/`), hooks (`src/hooks/`), and pages (`src/pages/`).
    *   The main interaction logic in `src/components/Assistant.tsx` is around 300 lines, and `src/pages/index.tsx` is around 100 lines, indicating a non-trivial amount of UI and client-side logic.

## 2. Agent (LiveKit Voice Pipeline Agent)

*   **Role:** Handles the core voice processing pipeline: Speech-to-Text (STT), Language Model (LLM) interaction, Text-to-Speech (TTS), and communication with the Flask Audio Server for text validation.
*   **Primary Technologies:**
    *   **Language:** Python
    *   **Framework/SDK:** `livekit-agents` SDK
    *   **Key Libraries/Services:**
        *   `livekit-plugins-deepgram`: For Speech-to-Text (STT).
        *   `livekit-plugins-google`: For Language Model (LLM) interaction (specifically Gemini).
        *   `livekit-plugins-cartesia`: For Text-to-Speech (TTS).
        *   `livekit-plugins-silero`: For Voice Activity Detection (VAD).
        *   `requests`: For synchronous HTTP requests (used in prewarm to fetch Cartesia voices).
        *   `aiohttp`: For asynchronous HTTP requests (used in `before_tts_callback` to communicate with the Flask Audio Server).
        *   `python-dotenv`, `pydantic-settings`: For configuration management.
*   **Complexity Assessment:** **High**
    *   Orchestrates a multi-step voice processing pipeline (VAD -> STT -> LLM -> Pre-TTS Callback -> TTS).
    *   Manages real-time events from the LiveKit room (e.g., participant attribute changes for voice selection).
    *   Interacts with multiple external AI services (Deepgram, Google LLM, Cartesia).
    *   Implements custom callback logic (`before_tts_callback`) that involves asynchronous communication with the Audio Server for text validation and potential modification.
    *   Handles different states (user speaking, agent speaking, voice selection).
*   **Relative Size:** **Medium**
    *   `agent/main.py` (approx. 150 lines) contains the main agent logic.
    *   `agent/callbacks/before_tts.py` (approx. 100 lines) implements the audio length validation logic.
    *   `agent/config.py` (approx. 50 lines) manages settings.
    *   While the individual Python files are not excessively long, the overall system's functionality, reliance on multiple plugins, and the interaction flow contribute to its medium size.

## 3. Audio Server (Flask Backend)

*   **Role:** Provides an HTTP API endpoint (`/validate_audio_length`) to validate and trim text based on its estimated audio length, ensuring it doesn't exceed a predefined maximum.
*   **Primary Technologies:**
    *   **Language:** Python
    *   **Framework:** Flask
    *   **Key Libraries:**
        *   `Flask-CORS`: For Cross-Origin Resource Sharing.
*   **Complexity Assessment:** **Low to Moderate**
    *   Exposes a single primary API endpoint with well-defined request/response formats.
    *   The core logic involves text length calculation, ratio-based trimming, and attempting to adjust trim points to word boundaries.
    *   No external service integrations or complex state management.
*   **Relative Size:** **Small**
    *   The entire logic is contained within `audio_server/app.py` (approx. 100 lines).
    *   Minimal dependencies (`Flask`, `Flask-CORS`).
