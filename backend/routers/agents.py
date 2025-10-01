"""
Agent CRUD API - Agent Creation Standard Endpoints

Implements full agent lifecycle management via REST API:
- POST   /agents              → Create agent from JSON contract
- GET    /agents              → List all agents (filtered by tenant)
- GET    /agents/{id}         → Get agent details
- PATCH  /agents/{id}         → Update agent contract
- DELETE /agents/{id}         → Archive agent
- POST   /agents/{id}/chat    → Chat with agent
"""

from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional, List
import logging
import uuid

from models.agent import (
    AgentContract,
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentResponse,
    AgentType,
    AgentStatus,
    AgentIdentity,
    AgentTraits,
    AgentConfiguration,
    AgentMetadata
)
from services.agent_service import AgentService
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Global agent service instance
agent_service = AgentService()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    thread_id: Optional[str] = None
    metadata: Optional[dict] = {}


class ChatResponse(BaseModel):
    """Chat response model"""
    thread_id: str
    agent_id: str
    response: str
    metadata: dict


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_tenant_id(x_tenant_id: Optional[str] = Header(None)) -> str:
    """Extract tenant ID from header or use default"""
    if x_tenant_id:
        return x_tenant_id
    # Default tenant for development
    return "00000000-0000-0000-0000-000000000001"


def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user ID from header or use default"""
    if x_user_id:
        return x_user_id
    # Default user for development
    return "00000000-0000-0000-0000-000000000001"


# ============================================================================
# AGENT CRUD ENDPOINTS
# ============================================================================

@router.post("/agents", status_code=201)
async def create_agent(
    request: AgentCreateRequest,
    tenant_id: str = Header(None, alias="x-tenant-id"),
    user_id: str = Header(None, alias="x-user-id")
):
    """
    Create new agent from JSON contract

    **Process:**
    1. Validate JSON contract
    2. Create database record
    3. Initialize memory namespace
    4. Save filesystem JSON
    5. Create default thread
    6. Return agent object

    **Example Request:**
    ```json
    {
        "name": "Empowering Affirmation Guide",
        "type": "voice",
        "identity": {
            "short_description": "Compassionate guide for daily affirmations",
            "mission": "Empower users through positive self-talk"
        },
        "traits": {
            "empathy": 95,
            "confidence": 85
        },
        "voice": {
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "provider": "elevenlabs"
        }
    }
    ```
    """
    try:
        tenant_id = tenant_id or get_tenant_id()
        user_id = user_id or get_user_id()

        # Build complete contract
        contract = AgentContract(
            name=request.name,
            type=request.type,
            identity=request.identity,
            traits=request.traits or AgentTraits(),
            configuration=request.configuration or AgentConfiguration(),
            voice=request.voice,
            metadata=AgentMetadata(
                tenant_id=tenant_id,
                owner_id=user_id,
                tags=request.tags,
                status=AgentStatus.ACTIVE
            )
        )

        # Create agent via service
        agent = await agent_service.create_agent(contract, tenant_id, user_id)

        logger.info(f"✅ Agent created via API: {agent['name']} ({agent['id']})")

        return {
            "status": "success",
            "message": f"Agent '{agent['name']}' created successfully",
            "agent": agent
        }

    except Exception as e:
        logger.error(f"Agent creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.get("/agents")
async def list_agents(
    tenant_id: str = Header(None, alias="x-tenant-id"),
    status: Optional[str] = Query(None, description="Filter by status"),
    agent_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List all agents for tenant

    **Filters:**
    - status: active, inactive, archived
    - agent_type: conversational, voice, workflow, autonomous
    - limit: max results (default 50)
    - offset: pagination offset

    **Example Response:**
    ```json
    {
        "tenant_id": "...",
        "total": 10,
        "agents": [...]
    }
    ```
    """
    try:
        tenant_id = tenant_id or get_tenant_id()

        agents = await agent_service.list_agents(
            tenant_id=tenant_id,
            status=status,
            agent_type=agent_type,
            limit=limit,
            offset=offset
        )

        return {
            "tenant_id": tenant_id,
            "total": len(agents),
            "agents": agents,
            "filters": {
                "status": status,
                "type": agent_type,
                "limit": limit,
                "offset": offset
            }
        }

    except Exception as e:
        logger.error(f"Failed to list agents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list agents")


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    tenant_id: str = Header(None, alias="x-tenant-id")
):
    """
    Get agent details by ID

    Returns complete agent record including:
    - Full JSON contract
    - Interaction metrics
    - Creation/update timestamps

    **Example Response:**
    ```json
    {
        "id": "...",
        "name": "Empowering Guide",
        "contract": {...},
        "interaction_count": 42,
        "last_interaction_at": "2025-01-15T10:30:00Z"
    }
    ```
    """
    try:
        tenant_id = tenant_id or get_tenant_id()

        agent = await agent_service.get_agent(agent_id, tenant_id)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent")


@router.patch("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    tenant_id: str = Header(None, alias="x-tenant-id")
):
    """
    Update agent contract

    **Supports partial updates to:**
    - name
    - identity
    - traits
    - configuration
    - voice
    - tags
    - status

    **Creates version snapshot before updating.**

    **Example Request:**
    ```json
    {
        "traits": {
            "empathy": 98,
            "confidence": 90
        },
        "change_summary": "Increased empathy and confidence"
    }
    ```
    """
    try:
        tenant_id = tenant_id or get_tenant_id()

        # Build updates dict
        updates = {}
        if request.name:
            updates["name"] = request.name
        if request.identity:
            updates["identity"] = request.identity.model_dump()
        if request.traits:
            updates["traits"] = request.traits.model_dump()
        if request.configuration:
            updates["configuration"] = request.configuration.model_dump()
        if request.voice:
            updates["voice"] = request.voice.model_dump()
        if request.tags is not None:
            updates["tags"] = request.tags
        if request.status:
            updates["status"] = request.status.value

        # Update via service
        updated_agent = await agent_service.update_agent(agent_id, tenant_id, updates)

        if not updated_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return {
            "status": "success",
            "message": "Agent updated successfully",
            "agent": updated_agent
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")


@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    tenant_id: str = Header(None, alias="x-tenant-id")
):
    """
    Archive agent (soft delete)

    Sets agent status to 'archived'.
    Agent will no longer appear in default listings.
    All historical data is preserved.

    **Example Response:**
    ```json
    {
        "status": "success",
        "message": "Agent archived successfully"
    }
    ```
    """
    try:
        tenant_id = tenant_id or get_tenant_id()

        success = await agent_service.delete_agent(agent_id, tenant_id)

        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")

        return {
            "status": "success",
            "message": f"Agent {agent_id} archived successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to archive agent")


# ============================================================================
# AGENT INTERACTION ENDPOINT
# ============================================================================

@router.post("/agents/{agent_id}/chat")
async def chat_with_agent(
    agent_id: str,
    request: ChatRequest,
    tenant_id: str = Header(None, alias="x-tenant-id"),
    user_id: str = Header(None, alias="x-user-id")
):
    """
    Chat with agent

    **Standard agent interaction endpoint.**

    Process:
    1. Load agent contract
    2. Get or create thread
    3. Retrieve memory context
    4. Process through LangGraph
    5. Store interaction
    6. Return response

    **Example Request:**
    ```json
    {
        "message": "I want to build confidence in public speaking",
        "thread_id": "optional-existing-thread-id",
        "metadata": {
            "source": "mobile_app"
        }
    }
    ```

    **Example Response:**
    ```json
    {
        "thread_id": "...",
        "agent_id": "...",
        "response": "Let's work on building your confidence...",
        "metadata": {
            "memory_confidence": 0.85,
            "retrieved_memories": 3
        }
    }
    ```
    """
    try:
        tenant_id = tenant_id or get_tenant_id()
        user_id = user_id or get_user_id()

        result = await agent_service.process_interaction(
            agent_id=agent_id,
            tenant_id=tenant_id,
            user_id=user_id,
            user_input=request.message,
            thread_id=request.thread_id,
            metadata=request.metadata
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Chat interaction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Interaction failed: {str(e)}")


# ============================================================================
# AGENT METRICS & HISTORY
# ============================================================================

@router.get("/agents/{agent_id}/threads")
async def get_agent_threads(
    agent_id: str,
    tenant_id: str = Header(None, alias="x-tenant-id"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get all conversation threads for agent

    Returns list of threads with:
    - Thread ID
    - User ID
    - Message count
    - Last message timestamp
    - Context summary (if available)
    """
    try:
        tenant_id = tenant_id or get_tenant_id()

        from database import get_pg_pool
        pool = get_pg_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    id, user_id, title,
                    message_count, last_message_at,
                    context_summary, created_at
                FROM threads
                WHERE agent_id = $1::uuid
                  AND tenant_id = $2::uuid
                  AND status = 'active'
                ORDER BY last_message_at DESC NULLS LAST
                LIMIT $3
            """, agent_id, tenant_id, limit)

            threads = [
                {
                    "id": str(row["id"]),
                    "user_id": str(row["user_id"]),
                    "title": row["title"],
                    "message_count": row["message_count"],
                    "last_message_at": row["last_message_at"].isoformat() if row["last_message_at"] else None,
                    "context_summary": row["context_summary"],
                    "created_at": row["created_at"].isoformat()
                }
                for row in rows
            ]

            return {
                "agent_id": agent_id,
                "total": len(threads),
                "threads": threads
            }

    except Exception as e:
        logger.error(f"Failed to get agent threads: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve threads")


@router.get("/agents/{agent_id}/versions")
async def get_agent_versions(
    agent_id: str,
    tenant_id: str = Header(None, alias="x-tenant-id"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get agent version history

    Returns all contract versions with:
    - Version number
    - Contract snapshot
    - Change summary
    - Created timestamp
    """
    try:
        tenant_id = tenant_id or get_tenant_id()

        from database import get_pg_pool
        pool = get_pg_pool()

        async with pool.acquire() as conn:
            # Verify agent exists and belongs to tenant
            agent_check = await conn.fetchrow("""
                SELECT id FROM agents
                WHERE id = $1::uuid AND tenant_id = $2::uuid
            """, agent_id, tenant_id)

            if not agent_check:
                raise HTTPException(status_code=404, detail="Agent not found")

            # Get versions
            rows = await conn.fetch("""
                SELECT
                    id, version, contract,
                    change_summary, created_at
                FROM agent_versions
                WHERE agent_id = $1::uuid
                ORDER BY created_at DESC
                LIMIT $2
            """, agent_id, limit)

            versions = [
                {
                    "id": str(row["id"]),
                    "version": row["version"],
                    "contract": row["contract"],
                    "change_summary": row["change_summary"],
                    "created_at": row["created_at"].isoformat()
                }
                for row in rows
            ]

            return {
                "agent_id": agent_id,
                "total": len(versions),
                "versions": versions
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent versions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve versions")
