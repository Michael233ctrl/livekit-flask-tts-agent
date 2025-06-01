# Conceptual Test Plan

This document outlines conceptual test cases for the `agent` and `audio_server` components, focusing on error handling and key functionalities.

## Agent Component (`agent/`)

### 1. `callbacks.utils.estimate_audio_length`

*   **Test Case 1.1: Zero WPM**
    *   **Setup:** Call `estimate_audio_length(text="some text", words_per_minute=0)`.
    *   **Assertions:**
        *   Returns `60.0`.
        *   Log warning: "words_per_minute is 0. Returning fallback duration...".
*   **Test Case 1.2: Non-numeric WPM (TypeError internally if not caught by Pydantic earlier)**
    *   **Setup:** (Assuming Pydantic or type hints don't prevent this) Call `estimate_audio_length(text="some text", words_per_minute="invalid")`.
    *   **Assertions:**
        *   Returns `60.0`.
        *   Log error: "Unexpected error during audio length calculation: ..." (TypeError).
*   **Test Case 1.3: ZeroDivisionError (if initial WPM check is bypassed)**
    *   **Setup:** (Requires modifying the function to allow WPM to be set to 0 after initial check, or mocking `settings.DEFAULT_VOICE_WPM` to 0 and calling with `words_per_minute=None`).
    *   **Assertions:**
        *   Returns `60.0`.
        *   Log warning: "ZeroDivisionError during audio length calculation...".

### 2. `main.prewarm` (Cartesia Voice Fetching)

*   **Test Case 2.1: Network Failure (e.g., `requests.exceptions.ConnectionError`)**
    *   **Setup:** Mock `requests.get` to raise `requests.exceptions.ConnectionError` for all 3 attempts.
    *   **Assertions:**
        *   `proc.userdata["cartesia_voices"]` is `[]`.
        *   Log: "Attempt 1/3 failed... ConnectionError..."
        *   Log: "Attempt 2/3 failed... ConnectionError..."
        *   Log: "Attempt 3/3 failed... ConnectionError..."
        *   Log error: "All attempts to fetch Cartesia voices failed...".
*   **Test Case 2.2: HTTP Error (e.g., 500 Server Error)**
    *   **Setup:** Mock `requests.get` to return a response with `status_code=500` for all 3 attempts.
    *   **Assertions:**
        *   `proc.userdata["cartesia_voices"]` is `[]`.
        *   Log: "Attempt 1/3 failed... HTTP 500"
        *   Log: "Attempt 2/3 failed... HTTP 500"
        *   Log: "Attempt 3/3 failed... HTTP 500"
        *   Log error: "All attempts to fetch Cartesia voices failed...".
*   **Test Case 2.3: Success on Retry**
    *   **Setup:** Mock `requests.get` to fail on the first attempt (e.g., raise `ConnectionError`) and succeed on the second attempt with `status_code=200` and valid JSON voice data.
    *   **Assertions:**
        *   Log: "Attempt 1/3 failed... ConnectionError..."
        *   Log: "Waiting ... seconds before next retry..."
        *   Log: "Attempt 2/3 ... Fetch Cartesia voices..."
        *   Log info: "Fetched X Cartesia voices successfully."
        *   `proc.userdata["cartesia_voices"]` contains the fetched voice data.

### 3. `main.entrypoint` (Plugin Initialization)

*   **Test Case 3.1: STT Initialization Failure**
    *   **Setup:** Mock `deepgram.STT()` to raise an Exception.
    *   **Assertions:**
        *   Log critical: "CRITICAL: Failed to initialize Deepgram STT: <error_message>".
        *   Agent continues to attempt to start (as per current implementation).
*   **Test Case 3.2: LLM Initialization Failure**
    *   **Setup:** Mock `google.LLM()` to raise an Exception.
    *   **Assertions:**
        *   Log critical: "CRITICAL: Failed to initialize Google LLM: <error_message>".
*   **Test Case 3.3: TTS Initialization Failure**
    *   **Setup:** Mock `cartesia.TTS()` to raise an Exception.
    *   **Assertions:**
        *   Log critical: "CRITICAL: Failed to initialize Cartesia TTS: <error_message>".

### 4. `main.entrypoint` (`agent.say()` calls)

*   **Test Case 4.1: `agent.say()` failure during voice change confirmation**
    *   **Setup:**
        *   Initialize agent successfully.
        *   Trigger `on_participant_attributes_changed` with a voice change.
        *   Mock the `agent.say()` call within this handler to raise an Exception.
    *   **Assertions:**
        *   Log warning: "agent.say() failed during voice change confirmation: <error_message>".
*   **Test Case 4.2: `agent.say()` failure for initial greeting**
    *   **Setup:** Mock the final `agent.say()` call in `entrypoint` to raise an Exception.
    *   **Assertions:**
        *   Log warning: "agent.say() failed for initial greeting: <error_message>".

### 5. `callbacks.before_tts._send_validation_request` (Audio Server Calls)

*   **Test Case 5.1: Network Failure (e.g., `aiohttp.ClientConnectionError`)**
    *   **Setup:** Mock `aiohttp.ClientSession().post()` to raise `aiohttp.ClientConnectionError` for all 3 attempts.
    *   **Input:** Some `validation_data`.
    *   **Assertions:**
        *   Returns `None`.
        *   Log: "Attempt 1/3 ... failed with HTTP error: ClientConnectionError..." (or similar depending on exact error)
        *   Log: "Attempt 2/3 ... failed with HTTP error: ClientConnectionError..."
        *   Log: "Attempt 3/3 ... failed with HTTP error: ClientConnectionError..."
        *   Log error: "All 3 attempts to send validation request failed."
*   **Test Case 5.2: HTTP Error (e.g., 500 Server Error from audio_server)**
    *   **Setup:** Mock `aiohttp.ClientSession().post()` to return a response with `status=500` for all 3 attempts.
    *   **Input:** Some `validation_data`.
    *   **Assertions:**
        *   Returns `None`.
        *   Log: "Attempt 1/3 for text validation failed with status 500..."
        *   Log: "Attempt 2/3 for text validation failed with status 500..."
        *   Log: "Attempt 3/3 for text validation failed with status 500..."
        *   Log error: "All 3 attempts to send validation request failed."
*   **Test Case 5.3: Timeout (`aiohttp.ClientTimeout`)**
    *   **Setup:** Mock `aiohttp.ClientSession().post()` to raise `asyncio.TimeoutError` (which `aiohttp.ClientTimeout` would typically cause).
    *   **Input:** Some `validation_data`.
    *   **Assertions:**
        *   Returns `None`.
        *   Log: "Attempt 1/3 ... failed with HTTP error: TimeoutError..." (or ClientTimeout exception string)
        *   Log error: "All 3 attempts to send validation request failed."
*   **Test Case 5.4: Success on Retry**
    *   **Setup:** Mock `aiohttp.ClientSession().post()` to fail on the first attempt (e.g., raise `ClientConnectionError`) and succeed on the second with `status=200` and valid JSON.
    *   **Input:** Some `validation_data`.
    *   **Assertions:**
        *   Log: "Attempt 1/3 ... failed..."
        *   Log: "Waiting ... seconds before next retry..."
        *   Log: "Attempt 2/3 ... send validation request..."
        *   Log info: "Validation request successful (Attempt 2)."
        *   Returns the expected JSON response.

### 6. `callbacks.before_tts._collect_streaming_text`

*   **Test Case 6.1: Error during stream iteration**
    *   **Setup:** Create a mock async iterable that raises an Exception partway through iteration.
    *   **Input:** The mock async iterable.
    *   **Assertions:**
        *   Log error: "Error encountered while collecting streaming text: <error_message>".
        *   Returns a string containing chunks collected before the error.

## Audio Server Component (`audio_server/app.py`)

All tests target the `/validate_audio_length` endpoint.

### 1. Malformed Requests

*   **Test Case 1.1: No JSON body**
    *   **Setup:** Send POST request with `Content-Type: application/json` but an empty body or non-JSON body.
    *   **Assertions:**
        *   Status Code: 400.
        *   Response Body: `{"error": {"code": "NO_DATA_PROVIDED", "message": "No data provided"}}` (or similar if Flask handles it differently before view, e.g. Werkzeug's BadRequest).
*   **Test Case 1.2: Missing `text` field**
    *   **Setup:** Send JSON: `{"estimated_length": 30.0}`.
    *   **Assertions:**
        *   Status Code: 400.
        *   Response Body: `{"error": {"code": "MISSING_REQUIRED_FIELDS", "message": "Missing required fields: text and estimated_length are mandatory"}}`.
*   **Test Case 1.3: Missing `estimated_length` field**
    *   **Setup:** Send JSON: `{"text": "hello"}`.
    *   **Assertions:**
        *   Status Code: 400.
        *   Response Body: `{"error": {"code": "MISSING_REQUIRED_FIELDS", "message": "Missing required fields: text and estimated_length are mandatory"}}`.
*   **Test Case 1.4: Invalid `estimated_length` type (e.g., string)**
    *   **Setup:** Send JSON: `{"text": "hello", "estimated_length": "thirty"}`.
    *   **Assertions:**
        *   Status Code: 400.
        *   Response Body: `{"error": {"code": "INVALID_INPUT_TYPE", "message": "estimated_length must be a non-negative number"}}`.
*   **Test Case 1.5: Negative `estimated_length`**
    *   **Setup:** Send JSON: `{"text": "hello", "estimated_length": -5.0}`.
    *   **Assertions:**
        *   Status Code: 400.
        *   Response Body: `{"error": {"code": "INVALID_INPUT_TYPE", "message": "estimated_length must be a non-negative number"}}`.
*   **Test Case 1.6: Invalid `max_length` type (e.g., string)**
    *   **Setup:** Send JSON: `{"text": "hello", "estimated_length": 30.0, "max_length": "sixty"}`.
    *   **Assertions:**
        *   Status Code: 400.
        *   Response Body: `{"error": {"code": "INVALID_INPUT_TYPE", "message": "max_length must be a positive number"}}`.
*   **Test Case 1.7: Non-positive `max_length` (e.g., 0 or negative)**
    *   **Setup:** Send JSON: `{"text": "hello", "estimated_length": 30.0, "max_length": 0}`.
    *   **Assertions:**
        *   Status Code: 400.
        *   Response Body: `{"error": {"code": "INVALID_INPUT_TYPE", "message": "max_length must be a positive number"}}`.
*   **Test Case 1.8: `text` field is not a string**
    *   **Setup:** Send JSON: `{"text": 123, "estimated_length": 30.0}`.
    *   **Assertions:**
        *   Status Code: 400.
        *   Response Body: `{"error": {"code": "INVALID_INPUT_TYPE", "message": "text must be a string"}}`.

### 2. `estimated_length == 0` Scenarios

*   **Test Case 2.1: `estimated_length = 0`, `max_length` positive (no trimming needed)**
    *   **Setup:** Send JSON: `{"text": "hello", "estimated_length": 0, "max_length": 60.0}`.
    *   **Assertions:**
        *   Status Code: 200.
        *   Response Body: `{"text": "hello", "modified": False, "estimated_duration": 0}`.
        *   Log: "Text is within time limit...".
*   **Test Case 2.2: `estimated_length = 0`, `max_length = 0` (edge case for trimming logic, should be caught by `max_length` positive validation but testing directly if validation was bypassed)**
    *   **Setup:** (Assuming `max_length > 0` validation could be bypassed for test) Send JSON: `{"text": "hello", "estimated_length": 0, "max_length": 0}`.
    *   **Assertions (if `max_length > 0` validation is active, this won't be hit):**
        *   Status Code: 400 due to `max_length` not positive.
    *   **Assertions (if `max_length > 0` validation is bypassed and code proceeds to trimming logic):**
        *   Status Code: 200 (as per current implementation for zero estimated_length in trimming path).
        *   Response Body: `{"text": "...", "modified": True, "original_length": 5, "trimmed_length": 3, "estimated_original_duration": 0, "estimated_new_duration": 0.0}`.
        *   Log warning: "estimated_length is 0, but trimming was attempted...".

### 3. `chars_to_keep <= 0` Scenarios

*   **Test Case 3.1: `chars_to_keep` becomes zero (e.g., short text, long `estimated_length`, short `max_length`)**
    *   **Setup:** Send JSON: `{"text": "hi", "estimated_length": 100.0, "max_length": 0.01}`. (This should lead to `chars_to_keep = 0`).
    *   **Assertions:**
        *   Status Code: 200.
        *   Response Body: `{"text": "...", "modified": True, "original_length": 2, "trimmed_length": 3, "estimated_original_duration": 100.0, "estimated_new_duration": 0.0}`.
        *   Log warning: "Calculated chars_to_keep is 0. Returning minimal trimmed text.".
*   **Test Case 3.2: `chars_to_keep` becomes negative (not possible with `int(total_chars * keep_ratio)` if `keep_ratio` is positive, but good to be aware if logic changed)**
    *   **This scenario is effectively covered by `chars_to_keep <= 0`.**

### 4. Invalid Slice Index Scenarios During Trimming

*   **Test Case 4.1: `start_index >= end_index` initially (e.g., very aggressive trim ratio on short text)**
    *   **Setup:** Send JSON: `{"text": "a b c", "estimated_length": 10.0, "max_length": 0.1}`. (This might make `chars_to_keep` very small, e.g., 0 or 1, potentially leading to `start_index >= end_index`).
    *   **Assertions:**
        *   Status Code: 200.
        *   Response Body: `{"text": "...", "modified": True, ... "estimated_new_duration": 0.0}` (if `chars_to_keep` became <=0) OR `{"text": "...", "modified": True, ... "estimated_new_duration": 0.1}` (if `chars_to_keep` was >0 but slice invalid).
        *   Log warning: "Trimming resulted in invalid indices..." or "Calculated chars_to_keep is...".
*   **Test Case 4.2: `start_index >= end_index` after word boundary adjustment**
    *   **Setup:** Send JSON with text that causes word boundary adjustments to make indices invalid. E.g., `{"text": "word", "estimated_length": 10.0, "max_length": 1.0}`. (If `chars_to_keep` is small, like 1, `start_index` might be 1, `end_index` 2. Word boundary adjustment might not find spaces and default, or might shift them to be invalid).
    *   **Assertions:**
        *   Status Code: 200.
        *   Response Body: `{"text": "...", "modified": True, ...}`.
        *   Log warning: "Trimming after word boundary adjustment resulted in invalid indices...".

### 5. General Internal Server Errors

*   **Test Case 5.1: Unexpected error during processing**
    *   **Setup:** Mock a part of the code (e.g., `text.split()`, if `text` was not validated as string and was some other object) to raise an unexpected `AttributeError` or `TypeError` after initial validations pass.
    *   **Input:** Valid JSON that would trigger the mocked error.
    *   **Assertions:**
        *   Status Code: 500.
        *   Response Body: `{"error": {"code": "INTERNAL_SERVER_ERROR", "message": "<error_message>"}}`.
        *   Log exception: "Error processing validation request: <error_message>".

This conceptual test plan provides a good starting point for verifying the robustness and correctness of the implemented error handling and core logic. Each conceptual test would ideally be translated into one or more concrete unit or integration tests.Okay, I have drafted the `CONCEPTUAL_TESTS.MD` file with the conceptual test plan as requested. It covers various scenarios for both the `agent` and `audio_server` components, focusing on the recently implemented error handling and edge cases.

The next step is to create this file in the repository.
