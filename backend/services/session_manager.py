"""
Session Manager - PostgreSQL-based session storage

Replaces Redis for session management using Supabase PostgreSQL.

Benefits:
- No separate Redis service needed
- ACID guarantees
- Better for persistent sessions
- Automatic TTL via PostgreSQL
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import json

from database import get_pg_pool

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session management using PostgreSQL
    Replaces Redis for session storage
    """

    @staticmethod
    async def create_session(
        session_id: str,
        user_id: str,
        agent_id: Optional[str],
        tenant_id: str,
        status: str = "pending",
        room_name: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = 3600
    ) -> Dict[str, Any]:
        """
        Create or update session in PostgreSQL

        Args:
            session_id: Session UUID
            user_id: User identifier
            agent_id: Agent UUID (optional)
            tenant_id: Tenant UUID
            status: Session status
            room_name: LiveKit room name (optional)
            data: Session data dictionary
            ttl_seconds: Time-to-live in seconds

        Returns:
            Session dictionary
        """
        pool = get_pg_pool()
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO sessions (
                        id, user_id, agent_id, tenant_id,
                        status, room_name, session_data, expires_at,
                        created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        session_data = $7,
                        expires_at = $8,
                        updated_at = NOW(),
                        status = $5
                """,
                    UUID(session_id),
                    user_id,
                    UUID(agent_id) if agent_id else None,
                    UUID(tenant_id),
                    status,
                    room_name,
                    json.dumps(data or {}),
                    expires_at
                )

            logger.info(f"✅ Session created/updated: {session_id}")

            return {
                "session_id": session_id,
                "user_id": user_id,
                "agent_id": agent_id,
                "tenant_id": tenant_id,
                "status": status,
                "room_name": room_name,
                "data": data or {},
                "expires_at": expires_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise

    @staticmethod
    async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session from PostgreSQL

        Args:
            session_id: Session UUID

        Returns:
            Session dictionary or None if not found/expired
        """
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT
                        id, user_id, agent_id, tenant_id,
                        status, room_name, session_data, expires_at,
                        created_at, updated_at
                    FROM sessions
                    WHERE id = $1 AND (expires_at IS NULL OR expires_at > NOW())
                """, UUID(session_id))

                if row:
                    return {
                        "session_id": str(row['id']),
                        "user_id": row['user_id'],
                        "agent_id": str(row['agent_id']) if row['agent_id'] else None,
                        "tenant_id": str(row['tenant_id']) if row['tenant_id'] else None,
                        "status": row['status'],
                        "room_name": row['room_name'],
                        "data": json.loads(row['session_data']) if row['session_data'] else {},
                        "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None,
                        "created_at": row['created_at'].isoformat(),
                        "updated_at": row['updated_at'].isoformat()
                    }

                return None

        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None

    @staticmethod
    async def update_session_data(
        session_id: str,
        data: Dict[str, Any],
        extend_ttl: bool = True,
        ttl_seconds: int = 3600
    ) -> bool:
        """
        Update session data

        Args:
            session_id: Session UUID
            data: New session data
            extend_ttl: Whether to extend expiration time
            ttl_seconds: TTL extension in seconds

        Returns:
            True if updated, False otherwise
        """
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                if extend_ttl:
                    expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
                    result = await conn.execute("""
                        UPDATE sessions
                        SET session_data = $1,
                            expires_at = $2,
                            updated_at = NOW()
                        WHERE id = $3
                    """, json.dumps(data), expires_at, UUID(session_id))
                else:
                    result = await conn.execute("""
                        UPDATE sessions
                        SET session_data = $1,
                            updated_at = NOW()
                        WHERE id = $2
                    """, json.dumps(data), UUID(session_id))

                return result != "UPDATE 0"

        except Exception as e:
            logger.error(f"Failed to update session data: {e}")
            return False

    @staticmethod
    async def update_session_status(
        session_id: str,
        status: str
    ) -> bool:
        """
        Update session status

        Args:
            session_id: Session UUID
            status: New status

        Returns:
            True if updated, False otherwise
        """
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE sessions
                    SET status = $1, updated_at = NOW()
                    WHERE id = $2
                """, status, UUID(session_id))

                return result != "UPDATE 0"

        except Exception as e:
            logger.error(f"Failed to update session status: {e}")
            return False

    @staticmethod
    async def delete_session(session_id: str) -> bool:
        """
        Delete session

        Args:
            session_id: Session UUID

        Returns:
            True if deleted, False otherwise
        """
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM sessions WHERE id = $1",
                    UUID(session_id)
                )

                return result != "DELETE 0"

        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    @staticmethod
    async def cleanup_expired_sessions() -> int:
        """
        Delete all expired sessions

        Returns:
            Number of sessions deleted
        """
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM sessions
                    WHERE expires_at IS NOT NULL AND expires_at < NOW()
                """)

                # Extract count from result string (e.g., "DELETE 5")
                count = int(result.split()[-1]) if result != "DELETE 0" else 0
                if count > 0:
                    logger.info(f"🧹 Cleaned up {count} expired sessions")

                return count

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    @staticmethod
    async def get_active_sessions_by_user(
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user

        Args:
            user_id: User identifier
            tenant_id: Optional tenant filter

        Returns:
            List of active session dictionaries
        """
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                query = """
                    SELECT
                        id, user_id, agent_id, tenant_id,
                        status, room_name, session_data, expires_at,
                        created_at, updated_at
                    FROM sessions
                    WHERE user_id = $1
                      AND (expires_at IS NULL OR expires_at > NOW())
                      AND status NOT IN ('completed', 'failed')
                """
                params = [user_id]

                if tenant_id:
                    query += " AND tenant_id = $2"
                    params.append(UUID(tenant_id))

                query += " ORDER BY created_at DESC"

                rows = await conn.fetch(query, *params)

                return [
                    {
                        "session_id": str(row['id']),
                        "user_id": row['user_id'],
                        "agent_id": str(row['agent_id']) if row['agent_id'] else None,
                        "tenant_id": str(row['tenant_id']) if row['tenant_id'] else None,
                        "status": row['status'],
                        "room_name": row['room_name'],
                        "data": json.loads(row['session_data']) if row['session_data'] else {},
                        "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None,
                        "created_at": row['created_at'].isoformat(),
                        "updated_at": row['updated_at'].isoformat()
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []


# Backward compatibility with old memory.py interface
async def store_session_data(session_id: str, user_id: str, data: Dict[str, Any]):
    """Store session data (backward compatible)"""
    await SessionManager.update_session_data(session_id, data)


async def get_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session data (backward compatible)"""
    session = await SessionManager.get_session(session_id)
    return session.get("data") if session else None
