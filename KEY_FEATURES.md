# Key Features of the LiveKit Voice Assistant

This document highlights the core functionalities and notable features of the LiveKit Voice Assistant project.

## Core Functionalities

The voice assistant provides a comprehensive set of features for a conversational AI experience:

1.  **Voice Input:** Users can interact with the assistant using their voice through a web-based frontend.
2.  **Speech-to-Text (STT):** The system captures user audio and converts it into text using an STT engine (e.g., Deepgram).
3.  **Language Model (LLM) Interaction:** The transcribed text is processed by a large language model (e.g., Google Gemini) to generate intelligent and contextually relevant responses.
4.  **Text-to-Speech (TTS):** The LLM's text response is synthesized into natural-sounding speech using a TTS engine (e.g., Cartesia).
5.  **Voice Output:** The synthesized audio is streamed back to the user via the frontend, enabling a complete voice-based conversation.
6.  **LiveKit Integration:** Utilizes LiveKit's real-time audio and data transport capabilities to manage the voice pipeline and communication between the user and the agent.
7.  **Voice Activity Detection (VAD):** Employs VAD (e.g., Silero VAD) to detect when the user starts and stops speaking, improving the responsiveness and naturalness of the interaction.

## Unique Feature: Audio Length Validation and Text Trimming

A key and unique aspect of this project is the proactive management of TTS audio length:

*   **Pre-TTS Validation:** Before sending text to the TTS engine, the system estimates the potential duration of the resulting audio.
*   **Flask Backend for Validation:** A dedicated Flask server provides an endpoint (`/validate_audio_length`) that receives the text and its estimated audio length.
*   **Text Trimming Logic:** If the estimated audio length exceeds a configurable maximum (defaulting to 60 seconds), the Flask server intelligently trims the text. The trimming logic aims to preserve the core message by selecting a middle segment of the original text.
*   **Ensuring Brevity:** This mechanism prevents overly long TTS outputs, ensuring responses are concise and user-friendly, and potentially helping to manage TTS service costs.

## Other Notable Features

*   **Dynamic TTS Voice Selection:**
    *   The system can fetch available voices from the TTS provider (e.g., Cartesia).
    *   Users can select their preferred TTS voice through the UI.
    *   The LiveKit Agent updates the TTS engine with the selected voice, allowing for a personalized experience.
*   **Interactive Frontend:**
    *   A React-based UI provides controls for connecting/disconnecting, microphone management, and voice selection.
    *   Includes audio visualizations for both user input and agent output, enhancing the user experience.
*   **Configuration Management:** Utilizes environment variables and Pydantic settings for robust configuration of API keys, service URLs, and operational parameters.
*   **Dockerized Deployment:** All components (Frontend, Agent, Audio Server) are containerized using Docker, simplifying setup and deployment via Docker Compose.

This combination of core voice AI functionalities with the specialized audio length validation and dynamic voice selection makes the project a robust example of an advanced voice assistant.
