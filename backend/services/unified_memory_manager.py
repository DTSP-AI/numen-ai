"""
Unified Memory Manager - Streamlined with Supabase pgvector

Replaces:
- Qdrant (vector store) → Supabase pgvector
- Complex Mem0 setup → Simple direct pgvector access
- Multiple services → Single Supabase connection

This implementation uses Supabase's pgvector extension for vector similarity search,
eliminating the need for external Qdrant service.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
import openai
import os
import json

from database import get_pg_pool
from config import settings as config_settings

logger = logging.getLogger(__name__)


class MemorySettings(BaseModel):
    """Memory system configuration"""
    k: int = 6  # Number of memories to retrieve
    thread_window: int = 20  # Recent messages to include
    alpha_recency: float = 0.35  # Recency weight
    alpha_semantic: float = 0.45  # Semantic similarity weight
    alpha_reinforcement: float = 0.20  # Reinforcement weight
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536


class MemoryContext(BaseModel):
    """Memory context returned for agent processing"""
    retrieved_memories: List[Dict[str, Any]]
    recent_messages: List[Dict[str, Any]]
    confidence_score: float
    namespace: str


class UnifiedMemoryManager:
    """
    Unified memory manager using Supabase pgvector

    Architecture:
    - Single Supabase connection
    - pgvector for similarity search
    - Namespace isolation: {tenant_id}:{agent_id}:{context}
    - Direct SQL queries (no external dependencies)
    """

    def __init__(
        self,
        tenant_id: str,
        agent_id: str,
        agent_traits: Dict[str, Any],
        settings: Optional[MemorySettings] = None
    ):
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.agent_traits = agent_traits
        self.settings = settings or MemorySettings()

        # Namespace pattern: {tenant_id}:{agent_id}
        self.namespace = f"{tenant_id}:{agent_id}"

        # OpenAI for embeddings
        self.openai_client = openai.OpenAI(api_key=config_settings.openai_api_key)

    def agent_namespace(self) -> str:
        """Get agent-level namespace"""
        return self.namespace

    def thread_namespace(self, thread_id: str) -> str:
        """Get thread-level namespace"""
        return f"{self.namespace}:thread:{thread_id}"

    def user_namespace(self, user_id: str) -> str:
        """Get user-level namespace"""
        return f"{self.namespace}:user:{user_id}"

    async def add_memory(
        self,
        content: str,
        memory_type: str = "reflection",
        namespace: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store memory in Supabase pgvector

        Args:
            content: Memory text content
            memory_type: Type of memory (reflection, fact, preference, etc.)
            namespace: Override default namespace
            user_id: Optional user ID for user-specific memories
            metadata: Additional metadata
        """
        pool = get_pg_pool()

        try:
            # Generate embedding
            embedding_response = self.openai_client.embeddings.create(
                model=self.settings.embedding_model,
                input=content
            )
            embedding = embedding_response.data[0].embedding

            # Use provided namespace or default
            final_namespace = namespace or self.namespace

            # Store in pgvector
            # Convert embedding list to PostgreSQL vector format string
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'

            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO memory_embeddings (
                        tenant_id, agent_id, user_id,
                        content, embedding,
                        namespace, memory_type, metadata,
                        access_count, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5::vector, $6, $7, $8, 0, NOW(), NOW())
                """,
                    self.tenant_id,
                    self.agent_id,
                    user_id,
                    content,
                    embedding_str,
                    final_namespace,
                    memory_type,
                    json.dumps(metadata or {})
                )

            logger.info(f"✅ Memory stored in namespace: {final_namespace}")

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise

    async def search_memories(
        self,
        query: str,
        namespace: Optional[str] = None,
        limit: int = None,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories via pgvector similarity

        Args:
            query: Search query text
            namespace: Override default namespace
            limit: Number of results (default from settings)
            memory_type: Filter by memory type

        Returns:
            List of memory dictionaries with content, metadata, and similarity score
        """
        pool = get_pg_pool()
        limit = limit or self.settings.k

        try:
            # Generate query embedding
            embedding_response = self.openai_client.embeddings.create(
                model=self.settings.embedding_model,
                input=query
            )
            query_embedding = embedding_response.data[0].embedding

            # Search via cosine similarity
            final_namespace = namespace or self.namespace

            async with pool.acquire() as conn:
                query_sql = """
                    SELECT
                        id,
                        content,
                        memory_type,
                        metadata,
                        created_at,
                        access_count,
                        1 - (embedding <=> $1::vector) AS similarity
                    FROM memory_embeddings
                    WHERE namespace = $2
                """
                params = [query_embedding, final_namespace]

                # Add memory type filter if specified
                if memory_type:
                    query_sql += " AND memory_type = $3"
                    params.append(memory_type)

                query_sql += """
                    ORDER BY embedding <=> $1::vector
                    LIMIT $""" + str(len(params) + 1)
                params.append(limit)

                rows = await conn.fetch(query_sql, *params)

                # Update access count
                memory_ids = [row['id'] for row in rows]
                if memory_ids:
                    await conn.execute("""
                        UPDATE memory_embeddings
                        SET access_count = access_count + 1,
                            last_accessed_at = NOW()
                        WHERE id = ANY($1::uuid[])
                    """, memory_ids)

                return [
                    {
                        "content": row['content'],
                        "memory_type": row['memory_type'],
                        "metadata": row['metadata'],
                        "created_at": row['created_at'].isoformat(),
                        "access_count": row['access_count'],
                        "similarity": float(row['similarity'])
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []

    async def get_agent_context(
        self,
        user_input: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> MemoryContext:
        """
        Get memory context for agent processing

        Retrieves:
        1. Semantic memories from agent namespace
        2. Recent thread messages
        3. User-specific memories (if user_id provided)

        Returns:
            MemoryContext with retrieved memories and confidence score
        """
        thread_namespace = self.thread_namespace(session_id)

        try:
            # Semantic search in agent namespace
            semantic_memories = await self.search_memories(
                query=user_input,
                namespace=self.namespace,
                limit=self.settings.k
            )

            # User-specific memories (if applicable)
            user_memories = []
            if user_id:
                user_memories = await self.search_memories(
                    query=user_input,
                    namespace=self.user_namespace(user_id),
                    limit=3
                )

            # Get recent thread messages (from thread_messages table)
            recent_messages = await self._get_recent_thread_messages(
                session_id=session_id,
                limit=self.settings.thread_window
            )

            # Combine and calculate confidence
            all_memories = semantic_memories + user_memories
            confidence_score = self._calculate_confidence(all_memories)

            return MemoryContext(
                retrieved_memories=all_memories,
                recent_messages=recent_messages,
                confidence_score=confidence_score,
                namespace=thread_namespace
            )

        except Exception as e:
            logger.error(f"Failed to get agent context: {e}")
            return MemoryContext(
                retrieved_memories=[],
                recent_messages=[],
                confidence_score=0.0,
                namespace=thread_namespace
            )

    async def process_interaction(
        self,
        user_input: str,
        agent_response: str,
        session_id: str,
        user_id: Optional[str] = None
    ):
        """Process and store interaction in memory"""
        thread_namespace = self.thread_namespace(session_id)

        try:
            # Store conversation turn as memory
            conversation_memory = f"User: {user_input}\nAgent: {agent_response}"

            await self.add_memory(
                content=conversation_memory,
                memory_type="conversation",
                namespace=thread_namespace,
                user_id=user_id,
                metadata={
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            logger.info(f"✅ Interaction stored in namespace: {thread_namespace}")

        except Exception as e:
            logger.error(f"Failed to process interaction: {e}")

    async def _get_recent_thread_messages(
        self,
        session_id: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get recent thread messages from database"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT role, content, created_at, metadata
                    FROM thread_messages
                    WHERE thread_id = (
                        SELECT id FROM threads WHERE id::text = $1
                    )
                    ORDER BY created_at DESC
                    LIMIT $2
                """, session_id, limit)

                return [
                    {
                        "role": row['role'],
                        "content": row['content'],
                        "created_at": row['created_at'].isoformat(),
                        "metadata": row['metadata']
                    }
                    for row in reversed(list(rows))
                ]

        except Exception as e:
            logger.warning(f"Could not fetch thread messages: {e}")
            return []

    def _calculate_confidence(self, memories: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on memory relevance"""
        if not memories:
            return 0.0

        # Average similarity score
        avg_score = sum(m.get("similarity", 0.0) for m in memories) / len(memories)
        return min(avg_score, 1.0)


# Convenience functions for backward compatibility
async def store_user_preferences(
    user_id: str,
    tenant_id: str,
    agent_id: str,
    preferences: Dict[str, Any]
):
    """Store user preferences in memory"""
    manager = UnifiedMemoryManager(tenant_id, agent_id, {})
    await manager.add_memory(
        content=f"User preferences: {preferences}",
        memory_type="preference",
        namespace=manager.user_namespace(user_id),
        user_id=user_id,
        metadata=preferences
    )


async def get_user_preferences(
    user_id: str,
    tenant_id: str,
    agent_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieve user preferences from memory"""
    manager = UnifiedMemoryManager(tenant_id, agent_id, {})
    memories = await manager.search_memories(
        query="user preferences",
        namespace=manager.user_namespace(user_id),
        limit=1,
        memory_type="preference"
    )

    if memories:
        return memories[0].get("metadata", {})
    return None
