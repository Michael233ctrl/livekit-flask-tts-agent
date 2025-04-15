import logging
import os

from flask import Flask, request, jsonify
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("audio-validation-server")

MAX_AUDIO_LENGTH = float(os.getenv("MAX_AUDIO_LENGTH", 60))


@app.route("/health", methods=["GET"])
def health_check():
    """Simple endpoint to verify the server is running"""
    return jsonify({"status": "ok"})


@app.route("/validate_audio_length", methods=["POST"], strict_slashes=False)
def validate_audio_length():
    """
    Endpoint to validate text based on estimated audio length.
    If the estimated audio length exceeds the maximum (default 60 seconds),
    the text is trimmed to a middle segment that fits within the limit.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract data from request
        text = data.get("text")
        estimated_length = data.get("estimated_length")
        max_length = data.get("max_length", MAX_AUDIO_LENGTH)

        if not text or estimated_length is None:
            return jsonify({"error": "Missing required fields"}), 400

        # Validate inputs
        if not isinstance(estimated_length, (int, float)) or estimated_length < 0:
            return jsonify({"error": "estimated_length must be a positive number"}), 400

        if not isinstance(max_length, (int, float)) or max_length <= 0:
            return jsonify({"error": "max_length must be a positive number"}), 400

        logger.info(
            f"Received text for validation: {len(text)} chars, estimated length: {estimated_length:.2f}s"
        )

        # If within limit, return unchanged
        if estimated_length <= max_length:
            logger.info("Text is within time limit, returning unchanged")
            return jsonify(
                {
                    "text": text,
                    "modified": False,
                    "estimated_duration": estimated_length,
                }
            )

        # Text needs trimming - extract middle segment
        logger.info(f"Text exceeds {max_length}s limit, trimming to middle segment")

        # Calculate the proportion to keep
        keep_ratio = max_length / estimated_length
        total_chars = len(text)
        chars_to_keep = int(total_chars * keep_ratio)

        # Calculate start and end indices for middle segment
        extra_chars = total_chars - chars_to_keep
        start_index = extra_chars // 2
        end_index = start_index + chars_to_keep

        # Adjust indices to avoid cutting words in the middle
        # Find a space near the start index (going forward)
        i = start_index
        while i < start_index + 20 and i < total_chars:
            if text[i].isspace():
                start_index = i + 1  # Start after the space
                break
            i += 1

        # Find a space near the end index (going backward)
        i = end_index
        while i > end_index - 20 and i > 0:
            if text[i].isspace():
                end_index = i  # End at the space
                break
            i -= 1

        # Extract middle segment
        trimmed_text = text[start_index:end_index]

        logger.info(
            f"Original length: {len(text)} chars, Trimmed length: {len(trimmed_text)} chars"
        )

        # Add ellipsis to indicate trimming
        trimmed_text = "..." + trimmed_text + "..."

        return jsonify(
            {
                "text": trimmed_text,
                "modified": True,
                "original_length": len(text),
                "trimmed_length": len(trimmed_text),
                "estimated_original_duration": estimated_length,
                "estimated_new_duration": max_length,
            }
        )

    except Exception as e:
        logger.exception(f"Error processing validation request: {str(e)}")
        return jsonify({"error": str(e)}), 500
