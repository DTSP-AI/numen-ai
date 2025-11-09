"""
GuideAgent - Phase 2 Orchestrator (Discovery + Asset Generation)

This is the main orchestrator that:
1. Loads the immutable GuideContract created by IntakeAgent
2. Performs discovery conversation with user (via IntakeAgentCognitive)
3. Orchestrates sub-agents to generate assets:
   - AffirmationAgent - Generates affirmations, mantras, hypnosis scripts
   - ManifestationProtocolAgent - Builds daily schedule and protocol
   - TherapyAgent - Plans sessions and reflections
4. Synthesizes audio via ElevenLabs
5. Embeds assets for memory retrieval
6. Stores everything under the Guide's memory context

This is the "Phase 2" component from CurrentCodeBasePrompt.md
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid

from pydantic import BaseModel, Field

from models.agent import AgentContract
from memoryManager.memory_manager import MemoryManager
from graph.graph import build_agent_workflow, AgentState
from database import get_pg_pool
from services.audio_synthesis import AudioSynthesisService

# Sub-agents
from agents.guide_agent.guide_sub_agents.discovery_agent import run_discovery
from agents.guide_agent.guide_sub_agents.affirmation_agent import AffirmationAgent
from agents.guide_agent.guide_sub_agents.manifestation_protocol_agent import ManifestationProtocolAgent

logger = logging.getLogger(__name__)


# ============================================================================
# STATE MODELS
# ============================================================================

class GuideAgentState(BaseModel):
    """State for GuideAgent orchestration"""
    # Input
    agent_id: str
    user_id: str
    tenant_id: str
    thread_id: str

    # GuideContract (immutable base layer)
    guide_contract: Dict[str, Any] = Field(default_factory=dict)

    # Discovery phase
    discovery_complete: bool = False
    cognitive_data: Optional[Dict[str, Any]] = None

    # Generated assets
    affirmations: List[Dict[str, Any]] = Field(default_factory=list)
    hypnosis_scripts: List[Dict[str, Any]] = Field(default_factory=list)
    mantras: List[str] = Field(default_factory=list)
    daily_schedule: Optional[Dict[str, Any]] = None
    manifestation_protocol: Optional[Dict[str, Any]] = None

    # Audio assets
    audio_assets: List[Dict[str, str]] = Field(default_factory=list)

    # Flow control
    stage: str = "init"
    status: str = "pending"
    error_message: Optional[str] = None


# ============================================================================
# GUIDE AGENT ORCHESTRATOR
# ============================================================================

class GuideAgent:
    """
    Main orchestrator for Guide-driven discovery and asset generation

    Workflow:
    1. load_guide_context - Load GuideContract from database
    2. perform_discovery - Run cognitive intake conversation
    3. generate_assets - Orchestrate sub-agents
    4. synthesize_audio - ElevenLabs TTS
    5. embed_and_store - Memory + database
    """

    def __init__(self, contract: AgentContract, memory: MemoryManager):
        """
        Initialize GuideAgent with contract and memory

        Args:
            contract: GuideContract (created by IntakeAgent)
            memory: Memory manager for this guide
        """
        self.contract = contract
        self.memory = memory

        # Initialize sub-agents
        self.affirmation_agent = None  # Lazy init
        self.manifestation_agent = None  # Lazy init

        # Initialize audio synthesis service
        self.audio_service = AudioSynthesisService()

        # Build asset generation workflow using centralized graph
        self.asset_graph = build_agent_workflow(
            retrieve_context_fn=self._load_guide_context,
            build_prompt_fn=self._perform_discovery,
            invoke_llm_fn=self._generate_assets,
            post_process_fn=self._synthesize_audio,
            check_cognitive_triggers_fn=self._embed_and_store
        )

        # Build chat workflow (AGENT_ORCHESTRATION_STANDARD compliant)
        self.chat_graph = build_agent_workflow(
            retrieve_context_fn=self._chat_retrieve_context,
            build_prompt_fn=self._chat_build_prompt,
            invoke_llm_fn=self._chat_invoke_llm,
            post_process_fn=self._chat_post_process,
            check_cognitive_triggers_fn=self._chat_check_triggers
        )

        logger.info(f"✅ GuideAgent initialized with dual workflows: {contract.name}")

    async def _load_guide_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 1: Load GuideContract from database

        This loads the immutable base layer created by IntakeAgent.
        """
        try:
            pool = get_pg_pool()

            async with pool.acquire() as conn:
                agent_row = await conn.fetchrow("""
                    SELECT contract
                    FROM agents
                    WHERE id = $1::uuid AND tenant_id = $2::uuid
                """, state["agent_id"], state["tenant_id"])

                if not agent_row:
                    raise ValueError(f"GuideContract not found for agent {state['agent_id']}")

                guide_contract = agent_row["contract"]

            logger.info(f"✅ Loaded GuideContract for agent {state['agent_id']}")

            return {
                "guide_contract": guide_contract,
                "stage": "discovery",
                "workflow_status": "context_loaded"
            }

        except Exception as e:
            logger.error(f"Failed to load GuideContract: {e}")
            return {
                "error_message": str(e),
                "status": "failed",
                "workflow_status": "context_load_failed"
            }

    async def _perform_discovery(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 2: Perform cognitive discovery conversation

        Uses DiscoveryAgent to collect:
        - Goals (with GAS ratings)
        - Limiting beliefs
        - Desired outcomes
        - Ideal vs Actual ratings
        - Belief graph (CAM)
        """
        try:
            # Check if discovery already complete
            if state.get("discovery_complete"):
                logger.info("Discovery already complete, skipping")
                return {"workflow_status": "discovery_skipped"}

            # Get goals, beliefs, outcomes from memory or prompt
            # In production, this would be interactive conversation
            # For now, we'll check if they exist in state
            goals = state.get("goals", [])
            limiting_beliefs = state.get("limiting_beliefs", [])
            desired_outcomes = state.get("desired_outcomes", [])

            if not goals:
                # No discovery data provided, mark as incomplete
                logger.warning("No discovery data provided, cannot proceed")
                return {
                    "error_message": "Discovery data required (goals, beliefs, outcomes)",
                    "status": "awaiting_discovery",
                    "workflow_status": "discovery_incomplete"
                }

            # Run cognitive discovery
            cognitive_result = await run_discovery(
                user_id=state["user_id"],
                tenant_id=state["tenant_id"],
                guide_contract=state["guide_contract"],
                goals=goals,
                limiting_beliefs=limiting_beliefs,
                desired_outcomes=desired_outcomes
            )

            logger.info(f"✅ Cognitive discovery complete for user {state['user_id']}")

            return {
                "cognitive_data": cognitive_result,
                "discovery_complete": True,
                "stage": "asset_generation",
                "workflow_status": "discovery_complete"
            }

        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return {
                "error_message": str(e),
                "status": "failed",
                "workflow_status": "discovery_failed"
            }

    async def _generate_assets(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 3: Orchestrate sub-agents to generate all assets

        Sub-agents:
        1. AffirmationAgent - Affirmations, mantras, hypnosis scripts
        2. ManifestationProtocolAgent - Daily schedule, protocol
        """
        try:
            if not state.get("cognitive_data"):
                raise ValueError("Cognitive data required for asset generation")

            cognitive_data = state["cognitive_data"]["cognitive_data"]
            goals = cognitive_data.get("goals", [])
            primary_goal = goals[0] if goals else "Personal transformation"

            # Initialize sub-agents if needed
            if not self.affirmation_agent:
                self.affirmation_agent = AffirmationAgent(
                    contract=self.contract,
                    memory=self.memory
                )

            if not self.manifestation_agent:
                self.manifestation_agent = ManifestationProtocolAgent()

            # 1. Generate affirmations, mantras, hypnosis scripts
            logger.info("Generating affirmations and scripts...")
            affirmation_content = await self.affirmation_agent.generate_daily_content(
                user_id=state["user_id"],
                discovery_id=state.get("discovery_id", str(uuid.uuid4()))
            )

            # 2. Generate manifestation protocol and daily schedule
            logger.info("Generating manifestation protocol...")
            protocol = await self.manifestation_agent.generate_protocol(
                user_id=state["user_id"],
                goal=primary_goal,
                timeframe="30_days",
                commitment_level="moderate",
                agent_traits=self.contract.traits.model_dump()
            )

            logger.info(f"""
✅ Asset generation complete:
   - Affirmations: {len(affirmation_content.get('affirmations', []))}
   - Mantras: {len(affirmation_content.get('mantras', []))}
   - Hypnosis Scripts: {len(affirmation_content.get('hypnosis_scripts', []))}
   - Daily Practices: {len(protocol.get('daily_practices', []))}
""")

            return {
                "affirmations": affirmation_content.get("affirmations", []),
                "mantras": affirmation_content.get("mantras", []),
                "hypnosis_scripts": affirmation_content.get("hypnosis_scripts", []),
                "manifestation_protocol": protocol,
                "daily_schedule": protocol.get("daily_practices", []),
                "stage": "audio_synthesis",
                "workflow_status": "assets_generated"
            }

        except Exception as e:
            logger.error(f"Asset generation failed: {e}")
            return {
                "error_message": str(e),
                "status": "failed",
                "workflow_status": "asset_generation_failed"
            }

    async def _synthesize_audio(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 4: Synthesize audio for affirmations and scripts via ElevenLabs

        Creates audio files for:
        - Each affirmation
        - Each hypnosis script
        - Optional: Mantras
        """
        try:
            audio_assets = []

            # Get voice configuration from contract
            voice_config = self.contract.voice if self.contract.voice else None
            if not voice_config:
                logger.warning("No voice configuration in contract - skipping audio synthesis")
                return {
                    "audio_assets": [],
                    "stage": "embedding",
                    "workflow_status": "audio_skipped_no_voice_config"
                }

            # Synthesize affirmations
            affirmations = state.get("affirmations", [])
            for i, aff in enumerate(affirmations):
                text = aff.get("text", "")
                affirmation_id = aff.get("id", str(uuid.uuid4()))

                # Synthesize audio using ElevenLabs
                audio_url = await self.audio_service.synthesize_affirmation(
                    affirmation_id=affirmation_id,
                    text=text,
                    voice_config=voice_config
                )

                audio_assets.append({
                    "type": "affirmation",
                    "text": text,
                    "audio_url": audio_url if audio_url else f"synthesis_failed_aff_{i}.mp3",
                    "status": "synthesized" if audio_url else "synthesis_failed"
                })

            # Synthesize hypnosis scripts
            hypnosis_scripts = state.get("hypnosis_scripts", [])
            for i, script in enumerate(hypnosis_scripts):
                text = script.get("script_text", "")
                script_id = script.get("id", str(uuid.uuid4()))

                # Synthesize audio using ElevenLabs
                audio_url = await self.audio_service.synthesize_hypnosis_script(
                    script_id=script_id,
                    script_text=text,
                    voice_config=voice_config
                )

                audio_assets.append({
                    "type": "hypnosis",
                    "text": text,
                    "audio_url": audio_url if audio_url else f"synthesis_failed_script_{i}.mp3",
                    "status": "synthesized" if audio_url else "synthesis_failed"
                })

            successful = len([a for a in audio_assets if a["status"] == "synthesized"])
            logger.info(f"✅ Audio synthesis complete: {successful}/{len(audio_assets)} assets")

            return {
                "audio_assets": audio_assets,
                "stage": "embedding",
                "workflow_status": "audio_synthesized"
            }

        except Exception as e:
            logger.error(f"Audio synthesis failed: {e}", exc_info=True)
            return {
                "error_message": str(e),
                "workflow_status": "audio_synthesis_failed"
            }

    async def _embed_and_store(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 5: Embed assets for memory retrieval and store in database

        1. Embed affirmations and scripts using embeddings service
        2. Store in MemoryManager for semantic search
        3. Check reflex triggers
        4. Mark workflow complete
        """
        try:
            # Store assets in memory for semantic retrieval
            affirmations = state.get("affirmations", [])
            for aff in affirmations:
                await self.memory.add_memory(
                    message=aff.get("text", ""),
                    metadata={
                        "type": "affirmation",
                        "category": aff.get("category", "identity"),
                        "user_id": state["user_id"],
                        "agent_id": state["agent_id"]
                    }
                )

            # Store protocol in memory
            protocol = state.get("manifestation_protocol", {})
            if protocol:
                await self.memory.add_memory(
                    message=f"Manifestation protocol created for goal: {protocol.get('meta', {}).get('goal', '')}",
                    metadata={
                        "type": "protocol",
                        "user_id": state["user_id"],
                        "agent_id": state["agent_id"],
                        "protocol_id": str(uuid.uuid4())
                    }
                )

            logger.info(f"✅ Assets embedded and stored in memory")

            # Check cognitive triggers (reflex engine)
            from services.trigger_logic import check_and_handle_triggers

            intervention_prompts = await check_and_handle_triggers(
                user_id=state["user_id"],
                agent_id=state["agent_id"],
                tenant_id=state["tenant_id"],
                agent_contract=state["guide_contract"],
                context={"stage": "asset_generation_complete"}
            )

            if intervention_prompts:
                logger.info(f"🔔 Cognitive triggers fired: {len(intervention_prompts)} interventions")

            return {
                "status": "complete",
                "stage": "complete",
                "cognitive_triggers": intervention_prompts,
                "trigger_fired": len(intervention_prompts) > 0,
                "workflow_status": "completed"
            }

        except Exception as e:
            logger.error(f"Embedding and storage failed: {e}")
            return {
                "error_message": str(e),
                "status": "failed",
                "workflow_status": "embed_store_failed"
            }

    # ========================================================================
    # CHAT WORKFLOW NODES (AGENT_ORCHESTRATION_STANDARD Compliant)
    # ========================================================================

    async def _chat_retrieve_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 1: Retrieve memory context for chat message

        Uses MemoryManager to get relevant past interactions and recent messages.
        """
        try:
            user_input = state.get("user_input", "")
            thread_id = state.get("thread_id", "")
            user_id = state.get("user_id", "")

            # Get memory context from MemoryManager
            memory_context = await self.memory.get_agent_context(
                user_input=user_input,
                session_id=thread_id,
                user_id=user_id,
                k=5
            )

            logger.info(f"✅ Retrieved {len(memory_context.retrieved_memories)} memories for chat")

            return {
                "memory_context": memory_context,
                "retrieved_memories": memory_context.retrieved_memories,
                "recent_messages": memory_context.recent_messages,
                "workflow_status": "context_retrieved"
            }

        except Exception as e:
            logger.error(f"Failed to retrieve chat context: {e}")
            return {
                "memory_context": None,
                "retrieved_memories": [],
                "recent_messages": [],
                "workflow_status": "context_retrieval_failed"
            }

    async def _chat_build_prompt(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 2: Build LLM prompt from contract + memory context

        Constructs system prompt from JSON contract and prepares conversation history.
        CRITICAL: Recent messages must be formatted as proper message objects, not text.
        """
        try:
            # Build system prompt from contract
            system_prompt = self._build_system_prompt()

            # Add semantic memory context to system prompt
            retrieved_memories = state.get("retrieved_memories", [])
            if retrieved_memories:
                memory_context = "\n\n=== RELEVANT CONTEXT FROM MEMORY ===\n"
                for mem in retrieved_memories[:3]:
                    memory_context += f"• {mem.get('content', '')}\n"
                system_prompt += memory_context

            # Build conversation history as proper message list (NOT text in system prompt)
            conversation_history = []
            recent_messages = state.get("recent_messages", [])

            if recent_messages:
                logger.info(f"📜 Building conversation history with {len(recent_messages)} messages")
                for msg in recent_messages:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if content:  # Only add non-empty messages
                        conversation_history.append({
                            "role": role,
                            "content": content
                        })

            logger.info(f"✅ Built chat prompt with {len(retrieved_memories)} memories and {len(conversation_history)} history messages")

            return {
                "system_prompt": system_prompt,
                "conversation_history": conversation_history,
                "workflow_status": "prompt_built"
            }

        except Exception as e:
            logger.error(f"Failed to build chat prompt: {e}")
            return {
                "system_prompt": self._build_system_prompt(),
                "conversation_history": [],
                "workflow_status": "prompt_build_failed"
            }

    async def _chat_invoke_llm(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 3: Invoke LLM with constructed prompt and FULL conversation history

        CRITICAL: Must include entire thread conversation, not just current message.
        Uses ChatOpenAI with configuration from contract.
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import SystemMessage, HumanMessage, AIMessage
            from config import settings

            # Get OpenAI API key
            api_key = settings.openai_api_key or settings.OPENAI_API_KEY

            # Initialize LLM with contract configuration
            llm = ChatOpenAI(
                model=self.contract.configuration.llm_model,
                temperature=self.contract.configuration.temperature,
                max_tokens=self.contract.configuration.max_tokens,
                api_key=api_key
            )

            # Build messages with FULL conversation context
            system_prompt = state.get("system_prompt", "")
            user_input = state.get("user_input", "")
            conversation_history = state.get("conversation_history", [])

            # Start with system message
            messages = [SystemMessage(content=system_prompt)]

            # Add conversation history (preserving role context)
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))

            # Add current user input
            messages.append(HumanMessage(content=user_input))

            logger.info(f"🤖 Invoking LLM with {len(messages)} messages (system + {len(conversation_history)} history + current)")

            # Invoke LLM
            response = await llm.ainvoke(messages)
            response_text = response.content

            logger.info(f"✅ LLM invoked for chat (model: {self.contract.configuration.llm_model})")

            return {
                "llm_response": response_text,
                "workflow_status": "llm_invoked"
            }

        except Exception as e:
            logger.error(f"Failed to invoke LLM for chat: {e}", exc_info=True)
            return {
                "llm_response": "I apologize, but I'm having trouble processing your message right now. Please try again.",
                "workflow_status": "llm_invocation_failed",
                "error_message": str(e)
            }

    async def _chat_post_process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 4: Post-process LLM response

        Cleans up response, applies formatting, validates output.
        """
        try:
            llm_response = state.get("llm_response", "")

            # Basic post-processing
            response_text = llm_response.strip()

            # Ensure response is not empty
            if not response_text:
                response_text = "I'm here to support you on your journey. How can I help you today?"

            logger.info(f"✅ Chat response post-processed ({len(response_text)} chars)")

            return {
                "response_text": response_text,
                "workflow_status": "response_processed"
            }

        except Exception as e:
            logger.error(f"Failed to post-process chat response: {e}")
            return {
                "response_text": state.get("llm_response", "I'm here to help."),
                "workflow_status": "post_process_failed"
            }

    async def _chat_check_triggers(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 5: Check cognitive triggers and inject interventions

        Uses trigger_logic to detect cognitive patterns and provide interventions.
        """
        try:
            from services.trigger_logic import check_and_handle_triggers

            user_id = state.get("user_id", "")
            agent_id = str(self.contract.id)
            tenant_id = state.get("tenant_id", "")
            user_input = state.get("user_input", "")
            response_text = state.get("response_text", "")

            # Check for cognitive triggers
            intervention_prompts = await check_and_handle_triggers(
                user_id=user_id,
                agent_id=agent_id,
                tenant_id=tenant_id,
                agent_contract=self.contract.model_dump(),
                context={
                    "stage": "chat_response",
                    "user_input": user_input,
                    "agent_response": response_text
                }
            )

            trigger_fired = len(intervention_prompts) > 0

            if trigger_fired:
                logger.info(f"🔔 Cognitive triggers fired: {len(intervention_prompts)} interventions")
            else:
                logger.info("✅ No cognitive triggers detected")

            return {
                "cognitive_triggers": intervention_prompts,
                "trigger_fired": trigger_fired,
                "workflow_status": "completed"
            }

        except Exception as e:
            logger.error(f"Failed to check cognitive triggers: {e}")
            return {
                "cognitive_triggers": [],
                "trigger_fired": False,
                "workflow_status": "trigger_check_failed"
            }

    # ========================================================================
    # CHAT MESSAGE PROCESSING (LangGraph-Based)
    # ========================================================================

    async def process_chat_message(
        self,
        user_id: str,
        user_input: str,
        thread_id: str,
        memory_context: Any
    ) -> str:
        """
        Process a chat message using LangGraph workflow (AGENT_ORCHESTRATION_STANDARD compliant)

        Flows through 5-node LangGraph workflow:
        1. retrieve_context - Get memory context
        2. build_prompt - Build system prompt from contract + memory
        3. invoke_llm - Call ChatOpenAI with configured model
        4. post_process - Clean and format response
        5. check_cognitive_triggers - Check for intervention triggers

        Args:
            user_id: User UUID
            user_input: User's message
            thread_id: Thread ID for context
            memory_context: Memory context from MemoryManager (now retrieved in graph)

        Returns:
            Agent's response text
        """
        try:
            # Get tenant_id from contract
            tenant_id = self.contract.metadata.tenant_id

            # Build initial state for LangGraph
            initial_state = {
                "agent_id": str(self.contract.id),
                "user_id": user_id,
                "tenant_id": tenant_id,
                "thread_id": thread_id,
                "user_input": user_input,
                "input_text": user_input,
                "agent_contract": self.contract.model_dump(),
                "traits": self.contract.traits.model_dump(),
                "configuration": self.contract.configuration.model_dump()
            }

            logger.info(f"🚀 Starting LangGraph chat workflow for thread {thread_id}")

            # Invoke LangGraph chat workflow
            result = await self.chat_graph.ainvoke(initial_state)

            # Extract response from workflow result
            response_text = result.get("response_text", "I'm here to support you.")

            # Log workflow completion
            workflow_status = result.get("workflow_status", "unknown")
            trigger_fired = result.get("trigger_fired", False)

            logger.info(f"""
✅ LangGraph chat workflow complete:
   Thread: {thread_id}
   Status: {workflow_status}
   Triggers: {'🔔 YES' if trigger_fired else 'No'}
   Response length: {len(response_text)} chars
""")

            return response_text

        except Exception as e:
            logger.error(f"LangGraph chat workflow failed: {e}", exc_info=True)
            return "I apologize, but I'm having trouble processing your message right now. Please try again."

    def _build_system_prompt(self) -> str:
        """Build system prompt from agent contract with thread awareness"""
        traits_desc = "\n".join([
            f"- {trait.replace('_', ' ').title()}: {value}/100"
            for trait, value in self.contract.traits.model_dump().items()
        ])

        return f"""You are {self.contract.name}.

{self.contract.identity.full_description or self.contract.identity.short_description}

CHARACTER ROLE: {self.contract.identity.character_role}
MISSION: {self.contract.identity.mission}
INTERACTION STYLE: {self.contract.identity.interaction_style}

PERSONALITY TRAITS:
{traits_desc}

=== CRITICAL INSTRUCTIONS ===
1. ALWAYS respond in the context of the FULL conversation thread
2. Reference previous messages when relevant to show continuity
3. Build upon what the user has shared earlier in the conversation
4. Acknowledge the ongoing relationship and journey together
5. Use the conversation history to provide personalized, contextual responses
6. If relevant memory context is provided above, integrate it naturally

Respond to the user in a way that embodies your character, mission, and the full context of your relationship.
"""

    async def run_complete_flow(
        self,
        user_id: str,
        tenant_id: str,
        thread_id: str,
        goals: List[str],
        limiting_beliefs: List[str] = None,
        desired_outcomes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run the complete GuideAgent flow from discovery to asset generation

        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            thread_id: Thread UUID
            goals: User goals
            limiting_beliefs: Optional limiting beliefs
            desired_outcomes: Optional desired outcomes

        Returns:
            Dict with complete results
        """
        try:
            initial_state = {
                "agent_id": self.contract.id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "thread_id": thread_id,
                "goals": goals,
                "limiting_beliefs": limiting_beliefs or [],
                "desired_outcomes": desired_outcomes or [],
                "guide_contract": self.contract.model_dump()
            }

            logger.info(f"🚀 Starting complete GuideAgent flow for user {user_id}")

            # Run the asset generation workflow graph
            result = await self.asset_graph.ainvoke(initial_state)

            logger.info(f"""
✅ GuideAgent flow complete:
   Status: {result.get('status')}
   Stage: {result.get('stage')}
   Affirmations: {len(result.get('affirmations', []))}
   Hypnosis Scripts: {len(result.get('hypnosis_scripts', []))}
   Audio Assets: {len(result.get('audio_assets', []))}
""")

            return result

        except Exception as e:
            logger.error(f"GuideAgent flow failed: {e}")
            return {
                "status": "failed",
                "error_message": str(e)
            }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def create_and_run_guide(
    guide_contract: AgentContract,
    user_id: str,
    tenant_id: str,
    goals: List[str],
    limiting_beliefs: List[str] = None,
    desired_outcomes: List[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to create GuideAgent and run complete flow

    Args:
        guide_contract: GuideContract (from IntakeAgent)
        user_id: User UUID
        tenant_id: Tenant UUID
        goals: User goals
        limiting_beliefs: Optional limiting beliefs
        desired_outcomes: Optional desired outcomes

    Returns:
        Complete results dict
    """
    # Initialize memory manager
    memory = MemoryManager(
        tenant_id=tenant_id,
        agent_id=guide_contract.id,
        agent_traits=guide_contract.traits.model_dump()
    )

    # Create GuideAgent
    guide = GuideAgent(contract=guide_contract, memory=memory)

    # Run complete flow
    thread_id = str(uuid.uuid4())
    result = await guide.run_complete_flow(
        user_id=user_id,
        tenant_id=tenant_id,
        thread_id=thread_id,
        goals=goals,
        limiting_beliefs=limiting_beliefs,
        desired_outcomes=desired_outcomes
    )

    return result
