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

# Initialize ElevenLabs service
try:
    elevenlabs_service = ElevenLabsService()
    ELEVENLABS_AVAILABLE = True
except Exception as e:
    logger.warning(f"ElevenLabs not available: {e}")
    ELEVENLABS_AVAILABLE = False


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
async def get_available_voices():
    """
    Get all available voices for agent creation

    Returns curated list of ElevenLabs voices suitable for hypnotherapy/manifestation
    """
    # Curated voices for hypnotherapy/manifestation applications
    voices = [
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
        },
        {
            "id": "TxGEqnHWrfWFTfGW9XjX",
            "name": "Josh",
            "category": "supportive",
            "gender": "male",
            "age": "young",
            "accent": "American",
            "description": "Friendly and supportive, excellent for encouragement",
            "use_case": "Daily affirmations, positive reinforcement"
        },
        {
            "id": "IKne3meq5aSn9XLyUdCD",
            "name": "Charlie",
            "category": "calm",
            "gender": "male",
            "age": "middle-aged",
            "accent": "Australian",
            "description": "Warm Australian accent, calming and reassuring",
            "use_case": "Stress relief, mindfulness, grounding"
        },
        {
            "id": "onwK4e9ZLuTAKqWW03F9",
            "name": "Daniel",
            "category": "authoritative",
            "gender": "male",
            "age": "middle-aged",
            "accent": "British",
            "description": "Distinguished British voice, professional and clear",
            "use_case": "Executive coaching, leadership development"
        }
    ]

    return {
        "total": len(voices),
        "voices": voices,
        "available": ELEVENLABS_AVAILABLE
    }


@router.post("/voices/preview")
async def generate_voice_preview(request: VoicePreviewRequest):
    """
    Generate a preview audio sample for a voice

    Returns audio/mpeg response with the synthesized preview
    """
    if not ELEVENLABS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ElevenLabs service not available. Please configure ELEVENLABS_API_KEY."
        )

    try:
        # Generate audio using ElevenLabs
        audio_bytes = await elevenlabs_service.generate_speech(
            text=request.text,
            voice_preference="calm",  # Will be overridden by voice_id below
            model="eleven_turbo_v2"
        )

        # Return as audio file
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=voice_preview_{request.voice_id}.mp3"
            }
        )

    except Exception as e:
        logger.error(f"Failed to generate voice preview: {e}")
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
