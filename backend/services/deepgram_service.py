from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from typing import Callable, Optional
import asyncio
import logging

from config import settings

logger = logging.getLogger(__name__)


class DeepgramService:
    """Service for real-time speech-to-text using Deepgram"""

    def __init__(self):
        self.client = DeepgramClient(settings.deepgram_api_key)
        self.connection: Optional[any] = None
        self.is_connected = False

    async def start_streaming(
        self,
        on_transcript: Callable[[str], None],
        on_error: Optional[Callable[[str], None]] = None
    ):
        """Start streaming transcription"""
        try:
            # Create live transcription connection
            self.connection = self.client.listen.live.v("1")

            # Set up event handlers
            def on_message(result: any):
                sentence = result.channel.alternatives[0].transcript
                if sentence:
                    logger.debug(f"Deepgram transcript: {sentence}")
                    on_transcript(sentence)

            def on_error_event(error: any):
                error_msg = str(error)
                logger.error(f"Deepgram error: {error_msg}")
                if on_error:
                    on_error(error_msg)

            def on_close():
                logger.info("Deepgram connection closed")
                self.is_connected = False

            # Register handlers
            self.connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.connection.on(LiveTranscriptionEvents.Error, on_error_event)
            self.connection.on(LiveTranscriptionEvents.Close, on_close)

            # Configure transcription options
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                interim_results=False,
                punctuate=True,
                utterance_end_ms=1000
            )

            # Start connection
            await self.connection.start(options)
            self.is_connected = True

            logger.info("Deepgram streaming started")

        except Exception as e:
            logger.error(f"Failed to start Deepgram streaming: {e}")
            raise

    async def send_audio(self, audio_data: bytes):
        """Send audio data for transcription"""
        try:
            if self.connection and self.is_connected:
                await self.connection.send(audio_data)
            else:
                logger.warning("Deepgram connection not active")

        except Exception as e:
            logger.error(f"Failed to send audio to Deepgram: {e}")

    async def stop_streaming(self):
        """Stop streaming transcription"""
        try:
            if self.connection:
                await self.connection.finish()
                self.is_connected = False
                logger.info("Deepgram streaming stopped")

        except Exception as e:
            logger.error(f"Failed to stop Deepgram streaming: {e}")


class DeepgramTranscriber:
    """Wrapper for managing Deepgram transcription lifecycle"""

    def __init__(self):
        self.service = DeepgramService()
        self.transcript_buffer: list[str] = []

    async def start(
        self,
        on_transcript: Callable[[str], None]
    ):
        """Start transcription with callback"""

        def handle_transcript(text: str):
            self.transcript_buffer.append(text)
            on_transcript(text)

        await self.service.start_streaming(
            on_transcript=handle_transcript
        )

    async def process_audio(self, audio_data: bytes):
        """Process audio chunk"""
        await self.service.send_audio(audio_data)

    async def stop(self) -> str:
        """Stop transcription and return full transcript"""
        await self.service.stop_streaming()
        full_transcript = " ".join(self.transcript_buffer)
        self.transcript_buffer.clear()
        return full_transcript