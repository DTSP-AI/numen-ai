"""
Dashboard API - Unified User Content View

Implements Dashboard Agent functionality:
- Get all user content (agents, affirmations, scripts)
- Schedule management
- Analytics and insights
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Dict, Any, List
import logging

from database import get_pg_pool

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard/user/{user_id}")
async def get_user_dashboard(
    user_id: str,
    tenant_id: str = Header(None, alias="x-tenant-id")
):
    """
    Get complete user dashboard

    Returns:
    - All affirmation agents created for user
    - All affirmations with audio
    - All hypnosis scripts
    - Schedule information
    - Usage analytics
    - Thread history
    """
    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            # Get user's agents
            agents_rows = await conn.fetch("""
                SELECT id, name, type, status, interaction_count,
                       last_interaction_at, created_at
                FROM agents
                WHERE owner_id = $1::uuid
                  AND tenant_id = $2::uuid
                  AND status = 'active'
                ORDER BY created_at DESC
            """, user_id, tenant_id or "00000000-0000-0000-0000-000000000001")

            agents = [
                {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "type": row["type"],
                    "interaction_count": row["interaction_count"],
                    "last_interaction_at": row["last_interaction_at"].isoformat() if row["last_interaction_at"] else None,
                    "created_at": row["created_at"].isoformat()
                }
                for row in agents_rows
            ]

            # Get affirmations count by category
            affirmations_stats = await conn.fetch("""
                SELECT category, COUNT(*) as count, COUNT(audio_url) as audio_count
                FROM affirmations
                WHERE user_id = $1::uuid AND status = 'active'
                GROUP BY category
            """, user_id)

            affirmation_summary = {
                row["category"]: {
                    "total": row["count"],
                    "with_audio": row["audio_count"]
                }
                for row in affirmations_stats
            }

            # Get hypnosis scripts count
            scripts_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM hypnosis_scripts
                WHERE user_id = $1::uuid AND status = 'active'
            """, user_id)

            # Get scheduled sessions
            scheduled_sessions = await conn.fetch("""
                SELECT id, scheduled_at, recurrence_rule, notification_sent
                FROM scheduled_sessions
                WHERE user_id = $1::uuid
                  AND executed_at IS NULL
                ORDER BY scheduled_at ASC
                LIMIT 10
            """, user_id)

            schedule = [
                {
                    "id": str(row["id"]),
                    "scheduled_at": row["scheduled_at"].isoformat(),
                    "recurrence": row["recurrence_rule"],
                    "notification_sent": row["notification_sent"]
                }
                for row in scheduled_sessions
            ]

            # Get recent threads
            threads = await conn.fetch("""
                SELECT t.id, t.agent_id, a.name as agent_name,
                       t.message_count, t.last_message_at
                FROM threads t
                JOIN agents a ON t.agent_id = a.id
                WHERE t.user_id = $1::uuid
                  AND t.status = 'active'
                ORDER BY t.last_message_at DESC NULLS LAST
                LIMIT 5
            """, user_id)

            recent_threads = [
                {
                    "id": str(row["id"]),
                    "agent_id": str(row["agent_id"]),
                    "agent_name": row["agent_name"],
                    "message_count": row["message_count"],
                    "last_message_at": row["last_message_at"].isoformat() if row["last_message_at"] else None
                }
                for row in threads
            ]

        return {
            "user_id": user_id,
            "summary": {
                "total_agents": len(agents),
                "total_affirmations": sum(cat["total"] for cat in affirmation_summary.values()),
                "total_scripts": scripts_count,
                "upcoming_sessions": len(schedule)
            },
            "agents": agents,
            "affirmations_by_category": affirmation_summary,
            "schedule": schedule,
            "recent_threads": recent_threads
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard")


@router.post("/dashboard/schedule")
async def create_scheduled_session(
    user_id: str = Header(..., alias="x-user-id"),
    affirmation_id: str = None,
    script_id: str = None,
    scheduled_at: str = None,
    recurrence_rule: str = None
):
    """
    Schedule an affirmation or script session

    Examples:
    - Schedule morning affirmations daily
    - Schedule hypnosis script weekly
    """
    pool = get_pg_pool()

    try:
        from datetime import datetime
        scheduled_dt = datetime.fromisoformat(scheduled_at)

        async with pool.acquire() as conn:
            session_id = await conn.fetchval("""
                INSERT INTO scheduled_sessions (
                    id, user_id, affirmation_id, script_id,
                    scheduled_at, recurrence_rule,
                    created_at, updated_at
                )
                VALUES (gen_random_uuid(), $1::uuid, $2::uuid, $3::uuid, $4, $5, NOW(), NOW())
                RETURNING id
            """, user_id, affirmation_id, script_id, scheduled_dt, recurrence_rule)

        return {
            "status": "success",
            "session_id": str(session_id),
            "scheduled_at": scheduled_at
        }

    except Exception as e:
        logger.error(f"Failed to create scheduled session: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule session")
