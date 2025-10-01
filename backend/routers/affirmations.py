"""
Affirmations & Content API

CRUD operations for affirmations, scripts, and user content.
Part of the Dashboard Agent system.
"""

from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import time
import logging

from database import get_pg_pool
from services.audio_synthesis import audio_service
from models.agent import VoiceConfiguration

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# MODELS
# ============================================================================

class AffirmationResponse(BaseModel):
    """Affirmation response model"""
    id: str
    affirmation_text: str
    category: Optional[str]
    audio_url: Optional[str]
    audio_duration_seconds: Optional[int]
    schedule_type: Optional[str]
    schedule_time: Optional[str]
    play_count: int
    is_favorite: bool
    created_at: str


class HypnosisScriptResponse(BaseModel):
    """Hypnosis script response model"""
    id: str
    title: str
    script_text: str
    duration_minutes: int
    audio_url: Optional[str]
    focus_area: str
    play_count: int
    created_at: str


# ============================================================================
# AFFIRMATIONS ENDPOINTS
# ============================================================================

@router.get("/affirmations/user/{user_id}")
async def get_user_affirmations(
    user_id: str,
    tenant_id: str = Header(None, alias="x-tenant-id"),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get all affirmations for user

    Filters:
    - category: identity, gratitude, action, visualization
    - limit: max results
    """
    pool = get_pg_pool()

    try:
        query = """
            SELECT
                id, affirmation_text, category, tags,
                audio_url, audio_duration_seconds,
                schedule_type, schedule_time,
                play_count, is_favorite,
                created_at
            FROM affirmations
            WHERE user_id = $1::uuid
              AND status = 'active'
        """
        params = [user_id]

        if category:
            query += f" AND category = ${len(params) + 1}"
            params.append(category)

        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1}"
        params.append(limit)

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            affirmations = [
                {
                    "id": str(row["id"]),
                    "affirmation_text": row["affirmation_text"],
                    "category": row["category"],
                    "audio_url": row["audio_url"],
                    "audio_duration_seconds": row["audio_duration_seconds"],
                    "schedule_type": row["schedule_type"],
                    "schedule_time": row["schedule_time"].isoformat() if row["schedule_time"] else None,
                    "play_count": row["play_count"],
                    "is_favorite": row["is_favorite"],
                    "created_at": row["created_at"].isoformat()
                }
                for row in rows
            ]

            return {
                "user_id": user_id,
                "total": len(affirmations),
                "affirmations": affirmations
            }

    except Exception as e:
        logger.error(f"Failed to get affirmations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve affirmations")


@router.patch("/affirmations/{affirmation_id}/favorite")
async def toggle_favorite(
    affirmation_id: str,
    is_favorite: bool
):
    """Toggle affirmation favorite status"""
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE affirmations
                SET is_favorite = $1, updated_at = NOW()
                WHERE id = $2::uuid
            """, is_favorite, affirmation_id)

        return {"status": "success", "is_favorite": is_favorite}

    except Exception as e:
        logger.error(f"Failed to toggle favorite: {e}")
        raise HTTPException(status_code=500, detail="Failed to update favorite status")


@router.post("/affirmations/{affirmation_id}/play")
async def record_play(affirmation_id: str):
    """Record affirmation play event"""
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE affirmations
                SET play_count = play_count + 1,
                    last_played_at = NOW()
                WHERE id = $1::uuid
            """, affirmation_id)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Failed to record play: {e}")
        raise HTTPException(status_code=500, detail="Failed to record play")


@router.post("/affirmations/{affirmation_id}/synthesize")
async def synthesize_audio(
    affirmation_id: str,
    user_id: str = Header(None, alias="x-user-id")
):
    """
    Synthesize audio for affirmation

    Requires agent's voice configuration.
    """
    pool = get_pg_pool()

    try:
        # Get affirmation and agent
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT a.affirmation_text, a.agent_id, ag.contract
                FROM affirmations a
                JOIN agents ag ON a.agent_id = ag.id
                WHERE a.id = $1::uuid
            """, affirmation_id)

            if not row:
                raise HTTPException(status_code=404, detail="Affirmation not found")

            text = row["affirmation_text"]
            contract = row["contract"]

            # Extract voice config
            voice_config_data = contract.get("voice")
            if not voice_config_data:
                raise HTTPException(status_code=400, detail="Agent has no voice configuration")

            voice_config = VoiceConfiguration(**voice_config_data)

        # Synthesize audio
        audio_url = await audio_service.synthesize_affirmation(
            affirmation_id=affirmation_id,
            text=text,
            voice_config=voice_config
        )

        if not audio_url:
            raise HTTPException(status_code=500, detail="Audio synthesis failed")

        return {
            "status": "success",
            "audio_url": audio_url
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to synthesize audio: {e}")
        raise HTTPException(status_code=500, detail="Failed to synthesize audio")


# ============================================================================
# HYPNOSIS SCRIPTS ENDPOINTS
# ============================================================================

@router.get("/scripts/user/{user_id}")
async def get_user_scripts(
    user_id: str,
    limit: int = Query(20, ge=1, le=100)
):
    """Get all hypnosis scripts for user"""
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    id, title, script_text, duration_minutes,
                    audio_url, focus_area, play_count,
                    created_at
                FROM hypnosis_scripts
                WHERE user_id = $1::uuid
                  AND status = 'active'
                ORDER BY created_at DESC
                LIMIT $2
            """, user_id, limit)

            scripts = [
                {
                    "id": str(row["id"]),
                    "title": row["title"],
                    "script_text": row["script_text"],
                    "duration_minutes": row["duration_minutes"],
                    "audio_url": row["audio_url"],
                    "focus_area": row["focus_area"],
                    "play_count": row["play_count"],
                    "created_at": row["created_at"].isoformat()
                }
                for row in rows
            ]

            return {
                "user_id": user_id,
                "total": len(scripts),
                "scripts": scripts
            }

    except Exception as e:
        logger.error(f"Failed to get scripts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scripts")


@router.post("/scripts/{script_id}/synthesize")
async def synthesize_script_audio(script_id: str):
    """Synthesize audio for hypnosis script"""
    pool = get_pg_pool()

    try:
        # Get script and agent voice config
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT hs.script_text, ag.contract
                FROM hypnosis_scripts hs
                JOIN agents ag ON hs.agent_id = ag.id
                WHERE hs.id = $1::uuid
            """, script_id)

            if not row:
                raise HTTPException(status_code=404, detail="Script not found")

            script_text = row["script_text"]
            contract = row["contract"]

            voice_config_data = contract.get("voice")
            if not voice_config_data:
                raise HTTPException(status_code=400, detail="Agent has no voice configuration")

            voice_config = VoiceConfiguration(**voice_config_data)

        # Synthesize
        audio_url = await audio_service.synthesize_hypnosis_script(
            script_id=script_id,
            script_text=script_text,
            voice_config=voice_config
        )

        if not audio_url:
            raise HTTPException(status_code=500, detail="Audio synthesis failed")

        return {
            "status": "success",
            "audio_url": audio_url
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to synthesize script audio: {e}")
        raise HTTPException(status_code=500, detail="Failed to synthesize audio")
