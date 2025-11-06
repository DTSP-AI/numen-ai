"""
Affirmation Generation Helper Functions

Breaks down the large generate_affirmations() function into smaller,
testable components.
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def fetch_agent_contract(agent_id: str, conn) -> Tuple[str, dict]:
    """
    Fetch agent contract from database

    Args:
        agent_id: Agent UUID
        conn: Database connection

    Returns:
        Tuple of (agent_name, contract_dict)

    Raises:
        ValueError: If agent not found
    """
    agent_row = await conn.fetchrow("""
        SELECT id, name, contract
        FROM agents
        WHERE id = $1::uuid
    """, agent_id)

    if not agent_row:
        raise ValueError("Agent not found")

    return agent_row["name"], agent_row["contract"]


async def fetch_session_metadata(session_id: Optional[str], conn) -> Tuple[List[str], str, str]:
    """
    Fetch session metadata and extract goals

    Args:
        session_id: Optional session UUID
        conn: Database connection

    Returns:
        Tuple of (goals, commitment_level, timeframe)
    """
    goals = []
    commitment_level = "moderate"
    timeframe = "30_days"

    if session_id:
        session_row = await conn.fetchrow("""
            SELECT session_data
            FROM sessions
            WHERE id = $1::uuid
        """, session_id)

        if session_row and session_row["session_data"]:
            session_data = session_row["session_data"]
            intake_data = session_data.get("metadata", {}).get("intake_data", {})
            goals = intake_data.get("goals", [])

            # Map session type to commitment level and timeframe
            session_type = intake_data.get("session_type", "manifestation")
            if session_type in ["intensive", "habit_change"]:
                commitment_level = "intensive"
                timeframe = "90_days"
            elif session_type in ["anxiety_relief", "sleep_hypnosis"]:
                commitment_level = "light"
                timeframe = "7_days"

    return goals, commitment_level, timeframe


async def generate_protocol_with_agent(
    user_id: str,
    primary_goal: str,
    timeframe: str,
    commitment_level: str
) -> dict:
    """
    Generate manifestation protocol using ManifestationProtocolAgent

    Args:
        user_id: User UUID
        primary_goal: Primary goal text
        timeframe: Timeframe (7_days, 30_days, 90_days)
        commitment_level: Commitment level (light, moderate, intensive)

    Returns:
        Protocol dictionary
    """
    from agents.guide_agent.guide_sub_agents.manifestation_protocol_agent import ManifestationProtocolAgent

    logger.info(f"Generating manifestation protocol for goal: {primary_goal}")

    protocol_agent = ManifestationProtocolAgent()
    protocol = await protocol_agent.generate_protocol(
        user_id=user_id,
        goal=primary_goal,
        timeframe=timeframe,
        commitment_level=commitment_level
    )

    return protocol


def determine_affirmation_category(text: str) -> str:
    """
    Determine affirmation category based on content

    Args:
        text: Affirmation text

    Returns:
        Category string (identity, gratitude, action)
    """
    text_lower = text.lower()

    if "i am" in text:
        return "identity"
    elif "grateful" in text_lower or "thankful" in text_lower:
        return "gratitude"
    else:
        return "action"


def assign_schedule_to_affirmation(
    idx: int,
    daily_rotation: dict
) -> Tuple[Optional[str], Optional[str]]:
    """
    Assign schedule to affirmation using daily rotation

    Args:
        idx: Affirmation index
        daily_rotation: Daily rotation schedule from protocol

    Returns:
        Tuple of (schedule_type, schedule_time)
    """
    days = list(daily_rotation.keys())

    if not days:
        return None, None

    day_idx = idx % len(days)
    schedule_day = days[day_idx]

    # Default morning time
    return "daily", "08:00:00"


async def store_affirmations_in_db(
    affirmations: List[str],
    daily_rotation: dict,
    user_id: str,
    agent_id: str,
    tenant_id: str,
    count: int,
    conn
) -> List[dict]:
    """
    Store affirmations in database

    Args:
        affirmations: List of affirmation texts
        daily_rotation: Daily rotation schedule
        user_id: User UUID
        agent_id: Agent UUID
        tenant_id: Tenant UUID
        count: Max number to store
        conn: Database connection

    Returns:
        List of stored affirmation dictionaries
    """
    generated_affirmations = []

    for idx, affirmation_text in enumerate(affirmations[:count]):
        # Determine category
        category = determine_affirmation_category(affirmation_text)

        # Assign schedule
        schedule_type, schedule_time = assign_schedule_to_affirmation(idx, daily_rotation)

        # Determine schedule day
        days = list(daily_rotation.keys())
        day_idx = idx % len(days) if days else 0
        schedule_day = days[day_idx] if days else None

        # Insert affirmation
        aff_id = await conn.fetchval("""
            INSERT INTO affirmations (
                user_id, agent_id, tenant_id, affirmation_text,
                category, status, schedule_type, schedule_time
            )
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, 'active', $6, $7::time)
            RETURNING id
        """, user_id, agent_id, tenant_id, affirmation_text, category, schedule_type, schedule_time)

        generated_affirmations.append({
            "id": str(aff_id),
            "affirmation_text": affirmation_text,
            "category": category,
            "audio_url": None,
            "play_count": 0,
            "is_favorite": False,
            "schedule_day": schedule_day,
            "created_at": datetime.utcnow().isoformat()
        })

    return generated_affirmations


async def update_session_with_protocol(
    session_id: Optional[str],
    protocol: dict,
    conn
) -> None:
    """
    Update session with generated protocol

    Args:
        session_id: Session UUID
        protocol: Protocol dictionary
        conn: Database connection
    """
    if session_id:
        await conn.execute("""
            UPDATE sessions
            SET session_data = session_data || $1::jsonb
            WHERE id = $2::uuid
        """, {"manifestation_protocol": protocol}, session_id)


def build_protocol_summary(protocol: dict) -> dict:
    """
    Build protocol summary for API response

    Args:
        protocol: Protocol dictionary

    Returns:
        Summary dictionary
    """
    return {
        "daily_practices": len(protocol.get("daily_practices", [])),
        "visualizations": len(protocol.get("visualizations", [])),
        "success_metrics": len(protocol.get("success_metrics", [])),
        "checkpoints": len(protocol.get("checkpoints", []))
    }
