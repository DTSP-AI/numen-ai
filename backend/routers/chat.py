from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from database import get_pg_pool
from services.agent_service import AgentService
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessageRequest(BaseModel):
    user_id: str
    agent_id: str
    message: str


class ChatMessageResponse(BaseModel):
    user_message: dict
    agent_response: dict


class Message(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    messages: List[Message]


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_chat_message(session_id: str, request: ChatMessageRequest):
    """
    Send a message in a chat session and get agent response
    """
    pool = get_db_pool()

    try:
        async with pool.acquire() as conn:
            # Ensure messages table exists
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY,
                    session_id UUID NOT NULL REFERENCES sessions(id),
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    audio_url TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )

            # Get session
            session = await conn.fetchrow(
                "SELECT * FROM sessions WHERE id = $1",
                uuid.UUID(session_id)
            )

            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            # Get agent
            agent = await conn.fetchrow(
                "SELECT * FROM agents WHERE id = $1",
                uuid.UUID(request.agent_id)
            )

            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")

            # Store user message
            user_message_id = uuid.uuid4()
            user_timestamp = datetime.utcnow()
            await conn.execute(
                """
                INSERT INTO messages (id, session_id, role, content, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_message_id,
                uuid.UUID(session_id),
                "user",
                request.message,
                user_timestamp
            )

            # Get agent service
            agent_service = AgentService()

            # Process message with agent
            agent_response = await agent_service.process_chat_message(
                agent_id=request.agent_id,
                session_id=session_id,
                message=request.message,
                context=session.get("session_data", {})
            )

            # Store agent message
            agent_message_id = uuid.uuid4()
            agent_timestamp = datetime.utcnow()
            agent_content = agent_response.get("response", "I'm here to help guide you on your manifestation journey.")

            await conn.execute(
                """
                INSERT INTO messages (id, session_id, role, content, audio_url, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                agent_message_id,
                uuid.UUID(session_id),
                "agent",
                agent_content,
                agent_response.get("audio_url"),
                agent_timestamp
            )

            return ChatMessageResponse(
                user_message={
                    "id": str(user_message_id),
                    "role": "user",
                    "content": request.message,
                    "timestamp": user_timestamp.isoformat()
                },
                agent_response={
                    "id": str(agent_message_id),
                    "role": "agent",
                    "content": agent_content,
                    "timestamp": agent_timestamp.isoformat(),
                    "audio_url": agent_response.get("audio_url")
                }
            )

    except Exception as e:
        logger.error(f"Failed to process chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """
    Get all messages for a session
    """
    pool = get_db_pool()

    try:
        async with pool.acquire() as conn:
            # Check if messages table exists, if not create it
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY,
                    session_id UUID NOT NULL REFERENCES sessions(id),
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    audio_url TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )

            messages = await conn.fetch(
                """
                SELECT id, role, content, audio_url, created_at
                FROM messages
                WHERE session_id = $1
                ORDER BY created_at ASC
                """,
                uuid.UUID(session_id)
            )

            return ChatHistoryResponse(
                messages=[
                    Message(
                        id=str(msg["id"]),
                        role=msg["role"],
                        content=msg["content"],
                        timestamp=msg["created_at"].isoformat()
                    )
                    for msg in messages
                ]
            )

    except Exception as e:
        logger.error(f"Failed to load chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/affirmations/agent/{agent_id}")
async def get_agent_affirmations(agent_id: str):
    """
    Get affirmations created by a specific agent
    """
    pool = get_db_pool()

    try:
        async with pool.acquire() as conn:
            affirmations = await conn.fetch(
                """
                SELECT a.*
                FROM affirmations a
                JOIN sessions s ON a.user_id = s.user_id
                WHERE s.agent_id = $1
                ORDER BY a.created_at DESC
                LIMIT 20
                """,
                uuid.UUID(agent_id)
            )

            return {
                "affirmations": [
                    {
                        "id": str(aff["id"]),
                        "affirmation_text": aff["affirmation_text"],
                        "category": aff["category"],
                        "audio_url": aff.get("audio_url"),
                        "play_count": aff.get("play_count", 0),
                        "is_favorite": aff.get("is_favorite", False),
                        "created_at": aff["created_at"].isoformat()
                    }
                    for aff in affirmations
                ]
            }

    except Exception as e:
        logger.error(f"Failed to load agent affirmations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
