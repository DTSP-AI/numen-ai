# Code Quality Action Plan
**Based On**: CODE_QUALITY_AUDIT_REPORT.md
**Date**: 2025-11-04

---

## Quick Summary

**Status**: ✅ **PRODUCTION READY**
**Critical Issues**: 0
**High Priority**: 0
**Medium Priority**: 3
**Low Priority**: 5

---

## Immediate Actions (< 30 minutes)

### 1. Remove Unused Imports
**Effort**: 15 minutes
**Files**: `backend/routers/avatar.py`

```bash
# Remove these lines from avatar.py:
import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
```

### 2. Document GAS Rating as v2.0 Feature
**Effort**: 5 minutes
**File**: `backend/agents/guide_agent/guide_sub_agents/discovery_agent.py:54`

```python
# Change from:
"gas_rating": None,  # TODO: Implement GAS rating system

# To:
"gas_rating": None,  # Planned for v2.0 - Goals/Affirmations/Strengths rating
```

### 3. Add Filesystem Fallback Monitoring
**Effort**: 5 minutes
**File**: `backend/routers/avatar.py:146`

```python
if not avatar_url:
    logger.warning(
        f"⚠️  FALLBACK ALERT: Using filesystem for avatar. "
        f"Tenant: {tenant_id}, User: {user_id}. "
        f"Check Supabase Storage availability."
    )
```

---

## Short Term Actions (Next Sprint - 7 hours total)

### 1. Complete TherapyAgent Integration
**Effort**: 4 hours
**File**: `backend/routers/therapy.py`
**Priority**: Medium - Unlocks real-time therapy sessions

**Steps**:
```python
# 1. Uncomment import
from agents.guide_agent.guide_sub_agents.therapy_agent import TherapyAgent

# 2. Replace line 101 placeholder
# Get session context
async with pool.acquire() as conn:
    session_data = await conn.fetchrow(
        "SELECT tenant_id, agent_id FROM sessions WHERE id = $1",
        session_id
    )
    agent_row = await conn.fetchrow(
        "SELECT contract FROM agents WHERE id = $1::uuid",
        session_data["agent_id"]
    )

# Initialize agent
contract = AgentContract(**agent_row["contract"])
memory_manager = MemoryManager(
    tenant_id=session_data["tenant_id"],
    agent_id=session_data["agent_id"],
    agent_traits=contract.traits.dict() if contract.traits else {}
)
therapy_agent = TherapyAgent(contract=contract, memory=memory_manager)

# Get response
response = await therapy_agent.process_input(text, session_id)
response_text = response.get("response", "")

# 3. Replace line 194 script generation
therapy_state = await therapy_agent.generate_session(
    session_id=str(session_id),
    user_id=user_id,
    contract=contract
)
script = therapy_agent.get_script(therapy_state)
```

**Testing**:
```bash
# Test the WebSocket endpoint
python backend/tests/test_therapy_websocket.py  # Create this test
```

---

### 2. Centralize Tenant/User ID Extraction
**Effort**: 1 hour
**Priority**: Low - Code quality improvement

**Create**: `backend/dependencies.py`
```python
"""
Shared FastAPI dependencies for multi-tenant architecture
"""
from fastapi import Header
from typing import Optional

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"

def get_tenant_id(x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id")) -> str:
    """Extract tenant ID from header or use default for development"""
    return x_tenant_id or DEFAULT_TENANT_ID

def get_user_id(x_user_id: Optional[str] = Header(None, alias="x-user-id")) -> str:
    """Extract user ID from header or use default for development"""
    return x_user_id or DEFAULT_USER_ID
```

**Update routers** to use dependency injection:
```python
# In each router (agents.py, intake.py, etc.)
from dependencies import get_tenant_id, get_user_id
from fastapi import Depends

# Replace manual extraction with:
@router.post("/agents")
async def create_agent(
    request: AgentCreateRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
):
    # tenant_id and user_id automatically extracted
    pass
```

---

### 3. Evaluate Filesystem Contract Storage
**Effort**: 2 hours (decision + implementation)
**Priority**: Medium - Architectural simplification

**Decision Matrix**:

| Keep Filesystem | Remove Filesystem |
|----------------|-------------------|
| ✅ Faster reads (no DB query) | ✅ Single source of truth |
| ✅ Git-trackable contracts | ✅ No sync issues |
| ✅ Easy backup/restore | ✅ Simpler architecture |
| ❌ Sync complexity | ✅ Follows "Supabase handles everything" |
| ❌ Two sources of truth | ✅ Tenant isolation automatic |
| ❌ Manual migrations | ✅ Easier multi-instance deployment |

**Recommendation**: **Remove filesystem storage**

**Implementation** (if removing):
```python
# 1. Update agent_service.py - remove filesystem saving
async def create_agent(self, contract, tenant_id, owner_id):
    # Remove lines that write to backend/prompts/{agent_id}/
    # Keep only database storage

# 2. Delete contract_validator.py (no longer needed)
rm backend/services/contract_validator.py

# 3. Update agent retrieval to read from database only
async def get_agent_system_prompt(agent_id: str) -> str:
    """Generate system prompt from database contract"""
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT contract FROM agents WHERE id = $1::uuid",
            agent_id
        )
    contract = AgentContract(**row["contract"])
    return self._generate_system_prompt(contract)

# 4. Clean up existing backend/prompts/ directory
# Optional: Keep for backup, but don't create new ones
```

---

## Long Term Actions (v2.0)

### 1. GAS Rating System Implementation
**Effort**: 3 hours
**File**: `backend/agents/guide_agent/guide_sub_agents/discovery_agent.py`

```python
async def calculate_gas_rating(self, user_goals: List[str]) -> int:
    """
    Calculate GAS (Goals, Affirmations, Strengths) rating 1-10

    Evaluates:
    - Goal clarity and specificity
    - Actionability of stated goals
    - Alignment with evidence-based practices
    """
    from openai import AsyncOpenAI
    from config import settings

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    goals_text = "\n".join(f"- {goal}" for goal in user_goals)

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "system",
            "content": """Rate these goals from 1-10 based on:
            - Specificity (clear and concrete)
            - Measurability (can track progress)
            - Achievability (realistic)
            - Relevance (meaningful to person)
            - Time-bound (has timeframe)

            Return ONLY a number 1-10."""
        }, {
            "role": "user",
            "content": f"Goals:\n{goals_text}"
        }],
        max_tokens=5,
        temperature=0.3
    )

    try:
        rating = int(response.choices[0].message.content.strip())
        return max(1, min(10, rating))  # Clamp to 1-10
    except ValueError:
        return 5  # Default middle rating if parsing fails
```

---

### 2. ElevenLabs SDK Migration
**Effort**: 3 hours
**File**: `backend/agents/guide_agent/guide_agent.py`

```python
# Replace API calls with SDK
from elevenlabs import VoiceSettings, generate

async def generate_voice_preview(self, text: str, voice_id: str) -> bytes:
    """
    Generate voice preview using ElevenLabs SDK

    Replaces: Direct API calls in current implementation
    Benefits: Better error handling, type safety, auto-retry
    """
    audio = generate(
        text=text,
        voice=voice_id,
        model="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True
        )
    )

    return audio
```

---

## Testing After Changes

### Run Test Suite
```bash
cd backend

# Quick diagnostic
python -m tests.quick_diagnostic

# Full E2E
python -m tests.e2e_flow_diagnostic

# Specific component tests
python -m pytest tests/test_therapy_integration.py  # After TherapyAgent fix
python -m pytest tests/test_gas_rating.py           # After GAS implementation
```

### Manual Verification
```bash
# 1. Check health endpoint
curl http://localhost:8003/health

# 2. Test agent creation
curl -X POST http://localhost:8003/api/agents \
  -H "Content-Type: application/json" \
  -H "x-tenant-id: test-tenant" \
  -d '{"name": "Test", "identity": {...}}'

# 3. Test therapy WebSocket (if implemented)
wscat -c ws://localhost:8003/therapy/session/{session_id}
```

---

## Checklist

### Immediate (< 30 min)
- [ ] Remove unused imports from `avatar.py`
- [ ] Update GAS rating comment to v2.0
- [ ] Add filesystem fallback monitoring log

### Next Sprint (7 hours)
- [ ] Complete TherapyAgent integration
  - [ ] Update imports
  - [ ] Replace line 101 placeholder
  - [ ] Replace line 194 script generation
  - [ ] Write tests
  - [ ] Test WebSocket endpoint
- [ ] Create `dependencies.py`
  - [ ] Add tenant/user extraction functions
  - [ ] Update all routers to use Depends()
  - [ ] Test with E2E suite
- [ ] Evaluate filesystem storage
  - [ ] Make decision (keep or remove)
  - [ ] If removing: update agent_service.py
  - [ ] If removing: delete contract_validator.py
  - [ ] Test agent creation and retrieval

### v2.0 (Future)
- [ ] Implement GAS rating system
- [ ] Migrate to ElevenLabs SDK
- [ ] Remove legacy compatibility code

---

## Risk Assessment

| Change | Risk Level | Mitigation |
|--------|-----------|------------|
| Remove unused imports | 🟢 None | Simple cleanup |
| TherapyAgent integration | 🟡 Medium | Test thoroughly, have rollback plan |
| Centralize dependencies | 🟢 Low | FastAPI supports Depends() well |
| Remove filesystem storage | 🟡 Medium | Backup existing files, gradual migration |
| GAS rating | 🟢 Low | New feature, doesn't affect existing |

---

## Success Criteria

### Immediate Actions
✅ All unused imports removed
✅ No references to TODO in main code paths
✅ Filesystem fallback monitoring added

### Next Sprint
✅ TherapyAgent working in WebSocket sessions
✅ All routers use centralized dependency injection
✅ Decision made on filesystem storage (documented)
✅ All tests passing
✅ No regressions in E2E test suite

### v2.0
✅ GAS ratings returned for all discovery flows
✅ ElevenLabs SDK integrated
✅ Legacy code removed

---

## Rollback Plans

### If TherapyAgent Integration Fails
```python
# Revert to placeholder implementation
response_text = f"Thank you for sharing. I understand you're focused on: {text}"
script = "Therapy session temporarily unavailable."

# Add logging
logger.error("TherapyAgent integration issue - using fallback")
```

### If Dependency Injection Breaks
```python
# Revert to manual header extraction in each router
tenant_id = x_tenant_id or "00000000-0000-0000-0000-000000000001"
user_id = x_user_id or "00000000-0000-0000-0000-000000000001"
```

### If Filesystem Removal Causes Issues
```bash
# Restore from backup
git checkout HEAD -- backend/prompts/
git checkout HEAD -- backend/services/contract_validator.py
```

---

## Monitoring After Deployment

### Key Metrics to Watch
```python
# Add to monitoring dashboard:
- Filesystem fallback usage count (should be 0)
- TherapyAgent session success rate (should be > 95%)
- Agent creation time (should be < 2s)
- Memory manager cache hit rate (should be > 80%)
```

### Alert Thresholds
```yaml
alerts:
  - name: filesystem_fallback_triggered
    condition: count > 0
    severity: warning

  - name: therapy_agent_failure_rate
    condition: rate > 5%
    severity: critical

  - name: agent_creation_slow
    condition: p95 > 5s
    severity: warning
```

---

**Last Updated**: 2025-11-04 23:15:00 UTC
**Next Review**: After Next Sprint
