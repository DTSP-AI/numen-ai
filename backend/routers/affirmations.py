"""
Affirmations & Content API

CRUD operations for affirmations, scripts, and user content.
Part of the Dashboard Agent system.
"""

from fastapi import APIRouter, HTTPException, Header, Query, Depends
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import time, datetime
import logging

from database import get_pg_pool
from services.audio_synthesis import audio_service
from models.agent import VoiceConfiguration
from dependencies import get_user_id, get_tenant_id
from agents.guide_agent.guide_sub_agents.manifestation_protocol_agent import ManifestationProtocolAgent

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

class GenerateAffirmationsRequest(BaseModel):
    """Request to generate affirmations using an agent"""
    user_id: str
    agent_id: str
    session_id: Optional[str] = None
    count: int = Field(default=10, ge=3, le=20)


@router.post("/affirmations/generate")
async def generate_affirmations(request: GenerateAffirmationsRequest):
    """
    Generate personalized affirmations using an agent's ManifestationProtocolAgent

    This endpoint:
    1. Loads the agent contract
    2. Retrieves user goals from session metadata
    3. Uses ManifestationProtocolAgent to generate AI-powered affirmations
    4. Stores affirmations in database with schedules
    5. Returns generated affirmations
    """
    pool = get_pg_pool()

    try:
        # Get agent contract and session data
        async with pool.acquire() as conn:
            agent_row = await conn.fetchrow("""
                SELECT id, name, contract
                FROM agents
                WHERE id = $1::uuid
            """, request.agent_id)

            if not agent_row:
                raise HTTPException(status_code=404, detail="Agent not found")

            agent_contract = agent_row["contract"]
            agent_name = agent_row["name"]

            # Get session metadata which contains intake data
            goals = []
            commitment_level = "moderate"
            timeframe = "30_days"

            if request.session_id:
                session_row = await conn.fetchrow("""
                    SELECT session_data
                    FROM sessions
                    WHERE id = $1::uuid
                """, request.session_id)

                if session_row and session_row["session_data"]:
                    session_data = session_row["session_data"]
                    intake_data = session_data.get("metadata", {}).get("intake_data", {})
                    goals = intake_data.get("goals", [])

                    # Map session type to commitment level and timeframe
                    session_type = intake_data.get("session_type", "manifestation")
                    if session_type in ["intensive", "habit_change"]:
                        commitment_level = "intensive"
                        timeframe = "90_days"
                    elif session_type in ["anxiety_relief", "sleep_hypnosis"]:
                        commitment_level = "light"
                        timeframe = "7_days"

            # Combine goals into single manifestation goal
            primary_goal = goals[0] if goals else "personal transformation and growth"

            # Use ManifestationProtocolAgent to generate complete protocol
            logger.info(f"Generating manifestation protocol for goal: {primary_goal}")
            protocol_agent = ManifestationProtocolAgent()
            protocol = await protocol_agent.generate_protocol(
                user_id=request.user_id,
                goal=primary_goal,
                timeframe=timeframe,
                commitment_level=commitment_level
            )

            # Extract affirmations from protocol
            affirmations_data = protocol.get("affirmations", {})
            all_affirmations = affirmations_data.get("all", [])
            daily_rotation = affirmations_data.get("daily_rotation", {})

            # Store affirmations in database with schedule
            generated_affirmations = []

            for idx, affirmation_text in enumerate(all_affirmations[:request.count]):
                # Determine category based on content
                category = "identity" if "I am" in affirmation_text else \
                          "gratitude" if "grateful" in affirmation_text.lower() else \
                          "action"

                # Determine schedule - rotate through days
                days = list(daily_rotation.keys())
                day_idx = idx % len(days) if days else 0
                schedule_day = days[day_idx] if days else None

                # Insert affirmation
                aff_id = await conn.fetchval("""
                    INSERT INTO affirmations (
                        user_id, agent_id, affirmation_text,
                        category, status, schedule_type, schedule_time
                    )
                    VALUES ($1::uuid, $2::uuid, $3, $4, 'active', $5, $6::time)
                    RETURNING id
                """, request.user_id, request.agent_id, affirmation_text, category,
                "daily" if schedule_day else None,
                "08:00:00" if schedule_day else None)  # Default morning time

                generated_affirmations.append({
                    "id": str(aff_id),
                    "affirmation_text": affirmation_text,
                    "category": category,
                    "audio_url": None,
                    "play_count": 0,
                    "is_favorite": False,
                    "schedule_day": schedule_day,
                    "created_at": datetime.utcnow().isoformat()
                })

            # Store full protocol in session metadata for future reference
            await conn.execute("""
                UPDATE sessions
                SET session_data = session_data || $1::jsonb
                WHERE id = $2::uuid
            """, {"manifestation_protocol": protocol}, request.session_id)

            logger.info(f"Generated {len(generated_affirmations)} AI-powered affirmations for user {request.user_id} using agent {agent_name}")

            return {
                "status": "success",
                "agent_name": agent_name,
                "count": len(generated_affirmations),
                "affirmations": generated_affirmations,
                "protocol_summary": {
                    "daily_practices": len(protocol.get("daily_practices", [])),
                    "visualizations": len(protocol.get("visualizations", [])),
                    "success_metrics": len(protocol.get("success_metrics", [])),
                    "checkpoints": len(protocol.get("checkpoints", []))
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate affirmations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate affirmations: {str(e)}")


@router.get("/affirmations/user/{user_id}")
async def get_user_affirmations(
    user_id: str,
    tenant_id: str = Depends(get_tenant_id),
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
    user_id: str = Depends(get_user_id)
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

            # Extract voice config with default fallback
            voice_config_data = contract.get("voice")
            if not voice_config_data:
                # Provide default Rachel voice instead of raising error
                logger.warning(f"Agent has no voice config, using default Rachel voice")
                voice_config_data = {
                    "provider": "elevenlabs",
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel - calm female voice
                    "language": "en-US",
                    "speed": 1.0,
                    "stability": 0.75,
                    "similarity_boost": 0.75,
                    "stt_provider": "deepgram",
                    "stt_model": "nova-2",
                    "stt_language": "en",
                    "vad_enabled": True
                }

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
                # Provide default Rachel voice instead of raising error
                logger.warning(f"Agent has no voice config for script, using default Rachel voice")
                voice_config_data = {
                    "provider": "elevenlabs",
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel - calm female voice
                    "language": "en-US",
                    "speed": 1.0,
                    "stability": 0.75,
                    "similarity_boost": 0.75,
                    "stt_provider": "deepgram",
                    "stt_model": "nova-2",
                    "stt_language": "en",
                    "vad_enabled": True
                }

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
