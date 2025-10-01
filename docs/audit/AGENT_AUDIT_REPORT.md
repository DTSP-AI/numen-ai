# Agent Pipeline Audit Report
**Numen AI - Manifestation/Hypnotherapy Voice Agent**

**Date**: 2025-10-01
**Audited Against**: `AGENT_CREATION_STANDARD.md` - JSON Contract-First Architecture

---

## Executive Summary

The current Numen AI codebase implements a **voice-enabled hypnotherapy platform** with LangGraph agents (IntakeAgent, TherapyAgent) but **significantly deviates** from the AGENT_CREATION_STANDARD in critical areas:

- ❌ **No JSON Contract-First Design** - Agents are hardcoded, not database-backed with JSON contracts
- ❌ **No Agent Lifecycle Management** - No CRUD operations for agents as database entities
- ❌ **No Thread Management** - Missing structured thread/message persistence for conversations
- ❌ **Incomplete Memory Architecture** - Basic Mem0 integration without unified memory manager or namespace isolation
- ❌ **No Multi-Tenancy** - Missing tenant_id isolation across all entities
- ⚠️ **Partial Agent State Management** - LangGraph state exists but doesn't follow contract-driven pattern

### Compliance Score: **18/100**

---

## Detailed Gap Analysis

### 1. JSON Contract Specification ❌

**Standard Requirement**:
- Every agent defined by complete JSON contract with identity, traits, configuration, capabilities, metadata
- Stored in database + filesystem (`backend/prompts/{agent_id}/agent_specific_prompt.json`)
- Pydantic models for validation (`AgentContract`, `AgentTraits`, `AgentIdentity`, etc.)
- Runtime trait adjustment without code changes

**Current Implementation**:
```python
# backend/agents/intake_agent.py:32-38
class IntakeAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
```

**Deficits**:
- ✗ No JSON contract files
- ✗ Agents instantiated with hardcoded personality/behavior in code
- ✗ No trait system (creativity, empathy, assertiveness, etc.)
- ✗ No identity configuration (mission, interaction_style, character_role)
- ✗ No configuration flexibility (llm_provider, temperature, max_tokens defined per-instance)
- ✗ No filesystem storage for prompts

**Impact**: **CRITICAL**
- Cannot create multiple agent variations without code changes
- No runtime personality adjustment
- No ability to version or audit agent behavior changes

---

### 2. Agent Lifecycle Management ❌

**Standard Requirement**:
```python
# Required API endpoints:
POST   /api/v1/agents              # Create agent
GET    /api/v1/agents              # List agents
GET    /api/v1/agents/{id}         # Get agent details
PATCH  /api/v1/agents/{id}         # Update agent contract
DELETE /api/v1/agents/{id}         # Archive agent

# Required process:
1. Validate JSON schema (Pydantic)
2. Create database record (agents table)
3. Initialize memory namespace
4. Save filesystem JSON
5. Create default thread
6. Return agent object
```

**Current Implementation**:
```python
# backend/routers/sessions.py:15-65
# Only has session creation, no agent CRUD
@router.post("/", response_model=SessionResponse)
async def create_session(session: SessionCreate):
    # Creates session + LiveKit room only
    # No agent creation/management
```

**Deficits**:
- ✗ No agent CRUD endpoints
- ✗ No agent database table/schema
- ✗ No agent service layer (`AgentService` class missing)
- ✗ No agent creation flow with validation → DB → memory → filesystem
- ✗ No agent versioning (`agent_versions` table)
- ✗ No agent metrics tracking (interaction_count, last_interaction_at)

**Impact**: **CRITICAL**
- Cannot dynamically create/manage agents
- No audit trail for agent modifications
- No ability to scale to multiple agents per tenant

---

### 3. Database Schema Design ❌

**Standard Requirement**:
```sql
-- Required tables:
- tenants (multi-tenancy)
- users (per-tenant users)
- agents (JSON contract storage)
- agent_versions (contract history)
- threads (conversation threads)
- thread_messages (message history)
```

**Current Implementation**:
```python
# backend/database.py:46-99
# Only has:
CREATE TABLE sessions (...)
CREATE TABLE contracts (...)
CREATE TABLE transcripts (...)
CREATE TABLE manifestation_protocols (...)
```

**Deficits**:
- ✗ No `agents` table with JSON contract column
- ✗ No `agent_versions` table for versioning
- ✗ No `tenants` table (multi-tenancy missing)
- ✗ No `threads` table (structured conversation management)
- ✗ No `thread_messages` table (message persistence)
- ✗ No `users` table with tenant_id FK
- ✗ Sessions table lacks agent_id FK

**Current Schema Issues**:
```sql
-- sessions table missing:
agent_id UUID,  -- which agent is handling this session?
tenant_id UUID  -- multi-tenancy isolation

-- contracts table issues:
-- Should be part of agent JSON contract, not standalone
-- Missing tenant_id, agent_id relationship
```

**Impact**: **CRITICAL**
- Cannot implement JSON contract-first architecture
- No multi-tenancy support
- No conversation thread persistence
- No agent-session linkage

---

### 4. Memory System Architecture ⚠️

**Standard Requirement**:
```python
# UnifiedMemoryManager with:
class MemoryNamespace:
    @staticmethod
    def agent_namespace(tenant_id: str, agent_id: str) -> str:
        return f"{tenant_id}:{agent_id}"

    @staticmethod
    def thread_namespace(tenant_id: str, agent_id: str, thread_id: str) -> str:
        return f"{tenant_id}:{agent_id}:thread:{thread_id}"

    @staticmethod
    def user_namespace(tenant_id: str, agent_id: str, user_id: str) -> str:
        return f"{tenant_id}:{agent_id}:user:{user_id}"
```

**Current Implementation**:
```python
# backend/services/memory.py:11-169
class MemoryService:
    async def store_user_preferences(self, user_id: str, preferences: Dict):
        self.memory.add(
            messages=[f"User preferences: {preferences}"],
            user_id=user_id,
            metadata={"type": "preferences", "namespace": "user"}
        )
```

**Deficits**:
- ⚠️ Basic Mem0 integration exists but incomplete
- ✗ No `UnifiedMemoryManager` class
- ✗ No namespace isolation pattern (`{tenant_id}:{agent_id}:{context}`)
- ✗ No memory settings from agent contract
- ✗ No hybrid memory retrieval (recency + semantic + reinforcement)
- ✗ Memory not initialized during agent creation
- ✗ No per-thread memory context

**Current Memory Issues**:
```python
# memory.py:54 - No tenant_id in namespace
self.memory.add(
    messages=[...],
    user_id=user_id,  # ❌ Should be namespace: f"{tenant_id}:{agent_id}"
    metadata={"namespace": "user"}  # ❌ Metadata field, not actual namespace
)
```

**Impact**: **HIGH**
- Memory not isolated per agent/tenant
- Risk of cross-tenant data leakage
- Cannot implement contract-driven memory settings
- No semantic memory retrieval

---

### 5. Thread Management ❌

**Standard Requirement**:
```python
# ThreadManager with:
- create_thread(agent_id, user_id, tenant_id) -> Thread
- get_or_create_thread(...) -> Thread
- add_message(thread_id, role, content) -> ThreadMessage
- get_thread_history(thread_id, limit) -> List[ThreadMessage]

# Tables:
threads (id, agent_id, user_id, tenant_id, title, message_count, ...)
thread_messages (id, thread_id, role, content, metadata, ...)
```

**Current Implementation**:
```python
# backend/database.py:69-77
# Only has transcripts table (session-level, not thread-level)
CREATE TABLE transcripts (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    speaker TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
)
```

**Deficits**:
- ✗ No `threads` table with agent_id, user_id, tenant_id
- ✗ No `thread_messages` table for structured message history
- ✗ No `ThreadManager` service class
- ✗ Current `transcripts` table is session-scoped, not thread-scoped
- ✗ No thread lifecycle management (create, archive, delete)
- ✗ No message_count tracking per thread
- ✗ No context_summary for thread state

**Impact**: **HIGH**
- Cannot maintain conversation context across sessions
- No way to resume conversations with same agent
- Transcript storage is flat, not threaded
- Missing conversation continuity

---

### 6. Agent-User Interaction Pattern ⚠️

**Standard Requirement**:
```python
async def process_agent_interaction(
    agent_id: str,
    user_id: str,
    tenant_id: str,
    user_input: str,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    # 1. Get/create thread
    # 2. Load agent contract from DB
    # 3. Initialize memory manager with agent contract
    # 4. Get memory context
    # 5. Process through LangGraph with contract-driven state
    # 6. Store interaction in thread_messages
    # 7. Update agent metrics
    # 8. Return response
```

**Current Implementation**:
```python
# backend/agents/intake_agent.py:158-188
async def process_message(
    self,
    session_id: str,
    user_id: str,
    message: str,
    current_state: Optional[IntakeAgentState] = None
):
    # Processes message through LangGraph
    # But no thread management, no agent contract loading
    result = await self.graph.ainvoke(current_state)
    return result
```

**Deficits**:
- ⚠️ LangGraph integration exists but doesn't follow standard pattern
- ✗ No agent contract loading from database
- ✗ No thread management in interaction flow
- ✗ No memory context retrieval before processing
- ✗ No agent metrics updates (interaction_count, last_interaction_at)
- ✗ Direct instantiation (`IntakeAgent()`) instead of service layer
- ✗ No unified interaction endpoint (`/agents/{agent_id}/chat`)

**Current Flow**:
```
User Input → IntakeAgent.process_message() → LangGraph → Response
```

**Should Be**:
```
User Input → AgentService.process_interaction() →
  Load Contract → Get Memory Context → LangGraph with Contract State →
  Store in Thread → Update Metrics → Response
```

**Impact**: **HIGH**
- Agents not contract-driven at runtime
- No conversation persistence
- No memory-aware interactions
- Cannot track agent usage metrics

---

### 7. Multi-Tenancy ❌

**Standard Requirement**:
- Every entity has `tenant_id` FK
- All queries filtered by tenant_id
- Namespace isolation: `{tenant_id}:{agent_id}:{context}`
- `tenants` table with organizations

**Current Implementation**:
```python
# backend/database.py:46-99
# No tenant_id in any table
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,  # ❌ No tenant_id
    status TEXT NOT NULL,
    ...
)
```

**Deficits**:
- ✗ No `tenants` table
- ✗ No `tenant_id` column in any table
- ✗ No tenant isolation in queries
- ✗ No tenant context in API endpoints
- ✗ No `get_tenant_id()` dependency
- ✗ Memory namespace doesn't include tenant_id

**Impact**: **CRITICAL** (for production/SaaS)
- Cannot deploy as multi-tenant SaaS
- Data isolation impossible
- Security risk if deployed to multiple organizations

---

### 8. Agent Pydantic Models ❌

**Standard Requirement**:
```python
# models/agent.py
class AgentTraits(BaseModel):
    creativity: int = Field(ge=0, le=100, default=50)
    empathy: int = Field(ge=0, le=100, default=50)
    assertiveness: int = Field(ge=0, le=100, default=50)
    humor: int = Field(ge=0, le=100, default=30)
    # ... 9 total traits

class AgentIdentity(BaseModel):
    short_description: str
    full_description: Optional[str]
    character_role: Optional[str]
    mission: Optional[str]
    interaction_style: Optional[str]

class AgentConfiguration(BaseModel):
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    max_tokens: int = Field(ge=50, le=4000, default=500)
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    memory_enabled: bool = True
    voice_enabled: bool = False
    tools_enabled: bool = False

class AgentContract(BaseModel):
    id: str
    name: str
    type: str  # conversational|voice|workflow|autonomous
    version: str
    identity: AgentIdentity
    traits: AgentTraits
    configuration: AgentConfiguration
    metadata: Dict[str, Any]
```

**Current Implementation**:
```python
# backend/models/schemas.py:1-95
# Only has session/contract models:
class SessionCreate(BaseModel): ...
class ContractCreate(BaseModel): ...  # ❌ This is NOT agent contract
class IntakeState(BaseModel): ...     # LangGraph state, not agent contract
class TherapyState(BaseModel): ...
```

**Deficits**:
- ✗ No `AgentContract` model
- ✗ No `AgentTraits` model
- ✗ No `AgentIdentity` model
- ✗ No `AgentConfiguration` model
- ✗ `ContractCreate` is user session contract (goals, tone), not agent contract
- ✗ No Pydantic validation for agent JSON contracts

**Impact**: **CRITICAL**
- Cannot implement JSON contract-first design
- No validation layer for agent definitions
- Confusion between "user contract" and "agent contract"

---

### 9. Agent Graph Building ⚠️

**Standard Requirement**:
```python
# Agent graph should be built FROM contract at runtime
def build_agent_graph(memory_manager: UnifiedMemoryManager) -> StateGraph:
    """Build graph from agent contract, not hardcoded"""

    graph_state = {
        "agent_contract": contract.model_dump(),  # Full contract in state
        "traits": contract.traits.model_dump(),
        "memory_context": memory_context,
        "configuration": contract.configuration.model_dump()
    }

    # Nodes use traits to adjust behavior dynamically
    return graph.compile()
```

**Current Implementation**:
```python
# backend/agents/intake_agent.py:40-66
def _build_graph(self) -> StateGraph:
    workflow = StateGraph(IntakeAgentState)

    # ❌ Hardcoded nodes with fixed behavior
    workflow.add_node("greeting", self._greeting_node)
    workflow.add_node("collect_goals", self._collect_goals_node)
    workflow.add_edge("greeting", "collect_goals")  # ❌ Fixed edges

    return workflow.compile()

# backend/agents/intake_agent.py:68-83
def _greeting_node(self, state: IntakeAgentState) -> IntakeAgentState:
    # ❌ Hardcoded greeting message
    greeting_message = (
        "Welcome to your personalized hypnotherapy session. "
        "I'm here to understand your goals..."
    )
```

**Deficits**:
- ⚠️ LangGraph structure exists but is hardcoded
- ✗ No contract-driven node behavior
- ✗ No trait-based personality adjustment
- ✗ Fixed greeting/prompts instead of using identity.interaction_style
- ✗ Graph built at agent __init__, not per-interaction with contract
- ✗ No memory_manager passed to graph

**Impact**: **HIGH**
- Cannot adjust agent personality without code changes
- Every agent of same type behaves identically
- No runtime configuration

---

### 10. Testing & Validation ❌

**Standard Requirement**:
```python
# tests/test_agent_lifecycle.py
@pytest.mark.asyncio
async def test_agent_creation(db_session, sample_contract):
    service = AgentService(db_session)
    agent = await service.create_agent(
        contract=sample_contract,
        tenant_id=str(uuid.uuid4()),
        owner_id=str(uuid.uuid4())
    )
    assert agent.contract['name'] == sample_contract.name

async def test_agent_interaction(...)
async def test_thread_persistence(...)
```

**Current Implementation**:
```bash
# No test files found for agent lifecycle
$ find backend/tests -name "*agent*"
# (empty)
```

**Deficits**:
- ✗ No agent lifecycle tests (create, read, update, delete)
- ✗ No thread persistence tests
- ✗ No memory isolation tests
- ✗ No contract validation tests
- ✗ No multi-tenant tests

**Impact**: **MEDIUM**
- No confidence in standard compliance
- Cannot verify contract-driven behavior

---

## Summary of Critical Gaps

| **Standard Component** | **Status** | **Priority** | **LOE** |
|---|---|---|---|
| 1. JSON Contract Models (Pydantic) | ❌ Missing | P0 - CRITICAL | 4h |
| 2. Agents Database Table + Schema | ❌ Missing | P0 - CRITICAL | 4h |
| 3. Agent CRUD Endpoints + Service | ❌ Missing | P0 - CRITICAL | 8h |
| 4. Threads + Messages Tables | ❌ Missing | P0 - CRITICAL | 4h |
| 5. ThreadManager Service | ❌ Missing | P0 - CRITICAL | 6h |
| 6. UnifiedMemoryManager | ⚠️ Partial | P1 - HIGH | 8h |
| 7. Multi-Tenancy (tenant_id everywhere) | ❌ Missing | P1 - HIGH | 8h |
| 8. Contract-Driven Graph Building | ⚠️ Partial | P1 - HIGH | 8h |
| 9. Agent-User Interaction Standard Flow | ⚠️ Partial | P1 - HIGH | 6h |
| 10. Filesystem JSON Storage (prompts/) | ❌ Missing | P2 - MEDIUM | 2h |
| 11. Agent Versioning (agent_versions) | ❌ Missing | P2 - MEDIUM | 4h |
| 12. Testing Suite (pytest) | ❌ Missing | P2 - MEDIUM | 8h |

**Total LOE**: ~70 hours (~2 weeks for 1 developer)

---

## Architectural Comparison

### Current Architecture (Simplified)

```
User → Frontend (Next.js) → Backend API (FastAPI)
                               ↓
                          [IntakeAgent] → Hardcoded LangGraph
                               ↓
                          [TherapyAgent] → Hardcoded LangGraph
                               ↓
                          Session + Contract (DB)
                               ↓
                          Basic Mem0 (no namespaces)
```

**Issues**:
- Agents instantiated directly in code, not loaded from DB
- No agent identity/trait system
- Single-tenant only
- No conversation threads
- Memory not agent-aware

---

### Target Architecture (AGENT_CREATION_STANDARD)

```
User → Frontend → Backend API
                     ↓
               [AgentService]
                     ↓
      ┌──────────────┼──────────────┐
      ↓              ↓               ↓
  [Agents DB]  [Threads DB]  [UnifiedMemoryManager]
   (JSON          (Messages)      (Qdrant + Mem0)
   Contract)                        ↓
      ↓                       Namespace Isolation:
   Load Agent              tenant:agent:thread
   Contract at              tenant:agent:user
   Runtime                  tenant:agent
      ↓
  Build LangGraph
  from Contract
  (Traits → Behavior)
      ↓
  Process Interaction
  with Memory Context
```

**Benefits**:
- ✅ Multiple agents per tenant
- ✅ Runtime personality configuration
- ✅ Multi-tenant isolation
- ✅ Conversation continuity (threads)
- ✅ Memory-aware agents
- ✅ Full audit trail
- ✅ Scalable to thousands of agents

---

## Conclusion

The current Numen AI implementation has a **solid foundation** in:
- ✅ LangGraph agent workflows
- ✅ Voice pipeline (LiveKit, Deepgram, ElevenLabs)
- ✅ Basic database schema (sessions, contracts, transcripts)
- ✅ Mem0 integration (basic)

However, it **does not comply** with the AGENT_CREATION_STANDARD in the following critical areas:
- ❌ **No JSON contract-first architecture**
- ❌ **No agent lifecycle management**
- ❌ **No thread management**
- ❌ **No multi-tenancy**
- ⚠️ **Incomplete memory architecture**

**Compliance Score**: **18/100**

To achieve 90%+ compliance, the roadmap in the next document (`AGENT_GAP_REMEDIATION_ROADMAP.md`) must be executed.

---

**Next Steps**: See `AGENT_GAP_REMEDIATION_ROADMAP.md` for phased implementation plan.
