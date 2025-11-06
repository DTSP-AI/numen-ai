from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Dict, Optional
from uuid import uuid4
import logging

from agents.guide_agent.guide_sub_agents.manifestation_protocol_agent import ManifestationProtocolAgent

logger = logging.getLogger(__name__)
router = APIRouter()

protocol_agent = ManifestationProtocolAgent()

# Try to import database, but make it optional
try:
    from database import get_pg_pool
    DB_AVAILABLE = True
except:
    DB_AVAILABLE = False
    logger.warning("Database not available - running in protocol-generation-only mode")


class ProtocolRequest(BaseModel):
    user_id: str
    goal: str
    timeframe: Literal["7_days", "30_days", "90_days"] = "30_days"
    commitment_level: Literal["light", "moderate", "intensive"] = "moderate"


class ProtocolResponse(BaseModel):
    id: str
    user_id: str
    goal: str
    timeframe: str
    commitment_level: str
    protocol: Dict


@router.post("/generate", response_model=ProtocolResponse)
async def generate_manifestation_protocol(request: ProtocolRequest):
    """
    Generate a complete, structured manifestation protocol.

    This creates a personalized protocol including:
    - Goal analysis
    - Daily practices
    - Affirmations (3 sets: identity, gratitude, action)
    - Visualization scripts
    - Success metrics
    - Obstacle identification & solutions
    - Accountability checkpoints
    """
    try:
        logger.info(f"Generating protocol for user {request.user_id}, goal: {request.goal}")

        # Generate protocol using agent
        protocol = await protocol_agent.generate_protocol(
            user_id=request.user_id,
            goal=request.goal,
            timeframe=request.timeframe,
            commitment_level=request.commitment_level
        )

        # Store in database if available
        protocol_id = str(uuid4())

        if DB_AVAILABLE:
            try:
                import json
                pool = get_pg_pool()
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO manifestation_protocols
                        (id, user_id, goal, timeframe, commitment_level, protocol_data)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        protocol_id,
                        request.user_id,
                        request.goal,
                        request.timeframe,
                        request.commitment_level,
                        json.dumps(protocol)
                    )
                logger.info(f"Protocol {protocol_id} stored in database")
            except Exception as e:
                logger.warning(f"Could not store in database: {e}")
        else:
            logger.info(f"Protocol {protocol_id} generated (not stored - DB unavailable)")

        return ProtocolResponse(
            id=protocol_id,
            user_id=request.user_id,
            goal=request.goal,
            timeframe=request.timeframe,
            commitment_level=request.commitment_level,
            protocol=protocol
        )

    except Exception as e:
        logger.error(f"Failed to generate protocol: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate protocol: {str(e)}")


@router.get("/{protocol_id}", response_model=ProtocolResponse)
async def get_protocol(protocol_id: str):
    """Retrieve a previously generated protocol"""
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, goal, timeframe, commitment_level, protocol_data
                FROM manifestation_protocols
                WHERE id = $1
                """,
                protocol_id
            )

            if not row:
                raise HTTPException(status_code=404, detail="Protocol not found")

            return ProtocolResponse(
                id=row["id"],
                user_id=row["user_id"],
                goal=row["goal"],
                timeframe=row["timeframe"],
                commitment_level=row["commitment_level"],
                protocol=json.loads(row["protocol_data"])
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve protocol: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve protocol")


@router.get("/user/{user_id}")
async def get_user_protocols(user_id: str):
    """Get all protocols for a user"""
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, goal, timeframe, commitment_level, created_at
                FROM manifestation_protocols
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id
            )

            protocols = [
                {
                    "id": row["id"],
                    "goal": row["goal"],
                    "timeframe": row["timeframe"],
                    "commitment_level": row["commitment_level"],
                    "created_at": row["created_at"].isoformat()
                }
                for row in rows
            ]

            return {"user_id": user_id, "protocols": protocols}

    except Exception as e:
        logger.error(f"Failed to get user protocols: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve protocols")


@router.post("/{protocol_id}/checkpoint")
async def log_checkpoint(protocol_id: str, checkpoint_data: Dict):
    """Log completion of a checkpoint"""
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO protocol_checkpoints
                (id, protocol_id, checkpoint_day, data)
                VALUES (gen_random_uuid(), $1, $2, $3)
                """,
                protocol_id,
                checkpoint_data.get("day"),
                json.dumps(checkpoint_data)
            )

        return {"message": "Checkpoint logged successfully"}

    except Exception as e:
        logger.error(f"Failed to log checkpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to log checkpoint")
