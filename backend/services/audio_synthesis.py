"""
Audio Synthesis Service - ElevenLabs Integration

Synthesizes text to speech for affirmations and hypnosis scripts.
Stores audio files in cloud storage and updates database with URLs.
"""

import logging
import os
from typing import Optional, Dict, Any, List
import httpx
import uuid
from pathlib import Path

from models.agent import VoiceConfiguration
from database import get_pg_pool

logger = logging.getLogger(__name__)


class AudioSynthesisService:
    """
    ElevenLabs audio synthesis service

    Converts text → audio and stores in file system (or cloud storage)
    """

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"

        if not self.api_key:
            logger.warning("WARNING: ELEVENLABS_API_KEY not set. Audio synthesis will be disabled.")

        # Storage configuration
        self.audio_storage_path = Path("backend/audio_files")
        self.audio_storage_path.mkdir(parents=True, exist_ok=True)

    async def synthesize_affirmation(
        self,
        affirmation_id: str,
        text: str,
        voice_config: VoiceConfiguration
    ) -> Optional[str]:
        """
        Synthesize affirmation to audio

        Args:
            affirmation_id: Affirmation UUID
            text: Affirmation text
            voice_config: Voice configuration from agent contract

        Returns:
            audio_url: Path/URL to audio file
        """

        if not self.api_key:
            logger.warning("Audio synthesis skipped (no API key)")
            return None

        try:
            # Call ElevenLabs API
            audio_data = await self._call_elevenlabs_api(
                text=text,
                voice_id=voice_config.voice_id,
                stability=voice_config.stability,
                similarity_boost=voice_config.similarity_boost
            )

            if not audio_data:
                return None

            # Save audio file
            audio_filename = f"affirmation_{affirmation_id}.mp3"
            audio_path = self.audio_storage_path / audio_filename
            audio_path.write_bytes(audio_data)

            # Generate URL (in production, upload to S3/Azure Blob)
            audio_url = f"/audio/{audio_filename}"

            # Update database
            await self._update_affirmation_audio(affirmation_id, audio_url, len(audio_data))

            logger.info(f"✅ Audio synthesized: {audio_filename}")
            return audio_url

        except Exception as e:
            logger.error(f"Audio synthesis failed: {e}")
            return None

    async def synthesize_hypnosis_script(
        self,
        script_id: str,
        script_text: str,
        voice_config: VoiceConfiguration
    ) -> Optional[str]:
        """
        Synthesize hypnosis script to audio

        Args:
            script_id: Script UUID
            script_text: Full hypnosis script text
            voice_config: Voice configuration

        Returns:
            audio_url: Path/URL to audio file
        """

        if not self.api_key:
            logger.warning("Audio synthesis skipped (no API key)")
            return None

        try:
            # Call ElevenLabs API
            audio_data = await self._call_elevenlabs_api(
                text=script_text,
                voice_id=voice_config.voice_id,
                stability=voice_config.stability,
                similarity_boost=voice_config.similarity_boost
            )

            if not audio_data:
                return None

            # Save audio file
            audio_filename = f"hypnosis_{script_id}.mp3"
            audio_path = self.audio_storage_path / audio_filename
            audio_path.write_bytes(audio_data)

            audio_url = f"/audio/{audio_filename}"

            # Update database
            await self._update_script_audio(script_id, audio_url)

            logger.info(f"✅ Hypnosis audio synthesized: {audio_filename}")
            return audio_url

        except Exception as e:
            logger.error(f"Hypnosis audio synthesis failed: {e}")
            return None

    async def _call_elevenlabs_api(
        self,
        text: str,
        voice_id: str,
        stability: float = 0.75,
        similarity_boost: float = 0.75
    ) -> Optional[bytes]:
        """
        Call ElevenLabs TTS API

        Args:
            text: Text to synthesize
            voice_id: ElevenLabs voice ID
            stability: Voice stability (0-1)
            similarity_boost: Similarity boost (0-1)

        Returns:
            Audio data as bytes
        """

        url = f"{self.base_url}/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        data = {
            "text": text,
            "model_id": "eleven_turbo_v2",  # Fast, low-latency model
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost
            }
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=data)

                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"ElevenLabs API call failed: {e}")
            return None

    async def _update_affirmation_audio(
        self,
        affirmation_id: str,
        audio_url: str,
        audio_size_bytes: int
    ):
        """Update affirmation record with audio URL"""
        pool = get_pg_pool()

        try:
            # Calculate duration (rough estimate: 150 words per minute, 5 chars per word)
            estimated_duration_seconds = (len(audio_url) * 60) // (150 * 5)

            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE affirmations
                    SET audio_url = $1,
                        audio_duration_seconds = $2,
                        updated_at = NOW()
                    WHERE id = $3::uuid
                """, audio_url, estimated_duration_seconds, affirmation_id)

            logger.info(f"✅ Affirmation audio URL updated: {affirmation_id}")

        except Exception as e:
            logger.error(f"Failed to update affirmation audio URL: {e}")

    async def _update_script_audio(
        self,
        script_id: str,
        audio_url: str
    ):
        """Update hypnosis script record with audio URL"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE hypnosis_scripts
                    SET audio_url = $1,
                        updated_at = NOW()
                    WHERE id = $2::uuid
                """, audio_url, script_id)

            logger.info(f"✅ Script audio URL updated: {script_id}")

        except Exception as e:
            logger.error(f"Failed to update script audio URL: {e}")

    async def batch_synthesize_affirmations(
        self,
        user_id: str,
        agent_id: str,
        voice_config: VoiceConfiguration
    ) -> Dict[str, int]:
        """
        Batch synthesize all affirmations for a user that don't have audio yet

        Returns:
            Dict with success/failure counts
        """
        pool = get_pg_pool()
        success_count = 0
        failure_count = 0

        try:
            async with pool.acquire() as conn:
                # Get affirmations without audio
                rows = await conn.fetch("""
                    SELECT id, affirmation_text
                    FROM affirmations
                    WHERE user_id = $1::uuid
                      AND agent_id = $2::uuid
                      AND audio_url IS NULL
                      AND status = 'active'
                    LIMIT 50
                """, user_id, agent_id)

                logger.info(f"Found {len(rows)} affirmations to synthesize")

                for row in rows:
                    affirmation_id = str(row["id"])
                    text = row["affirmation_text"]

                    audio_url = await self.synthesize_affirmation(
                        affirmation_id=affirmation_id,
                        text=text,
                        voice_config=voice_config
                    )

                    if audio_url:
                        success_count += 1
                    else:
                        failure_count += 1

            logger.info(f"✅ Batch synthesis complete: {success_count} success, {failure_count} failures")

            return {
                "success": success_count,
                "failure": failure_count,
                "total": len(rows)
            }

        except Exception as e:
            logger.error(f"Batch synthesis failed: {e}")
            return {"success": 0, "failure": 0, "total": 0}

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available ElevenLabs voices

        Returns:
            List of voice metadata
        """

        if not self.api_key:
            return []

        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    return data.get("voices", [])
                else:
                    logger.error(f"Failed to fetch voices: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Failed to fetch voices: {e}")
            return []


# Global service instance
audio_service = AudioSynthesisService()
