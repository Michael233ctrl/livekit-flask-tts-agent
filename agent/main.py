import asyncio
import json
import logging

from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, JobProcess
from livekit.agents.llm import (
    ChatContext,
    ChatMessage,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.agents.log import logger
from livekit.plugins import deepgram, silero, cartesia, openai, google
from typing import List, Any

from config import settings
from callbacks import before_tts_callback


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def prewarm(proc: JobProcess):
    """
    Preload models and resources when the process starts.

    Args:
        proc: The job process object for storing preloaded resources
    """
    logger.info("Prewarming models and resources...")

    # Preload VAD model
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("VAD model loaded")

    # Fetch available voices from Cartesia
    headers = {
        "X-API-Key": settings.CARTESIA_API_KEY,
        "Cartesia-Version": "2024-08-01",
        "Content-Type": "application/json",
    }

    try:
        import requests

        response = requests.get("https://api.cartesia.ai/voices", headers=headers)
        if response.status_code == 200:
            proc.userdata["cartesia_voices"] = response.json()
            logger.info(
                f"Fetched {len(proc.userdata['cartesia_voices'])} Cartesia voices"
            )
        else:
            logger.warning(f"Failed to fetch Cartesia voices: {response.status_code}")
            proc.userdata["cartesia_voices"] = []
    except Exception as e:
        logger.error(f"Error fetching Cartesia voices: {str(e)}")
        proc.userdata["cartesia_voices"] = []


async def entrypoint(ctx: JobContext):
    """
    Main entry point for the voice assistant agent.

    Args:
        ctx: The job context for the agent
    """
    logger.info(f"Starting voice assistant in room: {ctx.room.name}")

    initial_ctx = ChatContext(
        messages=[
            ChatMessage(
                role="system",
                content="You are a voice assistant created by LiveKit. Your interface with users will be voice. Pretend we're having a conversation, no special formatting or headings, just natural speech.",
            )
        ]
    )
    cartesia_voices: List[dict[str, Any]] = ctx.proc.userdata["cartesia_voices"]

    tts = cartesia.TTS(
        model="sonic-2",
    )
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(),
        llm=google.LLM(model="gemini-2.0-flash"),
        tts=tts,
        chat_ctx=initial_ctx,
        before_tts_cb=before_tts_callback,
    )

    is_user_speaking = False
    is_agent_speaking = False

    @ctx.room.on("participant_attributes_changed")
    def on_participant_attributes_changed(
        changed_attributes: dict[str, str], participant: rtc.Participant
    ):
        # check for attribute changes from the user itself
        if participant.kind != rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD:
            return

        if "voice" in changed_attributes:
            voice_id = participant.attributes.get("voice")
            logger.info(
                f"participant {participant.identity} requested voice change: {voice_id}"
            )
            if not voice_id:
                return

            voice_data = next(
                (voice for voice in cartesia_voices if voice["id"] == voice_id), None
            )
            if not voice_data:
                logger.warning(f"Voice {voice_id} not found")
                return
            if "embedding" in voice_data:
                language = "en"
                if "language" in voice_data and voice_data["language"] != "en":
                    language = voice_data["language"]
                tts._opts.voice = voice_data["embedding"]
                tts._opts.language = language
                # allow user to confirm voice change as long as no one is speaking
                if not (is_agent_speaking or is_user_speaking):
                    asyncio.create_task(
                        agent.say("How do I sound now?", allow_interruptions=True)
                    )

    await ctx.connect()

    @agent.on("agent_started_speaking")
    def agent_started_speaking():
        nonlocal is_agent_speaking
        is_agent_speaking = True

    @agent.on("agent_stopped_speaking")
    def agent_stopped_speaking():
        nonlocal is_agent_speaking
        is_agent_speaking = False

    @agent.on("user_started_speaking")
    def user_started_speaking():
        nonlocal is_user_speaking
        is_user_speaking = True

    @agent.on("user_stopped_speaking")
    def user_stopped_speaking():
        nonlocal is_user_speaking
        is_user_speaking = False

    # set voice listing as attribute for UI
    voices = []
    for voice in cartesia_voices:
        voices.append(
            {
                "id": voice["id"],
                "name": voice["name"],
            }
        )
    voices.sort(key=lambda x: x["name"])
    await ctx.room.local_participant.set_attributes({"voices": json.dumps(voices)})

    agent.start(ctx.room)
    await agent.say("Hi there, how are you doing today?", allow_interruptions=True)


def main():
    """Main entry point for the CLI application."""
    try:
        logger.info("Starting LiveKit Voice Assistant")
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
    except KeyboardInterrupt:
        logger.info("Voice assistant terminated by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        raise


if __name__ == "__main__":
    main()
