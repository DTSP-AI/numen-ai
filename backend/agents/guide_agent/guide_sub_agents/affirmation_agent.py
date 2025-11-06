"""
AffirmationAgent - Contract-First Content Generation

Role: Guide + Voice
Mission: Generate personalized affirmations, mantras, and hypnosis scripts

This agent is dynamically created from IntakeAgent's output contract.
It generates all manifestation content aligned with user's goals and beliefs.

Content Generated:
- Daily affirmations (morning/evening sets)
- Mantras (quantum shifting phrases)
- Hypnosis scripts (Law of Attraction, CBT-based)
- Audio via ElevenLabs SDK
- Scheduled routines
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, time
import json
import uuid

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from models.agent import AgentContract
from memoryManager.memory_manager import MemoryManager
from database import get_pg_pool

logger = logging.getLogger(__name__)


# ============================================================================
# STATE MODELS
# ============================================================================

class AffirmationContent(BaseModel):
    """Single affirmation"""
    text: str
    category: str  # identity, gratitude, action, visualization
    intensity: int = Field(ge=1, le=10, default=7)


class HypnosisScript(BaseModel):
    """Hypnosis script with pacing"""
    title: str
    script_text: str
    duration_minutes: int
    pacing_markers: List[Dict[str, Any]] = Field(default_factory=list)
    focus_area: str


class AffirmationAgentState(BaseModel):
    """State for AffirmationAgent graph"""
    session_id: str
    user_id: str
    agent_id: str

    # User's discovery data (loaded from database)
    goals: List[str] = Field(default_factory=list)
    limiting_beliefs: List[str] = Field(default_factory=list)
    desired_outcomes: List[str] = Field(default_factory=list)

    # Generated content
    affirmations: List[AffirmationContent] = Field(default_factory=list)
    mantras: List[str] = Field(default_factory=list)
    hypnosis_scripts: List[HypnosisScript] = Field(default_factory=list)

    # Audio generation
    audio_queue: List[Dict[str, str]] = Field(default_factory=list)

    # Flow control
    stage: str = "analyze_goals"
    generation_complete: bool = False


# ============================================================================
# AFFIRMATION AGENT (CONTRACT-FIRST)
# ============================================================================

class AffirmationAgent:
    """
    Contract-First AffirmationAgent

    Dynamically created by IntakeAgent.
    Generates personalized manifestation content.
    """

    def __init__(
        self,
        contract: AgentContract,
        memory: MemoryManager
    ):
        """
        Initialize from contract (Agent Creation Standard)

        Args:
            contract: Agent JSON contract (created by IntakeAgent)
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

        logger.info(f"✅ AffirmationAgent initialized: {contract.name}")

    def _build_graph(self) -> StateGraph:
        """Build content generation workflow"""
        workflow = StateGraph(AffirmationAgentState)

        # Define nodes
        workflow.add_node("analyze_goals", self._analyze_goals_node)
        workflow.add_node("generate_identity_affirmations", self._gen_identity_affirmations_node)
        workflow.add_node("generate_gratitude_affirmations", self._gen_gratitude_affirmations_node)
        workflow.add_node("generate_action_affirmations", self._gen_action_affirmations_node)
        workflow.add_node("generate_mantras", self._gen_mantras_node)
        workflow.add_node("generate_hypnosis_script", self._gen_hypnosis_script_node)
        workflow.add_node("finalize_content", self._finalize_content_node)

        # Build workflow
        workflow.set_entry_point("analyze_goals")
        workflow.add_edge("analyze_goals", "generate_identity_affirmations")
        workflow.add_edge("generate_identity_affirmations", "generate_gratitude_affirmations")
        workflow.add_edge("generate_gratitude_affirmations", "generate_action_affirmations")
        workflow.add_edge("generate_action_affirmations", "generate_mantras")
        workflow.add_edge("generate_mantras", "generate_hypnosis_script")
        workflow.add_edge("generate_hypnosis_script", "finalize_content")
        workflow.add_edge("finalize_content", END)

        return workflow.compile()

    def _analyze_goals_node(self, state: AffirmationAgentState) -> AffirmationAgentState:
        """Analyze goals and prepare generation strategy"""

        system_prompt = f"""You are {self.contract.name}.

{self.contract.identity.full_description}

MISSION: {self.contract.identity.mission}

Analyze the user's goals and limiting beliefs to prepare for affirmation generation.

User Goals:
{chr(10).join(f'- {goal}' for goal in state.goals)}

Limiting Beliefs:
{chr(10).join(f'- {belief}' for belief in state.limiting_beliefs)}

Identify:
1. Core emotional themes
2. Key identity shifts needed
3. Specific belief transformations required

Return a JSON object with these keys."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Analyze the goals and beliefs.")
            ])

            analysis = json.loads(response.content)
            logger.info(f"Goal analysis complete: {analysis}")

        except Exception as e:
            logger.warning(f"Goal analysis failed: {e}")

        state.stage = "generating_affirmations"
        return state

    def _gen_identity_affirmations_node(self, state: AffirmationAgentState) -> AffirmationAgentState:
        """Generate identity-based affirmations ("I am...")"""

        system_prompt = f"""Generate 7-10 powerful identity affirmations.

User Goals: {', '.join(state.goals)}
Limiting Beliefs to Transform: {', '.join(state.limiting_beliefs)}

Rules:
- Start with "I am..."
- Present tense only
- Vivid and sensory
- Emotionally resonant
- Believable yet stretching

Example: "I am a magnet for abundance and opportunities flow to me effortlessly."

Your personality: Empathy {self.contract.traits.empathy}/100, Confidence {self.contract.traits.confidence}/100

Return JSON array of objects with keys: "text", "category", "intensity"
Category must be "identity"."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate identity affirmations.")
            ])

            affirmations_data = json.loads(response.content)

            for aff in affirmations_data:
                state.affirmations.append(AffirmationContent(
                    text=aff["text"],
                    category="identity",
                    intensity=aff.get("intensity", 7)
                ))

            logger.info(f"✅ Generated {len(affirmations_data)} identity affirmations")

        except Exception as e:
            logger.error(f"Identity affirmation generation failed: {e}")
            # Fallback
            state.affirmations.append(AffirmationContent(
                text=f"I am actively manifesting {state.goals[0] if state.goals else 'my highest potential'}",
                category="identity",
                intensity=7
            ))

        return state

    def _gen_gratitude_affirmations_node(self, state: AffirmationAgentState) -> AffirmationAgentState:
        """Generate gratitude affirmations (as if already achieved)"""

        system_prompt = f"""Generate 7-10 gratitude affirmations (as if goals already achieved).

User Goals: {', '.join(state.goals)}

Rules:
- Start with "I'm grateful for..." or "Thank you for..."
- Speak as if it's already real
- Include sensory and emotional details
- Create the feeling of having achieved the goal

Example: "I'm grateful for the abundant financial freedom I now experience every day."

Return JSON array with keys: "text", "category", "intensity"
Category must be "gratitude"."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate gratitude affirmations.")
            ])

            affirmations_data = json.loads(response.content)

            for aff in affirmations_data:
                state.affirmations.append(AffirmationContent(
                    text=aff["text"],
                    category="gratitude",
                    intensity=aff.get("intensity", 8)
                ))

            logger.info(f"✅ Generated {len(affirmations_data)} gratitude affirmations")

        except Exception as e:
            logger.error(f"Gratitude affirmation generation failed: {e}")

        return state

    def _gen_action_affirmations_node(self, state: AffirmationAgentState) -> AffirmationAgentState:
        """Generate action-oriented affirmations ("I choose to...")"""

        system_prompt = f"""Generate 7-10 empowering action affirmations.

User Goals: {', '.join(state.goals)}

Rules:
- Start with "I choose to...", "I take action by...", "I easily..."
- Focus on aligned actions
- Make it feel natural and effortless
- Bridge belief to behavior

Example: "I choose to speak my truth with confidence and clarity."

Return JSON array with keys: "text", "category", "intensity"
Category must be "action"."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate action affirmations.")
            ])

            affirmations_data = json.loads(response.content)

            for aff in affirmations_data:
                state.affirmations.append(AffirmationContent(
                    text=aff["text"],
                    category="action",
                    intensity=aff.get("intensity", 7)
                ))

            logger.info(f"✅ Generated {len(affirmations_data)} action affirmations")

        except Exception as e:
            logger.error(f"Action affirmation generation failed: {e}")

        return state

    def _gen_mantras_node(self, state: AffirmationAgentState) -> AffirmationAgentState:
        """Generate short, powerful mantras"""

        system_prompt = f"""Generate 5 short, powerful mantras (3-8 words).

User Goals: {', '.join(state.goals)}

Mantras are:
- Rhythmic and repeatable
- Energetically charged
- Quantum shifting phrases
- Easy to remember

Examples:
- "I am abundant and free"
- "Confidence flows through me"
- "Every day I rise stronger"

Return JSON array of mantra strings."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate mantras.")
            ])

            mantras = json.loads(response.content)
            state.mantras = mantras

            logger.info(f"✅ Generated {len(mantras)} mantras")

        except Exception as e:
            logger.error(f"Mantra generation failed: {e}")
            state.mantras = [f"I manifest {state.goals[0]}" if state.goals else "I am aligned with abundance"]

        return state

    def _gen_hypnosis_script_node(self, state: AffirmationAgentState) -> AffirmationAgentState:
        """Generate guided hypnosis script"""

        system_prompt = f"""Generate a 10-15 minute guided hypnosis script.

User Goals: {', '.join(state.goals)}
Limiting Beliefs to Transform: {', '.join(state.limiting_beliefs)}

Script Structure:
1. Induction (2-3 min): Progressive relaxation, breath focus
2. Deepening (2 min): Counting down, deeper relaxation
3. Suggestion Phase (6-8 min): Core affirmations, visualizations, belief reprogramming
4. Future Pacing (2 min): See yourself living the goal
5. Emergence (1-2 min): Counting up, feeling refreshed

Techniques:
- Use second person ("You are...", "You feel...")
- Include pacing markers like [PAUSE 5s], [SLOW], [SOFTEN VOICE]
- Law of Attraction principles
- Quantum theory metaphors
- CBT/positive psychology
- Hypnotherapy pacing

Return JSON object with keys:
- title: Script title
- script_text: Full script with pacing markers
- duration_minutes: Estimated duration
- focus_area: Primary focus
- pacing_markers: Array of timing objects"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate complete hypnosis script.")
            ])

            script_data = json.loads(response.content)

            state.hypnosis_scripts.append(HypnosisScript(
                title=script_data.get("title", f"Hypnosis for {state.goals[0] if state.goals else 'Transformation'}"),
                script_text=script_data.get("script_text", ""),
                duration_minutes=script_data.get("duration_minutes", 12),
                pacing_markers=script_data.get("pacing_markers", []),
                focus_area=state.goals[0] if state.goals else "personal growth"
            ))

            logger.info(f"✅ Generated hypnosis script: {script_data.get('title')}")

        except Exception as e:
            logger.error(f"Hypnosis script generation failed: {e}")
            # Fallback minimal script
            state.hypnosis_scripts.append(HypnosisScript(
                title="Transformation Journey",
                script_text=f"You are deeply relaxed... You are manifesting {state.goals[0] if state.goals else 'your highest self'}...",
                duration_minutes=10,
                focus_area=state.goals[0] if state.goals else "growth"
            ))

        return state

    def _finalize_content_node(self, state: AffirmationAgentState) -> AffirmationAgentState:
        """Finalize and prepare for storage"""

        state.generation_complete = True
        state.stage = "complete"

        logger.info(f"""
✅ Content Generation Complete:
   - Affirmations: {len(state.affirmations)}
   - Mantras: {len(state.mantras)}
   - Hypnosis Scripts: {len(state.hypnosis_scripts)}
""")

        return state

    async def generate_daily_content(
        self,
        user_id: str,
        discovery_id: str
    ) -> Dict[str, Any]:
        """
        Generate complete daily content set

        Args:
            user_id: User UUID
            discovery_id: User discovery record UUID

        Returns:
            Dict with all generated content
        """
        pool = get_pg_pool()

        try:
            # Load discovery data
            async with pool.acquire() as conn:
                discovery_row = await conn.fetchrow("""
                    SELECT goals, limiting_beliefs, desired_outcomes
                    FROM user_discovery
                    WHERE id = $1::uuid AND user_id = $2::uuid
                """, discovery_id, user_id)

                if not discovery_row:
                    raise ValueError("Discovery data not found")

                goals = json.loads(discovery_row["goals"]) if discovery_row["goals"] else []
                limiting_beliefs = json.loads(discovery_row["limiting_beliefs"]) if discovery_row["limiting_beliefs"] else []
                desired_outcomes = json.loads(discovery_row["desired_outcomes"]) if discovery_row["desired_outcomes"] else []

            # Build initial state
            initial_state = AffirmationAgentState(
                session_id=str(uuid.uuid4()),
                user_id=user_id,
                agent_id=self.contract.id,
                goals=goals,
                limiting_beliefs=limiting_beliefs,
                desired_outcomes=desired_outcomes
            )

            # Run generation graph
            result = await self.graph.ainvoke(initial_state.model_dump())
            final_state = AffirmationAgentState(**result)

            # Store generated content
            await self._store_content(final_state)

            return {
                "affirmations": [aff.model_dump() for aff in final_state.affirmations],
                "mantras": final_state.mantras,
                "hypnosis_scripts": [script.model_dump() for script in final_state.hypnosis_scripts]
            }

        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise

    async def _store_content(self, state: AffirmationAgentState):
        """Store generated content in database"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                # Store affirmations
                for aff in state.affirmations:
                    affirmation_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO affirmations (
                            id, user_id, agent_id, tenant_id,
                            affirmation_text, category, tags,
                            status, created_at, updated_at
                        )
                        VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, $6, $7, 'active', NOW(), NOW())
                    """,
                        affirmation_id,
                        state.user_id,
                        state.agent_id,
                        self.contract.metadata.tenant_id,
                        aff.text,
                        aff.category,
                        [aff.category, f"intensity_{aff.intensity}"]
                    )

                # Store hypnosis scripts
                for script in state.hypnosis_scripts:
                    script_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO hypnosis_scripts (
                            id, user_id, agent_id, tenant_id,
                            title, script_text, duration_minutes,
                            pacing_markers, focus_area,
                            status, created_at, updated_at
                        )
                        VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, $6, $7, $8, $9, 'active', NOW(), NOW())
                    """,
                        script_id,
                        state.user_id,
                        state.agent_id,
                        self.contract.metadata.tenant_id,
                        script.title,
                        script.script_text,
                        script.duration_minutes,
                        json.dumps(script.pacing_markers),
                        script.focus_area
                    )

            logger.info(f"✅ Content stored for user {state.user_id}")

        except Exception as e:
            logger.error(f"Failed to store content: {e}")
            raise
