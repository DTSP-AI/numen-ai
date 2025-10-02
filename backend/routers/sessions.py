from fastapi import APIRouter, HTTPException, Depends, Request
from uuid import UUID, uuid4
from datetime import datetime
import logging

from models.schemas import SessionCreate, SessionResponse, SessionStatus, ConsentUpdate, ConsentResponse
from database import get_pg_pool
from services.livekit_service import LiveKitService

logger = logging.getLogger(__name__)
router = APIRouter()
livekit_service = LiveKitService()


@router.post("/", response_model=SessionResponse)
async def create_session(session: SessionCreate):
    """Create a new therapy session with LiveKit room"""
    logger.info(f"RAW BODY: {session.model_dump()}")

    pool = get_pg_pool()

    session_id = uuid4()
    room_name = f"session-{session_id}"
    now = datetime.utcnow()

    # Create LiveKit room (optional - graceful degradation)
    user_token = None
    try:
        room_info = await livekit_service.create_room(room_name)
        logger.info(f"Created LiveKit room: {room_name}")

        # Generate access token for user
        user_token = await livekit_service.generate_token(
            room_name=room_name,
            participant_name=f"user-{session.user_id}",
            is_agent=False
        )
    except Exception as lk_error:
        logger.warning(f"LiveKit unavailable, continuing without real-time voice: {lk_error}")

    # Create session in database
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sessions (id, user_id, status, room_name, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                session_id,
                session.user_id,
                SessionStatus.PENDING.value,
                room_name,
                now,
                now
            )

        logger.info(f"Created session {session_id} for user {session.user_id}")

        return SessionResponse(
            id=session_id,
            user_id=session.user_id,
            status=SessionStatus.PENDING,
            room_name=room_name,
            access_token=user_token,
            created_at=now,
            updated_at=now
        )

    except Exception as e:
        logger.error(f"Failed to create session in database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


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


@router.patch("/{session_id}/consent", response_model=ConsentResponse)
async def update_consent(session_id: UUID, consent: ConsentUpdate, request: Request):
    """
    Update user consent for therapy session

    This endpoint captures user consent with:
    - Timestamp (immutable once set)
    - IP address
    - User agent

    Required for HIPAA/SOC2 compliance.
    """
    pool = get_pg_pool()

    try:
        # Get client IP
        ip_address = consent.ip_address or request.client.host if request.client else "unknown"
        user_agent = consent.user_agent or request.headers.get("user-agent", "unknown")

        async with pool.acquire() as conn:
            # Check if session exists
            session = await conn.fetchrow(
                "SELECT id, session_data FROM sessions WHERE id = $1",
                session_id
            )

            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            # Get existing session data
            session_data = session["session_data"] or {}

            # Check if already consented (immutable)
            if session_data.get("consent", {}).get("consented"):
                logger.warning(f"Attempt to modify existing consent for session {session_id}")
                raise HTTPException(
                    status_code=400,
                    detail="Consent already provided and cannot be modified"
                )

            # Update session data with consent
            now = datetime.utcnow()
            session_data["consent"] = {
                "consented": consent.consented,
                "consented_at": now.isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent
            }

            # Update database
            await conn.execute(
                """
                UPDATE sessions
                SET session_data = $1, updated_at = $2
                WHERE id = $3
                """,
                session_data,
                now,
                session_id
            )

            logger.info(f"Consent updated for session {session_id}: consented={consent.consented}")

            return ConsentResponse(
                session_id=session_id,
                consented=consent.consented,
                consented_at=now if consent.consented else None,
                message="Consent recorded successfully" if consent.consented else "Consent declined"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update consent: {e}")
        raise HTTPException(status_code=500, detail="Failed to update consent")