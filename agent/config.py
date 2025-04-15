from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv("../.env.local")


class Settings(BaseSettings):
    """Application settings loaded from environment variables with type validation."""

    # LiveKit Configuration
    LIVEKIT_API_KEY: str = Field(..., description="LiveKit API key for authentication")
    LIVEKIT_API_SECRET: str = Field(
        ..., description="LiveKit API secret for authentication"
    )
    LIVEKIT_URL: str = Field(..., description="LiveKit server URL")
    LIVEKIT_ROOM: str = Field("voice-assistant", description="LiveKit room name")

    # API Keys
    CARTESIA_API_KEY: str = Field(..., description="Cartesia API key for TTS")
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API key")
    GOOGLE_API_KEY: Optional[str] = Field(None, description="Google API key")

    # Voice Configuration
    TTS_MODEL: str = Field("sonic-2", description="Text-to-speech model to use")
    LLM_MODEL: str = Field("gpt-4o-mini", description="LLM model to use")
    DEFAULT_VOICE_WPM: int = Field(
        150, description="Default words per minute for speech"
    )

    # External Services
    FLASK_SERVER_URL: Optional[str] = Field(
        None, description="URL for Flask validation server"
    )
    USE_EXTERNAL_VALIDATION: bool = Field(
        False, description="Whether to use external validation server"
    )

    # Application Configuration
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    DEBUG: bool = Field(False, description="Enable debug mode")
    USE_MOCK_LLM: bool = Field(False, description="Use mock LLM for testing")


settings = Settings()
