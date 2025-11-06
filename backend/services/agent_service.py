"""
Agent Service - Complete Lifecycle Management

Implements the Agent Creation Standard workflow:
1. Create agent from JSON contract
2. Initialize memory namespace
3. Create default thread
4. Process agent interactions
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import uuid
from collections import OrderedDict

from models.agent import AgentContract
from memoryManager.memory_manager import MemoryManager, initialize_agent_memory
from database import get_pg_pool

logger = logging.getLogger(__name__)


class LRUMemoryCache:
    """
    LRU cache for memory managers to prevent memory leaks

    Maintains a bounded cache of memory managers with automatic cleanup
    of least recently used items.
    """

    def __init__(self, max_size: int = 100):
        self.cache: OrderedDict[str, MemoryManager] = OrderedDict()
        self.max_size = max_size

    def get(self, key: str) -> Optional[MemoryManager]:
        """Get memory manager from cache, moving it to end (most recent)"""
        if key not in self.cache:
            return None

        # Move to end to mark as recently used
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, manager: MemoryManager):
        """Add memory manager to cache, evicting oldest if needed"""
        # If key exists, move to end
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            # If at capacity, remove oldest item
            if len(self.cache) >= self.max_size:
                oldest_key, oldest_manager = self.cache.popitem(last=False)
                logger.info(f"Evicting memory manager from cache: {oldest_key}")
                # Optional: cleanup resources if needed
                # await oldest_manager.cleanup()

        self.cache[key] = manager

    def remove(self, key: str) -> Optional[MemoryManager]:
        """Remove memory manager from cache"""
        return self.cache.pop(key, None)

    def clear(self):
        """Clear all memory managers from cache"""
        self.cache.clear()

    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)


class AgentService:
    """Production agent service with complete lifecycle management"""

    def __init__(self, max_memory_cache_size: int = 100):
        # Use LRU cache instead of unbounded dictionary
        self.memory_cache = LRUMemoryCache(max_size=max_memory_cache_size)

    async def create_agent(
        self,
        contract: AgentContract,
        tenant_id: str,
        owner_id: str
    ) -> Dict[str, Any]:
        """
        Create new agent with complete initialization

        Process:
        1. Validate contract
        2. Create database record
        3. Initialize memory namespace
        4. Create default thread
        5. Return agent object

        Returns:
            Dict: Complete agent record
        """
        pool = get_pg_pool()

        try:
            # Ensure IDs are set
            if not contract.metadata.tenant_id:
                contract.metadata.tenant_id = tenant_id
            if not contract.metadata.owner_id:
                contract.metadata.owner_id = owner_id

            # 1. Create database record
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agents (
                        id, tenant_id, owner_id,
                        name, type, version,
                        contract, status,
                        interaction_count, last_interaction_at,
                        created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                    contract.id,
                    tenant_id,
                    owner_id,
                    contract.name,
                    contract.type.value,
                    contract.version,
                    json.dumps(contract.model_dump(), default=str),
                    contract.metadata.status.value,
                    0,
                    None,
                    contract.created_at,
                    contract.updated_at
                )

            logger.info(f"✅ Agent database record created: {contract.id}")

            # 2. Initialize memory namespace
            await self._initialize_memory(contract.id, tenant_id, contract)

            # 3. Create default thread (optional, for conversational agents)
            if contract.type.value in ["conversational", "voice"]:
                await self._create_default_thread(contract.id, tenant_id, owner_id)

            logger.info(f"🚀 Agent fully initialized: {contract.name} ({contract.id})")

            # Return agent data with all necessary fields
            return {
                "id": str(contract.id),
                "tenant_id": tenant_id,
                "owner_id": owner_id,
                "name": contract.name,
                "type": contract.type.value,
                "version": contract.version,
                "status": contract.metadata.status.value,
                "contract": contract.model_dump(),
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Agent creation failed: {str(e)}")
            raise

    async def get_agent(
        self,
        agent_id: str,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get agent by ID with tenant validation

        Args:
            agent_id: Agent UUID
            tenant_id: Tenant UUID

        Returns:
            Agent data or None if not found
        """
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT
                        id, tenant_id, owner_id,
                        name, type, version,
                        contract, status,
                        interaction_count, last_interaction_at,
                        created_at, updated_at
                    FROM agents
                    WHERE id = $1::uuid AND tenant_id = $2::uuid AND status != 'archived'
                """, agent_id, tenant_id)

                if not row:
                    return None

                # Parse contract if it's a string (JSONB from database)
                contract_data = row["contract"]
                if isinstance(contract_data, str):
                    import json
                    contract_data = json.loads(contract_data)

                agent_data = {
                    "id": str(row["id"]),
                    "tenant_id": str(row["tenant_id"]),
                    "owner_id": str(row["owner_id"]),
                    "name": row["name"],
                    "type": row["type"],
                    "version": row["version"],
                    "contract": contract_data,
                    "status": row["status"],
                    "interaction_count": row["interaction_count"],
                    "last_interaction_at": row["last_interaction_at"].isoformat() if row["last_interaction_at"] else None,
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat()
                }

                return agent_data

        except Exception as e:
            logger.error(f"Failed to get agent: {str(e)}")
            return None

    async def list_agents(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        agent_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List agents with filtering"""
        pool = get_pg_pool()

        try:
            query = """
                SELECT
                    id, name, type, status,
                    interaction_count, last_interaction_at,
                    created_at, updated_at
                FROM agents
                WHERE tenant_id = $1::uuid
            """
            params = [tenant_id]

            if status:
                params.append(status)
                query += f" AND status = ${len(params)}"

            if agent_type:
                params.append(agent_type)
                query += f" AND type = ${len(params)}"

            query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
            params.extend([limit, offset])

            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

                return [
                    {
                        "id": str(row["id"]),
                        "name": row["name"],
                        "type": row["type"],
                        "status": row["status"],
                        "interaction_count": row["interaction_count"],
                        "last_interaction_at": row["last_interaction_at"].isoformat() if row["last_interaction_at"] else None,
                        "created_at": row["created_at"].isoformat(),
                        "updated_at": row["updated_at"].isoformat()
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to list agents: {str(e)}")
            return []

    async def update_agent(
        self,
        agent_id: str,
        tenant_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update agent contract with versioning"""
        pool = get_pg_pool()

        try:
            # Get current agent
            agent = await self.get_agent(agent_id, tenant_id)
            if not agent:
                raise ValueError("Agent not found")

            # Create version snapshot
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_versions (
                        id, agent_id, version, contract, change_summary, created_at
                    )
                    VALUES (gen_random_uuid(), $1::uuid, $2, $3, $4, NOW())
                """,
                    agent_id,
                    agent["version"],
                    json.dumps(agent["contract"]),
                    updates.get("change_summary", "Updated agent contract")
                )

            # Update contract
            current_contract = agent["contract"]

            # Apply updates to contract
            if "identity" in updates:
                current_contract["identity"].update(updates["identity"])
            if "traits" in updates:
                current_contract["traits"].update(updates["traits"])
            if "configuration" in updates:
                current_contract["configuration"].update(updates["configuration"])
            if "voice" in updates:
                current_contract["voice"] = updates["voice"]
            if "status" in updates:
                current_contract["metadata"]["status"] = updates["status"]

            # Update database
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agents
                    SET contract = $1, updated_at = NOW()
                    WHERE id = $2::uuid AND tenant_id = $3::uuid
                """,
                    json.dumps(current_contract, default=str),
                    agent_id,
                    tenant_id
                )

            logger.info(f"✅ Agent updated: {agent_id}")
            return await self.get_agent(agent_id, tenant_id)

        except Exception as e:
            logger.error(f"Failed to update agent: {str(e)}")
            raise

    async def delete_agent(
        self,
        agent_id: str,
        tenant_id: str
    ) -> bool:
        """Soft delete agent (archive)"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agents
                    SET status = 'archived', updated_at = NOW()
                    WHERE id = $1::uuid AND tenant_id = $2::uuid
                """, agent_id, tenant_id)

            logger.info(f"✅ Agent archived: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to archive agent: {str(e)}")
            return False

    async def process_interaction(
        self,
        agent_id: str,
        tenant_id: str,
        user_id: str,
        user_input: str,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process agent interaction with complete flow

        Steps:
        1. Load agent contract
        2. Get or create thread
        3. Initialize memory manager
        4. Get memory context
        5. Build and invoke LangGraph
        6. Store messages
        7. Update metrics
        8. Return response

        Returns:
            Dict containing response and metadata
        """
        pool = get_pg_pool()

        try:
            # 1. Load agent
            agent = await self.get_agent(agent_id, tenant_id)
            if not agent:
                raise ValueError("Agent not found")

            contract = AgentContract(**agent["contract"])

            # 2. Get or create thread
            if not thread_id:
                thread_id = str(uuid.uuid4())
                async with pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO threads (
                            id, agent_id, user_id, tenant_id,
                            title, status, message_count,
                            created_at, updated_at
                        )
                        VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, 'active', 0, NOW(), NOW())
                    """,
                        thread_id, agent_id, user_id, tenant_id,
                        f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
                    )

            # 3. Get or create memory manager
            memory_manager = await self._get_memory_manager(
                agent_id, tenant_id, contract.model_dump()
            )

            # 4. Get memory context
            memory_context = await memory_manager.get_agent_context(
                user_input=user_input,
                session_id=thread_id,
                user_id=user_id
            )

            # 5. Invoke GuideAgent with contract-first approach
            from agents.guide_agent.guide_agent import GuideAgent

            # Create GuideAgent instance with contract and memory
            guide_agent = GuideAgent(contract=contract, memory=memory_manager)

            # Use the chat-specific method (not the asset generation workflow)
            response_text = await guide_agent.process_chat_message(
                user_id=user_id,
                user_input=user_input,
                thread_id=thread_id,
                memory_context=memory_context
            )

            # 6. Store messages
            async with pool.acquire() as conn:
                # User message
                await conn.execute("""
                    INSERT INTO thread_messages (
                        id, thread_id, role, content, metadata, created_at
                    )
                    VALUES (gen_random_uuid(), $1::uuid, 'user', $2, $3, NOW())
                """, thread_id, user_input, json.dumps(metadata or {}))

                # Agent message
                await conn.execute("""
                    INSERT INTO thread_messages (
                        id, thread_id, role, content, metadata, created_at
                    )
                    VALUES (gen_random_uuid(), $1::uuid, 'assistant', $2, $3, NOW())
                """, thread_id, response_text, json.dumps({
                    "confidence": memory_context.confidence_score
                }))

                # Update thread
                await conn.execute("""
                    UPDATE threads
                    SET message_count = message_count + 2,
                        last_message_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $1::uuid
                """, thread_id)

            # 7. Process interaction through memory
            await memory_manager.process_interaction(
                user_input=user_input,
                agent_response=response_text,
                session_id=thread_id,
                user_id=user_id
            )

            # 8. Update agent metrics
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agents
                    SET interaction_count = interaction_count + 1,
                        last_interaction_at = NOW()
                    WHERE id = $1::uuid
                """, agent_id)

            return {
                "thread_id": thread_id,
                "agent_id": agent_id,
                "response": response_text,
                "metadata": {
                    "memory_confidence": memory_context.confidence_score,
                    "retrieved_memories": len(memory_context.retrieved_memories)
                }
            }

        except Exception as e:
            logger.error(f"Interaction failed: {str(e)}")
            raise

    async def _initialize_memory(
        self,
        agent_id: str,
        tenant_id: str,
        contract: AgentContract
    ):
        """Initialize memory namespace for new agent using Mem0"""
        try:
            # Initialize using Mem0-based MemoryManager
            memory_manager = await initialize_agent_memory(
                agent_id=agent_id,
                tenant_id=tenant_id,
                agent_contract=contract.model_dump()
            )

            logger.info(f"✅ Mem0 memory initialized for agent: {agent_id}")

        except Exception as e:
            logger.error(f"Mem0 memory initialization failed: {str(e)}")
            # Non-critical - agent can still function without memory
            logger.warning("Agent created without memory - continuing")

    def _generate_system_prompt(self, contract: AgentContract) -> str:
        """Generate system prompt from agent contract with trait-based behavioral directives"""
        from services.trait_modulator import TraitModulator

        modulator = TraitModulator()

        traits_desc = "\n".join([
            f"- {trait.replace('_', ' ').title()}: {value}/100"
            for trait, value in contract.traits.model_dump().items()
        ])

        # Generate specific behavioral instructions from traits
        behavior_instructions = modulator.generate_behavior_instructions(contract.traits)
        trait_summary = modulator.get_trait_summary(contract.traits)

        return f"""You are {contract.name}.

{contract.identity.full_description or contract.identity.short_description}

CHARACTER ROLE: {contract.identity.character_role}
MISSION: {contract.identity.mission}
INTERACTION STYLE: {contract.identity.interaction_style}

PERSONALITY TRAITS (Quantified):
{traits_desc}

{trait_summary}

{behavior_instructions}

CORE DIRECTIVES:
- Embody the character role in every interaction
- Align all responses with your mission
- Follow the behavioral directives above PRECISELY
- Your personality is defined by the trait instructions - not by generic LLM behavior

CONFIGURATION:
- Model: {contract.configuration.llm_model}
- Temperature: {contract.configuration.temperature}
- Max tokens: {contract.configuration.max_tokens}
"""

    async def _create_default_thread(
        self,
        agent_id: str,
        tenant_id: str,
        user_id: str
    ):
        """Create default thread for agent"""
        pool = get_pg_pool()

        try:
            thread_id = str(uuid.uuid4())
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO threads (
                        id, agent_id, user_id, tenant_id,
                        title, status, message_count,
                        created_at, updated_at
                    )
                    VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, 'Default Thread', 'active', 0, NOW(), NOW())
                """, thread_id, agent_id, user_id, tenant_id)

            logger.info(f"✅ Default thread created: {thread_id}")

        except Exception as e:
            logger.warning(f"Could not create default thread: {str(e)}")

    async def _get_memory_manager(
        self,
        agent_id: str,
        tenant_id: str,
        contract: Dict[str, Any]
    ) -> MemoryManager:
        """Get or create Mem0-based memory manager for agent with LRU caching"""
        key = f"{tenant_id}:{agent_id}"

        # Try to get from cache
        manager = self.memory_cache.get(key)

        if manager is None:
            # Create new manager
            manager = MemoryManager(
                tenant_id=tenant_id,
                agent_id=agent_id,
                agent_traits=contract.get("traits", {})
            )

            # Add to cache (will auto-evict oldest if needed)
            self.memory_cache.set(key, manager)

            logger.info(f"Created new memory manager for {key} (cache size: {self.memory_cache.size()})")

        return manager
