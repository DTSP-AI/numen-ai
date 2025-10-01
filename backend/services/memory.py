"""
Memory Service - Streamlined with Supabase pgvector

This replaces the old Qdrant-based memory system with Supabase pgvector,
eliminating the need for external Qdrant service while maintaining
backward compatibility with the existing MemoryService interface.

Architecture:
- Supabase pgvector for vector similarity search
- Direct SQL queries (no Qdrant dependency)
- Namespace isolation for multi-tenancy
- Single database connection
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import openai
import os

from database import get_pg_pool

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Streamlined memory service using Supabase pgvector

    Maintains backward compatibility with old MemoryService interface
    while using pgvector instead of Qdrant internally.
    """

    def __init__(self):
        from config import settings
        self.embedding_model = "text-embedding-ada-002"
        self.embedding_dimension = 1536
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key or os.getenv("OPENAI_API_KEY"))
        logger.info("✅ MemoryService initialized (using Supabase pgvector)")

    async def initialize(self):
        """
        Initialize memory service (no-op for backward compatibility)

        Old version initialized Qdrant client here.
        New version uses Supabase connection from database.py
        """
        logger.info("✅ Memory service ready (Supabase pgvector)")

    async def store_user_preferences(
        self,
        user_id: str,
        preferences: Dict
    ):
        """Store persistent user preferences in user namespace"""
        pool = get_pg_pool()

        try:
            content = f"User preferences: {preferences}"

            # Generate embedding
            embedding_response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=content
            )
            embedding = embedding_response.data[0].embedding

            # Store in pgvector
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO memory_embeddings (
                        tenant_id, agent_id, user_id,
                        content, embedding,
                        namespace, memory_type, metadata,
                        created_at, updated_at
                    )
                    VALUES (
                        (SELECT id FROM tenants LIMIT 1), -- Default tenant for now
                        (SELECT id FROM agents LIMIT 1),  -- Default agent for now
                        $1::uuid,
                        $2,
                        $3::vector,
                        $4,
                        'preferences',
                        $5,
                        NOW(),
                        NOW()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        content = $2,
                        embedding = $3::vector,
                        metadata = $5,
                        updated_at = NOW()
                """,
                    user_id,
                    content,
                    embedding,
                    f"user:{user_id}",
                    preferences
                )

            logger.info(f"✅ Stored preferences for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to store user preferences: {e}")
            raise

    async def get_user_preferences(
        self,
        user_id: str
    ) -> Optional[Dict]:
        """Retrieve user preferences from memory"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT metadata
                    FROM memory_embeddings
                    WHERE user_id = $1::uuid
                      AND memory_type = 'preferences'
                    ORDER BY created_at DESC
                    LIMIT 1
                """, user_id)

                if row:
                    return row['metadata']
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve user preferences: {e}")
            return None

    async def store_session_reflection(
        self,
        session_id: str,
        user_id: str,
        reflection: str
    ):
        """Store session reflection in session namespace"""
        pool = get_pg_pool()

        try:
            # Generate embedding
            embedding_response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=reflection
            )
            embedding = embedding_response.data[0].embedding

            # Store in pgvector
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO memory_embeddings (
                        tenant_id, agent_id, user_id,
                        content, embedding,
                        namespace, memory_type, metadata,
                        created_at, updated_at
                    )
                    VALUES (
                        (SELECT id FROM tenants LIMIT 1),
                        (SELECT id FROM agents LIMIT 1),
                        $1::uuid,
                        $2,
                        $3::vector,
                        $4,
                        'reflection',
                        $5,
                        NOW(),
                        NOW()
                    )
                """,
                    user_id,
                    reflection,
                    embedding,
                    f"session:{session_id}",
                    {"session_id": session_id, "timestamp": datetime.utcnow().isoformat()}
                )

            logger.info(f"✅ Stored reflection for session {session_id}")

        except Exception as e:
            logger.error(f"Failed to store session reflection: {e}")
            raise

    async def get_session_history(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """Retrieve recent session reflections"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT content, metadata, created_at
                    FROM memory_embeddings
                    WHERE user_id = $1::uuid
                      AND memory_type = 'reflection'
                    ORDER BY created_at DESC
                    LIMIT $2
                """, user_id, limit)

                return [
                    {
                        "session_id": row['metadata'].get("session_id"),
                        "content": row['content'],
                        "timestamp": row['created_at'].isoformat()
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to retrieve session history: {e}")
            return []

    async def store_session_data(
        self,
        session_id: str,
        user_id: str,
        data: Dict
    ):
        """Store complete session data including script and contract"""
        pool = get_pg_pool()

        try:
            import json
            session_summary = json.dumps(data)

            # Generate embedding
            embedding_response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=session_summary[:8000]  # Truncate for embedding
            )
            embedding = embedding_response.data[0].embedding

            # Store in pgvector
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO memory_embeddings (
                        tenant_id, agent_id, user_id,
                        content, embedding,
                        namespace, memory_type, metadata,
                        created_at, updated_at
                    )
                    VALUES (
                        (SELECT id FROM tenants LIMIT 1),
                        (SELECT id FROM agents LIMIT 1),
                        $1::uuid,
                        $2,
                        $3::vector,
                        $4,
                        'session_data',
                        $5,
                        NOW(),
                        NOW()
                    )
                """,
                    user_id,
                    session_summary,
                    embedding,
                    f"session:{session_id}",
                    {"session_id": session_id, **data}
                )

            logger.info(f"✅ Stored session data for {session_id}")

        except Exception as e:
            logger.error(f"Failed to store session data: {e}")
            raise

    async def clear_session_memory(
        self,
        session_id: str
    ):
        """Clear ephemeral session memory"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM memory_embeddings
                    WHERE namespace = $1
                """, f"session:{session_id}")

                logger.info(f"✅ Cleared session memory for {session_id}")

        except Exception as e:
            logger.error(f"Failed to clear session memory: {e}")

    # New enhanced methods for AGENT_CREATION_STANDARD

    async def store_memory(
        self,
        tenant_id: str,
        agent_id: str,
        user_id: Optional[str],
        content: str,
        namespace: str,
        memory_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store memory with full namespace support

        This is the new enhanced method for AGENT_CREATION_STANDARD
        """
        pool = get_pg_pool()

        try:
            # Generate embedding
            embedding_response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=content
            )
            embedding = embedding_response.data[0].embedding

            # Store in pgvector
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO memory_embeddings (
                        tenant_id, agent_id, user_id,
                        content, embedding,
                        namespace, memory_type, metadata,
                        created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5::vector, $6, $7, $8, NOW(), NOW())
                """,
                    tenant_id,
                    agent_id,
                    user_id,
                    content,
                    embedding,
                    namespace,
                    memory_type,
                    metadata or {}
                )

            logger.info(f"✅ Memory stored in namespace: {namespace}")

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise

    async def search_memories(
        self,
        query: str,
        namespace: str,
        limit: int = 6,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories via pgvector similarity

        This is the new enhanced method for AGENT_CREATION_STANDARD
        """
        pool = get_pg_pool()

        try:
            # Generate query embedding
            embedding_response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=query
            )
            query_embedding = embedding_response.data[0].embedding

            # Search via cosine similarity
            async with pool.acquire() as conn:
                query_sql = """
                    SELECT
                        content,
                        memory_type,
                        metadata,
                        created_at,
                        1 - (embedding <=> $1::vector) AS similarity
                    FROM memory_embeddings
                    WHERE namespace = $2
                """
                params = [query_embedding, namespace]

                if memory_type:
                    query_sql += " AND memory_type = $3"
                    params.append(memory_type)

                query_sql += f"""
                    ORDER BY embedding <=> $1::vector
                    LIMIT ${len(params) + 1}
                """
                params.append(limit)

                rows = await conn.fetch(query_sql, *params)

                return [
                    {
                        "content": row['content'],
                        "memory_type": row['memory_type'],
                        "metadata": row['metadata'],
                        "created_at": row['created_at'].isoformat(),
                        "similarity": float(row['similarity'])
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []
