from fastapi import APIRouter, HTTPException
from uuid import UUID, uuid4
from datetime import datetime
import logging
import json

from models.schemas import ContractCreate, ContractResponse
from database import get_pg_pool

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ContractResponse)
async def create_contract(contract: ContractCreate):
    """Create a therapy contract from intake session"""
    pool = get_pg_pool()

    contract_id = uuid4()
    now = datetime.utcnow()

    try:
        async with pool.acquire() as conn:
            # Verify session exists
            session = await conn.fetchrow(
                "SELECT id FROM sessions WHERE id = $1",
                contract.session_id
            )

            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            # Insert contract
            await conn.execute(
                """
                INSERT INTO contracts (id, session_id, user_id, goals, tone, voice_id, session_type, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                contract_id,
                contract.session_id,
                contract.user_id,
                json.dumps(contract.goals),
                contract.tone.value,
                contract.voice_id,
                contract.session_type.value,
                now
            )

        logger.info(f"Created contract {contract_id} for session {contract.session_id}")

        return ContractResponse(
            id=contract_id,
            session_id=contract.session_id,
            user_id=contract.user_id,
            goals=contract.goals,
            tone=contract.tone,
            voice_id=contract.voice_id,
            session_type=contract.session_type,
            created_at=now
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create contract: {e}")
        raise HTTPException(status_code=500, detail="Failed to create contract")


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(contract_id: UUID):
    """Get contract details"""
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM contracts WHERE id = $1",
                contract_id
            )

            if not row:
                raise HTTPException(status_code=404, detail="Contract not found")

            return ContractResponse(
                id=row["id"],
                session_id=row["session_id"],
                user_id=row["user_id"],
                goals=json.loads(row["goals"]),
                tone=row["tone"],
                voice_id=row["voice_id"],
                session_type=row["session_type"],
                created_at=row["created_at"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get contract: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve contract")


@router.get("/session/{session_id}", response_model=ContractResponse)
async def get_contract_by_session(session_id: UUID):
    """Get contract by session ID"""
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM contracts WHERE session_id = $1",
                session_id
            )

            if not row:
                raise HTTPException(status_code=404, detail="Contract not found for session")

            return ContractResponse(
                id=row["id"],
                session_id=row["session_id"],
                user_id=row["user_id"],
                goals=json.loads(row["goals"]),
                tone=row["tone"],
                voice_id=row["voice_id"],
                session_type=row["session_type"],
                created_at=row["created_at"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get contract by session: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve contract")