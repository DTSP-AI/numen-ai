from livekit import api, rtc
from livekit.api import AccessToken, VideoGrants
import logging
from typing import Optional
from datetime import timedelta

from config import settings

logger = logging.getLogger(__name__)


class LiveKitService:
    """Service for managing LiveKit rooms and connections"""

    def __init__(self):
        self.api_key = settings.livekit_api_key
        self.api_secret = settings.livekit_api_secret
        self.url = settings.livekit_url

    async def create_room(self, room_name: str) -> dict:
        """Create a new LiveKit room for therapy session"""
        try:
            room_service = api.RoomService(
                self.url,
                self.api_key,
                self.api_secret
            )

            room = await room_service.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=300,  # 5 minutes
                    max_participants=2  # User + Agent
                )
            )

            logger.info(f"Created LiveKit room: {room_name}")

            return {
                "room_name": room.name,
                "sid": room.sid,
                "created_at": room.creation_time
            }

        except Exception as e:
            logger.error(f"Failed to create LiveKit room: {e}")
            raise

    async def generate_token(
        self,
        room_name: str,
        participant_name: str,
        is_agent: bool = False
    ) -> str:
        """Generate access token for room participant"""
        try:
            token = AccessToken(
                self.api_key,
                self.api_secret
            )

            token.identity = participant_name
            token.name = participant_name

            # Grant permissions
            grants = VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True
            )

            if is_agent:
                # Agent can also record and moderate
                grants.room_record = True
                grants.room_admin = True

            token.add_grant(grants)

            # Set expiration
            token.ttl = timedelta(hours=2)

            jwt_token = token.to_jwt()

            logger.info(f"Generated token for {participant_name} in room {room_name}")

            return jwt_token

        except Exception as e:
            logger.error(f"Failed to generate LiveKit token: {e}")
            raise

    async def close_room(self, room_name: str):
        """Close LiveKit room after session completion"""
        try:
            room_service = api.RoomService(
                self.url,
                self.api_key,
                self.api_secret
            )

            await room_service.delete_room(
                api.RoomDeleteRequest(room=room_name)
            )

            logger.info(f"Closed LiveKit room: {room_name}")

        except Exception as e:
            logger.error(f"Failed to close LiveKit room: {e}")
            raise


class LiveKitAgent:
    """LiveKit agent participant for audio streaming"""

    def __init__(
        self,
        room_name: str,
        token: str,
        livekit_url: str
    ):
        self.room_name = room_name
        self.token = token
        self.url = livekit_url
        self.room: Optional[rtc.Room] = None
        self.audio_source: Optional[rtc.AudioSource] = None

    async def connect(self):
        """Connect agent to LiveKit room"""
        try:
            self.room = rtc.Room()

            # Set up event handlers
            @self.room.on("participant_connected")
            def on_participant_connected(participant: rtc.RemoteParticipant):
                logger.info(f"Participant connected: {participant.identity}")

            @self.room.on("track_subscribed")
            def on_track_subscribed(
                track: rtc.Track,
                publication: rtc.RemoteTrackPublication,
                participant: rtc.RemoteParticipant
            ):
                logger.info(f"Track subscribed: {track.kind} from {participant.identity}")

            # Connect to room
            await self.room.connect(self.url, self.token)

            logger.info(f"Agent connected to room: {self.room_name}")

        except Exception as e:
            logger.error(f"Failed to connect agent to room: {e}")
            raise

    async def publish_audio(self, audio_data: bytes, sample_rate: int = 48000):
        """Publish audio chunk to room"""
        try:
            if not self.audio_source:
                self.audio_source = rtc.AudioSource(sample_rate, 1)

                # Create audio track
                track = rtc.LocalAudioTrack.create_audio_track(
                    "agent-audio",
                    self.audio_source
                )

                # Publish track
                await self.room.local_participant.publish_track(
                    track,
                    rtc.TrackPublishOptions()
                )

            # Push audio frame
            await self.audio_source.capture_frame(
                rtc.AudioFrame.create(sample_rate, 1, len(audio_data) // 2)
            )

        except Exception as e:
            logger.error(f"Failed to publish audio: {e}")
            raise

    async def disconnect(self):
        """Disconnect agent from room"""
        if self.room:
            await self.room.disconnect()
            logger.info(f"Agent disconnected from room: {self.room_name}")