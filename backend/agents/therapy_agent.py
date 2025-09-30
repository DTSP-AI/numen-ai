from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import TypedDict, List, Optional
import logging

from models.schemas import ContractResponse, TherapyState, TonePreference, SessionType
from config import settings

logger = logging.getLogger(__name__)


class TherapyAgentState(TypedDict):
    """State for TherapyAgent graph"""
    session_id: str
    user_id: str
    contract: dict
    script: Optional[str]
    current_section: str
    audio_generated: bool
    reflections: List[str]


class TherapyAgent:
    """
    TherapyAgent consumes the contract from IntakeAgent and generates
    personalized hypnotherapy scripts with real-time audio streaming.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.8,
            openai_api_key=settings.openai_api_key
        )
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(TherapyAgentState)

        # Define nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("generate_induction", self._generate_induction_node)
        workflow.add_node("generate_deepening", self._generate_deepening_node)
        workflow.add_node("generate_therapy", self._generate_therapy_node)
        workflow.add_node("generate_emergence", self._generate_emergence_node)
        workflow.add_node("generate_reflection", self._generate_reflection_node)

        # Define edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "generate_induction")
        workflow.add_edge("generate_induction", "generate_deepening")
        workflow.add_edge("generate_deepening", "generate_therapy")
        workflow.add_edge("generate_therapy", "generate_emergence")
        workflow.add_edge("generate_emergence", "generate_reflection")
        workflow.add_edge("generate_reflection", END)

        return workflow.compile()

    def _initialize_node(self, state: TherapyAgentState) -> TherapyAgentState:
        """Initialize therapy session"""
        state["script"] = ""
        state["current_section"] = "induction"
        state["audio_generated"] = False

        logger.info(f"TherapyAgent: Initialized session {state['session_id']}")
        return state

    def _generate_induction_node(self, state: TherapyAgentState) -> TherapyAgentState:
        """Generate hypnotic induction script"""
        contract = state["contract"]
        tone = contract.get("tone", "calm")

        system_prompt = f"""You are an expert hypnotherapist creating a personalized induction script.

Tone: {tone}
Session Type: {contract.get('session_type', 'general')}

Generate a 2-3 minute hypnotic induction that:
1. Establishes rapport and safety
2. Guides progressive relaxation
3. Uses the {tone} tone throughout
4. Prepares for deepening

Write ONLY the script text that will be spoken. No meta-commentary."""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Generate the induction script.")
        ])

        induction_script = response.content
        state["script"] += f"\n\n=== INDUCTION ===\n{induction_script}"
        state["current_section"] = "deepening"

        logger.info(f"TherapyAgent: Induction generated for session {state['session_id']}")
        return state

    def _generate_deepening_node(self, state: TherapyAgentState) -> TherapyAgentState:
        """Generate deepening script"""
        contract = state["contract"]

        system_prompt = """You are an expert hypnotherapist creating a deepening script.

Generate a 1-2 minute deepening script that:
1. Deepens the hypnotic state
2. Uses counting or visualization techniques
3. Prepares the client for therapeutic work

Write ONLY the script text that will be spoken."""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Generate the deepening script.")
        ])

        deepening_script = response.content
        state["script"] += f"\n\n=== DEEPENING ===\n{deepening_script}"
        state["current_section"] = "therapy"

        return state

    def _generate_therapy_node(self, state: TherapyAgentState) -> TherapyAgentState:
        """Generate main therapeutic content"""
        contract = state["contract"]
        goals = contract.get("goals", [])
        session_type = contract.get("session_type", "general")

        system_prompt = f"""You are an expert hypnotherapist creating the main therapeutic script.

Client Goals: {', '.join(goals)}
Session Type: {session_type}

Generate a 5-7 minute therapeutic script that:
1. Addresses each goal directly
2. Uses positive affirmations and visualization
3. Incorporates therapeutic techniques for {session_type}
4. Builds confidence and empowerment

Write ONLY the script text that will be spoken."""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Generate the therapeutic script.")
        ])

        therapy_script = response.content
        state["script"] += f"\n\n=== THERAPY ===\n{therapy_script}"
        state["current_section"] = "emergence"

        logger.info(f"TherapyAgent: Therapy script generated for session {state['session_id']}")
        return state

    def _generate_emergence_node(self, state: TherapyAgentState) -> TherapyAgentState:
        """Generate emergence script"""
        system_prompt = """You are an expert hypnotherapist creating an emergence script.

Generate a 1-2 minute emergence script that:
1. Gradually brings the client back to full awareness
2. Reinforces positive suggestions
3. Ensures the client feels refreshed and alert
4. Provides post-hypnotic suggestions

Write ONLY the script text that will be spoken."""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Generate the emergence script.")
        ])

        emergence_script = response.content
        state["script"] += f"\n\n=== EMERGENCE ===\n{emergence_script}"
        state["current_section"] = "reflection"

        return state

    def _generate_reflection_node(self, state: TherapyAgentState) -> TherapyAgentState:
        """Generate session reflection for memory storage"""
        contract = state["contract"]

        reflection = f"""
Session Reflection:
- Goals addressed: {', '.join(contract.get('goals', []))}
- Session type: {contract.get('session_type', 'general')}
- Tone used: {contract.get('tone', 'calm')}
- Script sections completed: induction, deepening, therapy, emergence
"""

        state["reflections"].append(reflection)
        state["audio_generated"] = True

        logger.info(f"TherapyAgent: Reflection generated for session {state['session_id']}")
        return state

    async def generate_session(
        self,
        session_id: str,
        user_id: str,
        contract: ContractResponse
    ) -> TherapyAgentState:
        """Generate complete therapy session from contract"""
        initial_state = {
            "session_id": session_id,
            "user_id": user_id,
            "contract": {
                "goals": contract.goals,
                "tone": contract.tone.value,
                "voice_id": contract.voice_id,
                "session_type": contract.session_type.value
            },
            "script": None,
            "current_section": "initialize",
            "audio_generated": False,
            "reflections": []
        }

        result = await self.graph.ainvoke(initial_state)

        return result

    def get_script(self, state: TherapyAgentState) -> str:
        """Extract generated script"""
        return state.get("script", "")