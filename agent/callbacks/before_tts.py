import logging
import asyncio # Required for asyncio.sleep
from typing import Any, AsyncIterable, Dict, Optional

import aiohttp
from callbacks.utils import estimate_audio_length
from config import settings
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
    if not settings.AUDIO_SERVER_URL:
        logger.warning("AUDIO_SERVER_URL not configured")
        return None
    
    endpoint = f"{settings.AUDIO_SERVER_URL}/validate_audio_length"
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        logger.info(f"Attempt {attempt + 1}/{max_retries} to send validation request to {endpoint}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=validation_data,
                    timeout=aiohttp.ClientTimeout(total=5.0),
                ) as response:
                    if response.status == 200:
                        logger.info(f"Validation request successful (Attempt {attempt + 1}).")
                        return await response.json()
                    else:
                        error_msg = await response.text()
                        logger.warning(
                            f"Attempt {attempt + 1} for text validation failed with status {response.status}: {error_msg}"
                        )
        except aiohttp.ClientError as e:
            logger.warning(
                f"Attempt {attempt + 1} for text validation failed with HTTP error: {str(e)}"
            )
        except Exception as e:
            logger.warning(
                f"Attempt {attempt + 1} for text validation failed with unexpected error: {str(e)}"
            )

        if attempt < max_retries - 1:
            logger.info(f"Waiting {retry_delay} seconds before next retry...")
            await asyncio.sleep(retry_delay)
        else:
            logger.error(
                f"All {max_retries} attempts to send validation request failed."
            )
            return None


async def _collect_streaming_text(text_stream: AsyncIterable[str]) -> str:
    """
    Collects all chunks from an AsyncIterable text stream into a single string.
    
    Args:
        text_stream: AsyncIterable of text chunks
        
    Returns:
        Complete text as a single string
    """
    chunks = []
    try:
        async for chunk in text_stream:
            chunks.append(chunk)
    except Exception as e:
        logger.error(f"Error encountered while collecting streaming text: {e}")
        # Depending on desired behavior, you might want to re-raise or handle differently
        # For now, we return partially collected chunks.
    return "".join(chunks)


async def _create_text_stream(text: str) -> AsyncIterable[str]:
    """
    Creates an AsyncIterable stream from a string.
    
    Args:
        text: String to convert to an AsyncIterable stream
        
    Returns:
        AsyncIterable of the text
    """
    yield text


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
    
    # Handle both string and streaming text
    is_streaming = not isinstance(text, str)
    if is_streaming:
        # For streaming text, collect all chunks to process together
        original_stream = text
        text = await _collect_streaming_text(original_stream)
        logger.info(f"Collected streaming text (length: {len(text)} chars)")

    # Estimate audio length
    estimated_length = estimate_audio_length(
        text, words_per_minute=settings.DEFAULT_VOICE_WPM
    )
    logger.info(f"Estimated audio length: {estimated_length:.2f} seconds")

    # Prepare data for Flask server validation
    validation_data = {
        "text": text,
        "estimated_length": estimated_length,
        "max_length": 60.0  # 60 seconds max length
    }

    # Send to validation server
    response_data = await _send_validation_request(validation_data)
    if response_data and "text" in response_data:
        # Server may have modified the text if too long
        modified_text = response_data["text"]
        if modified_text != text:
            logger.info("Text modified by validation server (likely trimmed)")
            text = modified_text

            # Re-estimate with the modified text
            new_estimated_length = estimate_audio_length(
                text, words_per_minute=settings.DEFAULT_VOICE_WPM
            )
            logger.info(
                f"New estimated audio length after modification: {new_estimated_length:.2f} seconds"
            )
    else:
        logger.warning("Failed to validate with server, using original text")

    # Return in same format as received
    if is_streaming:
        logger.info(f"Returning text as AsyncIterable (length: {len(text)} chars)")
        return _create_text_stream(text)
    else:
        logger.info(f"Final text length: {len(text)} chars")
        return text