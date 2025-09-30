from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from typing import TypedDict, List, Optional
import logging

from models.schemas import IntakeState, TonePreference, SessionType, ContractCreate
from config import settings

logger = logging.getLogger(__name__)


class IntakeAgentState(TypedDict):
    """State for IntakeAgent graph"""
    session_id: str
    user_id: str
    messages: List[dict]
    goals: List[str]
    tone: Optional[str]
    voice_id: Optional[str]
    session_type: Optional[str]
    stage: str  # "greeting", "goals", "preferences", "confirmation", "complete"
    contract_ready: bool


class IntakeAgent:
    """
    IntakeAgent collects user goals, tone preferences, and voice selection.
    Outputs a JSON contract for TherapyAgent consumption.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(IntakeAgentState)

        # Define nodes
        workflow.add_node("greeting", self._greeting_node)
        workflow.add_node("collect_goals", self._collect_goals_node)
        workflow.add_node("collect_preferences", self._collect_preferences_node)
        workflow.add_node("confirm_contract", self._confirm_contract_node)
        workflow.add_node("generate_contract", self._generate_contract_node)

        # Define edges
        workflow.set_entry_point("greeting")
        workflow.add_edge("greeting", "collect_goals")
        workflow.add_edge("collect_goals", "collect_preferences")
        workflow.add_edge("collect_preferences", "confirm_contract")
        workflow.add_conditional_edges(
            "confirm_contract",
            self._should_continue,
            {
                "generate": "generate_contract",
                "retry": "collect_goals"
            }
        )
        workflow.add_edge("generate_contract", END)

        return workflow.compile()

    def _greeting_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """Initial greeting and purpose explanation"""
        greeting_message = (
            "Welcome to your personalized hypnotherapy session. "
            "I'm here to understand your goals and create a therapeutic experience "
            "tailored just for you. Let's begin by exploring what you'd like to achieve today."
        )

        state["messages"].append({
            "role": "agent",
            "content": greeting_message
        })
        state["stage"] = "goals"

        logger.info(f"IntakeAgent: Greeting sent for session {state['session_id']}")
        return state

    def _collect_goals_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """Collect and clarify user goals"""
        if len(state["goals"]) == 0:
            prompt = "What would you like to work on in this session? For example, building confidence, reducing anxiety, or manifesting specific goals."
        else:
            prompt = "Is there anything else you'd like to add to your goals?"

        state["messages"].append({
            "role": "agent",
            "content": prompt
        })
        state["stage"] = "goals"

        return state

    def _collect_preferences_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """Collect tone and voice preferences"""
        prompt = (
            "Great! Now, let's personalize your experience. "
            "What kind of tone would you prefer? "
            f"Options: {', '.join([t.value for t in TonePreference])}. "
            "And which voice style resonates with you?"
        )

        state["messages"].append({
            "role": "agent",
            "content": prompt
        })
        state["stage"] = "preferences"

        return state

    def _confirm_contract_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """Confirm collected information"""
        summary = f"""
Let me confirm what we've discussed:

Goals: {', '.join(state['goals'])}
Tone: {state.get('tone', 'Not specified')}
Voice: {state.get('voice_id', 'Not specified')}
Session Type: {state.get('session_type', 'General hypnotherapy')}

Does this look correct? If you'd like to make any changes, let me know!
"""

        state["messages"].append({
            "role": "agent",
            "content": summary
        })
        state["stage"] = "confirmation"

        return state

    def _generate_contract_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """Generate final contract JSON"""
        state["contract_ready"] = True
        state["stage"] = "complete"

        logger.info(f"IntakeAgent: Contract generated for session {state['session_id']}")
        return state

    def _should_continue(self, state: IntakeAgentState) -> str:
        """Decide whether to generate contract or retry collection"""
        # Check if we have all required information
        has_goals = len(state["goals"]) > 0
        has_tone = state["tone"] is not None
        has_voice = state["voice_id"] is not None
        has_session_type = state["session_type"] is not None

        if state["stage"] == "confirmation" and has_goals and has_tone and has_voice and has_session_type:
            return "generate"
        return "retry"

    async def process_message(
        self,
        session_id: str,
        user_id: str,
        message: str,
        current_state: Optional[IntakeAgentState] = None
    ) -> IntakeAgentState:
        """Process user message and return updated state"""
        if current_state is None:
            current_state = {
                "session_id": session_id,
                "user_id": user_id,
                "messages": [],
                "goals": [],
                "tone": None,
                "voice_id": None,
                "session_type": None,
                "stage": "greeting",
                "contract_ready": False
            }

        # Add user message
        current_state["messages"].append({
            "role": "user",
            "content": message
        })

        # Run graph
        result = await self.graph.ainvoke(current_state)

        return result

    def extract_contract(self, state: IntakeAgentState) -> ContractCreate:
        """Extract ContractCreate model from state"""
        return ContractCreate(
            session_id=state["session_id"],
            user_id=state["user_id"],
            goals=state["goals"],
            tone=TonePreference(state["tone"]) if state["tone"] else TonePreference.CALM,
            voice_id=state["voice_id"] or "default",
            session_type=SessionType(state["session_type"]) if state["session_type"] else SessionType.MANIFESTATION
        )