"""
IntakeAgent V2 - Contract-First Implementation

Role: Prompt Engineer
Mission: Convert user discovery data → JSON contract that creates AffirmationAgent

This is the refactored IntakeAgent that:
1. Loads its OWN behavior from AgentContract
2. Collects user discovery data (goals, limiting beliefs, outcomes, schedule)
3. OUTPUTS a complete AgentContract JSON for AffirmationAgent
4. Stores discovery data in user_discovery table

This fulfills the Numen AI pipeline requirement.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from models.agent import (
    AgentContract,
    AgentIdentity,
    AgentTraits,
    AgentConfiguration,
    VoiceConfiguration,
    AgentMetadata,
    AgentType,
    AgentStatus
)
from services.unified_memory_manager import UnifiedMemoryManager
from database import get_pg_pool

logger = logging.getLogger(__name__)


# ============================================================================
# STATE MODELS
# ============================================================================

class DiscoveryData(BaseModel):
    """User discovery data collected by IntakeAgent"""
    goals: List[str] = Field(default_factory=list, description="Primary goals")
    limiting_beliefs: List[str] = Field(default_factory=list, description="Identified limiting beliefs")
    desired_outcomes: List[str] = Field(default_factory=list, description="Specific desired outcomes")
    tone_preference: Optional[str] = Field(None, description="Preferred tone (calm, energetic, empowering)")
    voice_preference: Optional[str] = Field(None, description="Preferred voice type")
    schedule_preference: Optional[str] = Field(None, description="Morning, evening, or both")
    timeframe: Optional[str] = Field(None, description="7_days, 30_days, 90_days")
    commitment_level: Optional[str] = Field(None, description="light, moderate, intensive")


class IntakeAgentState(BaseModel):
    """State for IntakeAgent V2 graph"""
    session_id: str
    user_id: str
    tenant_id: str
    messages: List[Dict[str, str]] = Field(default_factory=list)

    # Discovery data
    discovery: DiscoveryData = Field(default_factory=DiscoveryData)

    # Flow control
    stage: str = "greeting"  # greeting, goals, beliefs, outcomes, preferences, confirmation, complete
    contract_generated: bool = False
    affirmation_agent_contract: Optional[Dict[str, Any]] = None


# ============================================================================
# INTAKE AGENT V2 (CONTRACT-FIRST)
# ============================================================================

class IntakeAgentV2:
    """
    Contract-First IntakeAgent

    Loads behavior from AgentContract JSON.
    Outputs AffirmationAgent contract.
    """

    def __init__(
        self,
        contract: AgentContract,
        memory: UnifiedMemoryManager
    ):
        """
        Initialize from contract (Agent Creation Standard)

        Args:
            contract: Agent JSON contract defining behavior
            memory: Memory manager for this agent
        """
        self.contract = contract
        self.memory = memory

        # Initialize LLM from contract configuration
        import os
        from config import settings
        self.llm = ChatOpenAI(
            model=contract.configuration.llm_model,
            temperature=contract.configuration.temperature,
            max_tokens=contract.configuration.max_tokens,
            openai_api_key=settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        )

        # Build LangGraph workflow
        self.graph = self._build_graph()

        logger.info(f"✅ IntakeAgentV2 initialized: {contract.name}")

    def _build_graph(self) -> StateGraph:
        """Build discovery workflow graph"""
        workflow = StateGraph(IntakeAgentState)

        # Define nodes
        workflow.add_node("greeting", self._greeting_node)
        workflow.add_node("collect_goals", self._collect_goals_node)
        workflow.add_node("collect_beliefs", self._collect_beliefs_node)
        workflow.add_node("collect_outcomes", self._collect_outcomes_node)
        workflow.add_node("collect_preferences", self._collect_preferences_node)
        workflow.add_node("confirm_discovery", self._confirm_discovery_node)
        workflow.add_node("generate_affirmation_agent", self._generate_affirmation_agent_node)

        # Define edges
        workflow.set_entry_point("greeting")
        workflow.add_edge("greeting", "collect_goals")
        workflow.add_edge("collect_goals", "collect_beliefs")
        workflow.add_edge("collect_beliefs", "collect_outcomes")
        workflow.add_edge("collect_outcomes", "collect_preferences")
        workflow.add_edge("collect_preferences", "confirm_discovery")

        workflow.add_conditional_edges(
            "confirm_discovery",
            self._should_generate_contract,
            {
                "generate": "generate_affirmation_agent",
                "retry": "collect_goals"
            }
        )

        workflow.add_edge("generate_affirmation_agent", END)

        return workflow.compile()

    def _greeting_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """Initial greeting using agent's personality"""

        # Use contract identity to shape greeting
        greeting = f"""Welcome! I'm {self.contract.name}.

{self.contract.identity.short_description}

{self.contract.identity.mission}

I'm here to understand your goals and create a personalized journey for you. Let's begin by exploring what you want to manifest in your life."""

        state.messages.append({
            "role": "assistant",
            "content": greeting
        })
        state.stage = "goals"

        logger.info(f"IntakeAgentV2: Greeting sent for session {state.session_id}")
        return state

    def _collect_goals_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """Collect primary goals"""

        if len(state.discovery.goals) == 0:
            prompt = """What are your primary goals? What would you like to manifest or achieve?

For example:
- Financial abundance
- Career advancement
- Confidence in relationships
- Inner peace and clarity
- Physical health transformation

Share as many goals as feel important to you."""
        else:
            prompt = "Would you like to add any other goals, or shall we continue?"

        state.messages.append({
            "role": "assistant",
            "content": prompt
        })
        state.stage = "goals"

        return state

    def _collect_beliefs_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """Identify limiting beliefs"""

        prompt = f"""Thank you for sharing your goals: {', '.join(state.discovery.goals)}

Now, let's identify any limiting beliefs that might be holding you back. These are thoughts or beliefs that create resistance.

For example:
- "Money is hard to earn"
- "I'm not confident enough"
- "Success requires sacrifice"

What beliefs or thoughts might be blocking your path?"""

        state.messages.append({
            "role": "assistant",
            "content": prompt
        })
        state.stage = "beliefs"

        return state

    def _collect_outcomes_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """Collect specific desired outcomes"""

        prompt = """Excellent. Now let's get specific about your desired outcomes.

What does success look like? Be as specific as possible.

For example:
- "Earning $100k by year-end"
- "Speaking confidently at my next presentation"
- "Waking up feeling energized every day"

What specific outcomes do you want to manifest?"""

        state.messages.append({
            "role": "assistant",
            "content": prompt
        })
        state.stage = "outcomes"

        return state

    def _collect_preferences_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """Collect preferences for affirmation experience"""

        prompt = """Perfect! Now let's personalize your experience.

1. **Tone**: Would you prefer a calm, energetic, or empowering tone?
2. **Voice**: What type of voice resonates with you? (warm female, confident male, soothing neutral)
3. **Schedule**: When would you like your affirmations? (morning, evening, both)
4. **Timeframe**: What timeframe are you working with? (7 days, 30 days, 90 days)
5. **Commitment**: How much time can you dedicate daily? (light: 15-30 min, moderate: 30-60 min, intensive: 1-2 hours)"""

        state.messages.append({
            "role": "assistant",
            "content": prompt
        })
        state.stage = "preferences"

        return state

    def _confirm_discovery_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """Confirm all collected discovery data"""

        summary = f"""Let me confirm what we've discovered:

**Your Goals:**
{chr(10).join(f'• {goal}' for goal in state.discovery.goals)}

**Limiting Beliefs to Transform:**
{chr(10).join(f'• {belief}' for belief in state.discovery.limiting_beliefs)}

**Desired Outcomes:**
{chr(10).join(f'• {outcome}' for outcome in state.discovery.desired_outcomes)}

**Your Preferences:**
• Tone: {state.discovery.tone_preference or 'Not specified'}
• Voice: {state.discovery.voice_preference or 'Not specified'}
• Schedule: {state.discovery.schedule_preference or 'Not specified'}
• Timeframe: {state.discovery.timeframe or 'Not specified'}
• Commitment: {state.discovery.commitment_level or 'Not specified'}

Does this look correct? If yes, I'll create your personalized Affirmation Agent now!"""

        state.messages.append({
            "role": "assistant",
            "content": summary
        })
        state.stage = "confirmation"

        return state

    def _generate_affirmation_agent_node(self, state: IntakeAgentState) -> IntakeAgentState:
        """
        CORE NUMEN AI FUNCTION

        Generate AffirmationAgent JSON contract from discovery data.
        This is where IntakeAgent becomes a Prompt Engineer.
        """

        discovery = state.discovery

        # Use LLM to engineer optimal agent traits based on discovery
        system_prompt = f"""You are an expert AI agent designer specializing in manifestation and affirmation coaching.

Your task is to analyze user discovery data and output optimal personality traits (0-100 scale) for an AffirmationAgent.

User Discovery Data:
- Goals: {', '.join(discovery.goals)}
- Limiting Beliefs: {', '.join(discovery.limiting_beliefs)}
- Desired Outcomes: {', '.join(discovery.desired_outcomes)}
- Tone Preference: {discovery.tone_preference}

Output a JSON object with these exact keys (0-100 integer values):
{{
    "creativity": <value>,
    "empathy": <value>,
    "assertiveness": <value>,
    "humor": <value>,
    "formality": <value>,
    "verbosity": <value>,
    "confidence": <value>,
    "technicality": <value>,
    "safety": <value>
}}

Guidelines:
- High empathy for emotional goals
- High confidence for confidence/assertiveness goals
- High creativity for manifestation/visualization
- Low formality for relaxed, accessible communication
- Moderate to high verbosity for detailed affirmations
"""

        try:
            # Generate traits via LLM
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate optimal traits for this AffirmationAgent.")
            ])

            traits_data = json.loads(response.content)

        except Exception as e:
            logger.warning(f"LLM trait generation failed, using defaults: {e}")
            # Fallback to intelligent defaults
            traits_data = {
                "creativity": 80,
                "empathy": 95,
                "assertiveness": 70,
                "humor": 40,
                "formality": 30,
                "verbosity": 70,
                "confidence": 85,
                "technicality": 30,
                "safety": 90
            }

        # Build AffirmationAgent contract
        affirmation_agent_contract = AgentContract(
            id=str(uuid.uuid4()),
            name=f"Affirmation Guide - {discovery.goals[0] if discovery.goals else 'Personal Growth'}",
            type=AgentType.VOICE if discovery.voice_preference else AgentType.CONVERSATIONAL,

            identity=AgentIdentity(
                short_description=f"Personalized guide for {', '.join(discovery.goals[:2])}",
                full_description=f"A compassionate, empowering guide specialized in helping you manifest {', '.join(discovery.goals)}. Expertly crafted to transform limiting beliefs and align your subconscious with your desired outcomes.",
                character_role="Empowering Manifestation Guide",
                mission=f"Help {state.user_id} manifest: {', '.join(discovery.goals)}",
                interaction_style=f"{discovery.tone_preference or 'Empowering'}, supportive, and deeply aligned with manifestation principles"
            ),

            traits=AgentTraits(**traits_data),

            configuration=AgentConfiguration(
                llm_provider="openai",
                llm_model="gpt-4",
                max_tokens=1000,
                temperature=0.8,
                memory_enabled=True,
                voice_enabled=bool(discovery.voice_preference),
                tools_enabled=False
            ),

            voice=VoiceConfiguration(
                provider="elevenlabs",
                voice_id=self._map_voice_preference(discovery.voice_preference),
                language="en-US",
                speed=0.95,
                stability=0.75,
                similarity_boost=0.75,
                stt_provider="deepgram",
                stt_model="nova-2"
            ) if discovery.voice_preference else None,

            metadata=AgentMetadata(
                tenant_id=state.tenant_id,
                owner_id=state.user_id,
                tags=["affirmation", "manifestation", "auto-generated"],
                status=AgentStatus.ACTIVE
            )
        )

        # Store contract in state
        state.affirmation_agent_contract = affirmation_agent_contract.model_dump()
        state.contract_generated = True
        state.stage = "complete"

        # Confirmation message
        state.messages.append({
            "role": "assistant",
            "content": f"""✨ Your personalized Affirmation Agent has been created!

**Agent Name:** {affirmation_agent_contract.name}
**Personality Traits:** Empathy {traits_data['empathy']}/100, Confidence {traits_data['confidence']}/100, Creativity {traits_data['creativity']}/100

Your agent is now ready to generate personalized affirmations, mantras, and hypnosis scripts aligned with your goals.

Would you like to start your first session?"""
        })

        logger.info(f"✅ AffirmationAgent contract generated for user {state.user_id}")

        return state

    def _should_generate_contract(self, state: IntakeAgentState) -> str:
        """Decide whether to generate contract or retry"""

        # Check completeness
        has_goals = len(state.discovery.goals) > 0
        has_beliefs = len(state.discovery.limiting_beliefs) > 0
        has_outcomes = len(state.discovery.desired_outcomes) > 0
        has_preferences = bool(state.discovery.tone_preference)

        if state.stage == "confirmation" and has_goals and has_outcomes:
            return "generate"

        return "retry"

    def _map_voice_preference(self, preference: Optional[str]) -> str:
        """Map user voice preference to ElevenLabs voice ID"""
        voice_map = {
            "warm female": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "confident male": "pNInz6obpgDQGcFmaJgB",  # Adam
            "soothing neutral": "EXAVITQu4vr4xnSDxMaL",  # Bella
            "empowering female": "ThT5KcBeYPX3keUQqHPh"  # Dorothy
        }
        return voice_map.get(preference, "21m00Tcm4TlvDq8ikWAM")  # Default Rachel

    async def process_message(
        self,
        session_id: str,
        user_id: str,
        tenant_id: str,
        message: str,
        current_state: Optional[IntakeAgentState] = None
    ) -> IntakeAgentState:
        """
        Process user message through graph

        Returns updated state with next agent response
        """

        if current_state is None:
            current_state = IntakeAgentState(
                session_id=session_id,
                user_id=user_id,
                tenant_id=tenant_id
            )

        # Add user message
        current_state.messages.append({
            "role": "user",
            "content": message
        })

        # Parse message to extract discovery data
        await self._extract_discovery_data(message, current_state)

        # Run graph
        result = await self.graph.ainvoke(current_state.model_dump())

        return IntakeAgentState(**result)

    async def _extract_discovery_data(self, message: str, state: IntakeAgentState):
        """Extract structured data from user message using LLM"""

        if state.stage == "goals":
            # Extract goals
            system_prompt = """Extract specific goals from the user's message.
Return a JSON array of strings. Example: ["Financial abundance", "Career growth"]"""

            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=message)
            ])

            try:
                goals = json.loads(response.content)
                if isinstance(goals, list):
                    state.discovery.goals.extend(goals)
            except:
                # Fallback: treat whole message as single goal
                state.discovery.goals.append(message)

        elif state.stage == "beliefs":
            # Extract limiting beliefs
            try:
                system_prompt = "Extract limiting beliefs. Return JSON array of strings."
                response = self.llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=message)
                ])
                beliefs = json.loads(response.content)
                if isinstance(beliefs, list):
                    state.discovery.limiting_beliefs.extend(beliefs)
            except:
                state.discovery.limiting_beliefs.append(message)

        elif state.stage == "outcomes":
            # Extract desired outcomes
            try:
                system_prompt = "Extract specific desired outcomes. Return JSON array of strings."
                response = self.llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=message)
                ])
                outcomes = json.loads(response.content)
                if isinstance(outcomes, list):
                    state.discovery.desired_outcomes.extend(outcomes)
            except:
                state.discovery.desired_outcomes.append(message)

        elif state.stage == "preferences":
            # Extract preferences from message
            msg_lower = message.lower()

            if "calm" in msg_lower:
                state.discovery.tone_preference = "calm"
            elif "energetic" in msg_lower or "energy" in msg_lower:
                state.discovery.tone_preference = "energetic"
            elif "empower" in msg_lower:
                state.discovery.tone_preference = "empowering"

            if "female" in msg_lower or "woman" in msg_lower:
                state.discovery.voice_preference = "warm female"
            elif "male" in msg_lower or "man" in msg_lower:
                state.discovery.voice_preference = "confident male"

            if "morning" in msg_lower:
                state.discovery.schedule_preference = "morning"
            elif "evening" in msg_lower:
                state.discovery.schedule_preference = "evening"
            elif "both" in msg_lower:
                state.discovery.schedule_preference = "both"

            if "7" in message or "week" in msg_lower:
                state.discovery.timeframe = "7_days"
            elif "30" in message or "month" in msg_lower:
                state.discovery.timeframe = "30_days"
            elif "90" in message:
                state.discovery.timeframe = "90_days"

            if "light" in msg_lower or "15" in message:
                state.discovery.commitment_level = "light"
            elif "intensive" in msg_lower or "hour" in msg_lower:
                state.discovery.commitment_level = "intensive"
            else:
                state.discovery.commitment_level = "moderate"

    async def save_discovery_and_create_agent(
        self,
        state: IntakeAgentState
    ) -> str:
        """
        Save discovery data and create AffirmationAgent

        Returns: agent_id of created AffirmationAgent
        """
        pool = get_pg_pool()

        try:
            # 1. Save discovery data
            async with pool.acquire() as conn:
                discovery_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO user_discovery (
                        id, user_id, tenant_id,
                        goals, limiting_beliefs, desired_outcomes, preferences,
                        schedule_preference, created_at, updated_at
                    )
                    VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, $7, $8, NOW(), NOW())
                """,
                    discovery_id,
                    state.user_id,
                    state.tenant_id,
                    json.dumps(state.discovery.goals),
                    json.dumps(state.discovery.limiting_beliefs),
                    json.dumps(state.discovery.desired_outcomes),
                    json.dumps({
                        "tone": state.discovery.tone_preference,
                        "voice": state.discovery.voice_preference,
                        "timeframe": state.discovery.timeframe,
                        "commitment": state.discovery.commitment_level
                    }),
                    state.discovery.schedule_preference
                )

            logger.info(f"✅ Discovery data saved: {discovery_id}")

            # 2. Create AffirmationAgent via AgentService
            from services.agent_service import AgentService
            service = AgentService()

            contract = AgentContract(**state.affirmation_agent_contract)
            agent = await service.create_agent(contract, state.tenant_id, state.user_id)

            # 3. Link discovery to agent
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE user_discovery
                    SET affirmation_agent_id = $1::uuid
                    WHERE id = $2::uuid
                """, agent["id"], discovery_id)

            logger.info(f"✅ AffirmationAgent created and linked: {agent['id']}")

            return agent["id"]

        except Exception as e:
            logger.error(f"Failed to save discovery and create agent: {e}")
            raise
