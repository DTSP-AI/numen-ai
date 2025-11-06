# Agent/Guide JSON Contract Management Report

**Date**: 2025-01-15 (Updated: 2025-11-06)
**Status**: Production Ready
**Scope**: Complete contract lifecycle management system

---

## Executive Summary

The application implements a comprehensive **JSON Contract-First Architecture** for agent/guide management. Contracts serve as the single source of truth for agent identity, behavior, and configuration. The system provides full CRUD operations, version history, validation, and multi-tenant support.

**Key Components:**
- ✅ Database-backed contract storage (PRIMARY - ONLY)
- ✅ Version history tracking
- ✅ Contract validation (Pydantic v2)
- ✅ Voice configuration enforcement
- ✅ Complete API endpoints
- ✅ Service layer with lifecycle management
- ✅ Filesystem storage REMOVED (as of 2025-11-06)

---

## 1. Contract Model Structure

### 1.1 Core Model: `AgentContract`

**Location**: `backend/models/agent.py:314-443`

The `AgentContract` Pydantic model defines the complete contract specification:

```python
class AgentContract(BaseModel):
    # Core identity
    id: str                    # UUID v4
    name: str                  # Display name
    type: AgentType            # conversational|voice|workflow|autonomous
    version: str               # Semver (default: "1.0.0")
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Contract components
    identity: AgentIdentity
    traits: AgentTraits
    configuration: AgentConfiguration
    voice: Optional[VoiceConfiguration]
    metadata: AgentMetadata
    
    # Cognitive assessment (Phase 1 - Optional)
    cognitive_kernel_ref: Optional[str]
    goal_assessment_enabled: bool
    belief_mapping_enabled: bool
    reflex_triggers_enabled: bool
    cognitive_kernel_config: Optional[Dict[str, Any]]
```

### 1.2 Component Models

#### `AgentIdentity` (`agent.py:102-153`)
- `short_description`: One-line purpose (max 100 chars)
- `full_description`: Detailed background
- `character_role`: Character archetype
- `roles`: List of guide roles (Stoic Sage, Manifestation Mentor, etc.)
- `mission`: Primary objective
- `interaction_style`: Communication approach
- `interaction_styles`: Multiple interaction styles
- `avatar_url`: Avatar image URL

#### `AgentTraits` (`agent.py:34-100`)
Personality traits on 0-100 scale:
- **Core 4**: `confidence`, `empathy`, `creativity`, `discipline`
- **Additional**: `assertiveness`, `humor`, `formality`, `verbosity`, `spirituality`, `supportiveness`

#### `AgentConfiguration` (`agent.py:155-218`)
Runtime configuration:
- LLM settings: `llm_provider`, `llm_model`, `max_tokens`, `temperature`
- Capability flags: `memory_enabled`, `voice_enabled`, `tools_enabled`
- Memory settings: `memory_k`, `thread_window`

#### `VoiceConfiguration` (`agent.py:220-288`)
Voice-specific settings:
- TTS: `provider`, `voice_id`, `language`, `speed`, `pitch`, `stability`, `similarity_boost`
- STT: `stt_provider`, `stt_model`, `stt_language`, `vad_enabled`

#### `AgentMetadata` (`agent.py:290-312`)
Organizational info:
- `tenant_id`: Multi-tenant isolation
- `owner_id`: Creator user ID
- `tags`: Organizational tags
- `status`: `active|inactive|archived`

### 1.3 Voice Configuration Validation

**Status**: ✅ **ENFORCED** (as of 2025-11-06)
**Validator**: `backend/models/agent.py:407-421` (`@model_validator`)

**Validation Rules**:
1. **VOICE agents** (type=`AgentType.VOICE`) **REQUIRE** voice configuration
2. **Agents with voice_enabled=True** **REQUIRE** voice configuration
3. **Conversational agents** without voice_enabled may omit voice configuration

**Implementation**:
- Pydantic v2 `@model_validator(mode='after')` for cross-field validation
- Validates after all fields are populated
- Provides clear error message when voice is missing

**Test Coverage**:
- ✅ VOICE agent without voice → Validation error
- ✅ VOICE agent with voice → Success
- ✅ voice_enabled=True without voice → Validation error
- ✅ voice_enabled=True with voice → Success
- ✅ Conversational without voice → Success

**API-Level Validation**:
- `create_agent()` endpoint validates voice requirements (lines 97-126)
- `update_agent()` endpoint prevents removing voice from voice agents (lines 314-328)
- Default voice applied for voice_enabled=True if not provided (ElevenLabs Rachel)

---

## 2. Storage Architecture

### 2.1 Database Storage (PRIMARY)

**Table**: `agents`  
**Location**: `backend/database.py:88-103`

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    owner_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0.0',
    contract JSONB NOT NULL,              -- Complete contract stored here
    status VARCHAR(20) DEFAULT 'active',
    interaction_count INTEGER DEFAULT 0,
    last_interaction_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Indexes**:
- `idx_agents_tenant` on `tenant_id`
- `idx_agents_status` on `status`
- `idx_agents_type` on `type`

**Characteristics**:
- ✅ Single source of truth
- ✅ JSONB for efficient querying
- ✅ Tenant isolation enforced
- ✅ Full CRUD operations
- ✅ Cloud-native (PostgreSQL/Supabase)

### 2.2 Version History Storage

**Table**: `agent_versions`  
**Location**: `backend/database.py:111-126`

```sql
CREATE TABLE agent_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    version VARCHAR(20) NOT NULL,
    contract JSONB NOT NULL,              -- Snapshot of contract at this version
    change_summary TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Index**: `idx_versions_agent` on `agent_id`

**Usage**:
- Automatic snapshot before contract updates
- Full audit trail
- Supports rollback scenarios
- Change summaries for tracking modifications

### 2.3 Filesystem Storage (REMOVED)

**Previous Location**: `backend/prompts/{agent_id}/`
**Status**: ✅ **REMOVED** (as of 2025-11-06)
**Reference**: `docs/CONTRACT_CLEANUP_AND_VOICE_FIX_PLAN.md`

**What Was Removed**:
- `backend/services/contract_validator.py` (335 lines deleted)
- `_save_contract_file()` method from `agent_service.py`
- All filesystem read/write operations
- `backend/prompts/` directory structure
- Filesystem sync validation logic

**Benefits**:
- ✅ Simplified architecture (335 lines of redundant code removed)
- ✅ Single source of truth (database only)
- ✅ Improved multi-tenant security
- ✅ Cloud-native design
- ✅ No sync complexity

**Migration**: Seamless - no code was reading from filesystem

---

## 3. Service Layer

### 3.1 AgentService

**Location**: `backend/services/agent_service.py:76-660`

**Key Methods**:

#### `create_agent()` (`agent_service.py:81-162`)
Complete agent initialization:
1. Validate contract (including voice requirements)
2. Create database record
3. Initialize memory namespace (Mem0)
4. Create default thread
5. Return agent object

#### `get_agent()` (`agent_service.py:163-221`)
Retrieve agent with tenant validation:
- Loads from database (ONLY source)
- Returns complete contract + metadata
- Tenant isolation enforced

#### `update_agent()` (`agent_service.py:277-338`)
Update contract with versioning:
1. Create version snapshot in `agent_versions` table
2. Apply updates to contract
3. Update database
4. Return updated agent

#### `delete_agent()` (`agent_service.py:357-378`)
Soft delete (archive):
- Sets status to `archived`
- Preserves all historical data
- Agent hidden from default listings

#### `process_interaction()` (`agent_service.py:380-515`)
Complete interaction flow:
1. Load agent contract
2. Get/create thread
3. Initialize memory manager (LRU cached)
4. Get memory context
5. Invoke GuideAgent
6. Store messages
7. Update metrics

**Memory Management**:
- LRU cache for memory managers (`LRUMemoryCache`, max 100)
- Prevents memory leaks
- Automatic eviction of least recently used

### 3.2 Contract Validator

**Previous Location**: `backend/services/contract_validator.py`
**Status**: ✅ **REMOVED** (335 lines deleted as of 2025-11-06)

**Previous Purpose**: Validated database ↔ filesystem sync (no longer needed)
- `validate_agent_contract()`: Single agent validation
- `validate_all_agents()`: Bulk validation
- `get_contract_hash()`: SHA256 hash for quick comparison
- `_find_differences()`: Recursive diff algorithm
- `_write_filesystem_contract()`: Auto-repair functionality

**Status**: ⚠️ Only used when `validate_sync=True` (defaults to False)

---

## 4. API Endpoints

### 4.1 Agent CRUD Endpoints

**Location**: `backend/routers/agents.py`

#### `POST /agents` (`agents.py:60-151`)
Create new agent from JSON contract
- Validates contract structure
- Applies defaults (voice, avatar)
- Creates via `AgentService.create_agent()`
- Returns complete agent object

#### `GET /agents` (`agents.py:154-203`)
List agents with filtering:
- Query params: `status`, `agent_type`, `limit`, `offset`
- Tenant-scoped automatically
- Returns paginated list

#### `GET /agents/{agent_id}` (`agents.py:206-242`)
Get agent details:
- Returns complete contract
- Includes interaction metrics
- Tenant validation enforced

#### `PATCH /agents/{agent_id}` (`agents.py:245-310`)
Update agent contract:
- Supports partial updates
- Creates version snapshot automatically
- Updates identity, traits, configuration, voice, tags, status

#### `DELETE /agents/{agent_id}` (`agents.py:313-348`)
Archive agent (soft delete):
- Sets status to `archived`
- Preserves all data

### 4.2 Interaction Endpoints

#### `POST /agents/{agent_id}/chat` (`agents.py:355-415`)
Chat with agent:
- Standard interaction endpoint
- Loads contract, retrieves memory, processes via GuideAgent
- Stores messages and updates metrics

### 4.3 History & Metrics

#### `GET /agents/{agent_id}/threads` (`agents.py:422-477`)
Get conversation threads for agent

#### `GET /agents/{agent_id}/versions` (`agents.py:480-541`)
Get contract version history:
- Returns all versions with snapshots
- Includes change summaries
- Ordered by creation date (newest first)

### 4.4 Baseline Flow Endpoint

#### `POST /agents/from_intake_contract` (`agents.py:548-738`)
Create guide agent from intake contract:
- Processes intake data
- Calculates traits from user preferences
- Creates AgentContract
- Auto-creates session
- Generates manifestation protocol

---

## 5. Contract Lifecycle

### 5.1 Creation Flow

```
User Request → AgentCreateRequest
    ↓
Validate Contract Structure
    ↓
Build AgentContract (apply defaults)
    ↓
AgentService.create_agent()
    ├─→ Insert into agents table
    ├─→ Initialize memory namespace
    ├─→ Save filesystem (DEPRECATED)
    └─→ Create default thread
    ↓
Return Agent Object
```

### 5.2 Update Flow

```
User Request → AgentUpdateRequest
    ↓
AgentService.update_agent()
    ├─→ Load current agent
    ├─→ Create version snapshot → agent_versions table
    ├─→ Apply updates to contract
    ├─→ Update agents table
    └─→ Update filesystem (DEPRECATED)
    ↓
Return Updated Agent
```

### 5.3 Runtime Usage Flow

```
User Interaction → POST /agents/{id}/chat
    ↓
AgentService.process_interaction()
    ├─→ Load contract from database
    ├─→ Get/create thread
    ├─→ Get memory manager (LRU cached)
    ├─→ Retrieve memory context
    ├─→ Invoke GuideAgent with contract
    ├─→ Store messages
    └─→ Update metrics
    ↓
Return Response
```

---

## 6. Contract Validation

### 6.1 Pydantic Validation

**Location**: `backend/models/agent.py`

- Automatic validation via Pydantic models
- Type checking
- Field constraints (e.g., trait values 0-100)
- Required field validation
- Custom validators:
  - `validate_type()`: Ensures valid AgentType
  - `validate_voice_for_voice_agents()`: Voice agents must have voice config

### 6.2 Database Constraints

- Foreign key constraints (tenant_id, owner_id)
- NOT NULL constraints
- Indexes for performance

### 6.3 Sync Validation (DEPRECATED)

**Location**: `backend/services/contract_validator.py`

- Database ↔ filesystem comparison
- Recursive diff algorithm
- Auto-repair capability
- Hash-based quick comparison

**Status**: Not used in production (validate_sync defaults to False)

---

## 7. System Prompt Generation

**Location**: `backend/services/agent_service.py:567-607`

The system generates a system prompt from the contract:

```python
def _generate_system_prompt(contract: AgentContract) -> str:
    # Uses TraitModulator to generate behavioral instructions
    # Includes:
    # - Agent name and description
    # - Character role and mission
    # - Personality traits (quantified)
    # - Behavioral directives from traits
    # - Configuration details
```

**Output**: Saved to `backend/prompts/{agent_id}/system_prompt.txt` (DEPRECATED)

**Note**: System prompt is generated on-demand from contract, not stored separately in database.

---

## 8. Multi-Tenancy

### 8.1 Tenant Isolation

- **Database**: `tenant_id` foreign key constraint
- **API**: Automatic tenant scoping via `get_tenant_id()` dependency
- **Service**: All queries filtered by `tenant_id`
- **Security**: Tenant validation on all operations

### 8.2 Filesystem Issues (DEPRECATED)

- ⚠️ Filesystem storage lacks tenant isolation
- All contracts in single directory structure
- Security concern for multi-tenant deployments
- **Recommendation**: Remove filesystem storage

---

## 9. Known Issues & Recommendations

### 9.1 Filesystem Storage (DEPRECATED)

**Issue**: Redundant filesystem storage adds complexity without benefit

**Impact**:
- 335 lines of validation code
- Sync complexity
- Multi-tenant security concerns
- No code reads from filesystem

**Recommendation**: Remove in next sprint
- Remove `_save_contract_file()` from `agent_service.py`
- Remove `contract_validator.py` (335 lines)
- Remove filesystem validation from `get_agent()`
- Update tests

**Reference**: `docs/FILESYSTEM_STORAGE_DECISION.md`

### 9.2 Version Management

**Current**: Version snapshots created automatically on update

**Potential Improvements**:
- API endpoint to restore from version
- Version comparison/diff endpoint
- Semantic versioning enforcement
- Change tracking per field

### 9.3 Contract Schema Evolution

**Current**: Pydantic models handle validation

**Considerations**:
- Backward compatibility for contract updates
- Migration path for schema changes
- Versioned contract schemas

---

## 10. Architecture Compliance

### 10.1 JSON Contract-First Design

✅ **Fully Implemented**:
- Agent behavior 100% defined by JSON
- No hardcoded personality
- Runtime trait adjustment
- Single source of truth

### 10.2 Database-Backed Management

✅ **Fully Implemented**:
- Agents are database entities
- Full CRUD lifecycle
- Audit trail (version history)
- Multi-tenancy by design

### 10.3 Separation of Concerns

✅ **Well Structured**:
- JSON Contract (What) → `AgentContract` model
- Business Logic (How) → `AgentService`
- Execution (When/Where) → API endpoints + GuideAgent

---

## 11. File Reference Summary

### Core Models
- `backend/models/agent.py`: AgentContract and component models
- `backend/models/schemas.py`: API request/response models

### Services
- `backend/services/agent_service.py`: Complete lifecycle management
- `backend/services/contract_validator.py`: Sync validation (DEPRECATED)

### API
- `backend/routers/agents.py`: CRUD and interaction endpoints
- `backend/routers/contracts.py`: Therapy session contracts (separate system)

### Database
- `backend/database.py`: Schema definitions
- `supabase/migrations/20250101000000_initial_schema.sql`: Migration scripts

### Documentation
- `docs/architecture/knowledgebase/AGENT_CREATION_STANDARD.md`: Architecture standard
- `docs/FILESYSTEM_STORAGE_DECISION.md`: Deprecation decision

---

## 12. Summary

### What's Working Well

✅ **Complete Contract Model**: Comprehensive Pydantic models with validation  
✅ **Database Storage**: Robust PostgreSQL JSONB storage with versioning  
✅ **Service Layer**: Well-structured lifecycle management  
✅ **API Endpoints**: Full CRUD + interaction endpoints  
✅ **Multi-Tenancy**: Proper tenant isolation  
✅ **Version History**: Automatic snapshots on updates  
✅ **Memory Integration**: LRU-cached memory managers  

### What Needs Attention

⚠️ **Filesystem Storage**: Deprecated, should be removed  
⚠️ **Version Management**: Could add restore/diff endpoints  
⚠️ **Schema Evolution**: Consider migration strategy  

### Overall Assessment

**Status**: ✅ **Production Ready**

The contract management system is well-architected and follows the JSON Contract-First design principle. The database-backed approach provides a solid foundation for multi-tenant agent management. The only significant cleanup needed is removing the deprecated filesystem storage layer.

---

**Report Generated**: 2025-01-15  
**Next Review**: After filesystem storage removal

