"""
TherapyAgent LiveKit Integration Service

Integrates TherapyAgent LangGraph workflow with LiveKit Agents framework
for real-time voice therapy sessions.

Based on official LiveKit documentation:
- https://docs.livekit.io/agents/models/llm/plugins/langchain/
- https://docs.livekit.io/agents/build/

References:
- Goal Attainment Scaling: https://www.physio-pedia.com/Goal_Attainment_Scaling
- LiveKit Agents: https://docs.livekit.io/agents/
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID

from livekit.agents import AgentSession, Agent, RoomIO
from livekit.plugins import langchain, deepgram, elevenlabs, silero
from langgraph.graph import StateGraph

from agents.guide_agent.guide_sub_agents.therapy_agent import TherapyAgent, TherapyAgentState
from models.schemas import ContractResponse
from config import settings

logger = logging.getLogger(__name__)


class TherapyLiveKitService:
    """
    Service for managing LiveKit voice sessions with TherapyAgent.

    Wraps TherapyAgent's LangGraph workflow with LiveKit's LLMAdapter
    to enable real-time voice interaction following official LiveKit patterns.
    """

    def __init__(self):
        """Initialize TherapyAgent and LiveKit components"""
        self.therapy_agent = TherapyAgent()

    def create_livekit_session(
        self,
        session_id: str,
        user_id: str,
        contract: ContractResponse,
        room_io: RoomIO
    ) -> AgentSession:
        """
        Create LiveKit AgentSession with TherapyAgent LangGraph workflow.

        Follows official LiveKit LangChain integration pattern:
        https://docs.livekit.io/agents/models/llm/plugins/langchain/

        Args:
            session_id: Therapy session UUID
            user_id: User UUID
            contract: IntakeContract with therapy goals and preferences
            room_io: LiveKit RoomIO for media stream management

        Returns:
            Configured AgentSession ready for voice interaction
        """
        logger.info(f"Creating LiveKit session for therapy session {session_id}")

        # Wrap TherapyAgent's compiled LangGraph workflow with LLMAdapter
        # This allows LiveKit to use the existing therapy workflow as the LLM
        llm_adapter = langchain.LLMAdapter(
            graph=self.therapy_agent.graph,
            # The adapter automatically converts LiveKit chat context to LangChain messages:
            # - system/developer → SystemMessage
            # - user → HumanMessage
            # - assistant → AIMessage
        )

        # Configure STT (Speech-to-Text)
        # Using Deepgram as specified in requirements
        stt = deepgram.STT(
            api_key=settings.deepgram_api_key,
            model="nova-2",  # Deepgram's latest model
            language="en",
            interim_results=True  # Enable real-time transcription
        )

        # Configure TTS (Text-to-Speech)
        # Using ElevenLabs as specified in requirements
        tts = elevenlabs.TTS(
            api_key=settings.elevenlabs_api_key,
            voice_id=contract.voice_id,  # Use agent's configured voice
            model_id="eleven_turbo_v2_5",  # Fast, low-latency model
            stability=0.75,
            similarity_boost=0.75
        )

        # Configure VAD (Voice Activity Detection)
        # Using Silero VAD for reliable turn detection
        vad = silero.VAD.load()

        # Create AgentSession with therapy workflow
        # Following official LiveKit build guide:
        # https://docs.livekit.io/agents/build/
        session = AgentSession(
            llm=llm_adapter,  # TherapyAgent's LangGraph workflow wrapped as LLM
            stt=stt,          # Deepgram speech-to-text
            tts=tts,          # ElevenLabs text-to-speech
            vad=vad,          # Silero voice activity detection
            turn_detection="server_side",  # Server handles turn detection
            interruption_handling=True,  # Allow user to interrupt agent
            room_io=room_io   # Media stream manager
        )

        # Create Agent with therapy instructions
        agent = Agent(
            instructions=self._build_therapy_instructions(contract),
            tools=[],  # Therapy agent doesn't need external tools
            session=session
        )

        logger.info(f"✅ LiveKit session created for therapy {session_id}")
        return session

    def _build_therapy_instructions(self, contract: ContractResponse) -> str:
        """
        Build system instructions for the therapy agent.

        These instructions guide the LangGraph workflow through the
        therapy session stages: induction, deepening, therapy, emergence.

        Args:
            contract: IntakeContract with goals and preferences

        Returns:
            System instruction string for the agent
        """
        goals_text = ', '.join(contract.goals)

        instructions = f"""You are an expert hypnotherapist conducting a personalized therapy session.

**Session Configuration:**
- Goals: {goals_text}
- Tone: {contract.tone.value}
- Session Type: {contract.session_type.value}

**Session Structure:**
You will guide the client through these stages:
1. **Induction**: Establish rapport and guide progressive relaxation
2. **Deepening**: Deepen the hypnotic state using visualization
3. **Therapy**: Address the client's goals with affirmations and therapeutic techniques
4. **Emergence**: Gradually bring the client back to full awareness

**Guidelines:**
- Use a {contract.tone.value} tone throughout
- Speak clearly and calmly
- Allow natural pauses for the client to process
- Respond to client feedback if they interrupt
- Maintain therapeutic boundaries

**Goal Attainment Tracking:**
The session uses Goal Attainment Scaling (GAS) where:
- Baseline (-2): Current state
- Expected (0): Goal achievement
- Optimal (+2): Beyond expectations

Your role is to guide the client from baseline towards their goals using evidence-based hypnotherapy techniques.
"""
        return instructions

    async def start_therapy_session(
        self,
        session: AgentSession,
        room_name: str
    ) -> None:
        """
        Start the LiveKit therapy session in a room.

        Args:
            session: Configured AgentSession
            room_name: LiveKit room name
        """
        try:
            logger.info(f"Starting therapy session in room: {room_name}")

            # Connect to LiveKit room and start session
            # The framework automatically handles:
            # - User speech → STT → LangGraph workflow → TTS → Audio output
            # - Interruption handling
            # - Turn detection
            # - Audio streaming
            await session.start(room_name)

            logger.info(f"✅ Therapy session started in room: {room_name}")

        except Exception as e:
            logger.error(f"Failed to start therapy session: {e}", exc_info=True)
            raise

    async def end_therapy_session(
        self,
        session: AgentSession
    ) -> Dict[str, Any]:
        """
        End the therapy session and retrieve session data.

        Args:
            session: Active AgentSession

        Returns:
            Session summary with transcripts and reflections
        """
        try:
            logger.info("Ending therapy session")

            # Stop the session
            await session.stop()

            # Extract session data
            # The LangGraph workflow state contains the full therapy script
            # and reflections generated during the session
            session_data = {
                "status": "completed",
                "transcript": session.transcript if hasattr(session, 'transcript') else None,
                "duration_seconds": session.duration if hasattr(session, 'duration') else None
            }

            logger.info(f"✅ Therapy session ended: {session_data['status']}")
            return session_data

        except Exception as e:
            logger.error(f"Failed to end therapy session: {e}", exc_info=True)
            raise


# Usage Example (for reference):
#
# ```python
# from services.therapy_livekit_service import TherapyLiveKitService
# from livekit.agents import RoomIO
#
# # Initialize service
# therapy_service = TherapyLiveKitService()
#
# # Create room I/O
# room_io = RoomIO()
#
# # Create session
# session = therapy_service.create_livekit_session(
#     session_id="uuid-here",
#     user_id="user-uuid",
#     contract=intake_contract,
#     room_io=room_io
# )
#
# # Start session in LiveKit room
# await therapy_service.start_therapy_session(
#     session=session,
#     room_name="therapy-room-123"
# )
#
# # Session runs...
#
# # End session
# summary = await therapy_service.end_therapy_session(session)
# ```
