# Breaking Issues Resolution Guide

**Generated:** October 29, 2025  
**Document Version:** 2.0.0  
**Status:** All code issues documented and resolutions provided

---

## ⚠️ Important Note on Configuration

**All `.env` files and credentials are configured and valid.**
- API keys (OpenAI, ElevenLabs, Deepgram, LiveKit, Mem0) are properly set
- Database connection strings (Supabase) are configured
- Environment variables are loaded correctly
- **This document focuses only on code bugs, not configuration issues.**

---

## Table of Contents

1. [Critical Breaking Issues (P0)](#critical-breaking-issues-p0)
2. [High Priority Issues (P1)](#high-priority-issues-p1)
3. [Medium Priority Issues (P2)](#medium-priority-issues-p2)
4. [Resolution Implementation Order](#resolution-implementation-order)

---

## Critical Breaking Issues (P0)

### Issue #1: Incorrect MemoryManager Import Path and Initialization
**Priority:** 🔴 CRITICAL  
**File:** `backend/routers/intake.py:104-106`  
**Status:** ⚠️ WILL CRASH

**Problem:**
```python
from services.memory_manager import MemoryManager  # ❌ Wrong path
memory_manager = MemoryManager()  # ❌ Missing required parameters
await memory_manager.initialize()  # ❌ Method doesn't exist
```

**Impact:**
- ImportError when `/api/intake/process` tries to store memory
- MemoryManager requires `tenant_id`, `agent_id`, `agent_traits` at initialization
- `initialize()` method doesn't exist in MemoryManager class
- Causes runtime crash on intake contract generation

**Root Cause Analysis:**
1. Wrong import path: Should be `memoryManager.memory_manager`, not `services.memory_manager`
2. Missing required constructor parameters: MemoryManager needs tenant_id, agent_id, agent_traits
3. Non-existent method: MemoryManager doesn't have `initialize()` method
4. Incorrect usage: `add_memory()` is the correct method, not `embed_and_upsert()`

**Resolution:**

**Option A: Skip Memory Storage at Intake Stage (Recommended)**
Since intake happens before agent creation, and MemoryManager requires an agent_id, the simplest fix is to skip memory storage here:

```python
# backend/routers/intake.py:103-119
# Store intake contract in semantic memory
# NOTE: Skipping memory storage at intake stage - will be stored when agent is created
# MemoryManager requires agent_id which doesn't exist yet
try:
    # For now, skip memory storage until agent is created
    # The agent creation process will handle storing intake data
    logger.debug("Skipping memory storage at intake - will be stored during agent creation")
except Exception as mem_error:
    logger.warning(f"Memory storage skipped: {mem_error}")
    # Non-blocking - continue even if memory storage fails
```

**Option B: Create User-Level Memory Manager**
If you need to store intake data immediately:

```python
# backend/routers/intake.py:103-114
# Store intake contract in semantic memory
try:
    from memoryManager.memory_manager import MemoryManager
    
    # Create user-level memory manager with placeholder agent_id
    # This allows storing data before agent creation
    tenant_id = request.tenant_id or "00000000-0000-0000-0000-000000000001"
    memory_manager = MemoryManager(
        tenant_id=tenant_id,
        agent_id="00000000-0000-0000-0000-000000000000",  # Placeholder for user-level
        agent_traits={}  # Empty for intake storage
    )
    
    # Use correct method name
    await memory_manager.add_memory(
        message=json.dumps(intake_contract.model_dump()),
        metadata={
            "type": "intake_contract", 
            "goals": normalized_goals, 
            "user_id": request.user_id
        }
    )
    
    logger.debug("Stored intake contract in semantic memory")
except Exception as mem_error:
    logger.warning(f"Failed to store in memory: {mem_error}")
    # Non-blocking - continue even if memory storage fails
```

**Files to Modify:**
- `backend/routers/intake.py` (lines 103-119)

---

### Issue #2: Therapy Router Broken Imports and Non-Existent Function Calls
**Priority:** 🔴 CRITICAL  
**File:** `backend/routers/therapy.py:13, 24, 37, 197`  
**Status:** ⚠️ WILL CRASH (Router disabled but file has errors)

**Problem:**
```python
# Line 13: Wrong import path
from agents.therapy_agent import TherapyAgent  # ❌ Doesn't exist at this path

# Line 24: Missing required parameters
therapy_agent = TherapyAgent()  # ❌ TherapyAgent requires parameters at instantiation

# Line 37: Function doesn't exist
redis = get_redis()  # ❌ get_redis() removed from database.py (Redis no longer used)

# Line 197: Variable doesn't exist
await memory_service.store_session_data(...)  # ❌ memory_service commented out on line 22
```

**Impact:**
- File has multiple import and function call errors
- Will cause ImportError if router is ever enabled in `main.py`
- References removed Redis functionality
- Broken memory service reference
- Prevents enabling therapy router even if functionality is needed

**Root Cause Analysis:**
1. Wrong import path: TherapyAgent moved to `guide_agent/guide_sub_agents/`
2. Module-level instantiation: TherapyAgent requires constructor parameters, can't be instantiated at module level
3. Removed Redis dependency: `get_redis()` function no longer exists
4. Commented service: `memory_service` was commented out but still referenced in code

**Resolution:**

**Option A: Fix All Imports and References (Recommended if router will be used)**
```python
# backend/routers/therapy.py

# Line 13: Fix import path
from agents.guide_agent.guide_sub_agents.therapy_agent import TherapyAgent

# Line 22-24: Remove module-level instantiation
# therapy_agent = TherapyAgent()  # ❌ Remove - requires constructor parameters
# Instantiate inside functions where needed:
#   therapy_agent = TherapyAgent(contract=..., memory=...)

# Line 37: Remove Redis reference
# redis = get_redis()  # ❌ Remove this line and all Redis usage
# Redis functionality replaced by PostgreSQL sessions table

# Line 197: Fix memory service reference
from memoryManager.memory_manager import MemoryManager

# In therapy_websocket function, replace:
# await memory_service.store_session_data(...)
# With:
memory_manager = MemoryManager(
    tenant_id=tenant_id,  # Get from session/request
    agent_id=agent_id,    # Get from session
    agent_traits={}
)
await memory_manager.store_interaction(
    role="system",
    content=script,
    session_id=str(session_id),
    user_id=user_id,
    metadata={
        "script": script,
        "contract": contract.dict(),
        "reflections": therapy_state["reflections"]
    }
)
```

**Option B: Delete File (Recommended if router not needed)**
If therapy router won't be used in the near term:
1. Delete `backend/routers/therapy.py`
2. Remove import from `backend/main.py` (already commented out)
3. Remove therapy.router inclusion from main.py (already commented out)

**Files to Modify:**
- `backend/routers/therapy.py` (multiple lines) OR delete file

---

## High Priority Issues (P1)

### Issue #3: Intake Process Missing Tenant ID Header Handling
**Priority:** 🟡 HIGH  
**File:** `backend/routers/intake.py:34`  
**Status:** ⚠️ DATA INTEGRITY

**Problem:**
```python
@router.post("/intake/process", response_model=IntakeContract)
async def process_intake(request: IntakeRequest):
    # Missing tenant_id and user_id from headers
```

The endpoint doesn't accept `tenant_id` or `user_id` from HTTP headers, but other endpoints use header-based authentication pattern (`x-tenant-id`, `x-user-id`).

**Impact:**
- Inconsistent API design with other endpoints
- Tenant isolation may not work correctly
- Memory storage attempts may fail due to missing tenant_id
- Potential data integrity issues in multi-tenant scenarios

**Resolution:**
```python
# backend/routers/intake.py:34-35
@router.post("/intake/process", response_model=IntakeContract)
async def process_intake(
    request: IntakeRequest,
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
    x_user_id: Optional[str] = Header(None, alias="x-user-id")
):
    # Use tenant_id from header, request, or fallback to default
    tenant_id = x_tenant_id or getattr(request, 'tenant_id', None) or "00000000-0000-0000-0000-000000000001"
    user_id = x_user_id or request.user_id
    
    logger.info(f"Processing intake for user: {user_id}, tenant: {tenant_id}")
    
    # Use tenant_id and user_id in memory storage and other operations
    # ... rest of function
```

**Files to Modify:**
- `backend/routers/intake.py` (line 34-35)

---

### Issue #4: OpenAI Client Missing Fallback Configuration Check
**Priority:** 🟡 HIGH  
**File:** `backend/routers/intake.py:21`  
**Status:** ⚠️ CODE CONSISTENCY

**Problem:**
```python
openai_client = OpenAI(api_key=settings.openai_api_key)
```

Only checks `settings.openai_api_key` but config.py supports both `openai_api_key` and `OPENAI_API_KEY` (uppercase). While credentials are configured, the code should handle both cases for consistency.

**Impact:**
- Code doesn't match configuration flexibility
- If env var naming changes, code breaks
- Inconsistent with other service initializations

**Resolution:**
```python
# backend/routers/intake.py:20-21
from openai import OpenAI
from config import settings

# Check both lowercase and uppercase env var names for consistency
_openai_api_key = settings.openai_api_key or settings.OPENAI_API_KEY
openai_client = OpenAI(api_key=_openai_api_key)
```

**Files to Modify:**
- `backend/routers/intake.py` (line 21)

---

## Medium Priority Issues (P2)

### Issue #5: TODO Comments with Incomplete Implementations
**Priority:** 🟢 MEDIUM  
**Files:** Multiple  
**Status:** ℹ️ DOCUMENTED - Non-breaking

**TODOs Found:**

1. **`backend/agents/guide_agent/guide_agent.py:292`**
   ```python
   # TODO: Integrate ElevenLabs SDK
   ```
   - Audio synthesis placeholder exists
   - Returns placeholder URLs
   - Doesn't break flow but limits functionality

2. **`backend/agents/guide_agent/guide_sub_agents/discovery_agent.py:54`**
   ```python
   "gas_rating": None,  # TODO: Implement GAS rating system
   ```
   - Returns None for GAS rating
   - Doesn't break flow, just incomplete data

3. **`backend/routers/therapy.py:22`**
   ```python
   # memory_service = MemoryService()  # TODO: Update to use MemoryManager
   ```
   - Comment references old MemoryService
   - Already migrated elsewhere, just needs cleanup

**Resolution:**
These are feature gaps, not breaking issues. Can be addressed incrementally:
- ElevenLabs integration: Audio synthesis works via ElevenLabsService, just needs wiring
- GAS rating: Returns None, doesn't break flow - implement when needed
- MemoryManager comment: Clean up comment when therapy.py is fixed

**Files to Modify:**
- `backend/agents/guide_agent/guide_agent.py` (line 292)
- `backend/agents/guide_agent/guide_sub_agents/discovery_agent.py` (line 54)
- `backend/routers/therapy.py` (line 22) - when fixing Issue #2

---

## Resolution Implementation Order

### Phase 1: Critical Fixes (Required for Stability)
1. ✅ **Fix Issue #1:** MemoryManager import path and initialization
   - **Time:** 15 minutes
   - **Impact:** Prevents crashes on `/api/intake/process`
   
2. ✅ **Fix Issue #2:** Clean up therapy.py imports
   - **Time:** 20 minutes
   - **Impact:** Removes import errors, enables router if needed

**Total Phase 1 Time:** ~35 minutes

### Phase 2: High Priority Fixes (Recommended)
3. ✅ **Fix Issue #3:** Add tenant_id header handling to intake
   - **Time:** 10 minutes
   - **Impact:** Improves data integrity and API consistency
   
4. ✅ **Fix Issue #4:** Add OpenAI API key fallback check
   - **Time:** 5 minutes
   - **Impact:** Code consistency improvement

**Total Phase 2 Time:** ~15 minutes

### Phase 3: Code Quality (Optional)
5. ✅ Clean up TODO comments
   - **Time:** 10 minutes
   - **Impact:** Documentation cleanup

**Total Phase 3 Time:** ~10 minutes

**Total Estimated Fix Time:** ~60 minutes for all issues

---

## Testing Checklist

After implementing fixes, verify:

- [ ] `/api/intake/process` completes without memory import errors
- [ ] `/api/intake/assist` works correctly (credentials are configured)
- [ ] Backend starts without import errors
- [ ] No Redis references remain in codebase
- [ ] All endpoints accept tenant_id headers properly
- [ ] MemoryManager methods are called correctly
- [ ] Therapy router either fixed or deleted

---

## Summary

**Total Critical Issues:** 2 (code bugs)  
**Total High Priority Issues:** 2 (code improvements)  
**Total Medium Priority Issues:** 1 (documentation)

**Quick Fix Summary:**
1. ✅ Fix MemoryManager import path and initialization (Issue #1)
2. ✅ Clean up therapy.py imports or delete file (Issue #2)
3. ✅ Add tenant_id header handling to intake endpoint (Issue #3)
4. ✅ Add OpenAI API key fallback check (Issue #4)

**All fixes are straightforward code changes. Credentials and configuration are already in place and working.**

---

**Document Version:** 2.0.0  
**Last Updated:** October 29, 2025  
**Maintained By:** Development Team
