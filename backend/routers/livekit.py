from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import logging
from livekit import api

from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class LiveKitTokenRequest(BaseModel):
    room_name: str
    participant_name: str
    metadata: Optional[Dict] = None


class LiveKitTokenResponse(BaseModel):
    token: str
    url: str


@router.post("/token", response_model=LiveKitTokenResponse)
async def create_livekit_token(request: LiveKitTokenRequest):
    """
    Generate a LiveKit access token for voice chat
    """
    try:
        # Get LiveKit credentials from config
        livekit_api_key = settings.LIVEKIT_API_KEY
        livekit_api_secret = settings.LIVEKIT_API_SECRET
        livekit_url = settings.LIVEKIT_URL

        if not all([livekit_api_key, livekit_api_secret, livekit_url]):
            raise HTTPException(
                status_code=500,
                detail="LiveKit credentials not configured"
            )

        # Create access token
        token = api.AccessToken(livekit_api_key, livekit_api_secret)
        token.with_identity(request.participant_name)
        token.with_name(request.participant_name)
        token.with_grants(
            api.VideoGrants(
                room_join=True,
                room=request.room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )

        # Add metadata if provided
        if request.metadata:
            token.with_metadata(str(request.metadata))

        # Generate JWT
        jwt_token = token.to_jwt()

        return LiveKitTokenResponse(
            token=jwt_token,
            url=livekit_url
        )

    except Exception as e:
        logger.error(f"Failed to create LiveKit token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rooms/{room_name}/disconnect")
async def disconnect_participant(room_name: str, participant_identity: str):
    """
    Disconnect a participant from a LiveKit room
    """
    try:
        livekit_api_key = settings.LIVEKIT_API_KEY
        livekit_api_secret = settings.LIVEKIT_API_SECRET
        livekit_url = settings.LIVEKIT_URL

        if not all([livekit_api_key, livekit_api_secret, livekit_url]):
            raise HTTPException(
                status_code=500,
                detail="LiveKit credentials not configured"
            )

        # Create room service client
        room_service = api.RoomService(livekit_url, livekit_api_key, livekit_api_secret)

        # Remove participant from room
        await room_service.remove_participant(
            api.RoomParticipantIdentity(
                room=room_name,
                identity=participant_identity
            )
        )

        return {"status": "disconnected", "room": room_name, "participant": participant_identity}

    except Exception as e:
        logger.error(f"Failed to disconnect participant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
