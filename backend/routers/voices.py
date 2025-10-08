"""
Voice Selection & Preview API

Provides endpoints for browsing ElevenLabs voices and generating preview audio.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
import logging

from services.elevenlabs_service import ElevenLabsService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize ElevenLabs service (lazy loading with forced refresh)
elevenlabs_service = None
ELEVENLABS_AVAILABLE = False
_initialization_attempted = False

def get_elevenlabs_service(force_refresh=False):
    """Get or initialize ElevenLabs service (lazy loading)"""
    global elevenlabs_service, ELEVENLABS_AVAILABLE, _initialization_attempted

    logger.info(f"get_elevenlabs_service called: force_refresh={force_refresh}, attempted={_initialization_attempted}, available={ELEVENLABS_AVAILABLE}")

    # Force refresh if requested (for hot reload scenarios)
    if force_refresh:
        elevenlabs_service = None
        ELEVENLABS_AVAILABLE = False
        _initialization_attempted = False
        logger.info("Forcing ElevenLabs service refresh")

    if not _initialization_attempted or elevenlabs_service is None:
        _initialization_attempted = True
        logger.info("Attempting to initialize ElevenLabs service...")
        try:
            elevenlabs_service = ElevenLabsService()
            ELEVENLABS_AVAILABLE = True
            logger.info("✅ ElevenLabs service initialized successfully")
        except Exception as e:
            logger.error(f"❌ ElevenLabs initialization failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            ELEVENLABS_AVAILABLE = False
            elevenlabs_service = None
            # Allow reattempts in future calls instead of permanent lockout
            _initialization_attempted = False
    return elevenlabs_service if ELEVENLABS_AVAILABLE else None


class VoiceOption(BaseModel):
    """Voice option for agent creation"""
    id: str
    name: str
    category: str
    gender: str
    age: str
    description: str
    preview_url: Optional[str] = None
    accent: Optional[str] = None
    use_case: str


class VoicePreviewRequest(BaseModel):
    """Request to generate voice preview"""
    voice_id: str
    text: str = "Hello, I'm your personalized manifestation guide. Together, we'll unlock your potential and create lasting transformation."


@router.get("/voices")
async def get_available_voices(force_refresh: bool = False):
    """
    Get all available voices for agent creation

    Returns voices from ElevenLabs SDK with metadata enriched for UI display
    """
    try:
        # Direct instantiation - bypass lazy loading issues
        from services.elevenlabs_service import ElevenLabsService
        service = ElevenLabsService()

        # Fetch voices from ElevenLabs SDK
        sdk_voices = service.get_available_voices()

        # Enrich with UI-friendly metadata
        enriched_voices = []
        for voice in sdk_voices:
            labels = voice.get("labels", {})

            # Extract gender, age, accent from labels
            gender = labels.get("gender", "unknown")
            age = labels.get("age", "unknown")
            accent = labels.get("accent", "")
            use_case = labels.get("use case", labels.get("use_case", "General purpose"))

            enriched_voice = {
                "id": voice["id"],
                "name": voice["name"],
                "category": voice.get("category", "general"),
                "gender": gender,
                "age": age,
                "accent": accent,
                "description": voice.get("description", f"Voice: {voice['name']}"),
                "preview_url": voice.get("preview_url"),
                "use_case": use_case
            }
            enriched_voices.append(enriched_voice)

        logger.info(f"Returning {len(enriched_voices)} voices from ElevenLabs SDK")

        return {
            "total": len(enriched_voices),
            "voices": enriched_voices,
            "available": True
        }

    except Exception as e:
        logger.error(f"Failed to fetch voices from ElevenLabs SDK: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

        # Fallback to curated list if SDK fails
        fallback_voices = [
            {
                "id": "21m00Tcm4TlvDq8ikWAM",
                "name": "Rachel",
                "category": "calm",
                "gender": "female",
                "age": "young",
                "accent": "American",
                "description": "Warm and soothing, perfect for calming affirmations",
                "use_case": "Anxiety relief, sleep hypnosis, gentle guidance"
            },
            {
                "id": "pNInz6obpgDQGcFmaJgB",
                "name": "Adam",
                "category": "energetic",
                "gender": "male",
                "age": "middle-aged",
                "accent": "American",
                "description": "Confident and motivating, great for empowerment",
                "use_case": "Confidence building, action-oriented affirmations"
            },
            {
                "id": "EXAVITQu4vr4xnSDxMaL",
                "name": "Bella",
                "category": "authoritative",
                "gender": "female",
                "age": "young",
                "accent": "American",
                "description": "Clear and authoritative, ideal for structured guidance",
                "use_case": "Habit change, professional development"
            },
            {
                "id": "XrExE9yKIg1WjnnlVkGX",
                "name": "Domi",
                "category": "gentle",
                "gender": "female",
                "age": "young",
                "accent": "American",
                "description": "Soft and nurturing, perfect for deep relaxation",
                "use_case": "Meditation, deep relaxation, inner child work"
            },
            {
                "id": "AZnzlk1XvdvUeBnXmlld",
                "name": "Daria",
                "category": "empowering",
                "gender": "female",
                "age": "young",
                "accent": "American",
                "description": "Strong and inspiring, great for manifestation work",
                "use_case": "Manifestation, goal achievement, empowerment"
            }
        ]

        return {
            "total": len(fallback_voices),
            "voices": fallback_voices,
            "available": True,
            "fallback": True,
            "message": "Using fallback voice list"
        }


@router.post("/voices/preview")
async def generate_voice_preview(request: VoicePreviewRequest):
    """
    Generate a preview audio sample for a voice

    Returns audio/mpeg response with the synthesized preview
    """
    # Lazy load service
    service = get_elevenlabs_service()

    if not service:
        raise HTTPException(
            status_code=503,
            detail="ElevenLabs service not available. Please configure ELEVENLABS_API_KEY."
        )

    try:
        # Generate audio using ElevenLabs with specified voice_id
        audio_bytes = await service.generate_speech_with_voice_id(
            text=request.text,
            voice_id=request.voice_id,
            model="eleven_turbo_v2"
        )

        if not audio_bytes:
            raise HTTPException(status_code=500, detail="No audio returned from ElevenLabs API")

        # Return as audio file
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=voice_preview_{request.voice_id}.mp3"
            }
        )

    except Exception as e:
        logger.error(f"Failed to generate voice preview for voice {request.voice_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.get("/voices/{voice_id}")
async def get_voice_details(voice_id: str):
    """Get detailed information about a specific voice"""
    # Get all voices
    voices_response = await get_available_voices()
    voices = voices_response["voices"]

    # Find matching voice
    voice = next((v for v in voices if v["id"] == voice_id), None)

    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")

    return voice
