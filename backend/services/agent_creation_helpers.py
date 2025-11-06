"""
Agent Creation Helper Functions

Breaks down the massive create_agent_from_intake() into smaller,
testable functions following single responsibility principle.
"""

import logging
import uuid
from typing import Dict, List, Optional, Tuple

from models.agent import (
    AgentContract,
    AgentIdentity,
    AgentTraits,
    AgentConfiguration,
    VoiceConfiguration,
    AgentMetadata,
    AgentStatus,
    AgentType
)

logger = logging.getLogger(__name__)


def calculate_role_and_styles(
    session_type: str,
    tone: str
) -> Tuple[str, List[str]]:
    """
    Calculate optimal role and interaction styles based on intake data

    Args:
        session_type: Type of session (manifestation, anxiety_relief, etc.)
        tone: Desired tone (calm, energetic, etc.)

    Returns:
        Tuple of (primary_role, interaction_styles)
    """
    # AI-powered role selection
    role_mapping = {
        "manifestation": "Manifestation Mentor",
        "anxiety_relief": "Stoic Sage",
        "sleep_hypnosis": "Mindfulness Teacher",
        "confidence": "Life Coach",
        "habit_change": "Wellness Coach"
    }
    primary_role = role_mapping.get(session_type, "Life Coach")

    # AI-powered interaction style selection
    style_mapping = {
        "calm": ["Gentle", "Supportive"],
        "energetic": ["Motivational", "Encouraging"],
        "authoritative": ["Direct", "Analytical"],
        "gentle": ["Compassionate", "Nurturing"],
        "empowering": ["Empowering", "Encouraging"]
    }
    interaction_styles = style_mapping.get(tone, ["Supportive", "Encouraging"])

    return primary_role, interaction_styles


def generate_guide_name(normalized_goals: List[str]) -> str:
    """
    Generate guide name from primary goal

    Args:
        normalized_goals: List of user goals

    Returns:
        Guide name string (max 30 chars + " Guide")
    """
    primary_goal = normalized_goals[0] if normalized_goals else "Personal Growth"
    return f"{primary_goal[:30]} Guide"


async def calculate_optimal_traits(
    intake_data: dict,
    user_controls: Optional[dict] = None
) -> AgentTraits:
    """
    Calculate optimal agent traits from intake data

    Priority:
    1. User-provided controls (if available)
    2. AI-calculated traits based on intake data
    3. Default fallback traits

    Args:
        intake_data: Intake contract data
        user_controls: Optional user-provided trait controls

    Returns:
        AgentTraits instance with calculated values
    """
    from models.schemas import IntakeContract
    from services.attribute_calculator import calculate_guide_attributes

    # Default fallback traits
    default_traits = AgentTraits()

    try:
        # Convert to IntakeContract schema
        intake_schema = IntakeContract(
            normalized_goals=intake_data.get("normalized_goals", []),
            prefs=intake_data.get("prefs", {}),
            notes=intake_data.get("notes", "")
        )

        # Priority 1: User controls
        if user_controls:
            logger.info(f"Using user-provided trait controls")
            calculated_traits = await calculate_guide_attributes(
                intake_schema,
                user_controls=user_controls
            )
            logger.info(f"Traits from user controls: {calculated_traits.model_dump()}")
            return calculated_traits

        # Priority 2: AI calculation
        calculated_traits = await calculate_guide_attributes(intake_schema)
        logger.info(f"AI-calculated traits: {calculated_traits.model_dump()}")
        return calculated_traits

    except Exception as e:
        logger.warning(f"Trait calculation failed, using defaults: {e}")
        return default_traits


def build_agent_identity(
    primary_role: str,
    primary_goal: str,
    normalized_goals: List[str],
    interaction_styles: List[str],
    notes: str = ""
) -> AgentIdentity:
    """
    Build AgentIdentity from calculated parameters

    Args:
        primary_role: Calculated primary role
        primary_goal: User's primary goal
        normalized_goals: All user goals
        interaction_styles: Calculated interaction styles
        notes: Additional notes from intake

    Returns:
        AgentIdentity instance
    """
    return AgentIdentity(
        short_description=f"{primary_role} focused on {primary_goal}",
        full_description=f"I am your personalized {primary_role}, here to guide you toward {primary_goal}. {notes}",
        character_role=primary_role,
        mission=f"Help you achieve: {', '.join(normalized_goals)}",
        interaction_style=", ".join(interaction_styles)
    )


def build_agent_configuration() -> AgentConfiguration:
    """
    Build standard AgentConfiguration for guide agents

    Returns:
        AgentConfiguration with production defaults
    """
    return AgentConfiguration(
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        max_tokens=800,
        temperature=0.7,
        memory_enabled=True,
        voice_enabled=True,
        tools_enabled=False,
        memory_k=6,
        thread_window=20
    )


def build_voice_configuration(tone: str = "calm") -> VoiceConfiguration:
    """
    Build VoiceConfiguration with defaults

    Args:
        tone: Desired tone (affects voice selection in future)

    Returns:
        VoiceConfiguration with Rachel voice (calm default)
    """
    return VoiceConfiguration(
        provider="elevenlabs",
        voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel - calm female voice
        language="en-US",
        stability=0.75,
        similarity_boost=0.75
    )


def build_agent_contract(
    guide_name: str,
    identity: AgentIdentity,
    traits: AgentTraits,
    voice_config: VoiceConfiguration,
    tenant_id: str,
    user_id: str,
    tags: List[str]
) -> AgentContract:
    """
    Build complete AgentContract from components

    Args:
        guide_name: Name of the guide
        identity: Agent identity
        traits: Agent traits
        voice_config: Voice configuration
        tenant_id: Tenant UUID
        user_id: User UUID
        tags: List of tags

    Returns:
        Complete AgentContract
    """
    return AgentContract(
        name=guide_name,
        type=AgentType.CONVERSATIONAL,
        identity=identity,
        traits=traits,
        configuration=build_agent_configuration(),
        voice=voice_config,
        metadata=AgentMetadata(
            tenant_id=tenant_id,
            owner_id=user_id,
            tags=tags,
            status=AgentStatus.ACTIVE
        )
    )


async def create_session_with_protocol(
    user_id: str,
    agent_id: str,
    tenant_id: str,
    intake_contract: dict,
    normalized_goals: List[str]
) -> Tuple[str, dict]:
    """
    Create session and generate manifestation protocol

    Args:
        user_id: User UUID
        agent_id: Agent UUID
        tenant_id: Tenant UUID
        intake_contract: Original intake contract
        normalized_goals: User goals

    Returns:
        Tuple of (session_id, protocol_dict)
    """
    from database import get_pg_pool
    from agents.guide_agent.guide_sub_agents.manifestation_protocol_agent import ManifestationProtocolAgent
    import json

    pool = get_pg_pool()
    session_id = str(uuid.uuid4())

    # Create session
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO sessions (id, user_id, agent_id, tenant_id, status, session_data, created_at, updated_at)
            VALUES ($1, $2, $3::uuid, $4::uuid, 'active', $5, NOW(), NOW())
        """,
            session_id,
            user_id,
            agent_id,
            tenant_id,
            json.dumps({"intake_data": intake_contract})
        )

    logger.info(f"Session created: {session_id}")

    # Generate manifestation protocol
    protocol_agent = ManifestationProtocolAgent()
    protocol = await protocol_agent.generate_protocol({
        "user_id": user_id,
        "goal": normalized_goals[0] if normalized_goals else "Personal growth",
        "timeframe": "30_days",
        "commitment_level": "moderate"
    })

    logger.info(f"Protocol generated for session: {session_id}")

    # Update session with protocol
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE sessions
            SET session_data = jsonb_set(
                session_data,
                '{manifestation_protocol}',
                $1::jsonb
            )
            WHERE id = $2::uuid
        """, json.dumps(protocol), session_id)

    return session_id, protocol


async def store_protocol_in_memory(
    session_id: str,
    agent_id: str,
    user_id: str,
    tenant_id: str,
    protocol: dict,
    normalized_goals: List[str]
) -> None:
    """
    Store protocol summary in memory (non-blocking)

    Args:
        session_id: Session UUID
        agent_id: Agent UUID
        user_id: User UUID
        tenant_id: Tenant UUID (required for MemoryManager)
        protocol: Protocol dictionary
        normalized_goals: User goals
    """
    try:
        from memoryManager.memory_manager import MemoryManager

        # MemoryManager requires tenant_id, agent_id, and agent_traits
        if not tenant_id or not agent_id:
            logger.warning("Cannot store protocol in memory: missing tenant_id or agent_id")
            return
        
        memory_manager = MemoryManager(
            tenant_id=tenant_id,
            agent_id=agent_id,
            agent_traits={}  # Empty traits - can be enhanced if needed
        )

        # Store protocol summary in memory
        protocol_summary = (
            f"Generated manifestation protocol with "
            f"{len(protocol.get('affirmations', {}).get('all', []))} affirmations, "
            f"{len(protocol.get('daily_practices', []))} practices, "
            f"{len(protocol.get('checkpoints', []))} checkpoints."
        )

        await memory_manager.add_memory(
            content=protocol_summary,
            memory_type="protocol",
            user_id=user_id,
            metadata={
                "type": "manifestation_protocol",
                "session_id": str(session_id),
                "goals": normalized_goals,
                "affirmations_count": len(protocol.get('affirmations', {}).get('all', [])),
                "practices_count": len(protocol.get('daily_practices', [])),
                "checkpoints_count": len(protocol.get('checkpoints', []))
            }
        )

        logger.debug("Stored protocol in memory")

    except Exception as e:
        logger.warning(f"Failed to store protocol in memory: {e}")
        # Non-blocking - continue
