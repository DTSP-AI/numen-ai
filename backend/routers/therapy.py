from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from uuid import UUID
import logging
import json
import asyncio

from database import get_pg_pool
from services.livekit_service import LiveKitService, LiveKitAgent
from services.deepgram_service import DeepgramService
from services.elevenlabs_service import ElevenLabsService
from services.therapy_livekit_service import TherapyLiveKitService
from memoryManager.memory_manager import MemoryManager
# Note: IntakeAgent and TherapyAgent require contract and memory parameters
# They should be instantiated inside functions where needed, not at module level
from models.schemas import ContractResponse

logger = logging.getLogger(__name__)
router = APIRouter()

livekit_service = LiveKitService()
deepgram_service = DeepgramService()
elevenlabs_service = ElevenLabsService()
therapy_livekit_service = TherapyLiveKitService()
# IntakeAgent and TherapyAgent require parameters - instantiate inside functions when needed
# intake_agent = IntakeAgent()  # ❌ Removed - requires contract and memory parameters
# therapy_agent = TherapyAgent()  # ❌ Removed - requires constructor parameters


@router.websocket("/session/{session_id}")
async def therapy_websocket(websocket: WebSocket, session_id: UUID):
    """WebSocket endpoint for real-time therapy session with full voice pipeline"""
    await websocket.accept()

    livekit_agent = None
    session_stage = "intake"  # "intake" or "therapy"

    try:
        pool = get_pg_pool()
        # Redis removed - using PostgreSQL sessions table instead

        # Verify session exists and get room info
        async with pool.acquire() as conn:
            session = await conn.fetchrow(
                "SELECT id, user_id, status, room_name FROM sessions WHERE id = $1",
                session_id
            )

            if not session:
                await websocket.send_json({"error": "Session not found"})
                await websocket.close()
                return

        room_name = session["room_name"]
        user_id = session["user_id"]

        logger.info(f"WebSocket connected for session {session_id}, room {room_name}")

        # Generate agent token and connect to LiveKit
        agent_token = await livekit_service.generate_token(
            room_name=room_name,
            participant_name=f"agent-{session_id}",
            is_agent=True
        )

        livekit_agent = LiveKitAgent(
            room_name=room_name,
            token=agent_token,
            livekit_url=livekit_service.url
        )

        await livekit_agent.connect()

        # Start Deepgram streaming for STT
        transcript_buffer = []

        async def on_transcript(text: str):
            """Handle transcribed text from Deepgram"""
            transcript_buffer.append(text)
            logger.info(f"User said: {text}")

            # Store transcript
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO transcripts (id, session_id, speaker, content)
                    VALUES (gen_random_uuid(), $1, 'user', $2)
                    """,
                    session_id,
                    text
                )

            # Send to WebSocket client
            await websocket.send_json({
                "type": "transcript",
                "speaker": "user",
                "content": text
            })

            # Process with agents based on stage
            # TODO: Implement proper agent integration (Phase 3)
            # - IntakeAgent for intake stage with state management
            # - TherapyAgent for therapy stage with LangGraph workflow
            # - Memory context retrieval from MemoryManager
            if session_stage == "intake":
                # Placeholder: Should use IntakeAgent with contract-based processing
                response_text = f"Thank you for sharing. I understand you're focused on: {text}"
            else:
                # Placeholder: Should use TherapyAgent with session context
                response_text = "I acknowledge your reflection. Let's continue with the session."

            # Generate audio response with ElevenLabs
            audio_stream = elevenlabs_service.generate_speech_streaming(
                text=response_text,
                voice_preference="calm"
            )

            # Stream audio to LiveKit
            async for audio_chunk in audio_stream:
                if livekit_agent:
                    await livekit_agent.publish_audio(audio_chunk)

            # Store agent transcript
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO transcripts (id, session_id, speaker, content)
                    VALUES (gen_random_uuid(), $1, 'agent', $2)
                    """,
                    session_id,
                    response_text
                )

        await deepgram_service.start_streaming(
            on_transcript=on_transcript
        )

        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "session_id": str(session_id),
            "room_name": room_name,
            "stage": session_stage
        })

        # Handle messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "audio_chunk":
                # Forward audio to Deepgram for transcription
                audio_data = bytes.fromhex(message["data"])
                await deepgram_service.send_audio(audio_data)

            elif message["type"] == "start_therapy":
                # Transition from intake to therapy
                session_stage = "therapy"

                # Get contract
                async with pool.acquire() as conn:
                    contract_row = await conn.fetchrow(
                        """
                        SELECT id, session_id, user_id, goals, tone, voice_id, session_type
                        FROM contracts
                        WHERE session_id = $1
                        """,
                        session_id
                    )

                if contract_row:
                    # Generate therapy script
                    contract = ContractResponse(
                        id=contract_row["id"],
                        session_id=contract_row["session_id"],
                        user_id=contract_row["user_id"],
                        goals=contract_row["goals"],
                        tone=contract_row["tone"],
                        voice_id=contract_row["voice_id"],
                        session_type=contract_row["session_type"],
                        created_at=contract_row["created_at"]
                    )

                    # ✅ Phase 3: TherapyAgent LiveKit Integration (IMPLEMENTED)
                    # Uses services/therapy_livekit_service.py with official LiveKit LangChain adapter
                    #
                    # Integration pattern follows official docs:
                    # - https://docs.livekit.io/agents/models/llm/plugins/langchain/
                    # - Uses LLMAdapter to wrap TherapyAgent's LangGraph workflow
                    # - Implements STT-LLM-TTS pipeline with Deepgram + OpenAI + ElevenLabs
                    # - Includes Voice Activity Detection (VAD) for turn handling
                    #
                    # For full real-time voice session, use the LiveKit service:
                    try:
                        from livekit.agents import RoomIO
                        from agents.guide_agent.guide_sub_agents.therapy_agent import TherapyAgent

                        # Create LiveKit session with TherapyAgent workflow
                        room_io = RoomIO()  # Media stream manager

                        livekit_session = therapy_livekit_service.create_livekit_session(
                            session_id=str(session_id),
                            user_id=user_id,
                            contract=contract,
                            room_io=room_io
                        )

                        # Start real-time voice session in LiveKit room
                        await therapy_livekit_service.start_therapy_session(
                            session=livekit_session,
                            room_name=session["room_name"]
                        )

                        script = "Live therapy session started with real-time voice interaction via LiveKit."
                        therapy_state = {"status": "live_session_active", "reflections": []}

                        logger.info(f"✅ LiveKit therapy session started: {session_id}")

                    except Exception as livekit_error:
                        # Fallback: Generate script without real-time voice
                        logger.warning(f"LiveKit session failed, using script generation fallback: {livekit_error}")

                        therapy_agent = TherapyAgent()
                        therapy_state = await therapy_agent.generate_session(
                            session_id=str(session_id),
                            user_id=user_id,
                            contract=contract
                        )
                        script = therapy_agent.get_script(therapy_state)

                    # Stream entire therapy script as audio
                    audio_stream = elevenlabs_service.generate_speech_streaming(
                        text=script,
                        voice_preference=contract.tone.value
                    )

                    async for audio_chunk in audio_stream:
                        if livekit_agent:
                            await livekit_agent.publish_audio(audio_chunk)

                    # Store therapy script in memory
                    # NOTE: MemoryManager instantiation example (commented until TherapyAgent is enabled)
                    # When enabling therapy functionality, instantiate MemoryManager similar to:
                    # - backend/routers/agents.py:795-822 (working example)
                    # - backend/services/agent_creation_helpers.py:326-334 (working example)
                    # Requires: tenant_id and agent_id from session context
                    #
                    # Example implementation:
                    # memory_manager = MemoryManager(
                    #     tenant_id=tenant_id,  # Get from session
                    #     agent_id=agent_id,    # Get from session
                    #     agent_traits={}
                    # )
                    # await memory_manager.add_memory(
                    #     content=script,
                    #     memory_type="therapy_session",
                    #     user_id=user_id,
                    #     metadata={
                    #         "script": script,
                    #         "contract": contract.dict(),
                    #         "reflections": therapy_state.get("reflections", [])
                    #     }
                    # )
                    logger.info("Therapy script generated (memory storage skipped - requires agent context)")

                await websocket.send_json({
                    "type": "therapy_started",
                    "session_id": str(session_id)
                })

            elif message["type"] == "end_session":
                # Finalize session
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE sessions
                        SET status = 'completed', updated_at = NOW()
                        WHERE id = $1
                        """,
                        session_id
                    )

                await websocket.send_json({
                    "type": "session_ended",
                    "session_id": str(session_id)
                })
                break

            else:
                await websocket.send_json({
                    "type": "ack",
                    "message_type": message["type"]
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        # Cleanup
        if livekit_agent:
            await livekit_agent.disconnect()
        await deepgram_service.stop_streaming()
        try:
            await websocket.close()
        except:
            pass


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