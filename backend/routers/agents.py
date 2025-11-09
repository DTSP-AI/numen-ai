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

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import logging
import uuid

from models.agent import (
    AgentContract,
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentType,
    AgentStatus,
    AgentIdentity,
    AgentTraits,
    AgentConfiguration,
    AgentMetadata,
    VoiceConfiguration
)
from services.agent_service import AgentService
from dependencies import get_tenant_id, get_user_id
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
# AGENT CRUD ENDPOINTS
# ============================================================================

@router.post("/agents", status_code=201)
async def create_agent(
    request: AgentCreateRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
):
    """
    Create new agent from JSON contract

    **Process:**
    1. Validate JSON contract
    2. Create database record
    3. Initialize memory namespace
    4. Create default thread
    5. Return agent object

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
        # Determine if voice is required
        voice_required = (
            request.type == AgentType.VOICE or
            (request.configuration and request.configuration.voice_enabled)
        )

        # Validate voice requirement
        voice_config = request.voice
        if voice_required and not voice_config:
            if request.type == AgentType.VOICE:
                raise HTTPException(
                    status_code=400,
                    detail="Voice configuration is required for voice agents. Provide 'voice' field with voice_id and provider."
                )
            else:
                # Apply default voice for voice_enabled=True
                logger.info("No voice provided but voice_enabled=True, using default voice (Rachel)")
                voice_config = VoiceConfiguration(
                    provider="elevenlabs",
                    voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel - default calm voice
                    language="en-US",
                    speed=1.0,
                    pitch=1.0,
                    stability=0.75,
                    similarity_boost=0.75,
                    stt_provider="deepgram",
                    stt_model="nova-2",
                    stt_language="en",
                    vad_enabled=True
                )

        # Apply default avatar if none provided
        identity = request.identity
        if not identity.avatar_url:
            logger.info("No avatar provided, using placeholder")
            identity.avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={uuid.uuid4()}"

        # Build complete contract
        contract = AgentContract(
            name=request.name,
            type=request.type,
            identity=identity,
            traits=request.traits or AgentTraits(),
            configuration=request.configuration or AgentConfiguration(),
            voice=voice_config,
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
    tenant_id: str = Depends(get_tenant_id),
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
    tenant_id: str = Depends(get_tenant_id)
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
    tenant_id: str = Depends(get_tenant_id)
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
        # Get current agent to validate voice requirements
        current_agent = await agent_service.get_agent(agent_id, tenant_id)
        if not current_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

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

        # Validate voice requirements for type or voice_enabled changes
        current_contract = current_agent["contract"]

        # Check if updating type to VOICE
        if updates.get("type") == AgentType.VOICE.value:
            if not updates.get("voice") and not current_contract.get("voice"):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot set agent type to VOICE without voice configuration. Provide 'voice' field."
                )

        # Check if enabling voice in configuration
        if updates.get("configuration", {}).get("voice_enabled") is True:
            if not updates.get("voice") and not current_contract.get("voice"):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot enable voice without voice configuration. Provide 'voice' field."
                )

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
    tenant_id: str = Depends(get_tenant_id)
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
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
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
    tenant_id: str = Depends(get_tenant_id),
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
    tenant_id: str = Depends(get_tenant_id),
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


# ============================================================================
# BASELINE FLOW ENDPOINT
# ============================================================================

@router.post("/agents/from_intake_contract")
async def create_agent_from_intake(
    user_id: str,
    intake_contract: dict,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Baseline Flow: Create Guide Agent + Session + Protocol in one call

    Process:
    1. Generate GuideContract from IntakeContract (AI-powered recommendations)
    2. Create Agent with 4 core attributes
    3. Auto-create Session
    4. Immediately generate Manifestation Protocol
    5. Return complete package

    Example Request:
    {
      "user_id": "uuid",
      "intake_contract": {
        "normalized_goals": ["Build confidence"],
        "prefs": {"tone": "calm", "session_type": "manifestation"},
        "notes": "..."
      }
    }

    Example Response:
    {
      "agent": {...},
      "session": {...},
      "protocol": {
        "affirmations": [...],
        "daily_practices": [...],
        ...
      }
    }
    """
    try:
        from agents.guide_agent.guide_sub_agents.manifestation_protocol_agent import ManifestationProtocolAgent
        import json
        import uuid as uuid_lib

        logger.info(f"🌟 Baseline flow: Creating guide from intake for user {user_id}")

        # 1. Generate GuideContract from intake
        normalized_goals = intake_contract.get("normalized_goals", [])
        prefs = intake_contract.get("prefs", {})
        tone = prefs.get("tone", "calm")
        session_type = prefs.get("session_type", "manifestation")

        # AI-powered role selection based on session_type
        role_mapping = {
            "manifestation": "Manifestation Mentor",
            "anxiety_relief": "Stoic Sage",
            "sleep_hypnosis": "Mindfulness Teacher",
            "confidence": "Life Coach",
            "habit_change": "Wellness Coach"
        }
        primary_role = role_mapping.get(session_type, "Life Coach")

        # AI-powered interaction style selection based on tone
        style_mapping = {
            "calm": ["Gentle", "Supportive"],
            "energetic": ["Motivational", "Encouraging"],
            "authoritative": ["Direct", "Analytical"],
            "gentle": ["Compassionate", "Nurturing"],
            "empowering": ["Empowering", "Encouraging"]
        }
        interaction_styles = style_mapping.get(tone, ["Supportive", "Encouraging"])

        # Generate guide name from primary goal
        primary_goal = normalized_goals[0] if normalized_goals else "Personal Growth"
        guide_name = f"{primary_goal[:30]} Guide"

        # Calculate optimal traits from intake data using AI OR user controls
        from services.attribute_calculator import calculate_guide_attributes
        from models.schemas import IntakeContract as SchemaIntakeContract

        # Default fallback traits
        calculated_traits = AgentTraits()

        try:
            # Convert to IntakeContract schema for calculator
            intake_schema = SchemaIntakeContract(
                normalized_goals=normalized_goals,
                prefs=prefs,
                notes=intake_contract.get("notes", "")
            )

            # Check if user provided guide controls (Priority 1)
            user_controls = None  # request.guide_controls if hasattr(request, 'guide_controls') else None

            if user_controls:
                logger.info(f"🎛️ User controls provided: {user_controls.model_dump()}")
                calculated_traits = await calculate_guide_attributes(intake_schema, user_controls=user_controls)
                logger.info(f"✅ Traits from user controls: {calculated_traits.model_dump()}")
            else:
                # Use AI to calculate personalized trait values (Priority 2)
                calculated_traits = await calculate_guide_attributes(intake_schema)
                logger.info(f"✅ AI-calculated traits: {calculated_traits.model_dump()}")
        except Exception as e:
            logger.warning(f"Trait calculation failed, using defaults: {e}")
            # Use fallback traits already set above

        # Build GuideContract with AI-calculated attributes
        guide_contract_dict = {
            "name": guide_name,
            "type": "conversational",
            "identity": {
                "short_description": f"{primary_role} focused on {primary_goal}",
                "full_description": f"I am your personalized {primary_role}, here to guide you toward {primary_goal}. {intake_contract.get('notes', '')}",
                "character_role": primary_role,
                "mission": f"Help you achieve: {', '.join(normalized_goals)}",
                "interaction_style": ", ".join(interaction_styles)
            },
            "traits": calculated_traits.model_dump(),  # Use AI-calculated traits
            "configuration": {
                "llm_provider": "openai",
                "llm_model": "gpt-5-nano",
                "max_tokens": 800,
                "temperature": 0.7,
                "memory_enabled": True,
                "voice_enabled": True,
                "tools_enabled": False,
                "memory_k": 6,
                "thread_window": 20
            },
            "voice": {
                "provider": "elevenlabs",
                "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Default: Rachel (calm)
                "language": "en-US",
                "stability": 0.75,
                "similarity_boost": 0.75
            },
            "tags": [session_type, tone, primary_role]
        }

        # Build AgentContract
        from models.agent import AgentContract, AgentIdentity, AgentTraits, AgentConfiguration, VoiceConfiguration, AgentMetadata, AgentStatus, AgentType

        contract = AgentContract(
            name=guide_contract_dict["name"],
            type=AgentType.CONVERSATIONAL,
            identity=AgentIdentity(**guide_contract_dict["identity"]),
            traits=calculated_traits,  # Use AI-calculated traits directly
            configuration=AgentConfiguration(**guide_contract_dict["configuration"]),
            voice=VoiceConfiguration(**guide_contract_dict["voice"]),
            metadata=AgentMetadata(
                tenant_id=tenant_id,
                owner_id=user_id,
                tags=guide_contract_dict["tags"],
                status=AgentStatus.ACTIVE
            )
        )

        # 2. Create Agent
        agent = await agent_service.create_agent(contract, tenant_id, user_id)
        agent_id = agent["id"]

        logger.info(f"✅ Guide created: {agent_id}")

        # 3. Auto-create Session
        session_id = str(uuid_lib.uuid4())
        from database import get_pg_pool
        pool = get_pg_pool()

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

        logger.info(f"✅ Session created: {session_id}")

        # 4. Immediately generate Manifestation Protocol
        protocol_agent = ManifestationProtocolAgent()

        protocol = await protocol_agent.generate_protocol({
            "user_id": user_id,
            "goal": normalized_goals[0] if normalized_goals else "Personal growth",
            "timeframe": "30_days",
            "commitment_level": "moderate"
        })

        logger.info(f"✅ Protocol generated for session: {session_id}")

        # 5. Update session with protocol
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

        # 6. Store protocol in memory (non-blocking)
        try:
            from memoryManager.memory_manager import MemoryManager
            
            # MemoryManager requires tenant_id, agent_id, and agent_traits
            # Use calculated traits from the contract we just created
            agent_traits = calculated_traits.model_dump() if calculated_traits else {}
            
            memory_manager = MemoryManager(
                tenant_id=tenant_id,
                agent_id=agent_id,
                agent_traits=agent_traits
            )
            
            # Store protocol summary in memory
            protocol_summary = f"Generated manifestation protocol with {len(protocol.get('affirmations', {}).get('all', []))} affirmations, {len(protocol.get('daily_practices', []))} practices, {len(protocol.get('checkpoints', []))} checkpoints."
            
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
        except Exception as mem_error:
            logger.warning(f"Failed to store protocol in memory: {mem_error}")
            # Non-blocking - continue

        logger.info(f"🎉 Baseline flow complete: agent={agent_id}, session={session_id}")

        return {
            "agent": agent,
            "session": {
                "id": session_id,
                "agent_id": agent_id,
                "user_id": user_id,
                "status": "active"
            },
            "protocol": {
                "affirmations_count": len(protocol.get("affirmations", {}).get("all", [])),
                "daily_practices_count": len(protocol.get("daily_practices", [])),
                "checkpoints_count": len(protocol.get("checkpoints", []))
            }
        }

    except Exception as e:
        logger.error(f"Baseline flow failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create guide from intake: {str(e)}")
