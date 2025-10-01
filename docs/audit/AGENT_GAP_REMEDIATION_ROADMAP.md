# Agent Gap Remediation Roadmap
**Numen AI - Path to AGENT_CREATION_STANDARD Compliance**

**Current Compliance**: 18/100
**Target Compliance**: 90+/100
**Estimated Total LOE**: 70 hours (~2 weeks with 1 developer)

---

## Executive Summary

This roadmap provides a **phased implementation plan** to transform Numen AI from a hardcoded agent system to a **JSON contract-first, multi-tenant, database-backed agent platform** compliant with the AGENT_CREATION_STANDARD.

### Strategic Approach

1. **Foundation First**: Database schema, models, and core services
2. **Agent Lifecycle**: CRUD operations and contract management
3. **Memory & Threads**: Namespace isolation and conversation management
4. **Integration**: Update existing agents to use new architecture
5. **Testing & Validation**: Comprehensive test suite

Each phase is designed to be **independently deployable** while maintaining backward compatibility with existing functionality.

---

## Phase 1: Foundation - Models & Database Schema

**Goal**: Establish database foundation and Pydantic models for agent contracts

**Duration**: 8 hours (Day 1)

**Priority**: P0 - CRITICAL

### 1.1 Create Agent Contract Pydantic Models

**File**: `backend/models/agent.py` (NEW)

```python
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid


class AgentType(str, Enum):
    CONVERSATIONAL = "conversational"
    VOICE = "voice"
    WORKFLOW = "workflow"
    AUTONOMOUS = "autonomous"


class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AgentTraits(BaseModel):
    """Agent personality traits (0-100 scale)"""
    creativity: int = Field(ge=0, le=100, default=50, description="Creative vs structured responses")
    empathy: int = Field(ge=0, le=100, default=50, description="Emotional sensitivity")
    assertiveness: int = Field(ge=0, le=100, default=50, description="Directive vs suggestive")
    humor: int = Field(ge=0, le=100, default=30, description="Lighthearted vs serious tone")
    formality: int = Field(ge=0, le=100, default=50, description="Formal vs casual language")
    verbosity: int = Field(ge=0, le=100, default=50, description="Concise vs detailed responses")
    confidence: int = Field(ge=0, le=100, default=70, description="Certainty in responses")
    technicality: int = Field(ge=0, le=100, default=50, description="Technical vs accessible language")
    safety: int = Field(ge=0, le=100, default=80, description="Risk aversion level")

    class Config:
        json_schema_extra = {
            "example": {
                "creativity": 75,
                "empathy": 90,
                "assertiveness": 60,
                "humor": 40,
                "formality": 30,
                "verbosity": 65,
                "confidence": 80,
                "technicality": 50,
                "safety": 85
            }
        }


class AgentIdentity(BaseModel):
    """Agent identity and character definition"""
    short_description: str = Field(..., description="One-line agent purpose")
    full_description: Optional[str] = Field(default="", description="Detailed background")
    character_role: Optional[str] = Field(default="", description="Character this agent embodies")
    mission: Optional[str] = Field(default="", description="Primary objective")
    interaction_style: Optional[str] = Field(default="", description="Communication approach")

    class Config:
        json_schema_extra = {
            "example": {
                "short_description": "Empathetic hypnotherapy guide for manifestation",
                "full_description": "A warm, supportive hypnotherapist specializing in positive psychology",
                "character_role": "Compassionate Guide",
                "mission": "Help users manifest their goals through hypnotherapy",
                "interaction_style": "Gentle, encouraging, and deeply empathetic"
            }
        }


class AgentConfiguration(BaseModel):
    """Agent runtime configuration"""
    llm_provider: str = Field(default="openai", description="LLM provider")
    llm_model: str = Field(default="gpt-4o-mini", description="Model name")
    max_tokens: int = Field(ge=50, le=4000, default=500, description="Max response tokens")
    temperature: float = Field(ge=0.0, le=2.0, default=0.7, description="LLM temperature")
    memory_enabled: bool = Field(default=True, description="Enable persistent memory")
    voice_enabled: bool = Field(default=False, description="Enable voice capabilities")
    tools_enabled: bool = Field(default=False, description="Enable tool use")

    # Memory settings
    memory_k: int = Field(ge=1, le=20, default=6, description="Number of memories to retrieve")
    thread_window: int = Field(ge=5, le=50, default=20, description="Recent messages to include")

    class Config:
        json_schema_extra = {
            "example": {
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "max_tokens": 800,
                "temperature": 0.8,
                "memory_enabled": True,
                "voice_enabled": True,
                "tools_enabled": False,
                "memory_k": 6,
                "thread_window": 20
            }
        }


class VoiceConfiguration(BaseModel):
    """Voice-specific configuration for voice agents"""
    provider: str = Field(default="elevenlabs", description="TTS provider")
    voice_id: str = Field(..., description="Voice ID or name")
    language: str = Field(default="en-US", description="Language code")
    speed: float = Field(ge=0.5, le=2.0, default=1.0, description="Speech speed")
    pitch: float = Field(ge=0.5, le=2.0, default=1.0, description="Voice pitch")
    stability: float = Field(ge=0.0, le=1.0, default=0.75, description="Voice stability")
    similarity_boost: float = Field(ge=0.0, le=1.0, default=0.75, description="Similarity boost")

    # STT configuration
    stt_provider: str = Field(default="deepgram", description="STT provider")
    stt_model: str = Field(default="nova-2", description="STT model")
    stt_language: str = Field(default="en", description="STT language")
    vad_enabled: bool = Field(default=True, description="Voice activity detection")


class AgentMetadata(BaseModel):
    """Agent metadata and organizational info"""
    tenant_id: str = Field(..., description="Organization/tenant ID")
    owner_id: str = Field(..., description="User ID of creator")
    tags: List[str] = Field(default_factory=list, description="Organizational tags")
    status: AgentStatus = Field(default=AgentStatus.ACTIVE, description="Agent status")


class AgentContract(BaseModel):
    """Complete agent JSON contract"""
    # Core identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Agent UUID")
    name: str = Field(..., description="Agent display name")
    type: AgentType = Field(default=AgentType.CONVERSATIONAL, description="Agent type")
    version: str = Field(default="1.0.0", description="Contract version")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Contract components
    identity: AgentIdentity
    traits: AgentTraits = Field(default_factory=AgentTraits)
    configuration: AgentConfiguration = Field(default_factory=AgentConfiguration)
    voice: Optional[VoiceConfiguration] = None
    metadata: AgentMetadata

    @validator('type')
    def validate_type(cls, v):
        if v not in AgentType.__members__.values():
            raise ValueError(f'type must be one of {list(AgentType.__members__.values())}')
        return v

    @validator('voice')
    def validate_voice_for_voice_agents(cls, v, values):
        if values.get('type') == AgentType.VOICE and v is None:
            raise ValueError('Voice agents must have voice configuration')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "IntakeAgent - Manifestation Coach",
                "type": "voice",
                "version": "1.0.0",
                "identity": {
                    "short_description": "Empathetic intake specialist for hypnotherapy",
                    "mission": "Collect user goals and preferences with compassion"
                },
                "traits": {
                    "creativity": 60,
                    "empathy": 95,
                    "assertiveness": 40
                },
                "configuration": {
                    "llm_model": "gpt-4",
                    "temperature": 0.7,
                    "voice_enabled": True
                },
                "metadata": {
                    "tenant_id": "tenant-uuid",
                    "owner_id": "user-uuid",
                    "tags": ["production", "hypnotherapy"],
                    "status": "active"
                }
            }
        }


class AgentCreateRequest(BaseModel):
    """API request model for creating agents"""
    name: str
    type: AgentType
    identity: AgentIdentity
    traits: Optional[AgentTraits] = None
    configuration: Optional[AgentConfiguration] = None
    voice: Optional[VoiceConfiguration] = None
    tags: List[str] = Field(default_factory=list)


class AgentUpdateRequest(BaseModel):
    """API request model for updating agents"""
    name: Optional[str] = None
    identity: Optional[AgentIdentity] = None
    traits: Optional[AgentTraits] = None
    configuration: Optional[AgentConfiguration] = None
    voice: Optional[VoiceConfiguration] = None
    tags: Optional[List[str]] = None
    status: Optional[AgentStatus] = None


class AgentResponse(BaseModel):
    """API response model for agent details"""
    id: str
    name: str
    type: AgentType
    version: str
    identity: AgentIdentity
    traits: AgentTraits
    configuration: AgentConfiguration
    voice: Optional[VoiceConfiguration]
    status: AgentStatus
    interaction_count: int
    last_interaction_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

**Action Items**:
- [ ] Create `backend/models/agent.py` with above code
- [ ] Update `backend/models/__init__.py` to export agent models
- [ ] Run validation tests with sample JSON contracts

---

### 1.2 Extend Database Schema

**File**: `backend/database.py` (UPDATE)

**Add Migration SQL**:

```python
# backend/database.py - Add to init_db()

async def init_db():
    # ... existing code ...

    async with pg_pool.acquire() as conn:
        # === NEW TABLES ===

        # Tenants table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(100) UNIQUE NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Users table (extended with tenant relationship)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID REFERENCES tenants(id),
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255),
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Agents table (JSON contract storage)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id UUID PRIMARY KEY,
                tenant_id UUID NOT NULL REFERENCES tenants(id),
                owner_id UUID NOT NULL REFERENCES users(id),
                name VARCHAR(255) NOT NULL,
                type VARCHAR(50) NOT NULL,
                version VARCHAR(20) DEFAULT '1.0.0',
                contract JSONB NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                interaction_count INTEGER DEFAULT 0,
                last_interaction_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agents_tenant ON agents(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
            CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);
        """)

        # Agent versions table (contract history)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_versions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id UUID NOT NULL REFERENCES agents(id),
                version VARCHAR(20) NOT NULL,
                contract JSONB NOT NULL,
                change_summary TEXT,
                created_by UUID REFERENCES users(id),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_versions_agent ON agent_versions(agent_id);
        """)

        # Threads table (conversation threads)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id UUID NOT NULL REFERENCES agents(id),
                user_id UUID NOT NULL REFERENCES users(id),
                tenant_id UUID NOT NULL REFERENCES tenants(id),
                title VARCHAR(500),
                status VARCHAR(20) DEFAULT 'active',
                message_count INTEGER DEFAULT 0,
                last_message_at TIMESTAMP,
                context_summary TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_threads_agent ON threads(agent_id);
            CREATE INDEX IF NOT EXISTS idx_threads_user ON threads(user_id);
            CREATE INDEX IF NOT EXISTS idx_threads_tenant ON threads(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_threads_status ON threads(status);
        """)

        # Thread messages table (message persistence)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS thread_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                metadata JSONB,
                feedback_score FLOAT,
                feedback_reason TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_thread ON thread_messages(thread_id);
            CREATE INDEX IF NOT EXISTS idx_messages_created ON thread_messages(created_at);
        """)

        # Update sessions table to include agent_id and tenant_id
        await conn.execute("""
            ALTER TABLE sessions
            ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES agents(id),
            ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON sessions(tenant_id);
        """)

        logger.info("All database tables initialized")
```

**Action Items**:
- [ ] Update `backend/database.py` with new tables
- [ ] Create Alembic migration script (optional, for version control)
- [ ] Test database creation in local environment
- [ ] Verify indexes created correctly

---

### 1.3 Create Default Tenant & Test User

**File**: `backend/scripts/seed_data.py` (NEW)

```python
"""Seed database with default tenant and test user"""
import asyncio
import uuid
from database import init_db, get_pg_pool


async def seed_database():
    await init_db()
    pool = get_pg_pool()

    async with pool.acquire() as conn:
        # Create default tenant
        tenant_id = uuid.uuid4()
        await conn.execute("""
            INSERT INTO tenants (id, name, slug, status)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (slug) DO NOTHING
        """, tenant_id, "Numen AI", "numen-ai", "active")

        # Create test user
        user_id = uuid.uuid4()
        await conn.execute("""
            INSERT INTO users (id, tenant_id, email, name, status)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (email) DO NOTHING
        """, user_id, tenant_id, "admin@numen.ai", "Admin User", "active")

        print(f"✅ Created tenant: {tenant_id}")
        print(f"✅ Created user: {user_id}")


if __name__ == "__main__":
    asyncio.run(seed_database())
```

**Action Items**:
- [ ] Create `backend/scripts/seed_data.py`
- [ ] Run: `python backend/scripts/seed_data.py`
- [ ] Verify tenant and user created in database

---

## Phase 2: Agent Lifecycle - CRUD Operations

**Goal**: Implement agent creation, retrieval, update, and delete operations

**Duration**: 12 hours (Day 2-3)

**Priority**: P0 - CRITICAL

### 2.1 Create Agent Service Layer

**File**: `backend/services/agent_service.py` (NEW)

```python
"""Agent service for CRUD operations and lifecycle management"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID

import asyncpg
from pydantic import ValidationError

from models.agent import (
    AgentContract,
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentResponse,
    AgentStatus,
    AgentMetadata
)
from database import get_pg_pool

logger = logging.getLogger(__name__)


class AgentService:
    """Service for agent lifecycle management"""

    def __init__(self):
        self.prompts_dir = Path("backend/prompts")
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    async def create_agent(
        self,
        request: AgentCreateRequest,
        tenant_id: str,
        owner_id: str
    ) -> AgentResponse:
        """
        Create new agent with complete initialization

        Steps:
        1. Build contract from request
        2. Validate contract
        3. Create database record
        4. Save filesystem JSON
        5. Initialize memory namespace (Phase 3)
        6. Return agent response
        """
        pool = get_pg_pool()

        try:
            # Build contract
            metadata = AgentMetadata(
                tenant_id=tenant_id,
                owner_id=owner_id,
                tags=request.tags,
                status=AgentStatus.ACTIVE
            )

            contract = AgentContract(
                name=request.name,
                type=request.type,
                identity=request.identity,
                traits=request.traits or AgentTraits(),
                configuration=request.configuration or AgentConfiguration(),
                voice=request.voice,
                metadata=metadata
            )

            # Validate contract
            contract_dict = contract.model_dump()

            # Insert into database
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agents (
                        id, tenant_id, owner_id, name, type, version,
                        contract, status, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                    UUID(contract.id),
                    UUID(tenant_id),
                    UUID(owner_id),
                    contract.name,
                    contract.type.value,
                    contract.version,
                    json.dumps(contract_dict),
                    AgentStatus.ACTIVE.value,
                    contract.created_at,
                    contract.updated_at
                )

            # Save filesystem JSON
            await self._save_contract_to_filesystem(contract.id, contract)

            logger.info(f"✅ Agent created: {contract.id} by {owner_id}")

            return AgentResponse(
                id=contract.id,
                name=contract.name,
                type=contract.type,
                version=contract.version,
                identity=contract.identity,
                traits=contract.traits,
                configuration=contract.configuration,
                voice=contract.voice,
                status=AgentStatus.ACTIVE,
                interaction_count=0,
                last_interaction_at=None,
                created_at=contract.created_at,
                updated_at=contract.updated_at
            )

        except ValidationError as e:
            logger.error(f"Contract validation failed: {e}")
            raise ValueError(f"Invalid agent contract: {e}")
        except Exception as e:
            logger.error(f"Agent creation failed: {e}")
            raise

    async def get_agent(
        self,
        agent_id: str,
        tenant_id: str
    ) -> Optional[AgentResponse]:
        """Get agent by ID with tenant validation"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM agents
                    WHERE id = $1 AND tenant_id = $2 AND status != 'deleted'
                """, UUID(agent_id), UUID(tenant_id))

                if not row:
                    return None

                contract = json.loads(row['contract'])

                return AgentResponse(
                    id=str(row['id']),
                    name=row['name'],
                    type=row['type'],
                    version=row['version'],
                    identity=contract['identity'],
                    traits=contract['traits'],
                    configuration=contract['configuration'],
                    voice=contract.get('voice'),
                    status=AgentStatus(row['status']),
                    interaction_count=row['interaction_count'],
                    last_interaction_at=row['last_interaction_at'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )

        except Exception as e:
            logger.error(f"Failed to get agent: {e}")
            raise

    async def list_agents(
        self,
        tenant_id: str,
        status: Optional[AgentStatus] = None,
        agent_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AgentResponse]:
        """List agents for tenant with filtering"""
        pool = get_pg_pool()

        try:
            query = "SELECT * FROM agents WHERE tenant_id = $1 AND status != 'deleted'"
            params = [UUID(tenant_id)]

            if status:
                query += f" AND status = ${len(params) + 1}"
                params.append(status.value)

            if agent_type:
                query += f" AND type = ${len(params) + 1}"
                params.append(agent_type)

            query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
            params.extend([limit, offset])

            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

                return [
                    AgentResponse(
                        id=str(row['id']),
                        name=row['name'],
                        type=row['type'],
                        version=row['version'],
                        identity=json.loads(row['contract'])['identity'],
                        traits=json.loads(row['contract'])['traits'],
                        configuration=json.loads(row['contract'])['configuration'],
                        voice=json.loads(row['contract']).get('voice'),
                        status=AgentStatus(row['status']),
                        interaction_count=row['interaction_count'],
                        last_interaction_at=row['last_interaction_at'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            raise

    async def update_agent(
        self,
        agent_id: str,
        tenant_id: str,
        updates: AgentUpdateRequest,
        updated_by: str
    ) -> AgentResponse:
        """Update agent contract with versioning"""
        pool = get_pg_pool()

        try:
            # Get current agent
            agent = await self.get_agent(agent_id, tenant_id)
            if not agent:
                raise ValueError("Agent not found")

            # Load current contract
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT contract FROM agents WHERE id = $1",
                    UUID(agent_id)
                )
                current_contract = json.loads(row['contract'])

            # Create version snapshot
            await self._create_version_snapshot(
                agent_id, current_contract, updated_by
            )

            # Apply updates
            if updates.name:
                current_contract['name'] = updates.name
            if updates.identity:
                current_contract['identity'] = updates.identity.model_dump()
            if updates.traits:
                current_contract['traits'] = updates.traits.model_dump()
            if updates.configuration:
                current_contract['configuration'] = updates.configuration.model_dump()
            if updates.voice:
                current_contract['voice'] = updates.voice.model_dump()
            if updates.tags:
                current_contract['metadata']['tags'] = updates.tags
            if updates.status:
                current_contract['metadata']['status'] = updates.status.value

            current_contract['updated_at'] = datetime.utcnow().isoformat()

            # Update database
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agents
                    SET contract = $1, updated_at = $2, name = $3, status = $4
                    WHERE id = $5
                """,
                    json.dumps(current_contract),
                    datetime.utcnow(),
                    current_contract['name'],
                    current_contract['metadata']['status'],
                    UUID(agent_id)
                )

            # Update filesystem
            contract = AgentContract(**current_contract)
            await self._save_contract_to_filesystem(agent_id, contract)

            logger.info(f"✅ Agent updated: {agent_id} by {updated_by}")

            return await self.get_agent(agent_id, tenant_id)

        except Exception as e:
            logger.error(f"Failed to update agent: {e}")
            raise

    async def delete_agent(
        self,
        agent_id: str,
        tenant_id: str
    ) -> bool:
        """Soft delete agent (set status to 'archived')"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE agents
                    SET status = 'archived', updated_at = $1
                    WHERE id = $2 AND tenant_id = $3
                """, datetime.utcnow(), UUID(agent_id), UUID(tenant_id))

                if result == "UPDATE 0":
                    return False

            logger.info(f"✅ Agent archived: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
            raise

    async def _save_contract_to_filesystem(
        self,
        agent_id: str,
        contract: AgentContract
    ):
        """Save agent contract to filesystem for prompt loading"""
        agent_dir = self.prompts_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)

        # Save complete contract
        contract_path = agent_dir / "agent_specific_prompt.json"
        with open(contract_path, 'w', encoding='utf-8') as f:
            json.dump(contract.model_dump(), f, indent=2, default=str)

        # Save attributes (for backward compatibility)
        attributes_path = agent_dir / "agent_attributes.json"
        with open(attributes_path, 'w', encoding='utf-8') as f:
            json.dump({
                "id": agent_id,
                "name": contract.name,
                "traits": contract.traits.model_dump(),
                "configuration": contract.configuration.model_dump()
            }, f, indent=2)

        logger.info(f"Saved contract to filesystem: {contract_path}")

    async def _create_version_snapshot(
        self,
        agent_id: str,
        contract: Dict[str, Any],
        created_by: str
    ):
        """Create version snapshot before update"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_versions (agent_id, version, contract, created_by)
                    VALUES ($1, $2, $3, $4)
                """,
                    UUID(agent_id),
                    contract.get('version', '1.0.0'),
                    json.dumps(contract),
                    UUID(created_by)
                )

            logger.info(f"Created version snapshot for agent {agent_id}")

        except Exception as e:
            logger.error(f"Failed to create version snapshot: {e}")
```

**Action Items**:
- [ ] Create `backend/services/agent_service.py`
- [ ] Create `backend/prompts/` directory
- [ ] Test agent CRUD operations with pytest

---

### 2.2 Create Agent CRUD API Endpoints

**File**: `backend/routers/agents.py` (NEW)

```python
"""Agent CRUD API endpoints"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID

from models.agent import (
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentResponse,
    AgentStatus
)
from services.agent_service import AgentService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


# TODO: Replace with real authentication
async def get_tenant_id() -> str:
    """Get tenant ID from auth context (placeholder)"""
    # In production, extract from JWT or session
    return "550e8400-e29b-41d4-a716-446655440000"


async def get_user_id() -> str:
    """Get user ID from auth context (placeholder)"""
    # In production, extract from JWT or session
    return "660e8400-e29b-41d4-a716-446655440001"


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(
    request: AgentCreateRequest,
    tenant_id: str = Depends(get_tenant_id),
    owner_id: str = Depends(get_user_id)
):
    """
    Create new agent with JSON contract

    Process:
    1. Validate request
    2. Create database record
    3. Save filesystem JSON
    4. Initialize memory namespace
    5. Return agent object
    """
    try:
        service = AgentService()
        agent = await service.create_agent(
            request=request,
            tenant_id=tenant_id,
            owner_id=owner_id
        )
        return agent

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create agent")


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    tenant_id: str = Depends(get_tenant_id),
    status: Optional[AgentStatus] = Query(None),
    agent_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List agents for tenant with filtering"""
    try:
        service = AgentService()
        agents = await service.list_agents(
            tenant_id=tenant_id,
            status=status,
            agent_type=agent_type,
            limit=limit,
            offset=offset
        )
        return agents

    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list agents")


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get agent details by ID"""
    try:
        service = AgentService()
        agent = await service.get_agent(agent_id, tenant_id)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent")


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    updates: AgentUpdateRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
):
    """Update agent contract"""
    try:
        service = AgentService()
        agent = await service.update_agent(
            agent_id=agent_id,
            tenant_id=tenant_id,
            updates=updates,
            updated_by=user_id
        )
        return agent

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to update agent")


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Archive agent (soft delete)"""
    try:
        service = AgentService()
        success = await service.delete_agent(agent_id, tenant_id)

        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete agent")
```

**Action Items**:
- [ ] Create `backend/routers/agents.py`
- [ ] Register router in `backend/main.py`: `app.include_router(agents.router)`
- [ ] Test endpoints with curl/Postman

---

## Phase 3: Memory & Thread Management

**Goal**: Implement UnifiedMemoryManager and ThreadManager with namespace isolation

**Duration**: 16 hours (Day 4-5)

**Priority**: P1 - HIGH

### 3.1 Create UnifiedMemoryManager

**File**: `backend/services/unified_memory_manager.py` (NEW)

```python
"""
Unified Memory Manager with namespace isolation and hybrid retrieval
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from mem0 import Memory
from qdrant_client import QdrantClient
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)


class MemorySettings(BaseModel):
    """Memory system configuration"""
    k: int = 6  # Number of memories to retrieve
    thread_window: int = 20  # Recent messages to include
    alpha_recency: float = 0.35  # Recency weight
    alpha_semantic: float = 0.45  # Semantic similarity weight
    alpha_reinforcement: float = 0.20  # Reinforcement weight


class MemoryContext(BaseModel):
    """Memory context returned for agent processing"""
    retrieved_memories: List[Dict[str, Any]]
    recent_messages: List[Dict[str, Any]]
    confidence_score: float
    namespace: str


class UnifiedMemoryManager:
    """
    Unified memory manager with:
    - Namespace isolation: {tenant_id}:{agent_id}:{context}
    - Hybrid retrieval: recency + semantic + reinforcement
    - Agent contract-driven settings
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

        # Initialize Mem0
        self.memory = None
        self.qdrant_client = None

    async def initialize(self):
        """Initialize memory connections"""
        try:
            # Initialize Qdrant
            self.qdrant_client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                api_key=settings.qdrant_api_key
            )

            # Initialize Mem0 with Qdrant backend
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "host": settings.qdrant_host,
                        "port": settings.qdrant_port,
                    }
                }
            }

            self.memory = Memory.from_config(config)
            logger.info(f"Memory initialized for namespace: {self.namespace}")

        except Exception as e:
            logger.error(f"Failed to initialize memory: {e}")
            raise

    def agent_namespace(self) -> str:
        """Get agent-level namespace"""
        return self.namespace

    def thread_namespace(self, thread_id: str) -> str:
        """Get thread-level namespace"""
        return f"{self.namespace}:thread:{thread_id}"

    def user_namespace(self, user_id: str) -> str:
        """Get user-level namespace"""
        return f"{self.namespace}:user:{user_id}"

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
        """
        try:
            if not self.memory:
                await self.initialize()

            thread_namespace = self.thread_namespace(session_id)

            # Semantic search in agent namespace
            semantic_memories = await self._search_memories(
                query=user_input,
                namespace=self.namespace,
                limit=self.settings.k
            )

            # Get recent thread messages
            recent_messages = await self._get_recent_thread_messages(
                session_id=session_id,
                limit=self.settings.thread_window
            )

            # User-specific memories (if applicable)
            user_memories = []
            if user_id:
                user_memories = await self._search_memories(
                    query=user_input,
                    namespace=self.user_namespace(user_id),
                    limit=3
                )

            # Combine and score
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
        try:
            if not self.memory:
                await self.initialize()

            thread_namespace = self.thread_namespace(session_id)

            # Store in thread namespace
            self.memory.add(
                messages=[
                    f"User: {user_input}",
                    f"Agent: {agent_response}"
                ],
                user_id=thread_namespace,
                metadata={
                    "namespace": thread_namespace,
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            logger.info(f"Stored interaction in namespace: {thread_namespace}")

        except Exception as e:
            logger.error(f"Failed to process interaction: {e}")

    async def store_agent_memory(
        self,
        content: str,
        memory_type: str = "reflection"
    ):
        """Store agent-level persistent memory"""
        try:
            if not self.memory:
                await self.initialize()

            self.memory.add(
                messages=[content],
                user_id=self.namespace,
                metadata={
                    "namespace": self.namespace,
                    "type": memory_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            logger.info(f"Stored agent memory in namespace: {self.namespace}")

        except Exception as e:
            logger.error(f"Failed to store agent memory: {e}")

    async def _search_memories(
        self,
        query: str,
        namespace: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search memories in specific namespace"""
        try:
            results = self.memory.search(
                query=query,
                user_id=namespace,
                limit=limit
            )

            return [
                {
                    "content": r.get("message", ""),
                    "metadata": r.get("metadata", {}),
                    "score": r.get("score", 0.0)
                }
                for r in (results or [])
            ]

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []

    async def _get_recent_thread_messages(
        self,
        session_id: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get recent thread messages from database"""
        # This will be implemented in ThreadManager integration
        # For now, return empty list
        return []

    def _calculate_confidence(self, memories: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on memory relevance"""
        if not memories:
            return 0.0

        avg_score = sum(m.get("score", 0.0) for m in memories) / len(memories)
        return min(avg_score, 1.0)
```

**Action Items**:
- [ ] Create `backend/services/unified_memory_manager.py`
- [ ] Test namespace isolation with different agent_id/tenant_id
- [ ] Verify Qdrant collections created correctly

---

### 3.2 Create ThreadManager Service

**File**: `backend/services/thread_manager.py` (NEW)

```python
"""Thread management service for conversation persistence"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID, uuid4

from database import get_pg_pool

logger = logging.getLogger(__name__)


class ThreadManager:
    """Manages conversation threads for agent-user interactions"""

    async def create_thread(
        self,
        agent_id: str,
        user_id: str,
        tenant_id: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create new conversation thread"""
        pool = get_pg_pool()
        thread_id = uuid4()

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO threads (
                        id, agent_id, user_id, tenant_id, title,
                        status, message_count, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    thread_id,
                    UUID(agent_id),
                    UUID(user_id),
                    UUID(tenant_id),
                    title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                    "active",
                    0,
                    datetime.utcnow(),
                    datetime.utcnow()
                )

            logger.info(f"Created thread {thread_id}")

            return {
                "id": str(thread_id),
                "agent_id": agent_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "title": title,
                "status": "active",
                "message_count": 0,
                "created_at": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            raise

    async def get_or_create_thread(
        self,
        agent_id: str,
        user_id: str,
        tenant_id: str,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get existing thread or create new one"""
        pool = get_pg_pool()

        try:
            if thread_id:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT * FROM threads
                        WHERE id = $1
                          AND agent_id = $2
                          AND user_id = $3
                          AND status = 'active'
                    """, UUID(thread_id), UUID(agent_id), UUID(user_id))

                    if row:
                        return {
                            "id": str(row['id']),
                            "agent_id": str(row['agent_id']),
                            "user_id": str(row['user_id']),
                            "tenant_id": str(row['tenant_id']),
                            "title": row['title'],
                            "status": row['status'],
                            "message_count": row['message_count'],
                            "created_at": row['created_at']
                        }

            # Create new thread
            return await self.create_thread(agent_id, user_id, tenant_id)

        except Exception as e:
            logger.error(f"Failed to get/create thread: {e}")
            raise

    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add message to thread"""
        pool = get_pg_pool()
        message_id = uuid4()

        try:
            async with pool.acquire() as conn:
                # Insert message
                await conn.execute("""
                    INSERT INTO thread_messages (id, thread_id, role, content, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    message_id,
                    UUID(thread_id),
                    role,
                    content,
                    metadata or {},
                    datetime.utcnow()
                )

                # Update thread
                await conn.execute("""
                    UPDATE threads
                    SET message_count = message_count + 1,
                        last_message_at = $1,
                        updated_at = $1
                    WHERE id = $2
                """, datetime.utcnow(), UUID(thread_id))

            logger.info(f"Added message to thread {thread_id}")

            return {
                "id": str(message_id),
                "thread_id": thread_id,
                "role": role,
                "content": content,
                "created_at": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise

    async def get_thread_history(
        self,
        thread_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent thread messages"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM thread_messages
                    WHERE thread_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, UUID(thread_id), limit)

                messages = [
                    {
                        "id": str(row['id']),
                        "role": row['role'],
                        "content": row['content'],
                        "metadata": row['metadata'],
                        "created_at": row['created_at']
                    }
                    for row in rows
                ]

                return list(reversed(messages))

        except Exception as e:
            logger.error(f"Failed to get thread history: {e}")
            return []
```

**Action Items**:
- [ ] Create `backend/services/thread_manager.py`
- [ ] Test thread creation and message persistence
- [ ] Verify message history retrieval works correctly

---

## Phase 4: Integration - Update Existing Agents

**Goal**: Refactor IntakeAgent and TherapyAgent to use new architecture

**Duration**: 10 hours (Day 6)

**Priority**: P1 - HIGH

### 4.1 Create Agent Interaction Service

**File**: `backend/services/agent_interaction_service.py` (NEW)

```python
"""
Agent interaction service - Standard flow for agent-user interactions
"""
import logging
from typing import Dict, Any, Optional

from services.agent_service import AgentService
from services.thread_manager import ThreadManager
from services.unified_memory_manager import UnifiedMemoryManager
from agents.intake_agent import IntakeAgent
from agents.therapy_agent import TherapyAgent

logger = logging.getLogger(__name__)


class AgentInteractionService:
    """Standard interaction processing for all agents"""

    def __init__(self):
        self.agent_service = AgentService()
        self.thread_manager = ThreadManager()

    async def process_interaction(
        self,
        agent_id: str,
        user_id: str,
        tenant_id: str,
        user_input: str,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Standard agent-user interaction processing

        Steps:
        1. Load agent contract from DB
        2. Get/create thread
        3. Initialize memory manager
        4. Get memory context
        5. Process through agent (LangGraph)
        6. Store interaction
        7. Update agent metrics
        8. Return response
        """

        try:
            # Step 1: Load agent contract
            agent = await self.agent_service.get_agent(agent_id, tenant_id)
            if not agent:
                raise ValueError("Agent not found")

            # Step 2: Get or create thread
            thread = await self.thread_manager.get_or_create_thread(
                agent_id=agent_id,
                user_id=user_id,
                tenant_id=tenant_id,
                thread_id=thread_id
            )

            # Step 3: Initialize memory manager
            memory_manager = UnifiedMemoryManager(
                tenant_id=tenant_id,
                agent_id=agent_id,
                agent_traits=agent.traits.model_dump()
            )
            await memory_manager.initialize()

            # Step 4: Get memory context
            memory_context = await memory_manager.get_agent_context(
                user_input=user_input,
                session_id=thread['id'],
                user_id=user_id
            )

            # Step 5: Process through agent
            # TODO: Build graph dynamically from contract
            # For now, route to existing agents
            response_text = await self._process_through_agent(
                agent=agent,
                user_input=user_input,
                memory_context=memory_context,
                thread_id=thread['id']
            )

            # Step 6: Store interaction
            await self.thread_manager.add_message(
                thread_id=thread['id'],
                role="user",
                content=user_input,
                metadata=metadata
            )

            await self.thread_manager.add_message(
                thread_id=thread['id'],
                role="assistant",
                content=response_text,
                metadata={
                    "confidence": memory_context.confidence_score
                }
            )

            # Process through memory
            await memory_manager.process_interaction(
                user_input=user_input,
                agent_response=response_text,
                session_id=thread['id'],
                user_id=user_id
            )

            # Step 7: Update agent metrics
            # TODO: Increment interaction_count, update last_interaction_at

            # Step 8: Return response
            return {
                "thread_id": thread['id'],
                "agent_id": agent_id,
                "response": response_text,
                "metadata": {
                    "memory_confidence": memory_context.confidence_score,
                    "message_count": thread['message_count'] + 2
                }
            }

        except Exception as e:
            logger.error(f"Interaction processing failed: {e}")
            raise

    async def _process_through_agent(
        self,
        agent: Any,
        user_input: str,
        memory_context: Any,
        thread_id: str
    ) -> str:
        """Process through specific agent type"""
        # TODO: Replace with contract-driven graph building
        # For now, route to existing agents
        if agent.type == "voice" and "Intake" in agent.name:
            intake_agent = IntakeAgent()
            # Process through intake agent
            return "Intake agent response (TODO: implement)"

        return "Agent response placeholder"
```

**Action Items**:
- [ ] Create `backend/services/agent_interaction_service.py`
- [ ] Add endpoint `/api/v1/agents/{agent_id}/chat` in `backend/routers/agents.py`
- [ ] Test end-to-end interaction flow

---

### 4.2 Update Main.py to Register New Routes

**File**: `backend/main.py` (UPDATE)

```python
# Add new router imports
from routers import agents

# Register new routes
app.include_router(agents.router)
```

---

## Phase 5: Testing & Validation

**Goal**: Create comprehensive test suite for agent lifecycle

**Duration**: 8 hours (Day 7)

**Priority**: P2 - MEDIUM

### 5.1 Create Test Suite

**File**: `backend/tests/test_agent_lifecycle.py` (NEW)

```python
"""Test agent lifecycle - CRUD, threads, memory"""
import pytest
import uuid
from models.agent import (
    AgentCreateRequest,
    AgentIdentity,
    AgentTraits,
    AgentType
)
from services.agent_service import AgentService
from services.thread_manager import ThreadManager


@pytest.fixture
def sample_agent_request():
    return AgentCreateRequest(
        name="Test Hypnotherapy Agent",
        type=AgentType.VOICE,
        identity=AgentIdentity(
            short_description="Test agent for validation",
            mission="Test agent capabilities"
        ),
        traits=AgentTraits(
            creativity=75,
            empathy=90,
            verbosity=50
        ),
        tags=["test", "hypnotherapy"]
    )


@pytest.mark.asyncio
async def test_agent_creation(sample_agent_request):
    """Test complete agent creation flow"""
    service = AgentService()
    tenant_id = str(uuid.uuid4())
    owner_id = str(uuid.uuid4())

    agent = await service.create_agent(
        request=sample_agent_request,
        tenant_id=tenant_id,
        owner_id=owner_id
    )

    assert agent.name == sample_agent_request.name
    assert agent.type == sample_agent_request.type
    assert agent.status == "active"
    assert agent.interaction_count == 0


@pytest.mark.asyncio
async def test_thread_creation():
    """Test thread management"""
    manager = ThreadManager()
    agent_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())

    thread = await manager.create_thread(
        agent_id=agent_id,
        user_id=user_id,
        tenant_id=tenant_id
    )

    assert thread['agent_id'] == agent_id
    assert thread['message_count'] == 0
    assert thread['status'] == 'active'


@pytest.mark.asyncio
async def test_message_persistence():
    """Test message storage and retrieval"""
    manager = ThreadManager()
    thread_id = str(uuid.uuid4())

    # Add messages
    await manager.add_message(thread_id, "user", "Hello")
    await manager.add_message(thread_id, "assistant", "Hi there")

    # Retrieve history
    history = await manager.get_thread_history(thread_id)
    assert len(history) == 2
    assert history[0]['role'] == 'user'
    assert history[1]['role'] == 'assistant'
```

**Action Items**:
- [ ] Create `backend/tests/test_agent_lifecycle.py`
- [ ] Run: `pytest backend/tests/test_agent_lifecycle.py -v`
- [ ] Achieve 80%+ test coverage

---

## Phase 6: Migration Strategy

**Goal**: Migrate existing IntakeAgent/TherapyAgent to new architecture

**Duration**: 8 hours (Day 8)

**Priority**: P2 - MEDIUM

### 6.1 Create Default Agent Contracts

**File**: `backend/scripts/create_default_agents.py` (NEW)

```python
"""Create default IntakeAgent and TherapyAgent contracts"""
import asyncio
from models.agent import (
    AgentCreateRequest,
    AgentIdentity,
    AgentTraits,
    AgentConfiguration,
    VoiceConfiguration,
    AgentType
)
from services.agent_service import AgentService


async def create_default_agents():
    """Create IntakeAgent and TherapyAgent with JSON contracts"""
    service = AgentService()

    # Default tenant/owner (from seed data)
    tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    owner_id = "660e8400-e29b-41d4-a716-446655440001"

    # IntakeAgent
    intake_request = AgentCreateRequest(
        name="IntakeAgent - Manifestation Coach",
        type=AgentType.VOICE,
        identity=AgentIdentity(
            short_description="Empathetic intake specialist for hypnotherapy",
            full_description="A warm, supportive intake agent that collects user goals and preferences with compassion",
            character_role="Compassionate Intake Guide",
            mission="Collect user goals and preferences to create personalized hypnotherapy sessions",
            interaction_style="Gentle, encouraging, deeply empathetic, and patient"
        ),
        traits=AgentTraits(
            creativity=60,
            empathy=95,
            assertiveness=40,
            humor=30,
            formality=30,
            verbosity=65,
            confidence=75,
            technicality=40,
            safety=90
        ),
        configuration=AgentConfiguration(
            llm_model="gpt-4",
            temperature=0.7,
            max_tokens=800,
            voice_enabled=True,
            memory_enabled=True
        ),
        voice=VoiceConfiguration(
            provider="elevenlabs",
            voice_id="calm-female",  # Replace with actual voice ID
            language="en-US",
            stability=0.75,
            similarity_boost=0.75,
            stt_provider="deepgram",
            stt_model="nova-2"
        ),
        tags=["production", "intake", "hypnotherapy"]
    )

    intake_agent = await service.create_agent(
        request=intake_request,
        tenant_id=tenant_id,
        owner_id=owner_id
    )

    print(f"✅ Created IntakeAgent: {intake_agent.id}")

    # TherapyAgent
    therapy_request = AgentCreateRequest(
        name="TherapyAgent - Hypnotherapist",
        type=AgentType.VOICE,
        identity=AgentIdentity(
            short_description="Expert hypnotherapist for manifestation and healing",
            full_description="A skilled hypnotherapist that creates personalized hypnotherapy scripts tailored to user goals",
            character_role="Master Hypnotherapist",
            mission="Guide users through transformative hypnotherapy sessions for manifestation and healing",
            interaction_style="Calm, authoritative yet gentle, deeply therapeutic"
        ),
        traits=AgentTraits(
            creativity=80,
            empathy=90,
            assertiveness=65,
            humor=20,
            formality=50,
            verbosity=70,
            confidence=85,
            technicality=55,
            safety=95
        ),
        configuration=AgentConfiguration(
            llm_model="gpt-4",
            temperature=0.8,
            max_tokens=1500,
            voice_enabled=True,
            memory_enabled=True
        ),
        voice=VoiceConfiguration(
            provider="elevenlabs",
            voice_id="soothing-male",  # Replace with actual voice ID
            language="en-US",
            speed=0.9,  # Slightly slower for hypnosis
            stability=0.85,
            similarity_boost=0.80,
            stt_provider="deepgram",
            stt_model="nova-2"
        ),
        tags=["production", "therapy", "hypnotherapy"]
    )

    therapy_agent = await service.create_agent(
        request=therapy_request,
        tenant_id=tenant_id,
        owner_id=owner_id
    )

    print(f"✅ Created TherapyAgent: {therapy_agent.id}")


if __name__ == "__main__":
    asyncio.run(create_default_agents())
```

**Action Items**:
- [ ] Create `backend/scripts/create_default_agents.py`
- [ ] Run: `python backend/scripts/create_default_agents.py`
- [ ] Verify agents created in database and filesystem (`backend/prompts/{agent_id}/`)

---

## Summary & Timeline

### Phased Implementation Timeline

| **Phase** | **Tasks** | **Duration** | **Priority** | **Deliverables** |
|---|---|---|---|---|
| **Phase 1** | Models & DB Schema | 8 hours (Day 1) | P0 | `models/agent.py`, DB tables, seed data |
| **Phase 2** | Agent CRUD | 12 hours (Day 2-3) | P0 | `services/agent_service.py`, `/api/v1/agents/*` |
| **Phase 3** | Memory & Threads | 16 hours (Day 4-5) | P1 | `UnifiedMemoryManager`, `ThreadManager` |
| **Phase 4** | Integration | 10 hours (Day 6) | P1 | `AgentInteractionService`, updated endpoints |
| **Phase 5** | Testing | 8 hours (Day 7) | P2 | Test suite, 80%+ coverage |
| **Phase 6** | Migration | 8 hours (Day 8) | P2 | Default agent contracts, documentation |

**Total**: ~62 hours (8 days with 1 developer)

---

### Success Criteria

**Phase 1-2 Complete (Foundation)**:
- ✅ Agents can be created via API with JSON contracts
- ✅ Agents stored in database with JSON contract column
- ✅ Agent CRUD operations functional
- ✅ Filesystem JSON storage working

**Phase 3-4 Complete (Memory & Integration)**:
- ✅ UnifiedMemoryManager with namespace isolation
- ✅ Thread management with message persistence
- ✅ Standard interaction flow (`process_interaction`)
- ✅ Memory context retrieved before agent processing

**Phase 5-6 Complete (Testing & Migration)**:
- ✅ 80%+ test coverage for agent lifecycle
- ✅ Existing IntakeAgent/TherapyAgent migrated to contracts
- ✅ All endpoints tested and documented

**Final Compliance Score**: **90+/100** ✅

---

### Risk Mitigation

**Risk**: Breaking existing functionality during refactor
- **Mitigation**: Maintain backward compatibility, create feature flags

**Risk**: Memory namespace collisions
- **Mitigation**: Strict namespace pattern validation, comprehensive tests

**Risk**: Performance degradation with memory retrieval
- **Mitigation**: Index Qdrant collections, cache frequent queries

**Risk**: Multi-tenancy data leakage
- **Mitigation**: Query-level tenant_id filtering, integration tests

---

## Next Steps

1. **Review & Approve**: Get stakeholder approval for roadmap
2. **Set Up Project Board**: Track tasks in Jira/GitHub Projects
3. **Begin Phase 1**: Create models and database schema
4. **Daily Standups**: Track progress and blockers
5. **Continuous Testing**: Write tests alongside implementation

---

**Document Version**: 1.0
**Last Updated**: 2025-10-01
**Owner**: Engineering Team
