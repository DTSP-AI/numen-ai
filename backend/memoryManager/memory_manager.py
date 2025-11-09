"""
Mem0-Based Memory Manager - Standards Compliant
Implements AGENT_CREATION_STANDARD.md Section: Memory System Architecture

Uses Mem0 cloud service for persistent agent memory with semantic search.
Replaces local FAISS vector store with Mem0's managed infrastructure.

Architecture:
- Mem0 cloud API for all memory operations
- Namespace isolation: {tenant_id}:{agent_id}
- Thread-specific and user-specific memory contexts
- No local vector store - fully cloud-based
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
import os

from mem0 import MemoryClient
from config import settings

logger = logging.getLogger(__name__)


class MemoryContext(BaseModel):
    """Memory context returned for agent processing"""
    retrieved_memories: List[Dict[str, Any]]
    recent_messages: List[Dict[str, Any]]
    confidence_score: float
    namespace: str


class MemoryManager:
    """
    Memory Manager for agents (AGENT_CREATION_STANDARD compliant)

    Implementation: Mem0 cloud-based semantic memory service

    Architecture:
    - Single Mem0 cloud connection
    - Namespace isolation per tenant/agent
    - Semantic search via Mem0 API
    - No local dependencies (FAISS, Qdrant)

    Namespace Pattern:
    - Agent: {tenant_id}:{agent_id}
    - Thread: {tenant_id}:{agent_id}:thread:{thread_id}
    - User: {tenant_id}:{agent_id}:user:{user_id}
    """

    def __init__(
        self,
        tenant_id: str,
        agent_id: str,
        agent_traits: Dict[str, Any]
    ):
        """
        Initialize Mem0-based memory manager

        Args:
            tenant_id: Tenant UUID for namespace isolation
            agent_id: Agent UUID for namespace isolation
            agent_traits: Agent trait values for context
        """
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.agent_traits = agent_traits

        # Namespace pattern: {tenant_id}:{agent_id}
        self.namespace = f"{tenant_id}:{agent_id}"

        # Initialize Mem0 client (API key from environment)
        mem0_api_key = (
            os.environ.get("MEM0_API_KEY") or
            os.environ.get("mem0_api_key") or
            getattr(settings, 'mem0_api_key', None) or
            getattr(settings, 'MEM0_API_KEY', None)
        )

        if not mem0_api_key:
            logger.warning("MEM0_API_KEY not set - memory operations will fail")
            self.client = None
        else:
            self.client = MemoryClient(api_key=mem0_api_key)
            logger.info(f"Mem0 client initialized for namespace: {self.namespace}")

    # ========================================================================
    # NAMESPACE METHODS (AGENT_CREATION_STANDARD Pattern)
    # ========================================================================

    def agent_namespace(self) -> str:
        """Get agent-level namespace"""
        return self.namespace

    def thread_namespace(self, thread_id: str) -> str:
        """Get thread-level namespace"""
        return f"{self.namespace}:thread:{thread_id}"

    def user_namespace(self, user_id: str) -> str:
        """Get user-level namespace"""
        return f"{self.namespace}:user:{user_id}"

    # ========================================================================
    # CORE MEMORY OPERATIONS
    # ========================================================================

    async def store_interaction(
        self,
        role: str,
        content: str,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Persist a message to Mem0 for later retrieval

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            session_id: Thread/session ID
            user_id: Optional user ID for user-specific memory
            metadata: Additional metadata
        """
        if not self.client:
            logger.error("Mem0 client not initialized - skipping storage")
            return

        try:
            # Prepare memory payload
            memory_metadata = {
                "role": role,
                "session_id": session_id,
                "agent_id": self.agent_id,
                "tenant_id": self.tenant_id,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }

            if user_id:
                memory_metadata["user_id"] = user_id

            # Store in Mem0 with thread namespace
            namespace = self.thread_namespace(session_id)

            self.client.add(
                messages=[{"role": role, "content": content}],
                user_id=namespace,  # Mem0 uses user_id as namespace
                metadata=memory_metadata
            )

            logger.info(f"✅ Stored {role} message in Mem0 namespace: {namespace}")

        except Exception as e:
            logger.error(f"Failed to store interaction in Mem0: {e}")
            # Non-blocking - continue execution

    async def get_agent_context(
        self,
        user_input: str,
        session_id: str,
        user_id: Optional[str] = None,
        k: int = 5
    ) -> MemoryContext:
        """
        Retrieve the top-k most relevant past interactions using Mem0 search

        CRITICAL: Recent thread messages MUST be retrieved from database regardless of Mem0 status.

        Args:
            user_input: Current user input for semantic search
            session_id: Thread/session ID
            user_id: Optional user ID for user-specific memories
            k: Number of memories to retrieve (default 5)

        Returns:
            MemoryContext with retrieved memories and confidence score
        """
        # ALWAYS get recent thread messages from database (Layer 1: Short-term memory)
        # This MUST happen regardless of Mem0 status
        recent_messages = await self._get_recent_thread_messages(session_id, limit=10)
        logger.info(f"📜 Retrieved {len(recent_messages)} recent messages from database")

        if not self.client:
            logger.warning("Mem0 client not initialized - returning context with DB messages only")
            return MemoryContext(
                retrieved_memories=[],
                recent_messages=recent_messages,
                confidence_score=0.0,
                namespace=self.thread_namespace(session_id)
            )

        try:
            # Search in thread namespace (Layer 2: Long-term memory)
            namespace = self.thread_namespace(session_id)

            results = self.client.search(
                query=user_input,
                user_id=namespace,
                limit=k
            )

            # Extract memory content and compute average relevance score
            memories = []
            total_score = 0.0

            # Mem0 returns a list directly, not a dict with "results"
            results_list = results if isinstance(results, list) else results.get("results", [])

            for result in results_list:
                memory_content = result.get("memory", "")
                score = result.get("score", 0.0)
                metadata = result.get("metadata", {})

                memories.append({
                    "content": memory_content,
                    "score": score,
                    "metadata": metadata,
                    "created_at": metadata.get("timestamp", "")
                })

                total_score += score

            avg_score = total_score / max(len(memories), 1)

            logger.info(f"✅ Retrieved {len(memories)} memories from Mem0 (confidence: {avg_score:.2f})")

            return MemoryContext(
                retrieved_memories=memories,
                recent_messages=recent_messages,
                confidence_score=avg_score,
                namespace=namespace
            )

        except Exception as e:
            logger.error(f"Failed to get semantic memories from Mem0: {e}")
            # Return with recent_messages from database (already retrieved above)
            return MemoryContext(
                retrieved_memories=[],
                recent_messages=recent_messages,  # ✅ Still have thread context
                confidence_score=0.0,
                namespace=self.thread_namespace(session_id)
            )

    async def process_interaction(
        self,
        user_input: str,
        agent_response: str,
        session_id: str,
        user_id: Optional[str] = None
    ):
        """
        Process and store conversation turn in Mem0

        Args:
            user_input: User message
            agent_response: Agent response
            session_id: Thread/session ID
            user_id: Optional user ID
        """
        # Store user message
        await self.store_interaction(
            role="user",
            content=user_input,
            session_id=session_id,
            user_id=user_id
        )

        # Store agent response
        await self.store_interaction(
            role="assistant",
            content=agent_response,
            session_id=session_id,
            user_id=user_id
        )

    # ========================================================================
    # ADVANCED MEMORY OPERATIONS
    # ========================================================================

    async def add_memory(
        self,
        content: str,
        memory_type: str = "reflection",
        namespace: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a memory to Mem0 with custom namespace

        Args:
            content: Memory text content
            memory_type: Type of memory (reflection, fact, preference, etc.)
            namespace: Override default namespace
            user_id: Optional user ID
            metadata: Additional metadata
        """
        if not self.client:
            logger.error("Mem0 client not initialized - skipping memory add")
            return

        try:
            final_namespace = namespace or self.namespace

            memory_metadata = {
                "memory_type": memory_type,
                "agent_id": self.agent_id,
                "tenant_id": self.tenant_id,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }

            if user_id:
                memory_metadata["user_id"] = user_id

            self.client.add(
                messages=[{"role": "system", "content": content}],
                user_id=final_namespace,
                metadata=memory_metadata
            )

            logger.info(f"✅ Added {memory_type} memory to Mem0 namespace: {final_namespace}")

        except Exception as e:
            logger.error(f"Failed to add memory to Mem0: {e}")

    async def search_memories(
        self,
        query: str,
        namespace: Optional[str] = None,
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories in Mem0 with optional filters

        Args:
            query: Search query text
            namespace: Override default namespace
            limit: Number of results
            memory_type: Filter by memory type

        Returns:
            List of memory dictionaries with content and metadata
        """
        if not self.client:
            logger.warning("Mem0 client not initialized - returning empty results")
            return []

        try:
            final_namespace = namespace or self.namespace

            results = self.client.search(
                query=query,
                user_id=final_namespace,
                limit=limit
            )

            memories = []
            results_list = results if isinstance(results, list) else results.get("results", [])

            for result in results_list:
                memory_content = result.get("memory", "")
                metadata = result.get("metadata", {})

                # Filter by memory_type if specified
                if memory_type and metadata.get("memory_type") != memory_type:
                    continue

                memories.append({
                    "content": memory_content,
                    "score": result.get("score", 0.0),
                    "metadata": metadata,
                    "memory_type": metadata.get("memory_type", "unknown")
                })

            logger.info(f"✅ Found {len(memories)} memories in Mem0")
            return memories

        except Exception as e:
            logger.error(f"Failed to search memories in Mem0: {e}")
            return []

    async def get_all_memories(
        self,
        namespace: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all memories for a namespace

        Args:
            namespace: Override default namespace
            user_id: User ID for user-specific memories

        Returns:
            List of all memories
        """
        if not self.client:
            logger.warning("Mem0 client not initialized - returning empty list")
            return []

        try:
            final_namespace = namespace or self.namespace

            # Mem0 get_all method
            results = self.client.get_all(user_id=final_namespace)

            memories = []
            results_list = results if isinstance(results, list) else results.get("results", [])

            for result in results_list:
                memories.append({
                    "content": result.get("memory", ""),
                    "metadata": result.get("metadata", {}),
                    "id": result.get("id", "")
                })

            logger.info(f"✅ Retrieved {len(memories)} memories from Mem0")
            return memories

        except Exception as e:
            logger.error(f"Failed to get all memories from Mem0: {e}")
            return []

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _get_recent_thread_messages(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent thread messages from database (for short-term context)

        Args:
            session_id: Thread/session ID
            limit: Number of recent messages

        Returns:
            List of message dictionaries
        """
        from database import get_pg_pool

        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT role, content, created_at, metadata
                    FROM thread_messages
                    WHERE thread_id = $1::uuid
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


# ============================================================================
# CONVENIENCE FUNCTIONS (AGENT_CREATION_STANDARD Pattern)
# ============================================================================

async def initialize_agent_memory(
    agent_id: str,
    tenant_id: str,
    agent_contract: Dict[str, Any]
) -> MemoryManager:
    """
    Initialize the Mem0-based memory system for a new agent.

    Creates:
    - Agent memory namespace in Mem0
    - Stores an initial system memory message

    Args:
        agent_id: Agent UUID
        tenant_id: Tenant UUID
        agent_contract: Full agent contract dict

    Returns:
        Initialized MemoryManager instance
    """
    # Create the Mem0-based memory manager
    memory_manager = MemoryManager(
        tenant_id=tenant_id,
        agent_id=agent_id,
        agent_traits=agent_contract.get("traits", {})
    )

    # Add initial system memory message to Mem0
    agent_name = agent_contract.get("name", "Agent")
    identity = agent_contract.get("identity", {})

    await memory_manager.add_memory(
        content=f"Agent '{agent_name}' initialized with identity: {identity.get('short_description', '')}",
        memory_type="system",
        metadata={
            "event": "agent_initialization",
            "agent_id": agent_id,
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    logger.info(f"✅ Mem0 memory initialized for agent: {agent_id}")

    return memory_manager


async def store_user_preferences(
    user_id: str,
    tenant_id: str,
    agent_id: str,
    preferences: Dict[str, Any]
):
    """
    Store user preferences in Mem0

    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        agent_id: Agent UUID
        preferences: Preferences dictionary
    """
    manager = MemoryManager(tenant_id, agent_id, {})

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
    """
    Retrieve user preferences from Mem0

    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        agent_id: Agent UUID

    Returns:
        Preferences dictionary or None
    """
    manager = MemoryManager(tenant_id, agent_id, {})

    memories = await manager.search_memories(
        query="user preferences",
        namespace=manager.user_namespace(user_id),
        limit=1,
        memory_type="preference"
    )

    if memories:
        return memories[0].get("metadata", {})
    return None


# ============================================================================
# PHASE 1: COGNITIVE ASSESSMENT MEMORY EXTENSIONS
# ============================================================================

async def store_goal_assessment(
    user_id: str,
    tenant_id: str,
    agent_id: str,
    goal_assessment: Dict[str, Any]
):
    """
    Store goal assessment data in Mem0

    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        agent_id: Agent UUID
        goal_assessment: GoalAssessment dict with GAS ratings

    Returns:
        Goal assessment ID
    """
    from database import get_pg_pool
    import uuid
    import json

    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            goal_id = str(uuid.uuid4())

            await conn.execute("""
                INSERT INTO goal_assessments (
                    id, user_id, agent_id, tenant_id,
                    goal_text, goal_category,
                    gas_current_level, gas_expected_level, gas_target_level,
                    ideal_state_rating, actual_state_rating,
                    confidence_score, motivation_score,
                    schema_version, intake_depth
                )
                VALUES (
                    $1::uuid, $2::uuid, $3::uuid, $4::uuid,
                    $5, $6,
                    $7, $8, $9,
                    $10, $11,
                    $12, $13,
                    $14, $15
                )
            """,
                goal_id,
                user_id,
                agent_id,
                tenant_id,
                goal_assessment.get("goal_text"),
                goal_assessment.get("goal_category", "other"),
                goal_assessment.get("gas_current_level", -1),
                goal_assessment.get("gas_expected_level", 0),
                goal_assessment.get("gas_target_level", 2),
                goal_assessment.get("ideal_state_rating", 100),
                goal_assessment.get("actual_state_rating", 50),
                goal_assessment.get("confidence_score", 0.5),
                goal_assessment.get("motivation_score", 0.5),
                "v1.0",
                goal_assessment.get("intake_depth", "cognitive_extended")
            )

        # Also store in Mem0 for semantic retrieval
        manager = MemoryManager(tenant_id, agent_id, {})

        await manager.add_memory(
            content=f"Goal: {goal_assessment.get('goal_text')} (Current: {goal_assessment.get('gas_current_level')}, Target: {goal_assessment.get('gas_target_level')})",
            memory_type="goal_assessment",
            namespace=manager.user_namespace(user_id),
            user_id=user_id,
            metadata={
                "goal_id": goal_id,
                "gas_current_level": goal_assessment.get("gas_current_level"),
                "gap_score": goal_assessment.get("ideal_state_rating", 100) - goal_assessment.get("actual_state_rating", 50)
            }
        )

        logger.info(f"✅ Goal assessment stored: {goal_id}")
        return goal_id

    except Exception as e:
        logger.error(f"Failed to store goal assessment: {e}")
        raise


async def store_belief_graph(
    user_id: str,
    tenant_id: str,
    agent_id: str,
    belief_graph: Dict[str, Any]
):
    """
    Store belief graph (CAM) in database and Mem0

    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        agent_id: Agent UUID
        belief_graph: BeliefGraph dict with nodes and edges

    Returns:
        Belief graph ID
    """
    from database import get_pg_pool
    import uuid
    import json

    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            graph_id = str(uuid.uuid4())

            await conn.execute("""
                INSERT INTO belief_graphs (
                    id, user_id, agent_id, tenant_id,
                    graph_name, graph_version,
                    nodes, edges,
                    conflict_score, tension_nodes, core_beliefs,
                    schema_version
                )
                VALUES (
                    $1::uuid, $2::uuid, $3::uuid, $4::uuid,
                    $5, $6,
                    $7::jsonb, $8::jsonb,
                    $9, $10::jsonb, $11::jsonb,
                    $12
                )
            """,
                graph_id,
                user_id,
                agent_id,
                tenant_id,
                belief_graph.get("graph_name", "User Belief System"),
                belief_graph.get("graph_version", 1),
                json.dumps(belief_graph.get("nodes", [])),
                json.dumps(belief_graph.get("edges", [])),
                belief_graph.get("conflict_score", 0.0),
                json.dumps(belief_graph.get("tension_nodes", [])),
                json.dumps(belief_graph.get("core_beliefs", [])),
                "v1.0"
            )

        # Store summary in Mem0
        manager = MemoryManager(tenant_id, agent_id, {})

        limiting_beliefs = [
            node.get("label") for node in belief_graph.get("nodes", [])
            if node.get("node_type") == "limiting_belief"
        ]

        await manager.add_memory(
            content=f"Limiting beliefs identified: {', '.join(limiting_beliefs[:5])}. Conflict score: {belief_graph.get('conflict_score', 0.0)}",
            memory_type="belief_graph",
            namespace=manager.user_namespace(user_id),
            user_id=user_id,
            metadata={
                "graph_id": graph_id,
                "conflict_score": belief_graph.get("conflict_score"),
                "node_count": len(belief_graph.get("nodes", []))
            }
        )

        logger.info(f"✅ Belief graph stored: {graph_id}")
        return graph_id

    except Exception as e:
        logger.error(f"Failed to store belief graph: {e}")
        raise


async def store_cognitive_metric(
    user_id: str,
    tenant_id: str,
    agent_id: str,
    metric_type: str,
    metric_value: float,
    context_data: Optional[Dict[str, Any]] = None,
    threshold_value: Optional[float] = None
):
    """
    Store cognitive metric (emotion conflict, goal progress, etc.)

    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        agent_id: Agent UUID
        metric_type: Type of metric (emotion_conflict, goal_progress, etc.)
        metric_value: Numeric metric value
        context_data: Additional context
        threshold_value: Threshold for triggering action

    Returns:
        Metric ID
    """
    from database import get_pg_pool
    import uuid
    import json

    pool = get_pg_pool()

    try:
        async with pool.acquire() as conn:
            metric_id = str(uuid.uuid4())

            threshold_exceeded = False
            if threshold_value is not None and metric_value >= threshold_value:
                threshold_exceeded = True

            await conn.execute("""
                INSERT INTO cognitive_metrics (
                    id, user_id, agent_id, tenant_id,
                    metric_type, metric_category,
                    metric_value, threshold_value, threshold_exceeded,
                    context_data, trigger_action,
                    schema_version
                )
                VALUES (
                    $1::uuid, $2::uuid, $3::uuid, $4::uuid,
                    $5, $6,
                    $7, $8, $9,
                    $10::jsonb, $11,
                    $12
                )
            """,
                metric_id,
                user_id,
                agent_id,
                tenant_id,
                metric_type,
                _get_metric_category(metric_type),
                metric_value,
                threshold_value,
                threshold_exceeded,
                json.dumps(context_data or {}),
                _get_trigger_action(metric_type, threshold_exceeded),
                "v1.0"
            )

        logger.info(f"✅ Cognitive metric stored: {metric_type} = {metric_value}")
        return metric_id

    except Exception as e:
        logger.error(f"Failed to store cognitive metric: {e}")
        raise


def _get_metric_category(metric_type: str) -> str:
    """Map metric type to category"""
    emotional_types = ["emotion_conflict", "motivation_drop"]
    behavioral_types = ["repeated_failure", "goal_progress"]
    cognitive_types = ["belief_shift", "breakthrough"]

    if metric_type in emotional_types:
        return "emotional"
    elif metric_type in behavioral_types:
        return "behavioral"
    elif metric_type in cognitive_types:
        return "cognitive"
    else:
        return "emotional"


def _get_trigger_action(metric_type: str, threshold_exceeded: bool) -> Optional[str]:
    """Determine trigger action based on metric type and threshold"""
    if not threshold_exceeded:
        return None

    actions = {
        "emotion_conflict": "Initiate belief reassessment conversation",
        "repeated_failure": "Suggest breaking goal into smaller steps",
        "motivation_drop": "Provide encouragement and progress review",
        "goal_progress": "Celebrate milestone achievement",
        "belief_shift": "Acknowledge positive transformation"
    }

    return actions.get(metric_type, "Review with user")
