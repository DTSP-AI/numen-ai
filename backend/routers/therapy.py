from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from uuid import UUID
import logging
import json

from database import get_pg_pool, get_redis

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/session/{session_id}")
async def therapy_websocket(websocket: WebSocket, session_id: UUID):
    """WebSocket endpoint for real-time therapy session"""
    await websocket.accept()

    try:
        pool = get_pg_pool()
        redis = get_redis()

        # Verify session exists
        async with pool.acquire() as conn:
            session = await conn.fetchrow(
                "SELECT id, user_id, status FROM sessions WHERE id = $1",
                session_id
            )

            if not session:
                await websocket.send_json({"error": "Session not found"})
                await websocket.close()
                return

        logger.info(f"WebSocket connected for session {session_id}")

        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "session_id": str(session_id)
        })

        # Handle messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "transcript":
                # Store transcript entry
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO transcripts (id, session_id, speaker, content)
                        VALUES (gen_random_uuid(), $1, $2, $3)
                        """,
                        session_id,
                        message["speaker"],
                        message["content"]
                    )

            elif message["type"] == "audio_chunk":
                # Store audio metadata (actual audio handled by LiveKit)
                logger.debug(f"Received audio chunk for session {session_id}")
                await websocket.send_json({
                    "type": "audio_ack",
                    "timestamp": message.get("timestamp")
                })

            elif message["type"] == "start_session":
                # Initialize therapy session
                await websocket.send_json({
                    "type": "session_started",
                    "session_id": str(session_id)
                })

            elif message["type"] == "end_session":
                # Finalize therapy session
                await websocket.send_json({
                    "type": "session_ended",
                    "session_id": str(session_id)
                })

            else:
                # Unknown message type
                await websocket.send_json({
                    "type": "ack",
                    "message_type": message["type"]
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"error": str(e)})
        await websocket.close()


@router.get("/transcripts/{session_id}")
async def get_session_transcripts(session_id: UUID):
    """Get all transcripts for a session"""
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, speaker, content, timestamp
                FROM transcripts
                WHERE session_id = $1
                ORDER BY timestamp ASC
                """,
                session_id
            )

            transcripts = [
                {
                    "id": str(row["id"]),
                    "speaker": row["speaker"],
                    "content": row["content"],
                    "timestamp": row["timestamp"].isoformat()
                }
                for row in rows
            ]

            return {"session_id": str(session_id), "transcripts": transcripts}

    except Exception as e:
        logger.error(f"Failed to get transcripts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transcripts")