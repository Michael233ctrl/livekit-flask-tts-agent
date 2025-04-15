import logging
import aiohttp
from typing import Dict, Any, AsyncIterable, Optional

from config import settings
from callbacks.utils import estimate_audio_length

from livekit.agents.pipeline import VoicePipelineAgent


logger = logging.getLogger(__name__)


async def _send_validation_request(
    validation_data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Sends the validation request to the external server.

    Args:
        validation_data: The data to send for validation.

    Returns:
        The response data if the request is successful, None otherwise.
    """
    if not settings.USE_EXTERNAL_VALIDATION or not settings.FLASK_SERVER_URL:
        return

    logger.info(
        f"Sending request to the {settings.FLASK_SERVER_URL}/validate_audio_length"
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.FLASK_SERVER_URL}/validate_audio_length",
                json=validation_data,
                timeout=aiohttp.ClientTimeout(total=3.0),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_msg = await response.text()
                    logger.warning(
                        f"Text validation failed with status {response.status}: {error_msg}"
                    )
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error while validating text: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error during text validation: {str(e)}")


async def before_tts_callback(
    agent: VoicePipelineAgent, text: str | AsyncIterable[str]
) -> str | AsyncIterable[str]:
    """
    Process text before TTS by estimating audio length and potentially modifying the text.

    Args:
        agent: The VoicePipelineAgent instance.
        text:  The text to be processed, either a string or an async iterable of strings.

    Returns:
        The (potentially modified) text.
    """
    if not text:
        logger.warning("No text provided for TTS")
        return text

    if isinstance(text, str):
        log_text = text
    else:
        log_text = "(streaming text)"  # Log in case of streaming

    logger.info(f"Processing TTS text (length: {len(log_text)} chars)")

    # Estimate audio length
    if isinstance(text, str):
        estimated_length = estimate_audio_length(
            text, words_per_minute=settings.DEFAULT_VOICE_WPM
        )
    else:
        estimated_length = 0.0  # For streaming, we don't know the length

    logger.info(f"Estimated audio length: {estimated_length:.2f} seconds")

    # Prepare data for external validation
    validation_data = {
        "text": text if isinstance(text, str) else "(streaming text)",
        "estimated_length": estimated_length,
        "context": {  #  Populate context as best as possible.
            "session_id": getattr(
                agent, "sid", "unknown"
            ),  # Try to get session ID from Agent
            "user_id": getattr(agent, "participant_identity", "unknown"),
            "room_name": getattr(agent, "room_name", "unknown"),
        },
    }
    # Send to external validation server if configured
    response_data = None  # await _send_validation_request(validation_data)

    if response_data:
        if isinstance(text, str):
            # Check if the server modified the text
            if response_data.get("text") != text:
                logger.info("Text modified by validation server")
                text = response_data["text"]
                validation_data["text"] = text  # update
                # Re-estimate with new text
                estimated_length = estimate_audio_length(
                    text, words_per_minute=settings.DEFAULT_VOICE_WPM
                )
                validation_data["estimated_length"] = estimated_length
        else:
            logger.info("Text modified by validation server")
            text = response_data["text"]  # hope server returns a stream
            validation_data["text"] = "(streaming text)"

    if isinstance(text, str):
        log_text = text
    else:
        log_text = "(streaming text)"
    # Log the final text and estimated length
    logger.info(
        f"Final text length: {len(log_text)} chars, "
        f"estimated duration: {estimated_length:.2f} seconds"
    )

    return text
