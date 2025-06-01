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
            return jsonify({"error": {"code": "NO_DATA_PROVIDED", "message": "No data provided"}}), 400

        # Extract data from request
        text = data.get("text")
        estimated_length = data.get("estimated_length")
        max_length = data.get("max_length", MAX_AUDIO_LENGTH)

        if text is None or estimated_length is None: # Check for presence of text
            return jsonify({"error": {"code": "MISSING_REQUIRED_FIELDS", "message": "Missing required fields: text and estimated_length are mandatory"}}), 400

        if not isinstance(text, str):
             return jsonify({"error": {"code": "INVALID_INPUT_TYPE", "message": "text must be a string"}}), 400

        # Validate inputs
        if not isinstance(estimated_length, (int, float)) or estimated_length < 0:
            return jsonify({"error": {"code": "INVALID_INPUT_TYPE", "message": "estimated_length must be a non-negative number"}}), 400

        if not isinstance(max_length, (int, float)) or max_length <= 0:
            return jsonify({"error": {"code": "INVALID_INPUT_TYPE", "message": "max_length must be a positive number"}}), 400

        # Proactive check for estimated_length == 0 before trimming logic
        if estimated_length == 0 and max_length > 0 : # If max_length is 0 or less, it's not a trimming scenario
            # This case implies we might try to divide by zero if not handled before keep_ratio.
            # However, it could also be valid if max_length is also 0.
            # The primary concern is division by zero in keep_ratio.
            # If it's not going to be trimmed (i.e. estimated_length <= max_length), it's fine.
            pass # Will be handled by the "within limit" check.

        logger.info(
            f"Received text for validation: {len(text)} chars, estimated length: {estimated_length:.2f}s, max_length: {max_length:.2f}s"
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
        total_chars = len(text)

        if estimated_length == 0: # Should not happen if max_length > 0 due to earlier checks, but safeguard for keep_ratio
            logger.warning("estimated_length is 0, but trimming was attempted. This implies max_length is also 0 or negative, which should be caught by validators.")
            # This scenario means max_length is likely 0 or negative.
            # If max_length is 0, keep_ratio is 0 / 0 (NaN) or X / 0 (Inf).
            # It's safer to return minimal text.
            return jsonify({
                "text": "..." if total_chars > 0 else "",
                "modified": True,
                "original_length": total_chars,
                "trimmed_length": len("...") if total_chars > 0 else 0,
                "estimated_original_duration": estimated_length,
                "estimated_new_duration": 0.0
            }), 200 # Still a 200 as we processed it, albeit with extreme trimming.

        # Calculate the proportion to keep
        keep_ratio = max_length / estimated_length
        chars_to_keep = int(total_chars * keep_ratio)

        if chars_to_keep <= 0:
            logger.warning(f"Calculated chars_to_keep is {chars_to_keep}. Returning minimal trimmed text.")
            fallback_text = "..." if total_chars > 0 else ""
            return jsonify({
                "text": fallback_text,
                "modified": True,
                "original_length": total_chars,
                "trimmed_length": len(fallback_text),
                "estimated_original_duration": estimated_length,
                "estimated_new_duration": 0.0
            })

        # Calculate start and end indices for middle segment
        extra_chars = total_chars - chars_to_keep
        start_index = extra_chars // 2
        end_index = start_index + chars_to_keep

        # Robust Indexing
        start_index = max(0, start_index)
        end_index = min(total_chars, end_index)

        trimmed_text = ""
        if start_index >= end_index:
            logger.warning(f"Trimming resulted in invalid indices (start: {start_index}, end: {end_index}). Using fallback.")
            trimmed_text = "..." if total_chars > 0 else ""
        else:
            # Adjust indices to avoid cutting words in the middle
            # Find a space near the start index (going forward)
            temp_start = start_index
            # Only adjust if not at the very beginning and if there's text to search within
            if temp_start > 0 and temp_start < total_chars:
                i = temp_start
                while i < temp_start + 20 and i < total_chars: # Check i < total_chars
                    if text[i].isspace():
                        start_index = i + 1
                        break
                    i += 1

            # Find a space near the end index (going backward)
            temp_end = end_index
            # Only adjust if not at the very end and if there's text to search within
            if temp_end < total_chars and temp_end > 0:
                i = temp_end
                while i > temp_end - 20 and i > 0: # Check i > 0
                    if text[i].isspace():
                        end_index = i
                        break
                    i -= 1

            # Ensure start_index is still valid after adjustments
            start_index = max(0, start_index)
            if start_index >= end_index: # Re-check after word boundary adjustments
                 logger.warning(f"Trimming after word boundary adjustment resulted in invalid indices (start: {start_index}, end: {end_index}). Using fallback.")
                 trimmed_text = "..." if total_chars > 0 else ""
            else:
                trimmed_text = text[start_index:end_index]


        final_trimmed_text = "..." + trimmed_text + "..." if trimmed_text else ("..." if total_chars > 0 else "")
        if not trimmed_text and total_chars > 0 : # If original text had content but trim is empty
             logger.info("Trimming resulted in an empty segment, using ellipsis.")
        elif not trimmed_text and total_chars == 0:
             logger.info("Original text was empty, trim is empty.")


        logger.info(
            f"Original length: {total_chars} chars, Trimmed length (before ellipsis): {len(trimmed_text)} chars, Final length: {len(final_trimmed_text)} chars"
        )

        # Estimate new duration based on the actual length of `trimmed_text` before ellipsis
        # This is a rough estimate, as ellipsis add characters but not much speech time.
        # Or, use max_length as it's the target. For simplicity, stick to max_length as "estimated_new_duration".
        # If chars_to_keep was 0, new_duration should be 0.
        new_duration = max_length if chars_to_keep > 0 else 0.0


        return jsonify({
            "text": final_trimmed_text,
            "modified": True,
            "original_length": total_chars,
            "trimmed_length": len(final_trimmed_text),
            "estimated_original_duration": estimated_length,
            "estimated_new_duration": float(new_duration)
        })

    except Exception as e:
        logger.exception(f"Error processing validation request: {str(e)}")
        return jsonify({"error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)}}), 500
