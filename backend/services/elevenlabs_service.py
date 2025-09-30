from elevenlabs.client import ElevenLabs
from typing import AsyncIterator, Optional
import logging

from config import settings

logger = logging.getLogger(__name__)


class ElevenLabsService:
    """Service for text-to-speech using ElevenLabs"""

    def __init__(self):
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)

        # Voice configurations
        self.voice_configs = {
            "calm": {
                "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel - calm female
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.3
            },
            "energetic": {
                "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam - energetic male
                "stability": 0.5,
                "similarity_boost": 0.9,
                "style": 0.7
            },
            "authoritative": {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella - authoritative female
                "stability": 0.8,
                "similarity_boost": 0.7,
                "style": 0.5
            },
            "gentle": {
                "voice_id": "XrExE9yKIg1WjnnlVkGX",  # Domi - gentle female
                "stability": 0.9,
                "similarity_boost": 0.8,
                "style": 0.2
            },
            "default": {
                "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.3
            }
        }

    async def generate_speech_streaming(
        self,
        text: str,
        voice_preference: str = "calm",
        model: str = "eleven_turbo_v2"
    ) -> AsyncIterator[bytes]:
        """
        Generate speech with streaming for low latency.
        Uses Turbo v2 for <300ms latency.
        """
        try:
            voice_config = self.voice_configs.get(
                voice_preference,
                self.voice_configs["default"]
            )

            # Generate audio (ElevenLabs 1.8.0 API)
            audio = self.client.generate(
                text=text,
                voice=voice_config["voice_id"],
                model=model
            )

            # Stream audio chunks
            for chunk in audio:
                yield chunk

            logger.info(f"Generated speech for voice: {voice_preference}")

        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            raise

    async def generate_speech(
        self,
        text: str,
        voice_preference: str = "calm",
        model: str = "eleven_turbo_v2"
    ) -> bytes:
        """
        Generate complete speech audio (non-streaming).
        Use for shorter texts or when buffering is acceptable.
        """
        try:
            voice_config = self.voice_configs.get(
                voice_preference,
                self.voice_configs["default"]
            )

            # Generate complete audio
            audio_bytes = self.client.generate(
                text=text,
                voice=voice_config["voice_id"],
                model=model
            )

            # Convert generator to bytes if needed
            if hasattr(audio_bytes, '__iter__'):
                audio_bytes = b"".join(audio_bytes)

            logger.info(f"Generated complete audio ({len(audio_bytes)} bytes)")

            return audio_bytes

        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            raise


class TTSStreamManager:
    """Manager for streaming TTS chunks to LiveKit"""

    def __init__(self, elevenlabs_service: ElevenLabsService):
        self.service = elevenlabs_service

    async def stream_to_livekit(
        self,
        text: str,
        voice_preference: str,
        livekit_agent
    ):
        """Stream TTS audio chunks directly to LiveKit agent"""
        try:
            # Stream audio chunks
            async for audio_chunk in self.service.generate_speech_streaming(
                text=text,
                voice_preference=voice_preference
            ):
                # Publish to LiveKit immediately
                await livekit_agent.publish_audio(audio_chunk)

            logger.info("Completed streaming audio to LiveKit")

        except Exception as e:
            logger.error(f"Failed to stream audio to LiveKit: {e}")
            raise