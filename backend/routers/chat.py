from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from database import get_pg_pool
from services.agent_service import AgentService
from services.elevenlabs_service import ElevenLabsService
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
elevenlabs_service = ElevenLabsService()


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
    Uses production LangGraph agent with memory, personality traits, and voice synthesis
    """
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            # Get session
            session = await conn.fetchrow(
                "SELECT * FROM sessions WHERE id = $1",
                uuid.UUID(session_id)
            )

            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            # Get agent with full contract
            agent = await conn.fetchrow(
                "SELECT * FROM agents WHERE id = $1",
                uuid.UUID(request.agent_id)
            )

            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")

            # Get tenant_id from session or use default
            tenant_id_value = session.get("tenant_id")
            if tenant_id_value is None:
                tenant_id = "00000000-0000-0000-0000-000000000001"
            else:
                tenant_id = str(tenant_id_value)

            # Store user message
            user_message_id = uuid.uuid4()
            user_timestamp = datetime.utcnow()

            # Get agent service and process with production workflow
            agent_service = AgentService()

            # Use process_interaction which invokes LangGraph agent with memory
            result = await agent_service.process_interaction(
                agent_id=request.agent_id,
                tenant_id=tenant_id,
                user_id=request.user_id,
                user_input=request.message,
                thread_id=session_id,  # Use session as thread
                metadata={"session_type": "chat"}
            )

            agent_content = result.get("response", "I'm here to help guide you on your manifestation journey.")

            # Generate voice audio if agent has voice configuration
            audio_url = None
            agent_contract = agent.get("contract", {})
            voice_config = agent_contract.get("voice", {})

            if voice_config and voice_config.get("enabled"):
                try:
                    # Generate TTS audio
                    voice_id = voice_config.get("voice_id")
                    audio_bytes = await elevenlabs_service.generate_speech_with_voice_id(
                        text=agent_content,
                        voice_id=voice_id,
                        model="eleven_turbo_v2"
                    )

                    # Save audio file
                    import os
                    from pathlib import Path

                    audio_dir = Path("backend/audio_files")
                    audio_dir.mkdir(parents=True, exist_ok=True)

                    audio_filename = f"{uuid.uuid4()}.mp3"
                    audio_path = audio_dir / audio_filename

                    with open(audio_path, 'wb') as f:
                        f.write(audio_bytes)

                    audio_url = f"/audio/{audio_filename}"
                    logger.info(f"Generated TTS audio: {audio_url}")

                except Exception as audio_error:
                    logger.warning(f"Failed to generate audio, continuing without: {audio_error}")

            agent_message_id = uuid.uuid4()
            agent_timestamp = datetime.utcnow()

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
                    "audio_url": audio_url
                }
            )

    except Exception as e:
        logger.error(f"Failed to process chat message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """
    Get all messages for a session
    """
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            # Check if messages table exists, if not create it (use thread_messages instead)
            # Note: We actually store messages in thread_messages table, not a separate messages table
            # This query should use thread_messages for consistency
            messages = await conn.fetch(
                """
                SELECT id, role, content, metadata, created_at
                FROM thread_messages
                WHERE thread_id = $1::uuid
                ORDER BY created_at ASC
                """,
                session_id
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
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            affirmations = await conn.fetch(
                """
                SELECT a.*
                FROM affirmations a
                JOIN sessions s ON a.user_id = s.user_id
                WHERE s.agent_id = $1::uuid
                ORDER BY a.created_at DESC
                LIMIT 20
                """,
                agent_id
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
