"""
Utility functions for voice assistant callbacks.
"""

import logging
from config import settings

# Configure logging
logger = logging.getLogger(__name__)


def estimate_audio_length(text: str, words_per_minute: int = None) -> float:
    """
    Estimate the duration of audio in seconds based on text length.

    Args:
        text: The text to estimate audio length for
        words_per_minute: Speaking rate (defaults to settings.DEFAULT_VOICE_WPM)

    Returns:
        Estimated duration in seconds

    Example:
        >>> estimate_audio_length("Hello world, this is a test.")
        1.85
    """
    if not text:
        logger.debug("Empty text provided, returning zero duration")
        return 0.0

    # Use default WPM from settings if not specified
    if words_per_minute is None:
        words_per_minute = settings.DEFAULT_VOICE_WPM

    # Split text into words and count them
    words = text.split()
    word_count = len(words)

    # Calculate duration in seconds
    # Formula: (word count / words per minute) * 60 seconds
    duration_seconds = (word_count / words_per_minute) * 60

    logger.debug(
        f"Audio length estimate: {duration_seconds:.2f} seconds "
        f"({word_count} words at {words_per_minute} WPM)"
    )

    return duration_seconds
