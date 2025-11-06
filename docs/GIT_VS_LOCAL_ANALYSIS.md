# Git vs Local Analysis Report
**Date:** 2025-11-03
**Repository:** AffirmationApplication (Numen AI)
**Last Stable Commit:** b0197b7 - "Fix: Avatar display in chat interface"

## Executive Summary

**Critical Finding:** The local working directory has **massive deletions** (34,257 lines deleted vs 919 lines added across 135 files). This represents a destructive refactoring that removed **working production code** including:
- All standalone agent implementations
- Complete test suite (16 test files)
- Memory manager implementation
- Extensive documentation
- Cognitive assessment infrastructure

**Status:** The git repository contains a **stable, working implementation** through the chat interaction. Local changes have broken this functionality.

---

## 1. What's in Git (Last Stable State)

### A. Commit History Analysis
Recent commits show steady progress with working features:

```
b0197b7 - Fix: Avatar display in chat interface (CURRENT HEAD)
d28ca6b - Fix: Remove emojis and enlarge Guide avatar
55c97d1 - Add three-dot menu + cognitive assessment infrastructure
be5b25e - Fix: Guide creation endpoint - E2E audit and critical bug fixes
9cd4025 - Fix Pydantic validation: 100-char limit
355be34 - Fix 404 error on GET /api/agents/{agent_id}
726c06d - Fix: AgentBuilder short_description validation
b706c59 - Production-Ready Avatar Generation + Complete System Documentation
67c1ebf - Active Agent Chat Page: LiveKit Voice + Message Thread ✅
```

### B. Working Backend Architecture (Git Version)

#### Agent System
**7 Standalone Agents** (all deleted locally):
- `backend/agents/affirmation_agent.py` (541 lines)
- `backend/agents/intake_agent.py` (252 lines)
- `backend/agents/intake_agent_cognitive.py` (615 lines)
- `backend/agents/intake_agent_v2.py` (630 lines)
- `backend/agents/langgraph_agent.py` (287 lines)
- `backend/agents/manifestation_protocol_agent.py` (536 lines)
- `backend/agents/therapy_agent.py` (224 lines)

**Architecture:** Each agent was a self-contained LangGraph workflow with:
- Contract-based initialization
- Memory management via MemoryManager
- LangChain OpenAI integration
- Database persistence
- State management

#### Memory System
**Working Implementation:**
- `backend/services/memory_manager.py` (860 lines) - **DELETED**
- Integrated with Mem0 AI
- Vector-based semantic memory
- Conversation history tracking
- Context retrieval with confidence scoring

#### Services Layer
**Agent Service** (`backend/services/agent_service.py`):
- Complete lifecycle management
- Process interaction with real LangGraph
- Memory initialization
- Contract-to-filesystem persistence

#### API Routers
**13 Production Routers:**
```
agents.py        - CRUD + chat endpoint ✅ Working
chat.py          - Session-based messaging ✅ Working
intake.py        - Discovery + contract generation
protocols.py     - Manifestation protocol generation
therapy.py       - Therapy session scheduling
affirmations.py  - Affirmation CRUD
sessions.py      - Session management
contracts.py     - Contract versioning
dashboard.py     - Analytics
voices.py        - ElevenLabs voice management
avatar.py        - DALL-E avatar generation
livekit.py       - Real-time voice
```

#### Database Schema
**Core Tables (Working):**
- `agents` - Agent contracts with full JSON
- `threads` - Conversation threads
- `thread_messages` - Message storage
- `sessions` - User sessions
- `agent_versions` - Contract versioning
- `affirmations` - Generated affirmations

**Cognitive Tables (In Git, Deleted Locally):**
- `cognitive_assessments`
- `cognitive_triggers`
- `belief_reflections`
- Migration file: `004_cognitive_assessment_tables.sql` **DELETED**

### C. Working Frontend (Git Version)

**React/Next.js Pages:**
- `/chat/[agentId]` - **Working chat interface with avatar display** ✅
- `/dashboard` - Agent listing
- `/creation` - AgentBuilder form
- `/voice-lab` - Voice preview

**Components:**
- `ChatInterface.tsx` - **Properly loads agent avatar, handles messages** ✅
- `MessageBubble.tsx` - **Renders user/agent messages with 64px avatars** ✅
- `AgentCard.tsx` - Agent preview cards
- `AgentBuilder.tsx` - Multi-step agent creation

### D. Complete Test Suite (Git Version)

**16 Test Files** covering critical paths (ALL DELETED LOCALLY):
```
test_agent_lifecycle.py (459 lines)
test_baseline_flow.py (130 lines)
test_cognitive_intake.py (441 lines)
test_mem0_integration.py (125 lines)
test_memory_manager.py (90 lines)
test_numen_pipeline.py (491 lines)
test_voice_creation_e2e.py (302 lines)
test_protocol_generation.py (116 lines)
test_deepak_chopra_agent.py (107 lines)
test_marcus_aurelius_agent.py (107 lines)
+ 6 more test files
```

**Test Coverage:** E2E flows, memory, agents, intake, protocols, voice synthesis

### E. Documentation (Git Version)

**Architecture Docs** (Most deleted locally):
```
ARCHITECTURE.md (734 lines) - DELETED
AGENT_CREATION_STANDARD.md (1,623 lines) - DELETED
AVATAR_GENERATION_GUIDE.md (1,286 lines) - DELETED
MEM0_MIGRATION_GUIDE.md (462 lines) - DELETED
```

**Audit Reports** (All deleted):
- 11 comprehensive audit reports totaling ~8,000 lines

---

## 2. What Was Deleted (Local Changes)

### Critical Deletions

#### A. Complete Agent Implementations (3,085 lines)
All 7 standalone agents with working LangGraph workflows:
- Each agent had state models, graph definitions, LLM integration
- Memory context retrieval
- Database persistence
- Audio generation (ElevenLabs)

**Impact:** **BREAKING** - No functioning agent logic remains

#### B. Memory Manager (860 lines)
`backend/services/memory_manager.py`:
- Mem0 integration
- Semantic memory search
- Conversation history
- Context window management
- Confidence scoring

**Impact:** **CRITICAL** - Chat cannot retrieve context or history

#### C. Complete Test Suite (3,584 lines)
16 test files covering:
- Agent lifecycle
- Memory operations
- Protocol generation
- Voice synthesis
- E2E workflows

**Impact:** **SEVERE** - No way to validate functionality

#### D. Cognitive Assessment System
- Migration SQL file (256 lines)
- Database tables for triggers and assessments
- Integration with agents

**Impact:** Loss of advanced cognitive features

#### E. Documentation (17,356 lines)
- Architecture guides
- Standards documents
- Audit reports
- Implementation summaries

**Impact:** Loss of tribal knowledge and standards

#### F. Avatar Storage
- 17 avatar images for default tenant
- Avatar migration scripts

**Impact:** Broken avatar display for seeded agents

#### G. Contract Storage
- 11 agent contract directories with JSON + system prompts
- Historical agent configurations

**Impact:** Cannot load previously created agents

### Total Deletion Stats
```
135 files changed
919 lines added
34,257 lines DELETED ⚠️
```

---

## 3. What Was Added (Local Untracked Files)

### A. New Agent Architecture

**GuideAgent System:**
```
backend/agents/guide_agent/
  ├── guide_agent.py (Orchestrator)
  ├── guide_sub_agents/
  │   ├── affirmation_agent.py
  │   ├── discovery_agent.py
  │   ├── manifestation_protocol_agent.py
  │   └── therapy_agent.py
```

**Architecture Change:**
- Old: Standalone agents with direct graph execution
- New: Orchestrator + sub-agents pattern

**Status:** Partial implementation, missing integration

**IntakeAgent Restructure:**
```
backend/agents/intake_agent/
  ├── intake_agent.py
  └── __init__.py
```

### B. New Graph System
```
backend/graph/
  ├── graph.py (Unified workflow builder)
  └── __init__.py
```

**Purpose:** Single source of truth for LangGraph workflows
**Workflow:**
1. retrieve_context
2. build_prompt
3. invoke_llm
4. post_process
5. check_cognitive_triggers

**Integration Status:** Referenced by GuideAgent but not fully wired

### C. New Memory Manager
```
backend/memoryManager/
  ├── memory_manager.py
  └── __init__.py
```

**Changes from Git Version:**
- Path moved from `services/` to `memoryManager/`
- Import paths changed throughout codebase

**Risk:** Import mismatches may cause runtime errors

### D. New Documentation
```
docs/
  ├── ARCHITECTURE_COMPREHENSIVE.md
  ├── CLEAN_ARCHITECTURE.md
  ├── BREAKING_ISSUES_RESOLUTION.md
  ├── AssetCreationAndSchedulingDesign.md
  └── architecture/knowledgebase/ (5 new docs)
```

### E. New Routers
```
backend/routers/auth.py (New authentication system)
```

**Status:** Exists but commented out in `main.py`:
```python
# app.include_router(auth.router)  # Disabled - not part of baseline
```

### F. Helper Services
```
backend/services/
  ├── affirmation_helpers.py
  ├── agent_creation_helpers.py
  └── auth.py
```

### G. New Tests
```
backend/tests/
  ├── test_auth_service.py
  └── test_protected_endpoints.py
```

**Note:** Only 2 new tests vs 16 deleted tests

---

## 4. Modified Files - Breaking Changes

### A. `backend/services/agent_service.py`

**Git Version:**
- Import: `from services.memory_manager import MemoryManager`
- Simple memory manager dict: `self.memory_managers: Dict[str, MemoryManager]`
- Direct process_interaction with LangGraph

**Local Version:**
- Import: `from memoryManager.memory_manager import MemoryManager` ⚠️
- LRU cache: `self.memory_cache = LRUMemoryCache()` (new complexity)
- **Critical:** GuideAgent integration at line 486-505:
  ```python
  from agents.guide_agent.guide_agent import GuideAgent
  guide_agent = GuideAgent(contract=contract, memory=memory_manager)
  result = await guide_agent.graph.ainvoke(graph_state)
  ```

**Breaking Change:** GuideAgent must exist and have `.graph` attribute
**Risk:** If GuideAgent incomplete, chat will fail

### B. `backend/main.py`

**Changes:**
- Therapy router import disabled:
  ```python
  # therapy router disabled - TherapyAgent module not implemented
  ```
- Health check expanded with service status
- Auth router commented out

**Impact:** Reduced functionality but non-breaking

### C. `backend/requirements.txt`

**Removed:**
- `redis==5.0.8` (Replaced by PostgreSQL)
- `qdrant-client==1.10.0` (Replaced by Mem0)

**Added:**
- `python-jose[cryptography]` (Auth)
- `passlib[bcrypt]` (Auth)

**Risk:** Auth dependencies unused if auth disabled

### D. `backend/routers/agents.py`

**Major Endpoint Addition:**
`POST /agents/from_intake_contract` (lines 586-848)

**Purpose:** Baseline flow endpoint
**Process:**
1. Generate GuideContract from IntakeContract
2. Create agent
3. Auto-create session
4. Generate manifestation protocol
5. Store in memory

**Dependencies:**
- `ManifestationProtocolAgent`
- `MemoryManager` at new path
- Attribute calculator

**Risk:** Complex orchestration may fail if any component incomplete

### E. Frontend Changes

**Minimal Cosmetic Changes:**
- "Agent" → "Guide" terminology
- No breaking functional changes

---

## 5. Where Things Went Wrong

### A. Architectural Refactor Without Completion

**Problem:** Attempted to refactor from **7 standalone agents** to **1 orchestrator + 4 sub-agents**

**Status:**
- Old agents: **DELETED**
- New agents: **PARTIALLY IMPLEMENTED**
- Integration: **INCOMPLETE**

**Result:** Chat endpoint broken because GuideAgent incomplete

### B. Path Changes Breaking Imports

**Change:** `services/memory_manager.py` → `memoryManager/memory_manager.py`

**Broken References:**
- Any code expecting old path will fail
- Circular dependency risks
- Runtime import errors

### C. Deleted Test Coverage

**Problem:** Deleted **ALL 16 working tests** before new system validated

**Impact:**
- No validation of new architecture
- Cannot verify chat still works
- Regression risks undetected

### D. Documentation Gap

**Problem:** Deleted comprehensive architecture docs before new system documented

**Impact:**
- Loss of design rationale
- Missing API contracts
- Standard violations

### E. Memory Manager Complexity Increase

**Old:** Simple dict of memory managers
**New:** LRU cache with eviction logic

**Risk:** Added complexity without verified need
**Bug Potential:** Cache eviction during active conversations

---

## 6. Critical Issues Preventing Chat Functionality

### Issue 1: GuideAgent Integration Incomplete

**Location:** `backend/services/agent_service.py:486-505`

**Code:**
```python
from agents.guide_agent.guide_agent import GuideAgent
guide_agent = GuideAgent(contract=contract, memory=memory_manager)
result = await guide_agent.graph.ainvoke(graph_state)
```

**Requirements:**
1. GuideAgent must be fully implemented
2. Must have `.graph` attribute (LangGraph compiled graph)
3. Graph must handle state with keys:
   - agent_id, tenant_id, user_id, thread_id
   - input_text, guide_contract, memory_context
   - traits, configuration

**Verification Needed:**
- [ ] GuideAgent.__init__ accepts contract and memory
- [ ] GuideAgent.graph exists and is compiled
- [ ] graph.ainvoke returns dict with "response_text" or "response"

### Issue 2: Sub-Agent Dependencies

**GuideAgent imports:**
```python
from agents.guide_agent.guide_sub_agents.affirmation_agent import AffirmationAgent
from agents.guide_agent.guide_sub_agents.manifestation_protocol_agent import ManifestationProtocolAgent
```

**Status:** Files exist but functionality unknown

**Risk:** GuideAgent may fail if sub-agents incomplete

### Issue 3: Graph Module Integration

**GuideAgent line 28:**
```python
from graph.graph import build_agent_workflow, AgentState
```

**Requirement:** GuideAgent must build graph using this module

**Verification Needed:**
- [ ] GuideAgent constructs graph properly
- [ ] All node functions implemented
- [ ] State keys match expectations

### Issue 4: Memory Manager Import Path Mismatch

**AgentService imports:**
```python
from memoryManager.memory_manager import MemoryManager
```

**Risk:** If any code still uses old path, will fail at runtime

**Files to Check:**
- All routers
- All agents
- All services

---

## 7. What Still Works (From Git)

### Confirmed Working (Before Local Changes)

✅ **Backend API:**
- FastAPI server starts
- Database connection established
- Agent CRUD endpoints functional
- Chat endpoint operational

✅ **Chat Flow:**
1. Frontend → `POST /sessions/{session_id}/messages`
2. Backend → `agent_service.process_interaction()`
3. LangGraph agent invocation
4. Memory retrieval and storage
5. Response generation
6. Database persistence
7. Frontend display

✅ **Frontend:**
- Chat interface renders
- Agent avatar displays (64px, no emojis)
- Message bubbles styled correctly
- Real-time message streaming

✅ **Voice Integration:**
- ElevenLabs TTS synthesis
- Audio file generation
- Voice preview endpoint

✅ **Agent Creation:**
- AgentBuilder form
- Trait configuration
- Avatar generation (DALL-E)
- Contract validation

---

## 8. Recommendations

### Immediate Actions (Critical)

#### 1. Restore Git Version ⚠️ URGENT
```bash
# Stash local changes
git stash push -u -m "WIP: Refactor to GuideAgent orchestrator"

# Verify working state
git log -1 --oneline  # Should show b0197b7

# Test chat functionality
npm run dev  # Frontend
uvicorn main:app --reload  # Backend
```

**Rationale:** Restore known working state before proceeding

#### 2. Validate Current Chat Endpoint
Test the stable git version:
```bash
# Test chat endpoint
curl -X POST http://localhost:8000/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"user_id":"...", "agent_id":"...", "message":"Hello"}'
```

**Expected:** Agent responds with memory context

#### 3. Create Feature Branch
```bash
git checkout -b feature/guide-agent-orchestrator
git stash pop
```

**Rationale:** Isolate refactor work from stable main

### Short-Term (Recovery)

#### 4. Incremental Integration
Instead of deleting old agents:
1. Keep old agents working
2. Add new GuideAgent alongside
3. Create feature flag to switch between implementations
4. Validate GuideAgent matches old behavior
5. Only then delete old agents

#### 5. Restore Critical Files
```bash
# Restore memory manager
git checkout HEAD -- backend/services/memory_manager.py

# Restore test suite
git checkout HEAD -- backend/tests/

# Restore documentation
git checkout HEAD -- docs/architecture/
```

#### 6. Add Integration Tests
Before deleting anything, create tests that validate:
```python
# test_guide_agent_integration.py
async def test_guide_agent_process_interaction():
    """Verify GuideAgent produces same output as old agents"""
    # Compare old vs new implementation
    pass

async def test_chat_endpoint_e2e():
    """Test complete chat flow from API to database"""
    pass
```

### Medium-Term (Refactor Properly)

#### 7. Contract-Driven Development
Define API contracts before implementation:
```python
# contracts/guide_agent.py
class GuideAgentInterface(Protocol):
    graph: StateGraph

    def __init__(self, contract: AgentContract, memory: MemoryManager):
        ...

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ...
```

#### 8. Parallel Implementation
Run both systems side-by-side:
```python
# Feature flag approach
if settings.USE_GUIDE_ORCHESTRATOR:
    result = await guide_agent.process()
else:
    result = await legacy_agent.process()
```

#### 9. Metrics and Validation
Compare implementations:
- Response quality
- Memory retrieval accuracy
- Latency
- Error rates

#### 10. Documentation-First Approach
Before deleting docs:
1. Write new architecture docs
2. Update API documentation
3. Create migration guide
4. Record design decisions

### Long-Term (Architecture)

#### 11. Staged Migration Plan

**Phase 1: Validation** (1 week)
- Restore git version
- Add comprehensive tests
- Establish performance baseline

**Phase 2: Parallel Implementation** (2 weeks)
- Implement GuideAgent fully
- Run both systems in parallel
- Validate output equivalence

**Phase 3: Feature Flag Rollout** (1 week)
- Enable GuideAgent for new agents
- Keep old agents for existing users
- Monitor metrics

**Phase 4: Deprecation** (1 week)
- Migrate existing agents to new system
- Archive old implementation
- Update documentation

#### 12. Maintain Test Coverage
Rule: **Never delete tests until replacement tests exist**

Target coverage:
- Unit tests: 80%+
- Integration tests: Key workflows
- E2E tests: Critical user paths

#### 13. Import Path Standardization
Create import alias to prevent breaks:
```python
# backend/services/memory.py
# Central import point
try:
    from memoryManager.memory_manager import MemoryManager
except ImportError:
    from services.memory_manager import MemoryManager
```

---

## 9. Git vs Local Comparison Matrix

| Component | Git Status | Local Status | Functional | Risk Level |
|-----------|------------|--------------|------------|------------|
| **Agents** |
| AffirmationAgent | ✅ Working (541 lines) | ❌ Deleted | ❌ No | 🔴 CRITICAL |
| IntakeAgent | ✅ Working (252 lines) | ❌ Deleted | ❌ No | 🔴 CRITICAL |
| TherapyAgent | ✅ Working (224 lines) | ❌ Deleted | ❌ No | 🔴 CRITICAL |
| ManifestationAgent | ✅ Working (536 lines) | ❌ Deleted | ❌ No | 🔴 CRITICAL |
| GuideAgent | ❌ N/A | ⚠️ Partial | ❓ Unknown | 🟡 HIGH |
| **Memory** |
| MemoryManager | ✅ Working (860 lines) | ⚠️ Moved | ❓ Unknown | 🟡 HIGH |
| Memory Context | ✅ Integrated | ⚠️ Modified | ❓ Unknown | 🟡 HIGH |
| **Services** |
| AgentService | ✅ Working | ⚠️ Modified | ❓ Unknown | 🟡 HIGH |
| ElevenLabs | ✅ Working | ✅ Unchanged | ✅ Yes | 🟢 LOW |
| DALL-E Avatar | ✅ Working | ✅ Unchanged | ✅ Yes | 🟢 LOW |
| **API Endpoints** |
| POST /agents | ✅ Working | ✅ Working | ✅ Yes | 🟢 LOW |
| GET /agents | ✅ Working | ✅ Working | ✅ Yes | 🟢 LOW |
| POST /agents/{id}/chat | ✅ Working | ⚠️ Modified | ❓ Unknown | 🔴 CRITICAL |
| Chat endpoint | ✅ Working | ⚠️ Modified | ❓ Unknown | 🔴 CRITICAL |
| **Frontend** |
| ChatInterface | ✅ Working | ✅ Working | ✅ Yes | 🟢 LOW |
| MessageBubble | ✅ Working | ✅ Working | ✅ Yes | 🟢 LOW |
| AgentCard | ✅ Working | ✅ Working | ✅ Yes | 🟢 LOW |
| **Tests** |
| Agent Tests | ✅ 16 files | ❌ Deleted | ❌ No | 🔴 CRITICAL |
| New Tests | ❌ N/A | ⚠️ 2 files | ❓ Unknown | 🟡 HIGH |
| **Documentation** |
| Architecture | ✅ Comprehensive | ❌ Deleted | ❌ No | 🟡 HIGH |
| Standards | ✅ 1,623 lines | ❌ Deleted | ❌ No | 🟡 HIGH |
| New Docs | ❌ N/A | ⚠️ Partial | ❓ Unknown | 🟡 HIGH |

**Legend:**
- 🔴 CRITICAL: Blocking issue, immediate action required
- 🟡 HIGH: Potential breaking change, needs verification
- 🟢 LOW: Stable, no immediate risk

---

## 10. Recovery Checklist

### Phase 1: Restore Stability ✅
- [ ] Stash local changes: `git stash push -u`
- [ ] Verify git HEAD: `git log -1`
- [ ] Test backend startup
- [ ] Test frontend startup
- [ ] Test chat endpoint E2E
- [ ] Verify agent creation
- [ ] Verify avatar display
- [ ] Verify voice synthesis

### Phase 2: Analyze Local Changes
- [ ] Review stashed changes: `git stash show -p`
- [ ] Extract GuideAgent implementation
- [ ] Extract new graph module
- [ ] Extract new memoryManager
- [ ] Document new architecture intent

### Phase 3: Create Safe Integration Branch
- [ ] Create feature branch: `git checkout -b feature/guide-agent`
- [ ] Apply stashed changes: `git stash pop`
- [ ] Fix import paths
- [ ] Add missing implementations
- [ ] Write integration tests

### Phase 4: Validate New System
- [ ] GuideAgent completes initialization
- [ ] GuideAgent.graph compiles
- [ ] Chat endpoint processes message
- [ ] Memory retrieval works
- [ ] Response generation matches old behavior
- [ ] All tests pass

### Phase 5: Gradual Migration
- [ ] Add feature flag in settings
- [ ] Deploy both implementations
- [ ] Monitor metrics
- [ ] Gradual rollout
- [ ] Deprecate old system

---

## 11. Conclusion

### Current State
**Git Version (b0197b7):** Stable, production-ready system with working chat functionality through the entire stack.

**Local Version:** Partially refactored architecture with critical components deleted before replacement validated.

### Risk Assessment
**Critical Risk:** Chat functionality likely broken due to:
1. Deleted agent implementations
2. Incomplete GuideAgent integration
3. No test coverage to validate changes
4. Import path mismatches

### Recommended Path Forward

**IMMEDIATE (Today):**
1. Restore git version
2. Validate all functionality works
3. Stash local changes to feature branch

**SHORT-TERM (This Week):**
1. Complete GuideAgent implementation
2. Add integration tests
3. Run parallel validation

**MEDIUM-TERM (Next 2 Weeks):**
1. Feature flag deployment
2. Side-by-side comparison
3. Gradual migration

**LONG-TERM (Next Month):**
1. Deprecate old agents
2. Update documentation
3. Clean up legacy code

### Success Criteria
- [ ] Chat endpoint functional
- [ ] Memory retrieval operational
- [ ] Agent responses contextual
- [ ] Voice synthesis working
- [ ] Test coverage >80%
- [ ] Zero regression bugs

---

## Appendix A: File Deletion Summary

### Backend Agents (7 files, 3,085 lines)
```
backend/agents/affirmation_agent.py          541 lines
backend/agents/intake_agent.py               252 lines
backend/agents/intake_agent_cognitive.py     615 lines
backend/agents/intake_agent_v2.py            630 lines
backend/agents/langgraph_agent.py            287 lines
backend/agents/manifestation_protocol_agent.py 536 lines
backend/agents/therapy_agent.py              224 lines
```

### Backend Services (2 files, 1,213 lines)
```
backend/services/memory_manager.py           860 lines
backend/services/memory_manager.py.backup    353 lines
```

### Tests (16 files, 3,584 lines)
```
backend/tests/test_agent_lifecycle.py        459 lines
backend/tests/test_baseline_flow.py          130 lines
backend/tests/test_cognitive_intake.py       441 lines
backend/tests/test_mem0_integration.py       125 lines
backend/tests/test_memory_manager.py          90 lines
backend/tests/test_numen_pipeline.py         491 lines
backend/tests/test_voice_creation_e2e.py     302 lines
backend/tests/test_protocol_generation.py    116 lines
+ 8 more test files
```

### Documentation (30+ files, 17,356 lines)
```
docs/ARCHITECTURE.md                          734 lines
docs/architecture/AGENT_CREATION_STANDARD.md 1,623 lines
docs/architecture/AVATAR_GENERATION_GUIDE.md 1,286 lines
docs/architecture/MEM0_MIGRATION_GUIDE.md     462 lines
docs/archive/ (26 files)                   ~12,000 lines
+ Multiple audit and implementation reports
```

### Database Migrations (2 files, 407 lines)
```
backend/database/migrations/004_cognitive_assessment_tables.sql  256 lines
backend/database/run_cognitive_migration.py                      151 lines
```

### Assets (20+ files)
```
backend/backend/avatars/          17 PNG/JPG images
backend/backend/prompts/          11 agent contract directories
infrastructure/                    1 SQL policy file
```

---

## Appendix B: Critical Code Comparison

### Memory Manager Import (Breaking Change)

**Git Version (agent_service.py:20):**
```python
from services.memory_manager import MemoryManager
```

**Local Version (agent_service.py:21):**
```python
from memoryManager.memory_manager import MemoryManager
```

**Impact:** Any code using old import will fail

### Agent Invocation (Architecture Change)

**Git Version (Simple, Direct):**
```python
# Direct response generation in agent_service
response_text = self._generate_response(message, history, context)
```

**Local Version (Complex, Orchestrator):**
```python
# Line 486-505
from agents.guide_agent.guide_agent import GuideAgent
guide_agent = GuideAgent(contract=contract, memory=memory_manager)
result = await guide_agent.graph.ainvoke(graph_state)
response_text = result.get("response_text", result.get("response", "..."))
```

**Impact:** GuideAgent must be fully implemented or chat breaks

---

**Report Generated:** 2025-11-03
**Analysis Tool:** Claude Code
**Repository:** DTSP-AI/numen-ai
