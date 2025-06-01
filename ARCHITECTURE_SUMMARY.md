# Project Architecture Summary

This document outlines the architecture of the LiveKit Voice Pipeline project, detailing its main components, their roles, and the communication flow between them.

## Main Components

The project is comprised of three primary components:

1.  **Frontend:** A React-based web application that serves as the user interface.
2.  **Agent (LiveKit Voice Pipeline Agent):** Handles the core voice processing logic.
3.  **Audio Server (Flask Backend):** A backend server responsible for validating and processing text based on estimated audio length.

## Component Roles

### 1. Frontend
   - Provides the user interface for interaction (e.g., speaking into a microphone).
   - Sends user's audio input to the LiveKit Agent.
   - Receives processed audio output from the LiveKit Agent and plays it back to the user.

### 2. Agent (LiveKit Voice Pipeline Agent)
   - Receives audio from the Frontend.
   - Performs Speech-to-Text (STT) conversion on the received audio.
   - Estimates the length of the audio that would be generated from the transcribed text.
   - Communicates with the Audio Server to validate and potentially trim the text based on its estimated audio length.
   - Sends the (potentially modified) text to a Text-to-Speech (TTS) engine.
   - Receives the generated audio from the TTS engine.
   - Sends the final audio back to the Frontend for playback.

### 3. Audio Server (Flask Backend)
   - Exposes an API endpoint (`/validate_audio_length`).
   - Receives text and its estimated audio length from the LiveKit Agent.
   - Validates if the estimated audio length exceeds a predefined maximum (e.g., 60 seconds).
   - If the length exceeds the maximum, it trims the text to fit within the limit.
   - Returns the original or trimmed text to the LiveKit Agent.
   - Also provides a `/health` endpoint for basic health checks.

## Communication Flow

The interaction between the components follows these steps:

1.  **User Interaction:** The user speaks into the microphone via the Frontend UI.
2.  **UI to LiveKit:** The Frontend sends the captured audio to the LiveKit Voice Pipeline Agent.
3.  **LiveKit STT & Estimation:** The LiveKit Agent performs STT on the audio to get text. It then estimates the potential audio length of this text.
4.  **LiveKit to Flask Server:** The Agent sends a POST request to the Audio Server's `/validate_audio_length` endpoint, including the text and its estimated length.
5.  **Flask Server Processing:**
    *   If the `estimated_length` is greater than the `max_length` (e.g., 60 seconds), the Flask server trims the text.
    *   Otherwise, it returns the original text.
6.  **Flask Server to LiveKit:** The Audio Server sends the processed (original or trimmed) text back to the LiveKit Agent.
7.  **LiveKit to TTS:** The LiveKit Agent sends this text to the TTS engine.
8.  **TTS Generation:** The TTS engine generates the audio.
9.  **LiveKit to UI:** The LiveKit Agent sends the generated audio back to the Frontend.
10. **UI Playback:** The Frontend plays the audio for the user.
