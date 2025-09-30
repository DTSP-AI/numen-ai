from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID, uuid4
from datetime import datetime
import logging

from models.schemas import SessionCreate, SessionResponse, SessionStatus
from database import get_pg_pool

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=SessionResponse)
async def create_session(session: SessionCreate):
    """Create a new therapy session"""
    pool = get_pg_pool()

    session_id = uuid4()
    now = datetime.utcnow()

    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sessions (id, user_id, status, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                session_id,
                session.user_id,
                SessionStatus.PENDING.value,
                now,
                now
            )

        logger.info(f"Created session {session_id} for user {session.user_id}")

        return SessionResponse(
            id=session_id,
            user_id=session.user_id,
            status=SessionStatus.PENDING,
            created_at=now,
            updated_at=now
        )

    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID):
    """Get session details"""
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM sessions WHERE id = $1",
                session_id
            )

            if not row:
                raise HTTPException(status_code=404, detail="Session not found")

            return SessionResponse(
                id=row["id"],
                user_id=row["user_id"],
                status=SessionStatus(row["status"]),
                room_name=row["room_name"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")


@router.patch("/{session_id}/status")
async def update_session_status(session_id: UUID, status: SessionStatus):
    """Update session status"""
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE sessions
                SET status = $1, updated_at = $2
                WHERE id = $3
                """,
                status.value,
                datetime.utcnow(),
                session_id
            )

            if result == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Session not found")

        logger.info(f"Updated session {session_id} status to {status.value}")

        return {"message": "Session status updated", "status": status.value}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update session")