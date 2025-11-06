# Contract Management Cleanup & Voice Configuration Fix Plan

**Date**: 2025-01-15  
**Status**: Ready for Implementation  
**Priority**: High

---

## Executive Summary

This plan addresses all issues identified in the Agent Contract Management Report:
1. Remove deprecated filesystem storage (335+ lines of redundant code)
2. Fix voice configuration to be properly required for voice agents
3. Ensure voice is handled throughout the entire agent lifecycle
4. Clean up redundant files and directories

---

## Phase 1: Remove Deprecated Filesystem Storage

### 1.1 Remove Filesystem Write Operations

**File**: `backend/services/agent_service.py`

**Changes**:
- Remove `_save_contract_file()` method (lines 539-565)
- Remove call to `_save_contract_file()` from `create_agent()` (line 144)
- Remove call to `_save_contract_file()` from `update_agent()` (line 348)
- Keep `_generate_system_prompt()` method (still needed for runtime generation)

**Impact**: Eliminates filesystem I/O operations during agent creation/updates

### 1.2 Remove Filesystem Validation

**File**: `backend/services/agent_service.py`

**Changes**:
- Remove `validate_sync` parameter from `get_agent()` method (line 173)
- Remove filesystem sync validation code (lines 225-229)
- Remove import of `validate_agent_sync` if present

**Impact**: Simplifies agent retrieval, removes unused validation path

### 1.3 Delete Contract Validator Service

**File**: `backend/services/contract_validator.py`

**Action**: Delete entire file (335 lines)

**Reason**: No longer needed - filesystem storage is deprecated

**Impact**: Removes 335 lines of redundant validation code

### 1.4 Remove Filesystem Directory References

**Directories**:
- `backend/prompts/dashboard-agent-001/`
- `backend/prompts/intake-agent-001/`
- Any other `backend/prompts/{agent_id}/` directories

**Action**: Delete all directories under `backend/prompts/`

**Note**: These are legacy directories from before database-only storage

### 1.5 Update Documentation

**Files to Update**:
- `backend/routers/agents.py`: Remove "Save filesystem JSON" from docstrings (line 73)
- `docs/AGENT_CONTRACT_MANAGEMENT_REPORT.md`: Update status to reflect removal
- `docs/FILESYSTEM_STORAGE_DECISION.md`: Mark as complete

---

## Phase 2: Fix Voice Configuration Requirements

### 2.1 Update AgentContract Model

**File**: `backend/models/agent.py`

**Current Issue**: Voice is `Optional[VoiceConfiguration] = None` but should be required for voice agents

**Changes**:
- Keep `voice: Optional[VoiceConfiguration] = None` in model (for flexibility)
- **Enhance validator** `validate_voice_for_voice_agents()` to:
  - Check if `type == AgentType.VOICE` OR `configuration.voice_enabled == True`
  - Require voice configuration in both cases
  - Provide clear error message

**Code Update**:
```python
@validator('voice')
def validate_voice_for_voice_agents(cls, v, values):
    """Voice agents and agents with voice_enabled must have voice configuration"""
    agent_type = values.get('type')
    config = values.get('configuration')
    
    # Check if voice is required
    requires_voice = (
        agent_type == AgentType.VOICE or
        (config and getattr(config, 'voice_enabled', False))
    )
    
    if requires_voice and v is None:
        raise ValueError(
            'Voice configuration is required for voice agents or when voice_enabled=True. '
            'Provide a VoiceConfiguration with at least voice_id and provider.'
        )
    return v
```

### 2.2 Update AgentCreateRequest Model

**File**: `backend/models/agent.py`

**Current Issue**: Voice is optional in request, but should be validated based on type/config

**Changes**:
- Keep `voice: Optional[VoiceConfiguration] = None` (for API flexibility)
- Add validation in API endpoint instead (see 2.3)

### 2.3 Update Agent Creation Endpoint

**File**: `backend/routers/agents.py`

**Current Issue**: Voice defaults are applied but not consistently enforced

**Changes**:
- **Enhance voice validation logic** (lines 98-114):
  - If `type == AgentType.VOICE` → voice is REQUIRED (raise error if missing)
  - If `configuration.voice_enabled == True` → voice is REQUIRED (apply default if missing)
  - If `type == AgentType.CONVERSATIONAL` and voice not provided → voice is optional

**Code Update**:
```python
# Determine if voice is required
voice_required = (
    request.type == AgentType.VOICE or
    (request.configuration and request.configuration.voice_enabled)
)

# Validate voice requirement
if voice_required and not request.voice:
    if request.type == AgentType.VOICE:
        raise HTTPException(
            status_code=400,
            detail="Voice configuration is required for voice agents. Provide 'voice' field with voice_id and provider."
        )
    else:
        # Apply default voice for voice_enabled=True
        logger.info("No voice provided but voice_enabled=True, using default voice (Rachel)")
        voice_config = VoiceConfiguration(...)
else:
    voice_config = request.voice
```

### 2.4 Update Agent Update Endpoint

**File**: `backend/routers/agents.py`

**Changes**:
- Add validation when updating agent type to VOICE
- Add validation when updating configuration.voice_enabled to True
- Ensure voice configuration exists before allowing these updates

**Code Update**:
```python
# In update_agent endpoint, before applying updates:
if updates.get("type") == AgentType.VOICE.value:
    # Check if voice exists in current contract or updates
    if not updates.get("voice") and not current_contract.get("voice"):
        raise HTTPException(
            status_code=400,
            detail="Cannot set agent type to VOICE without voice configuration. Provide 'voice' field."
        )

if updates.get("configuration", {}).get("voice_enabled") is True:
    # Check if voice exists
    if not updates.get("voice") and not current_contract.get("voice"):
        raise HTTPException(
            status_code=400,
            detail="Cannot enable voice without voice configuration. Provide 'voice' field."
        )
```

### 2.5 Update from_intake_contract Endpoint

**File**: `backend/routers/agents.py`

**Current Status**: Already includes voice configuration (lines 675-681)

**Verification**: Ensure voice is always provided (currently hardcoded, which is correct)

**No Changes Needed**: This endpoint already handles voice correctly

### 2.6 Update AgentService Methods

**File**: `backend/services/agent_service.py`

**Changes**:
- Add voice validation in `create_agent()` before database insert
- Add voice validation in `update_agent()` before applying updates
- Ensure voice configuration is preserved during updates

---

## Phase 3: Ensure Voice Handling Throughout System

### 3.1 Verify Voice Usage in GuideAgent

**File**: `backend/agents/guide_agent/guide_agent.py`

**Action**: Verify that GuideAgent properly uses voice configuration from contract

**Check**:
- Voice configuration is loaded from contract
- Voice settings are passed to audio synthesis services
- Voice is used in LiveKit sessions if applicable

### 3.2 Verify Voice Usage in LiveKit Services

**Files**:
- `backend/services/therapy_livekit_service.py`
- `backend/services/livekit_service.py`

**Action**: Ensure voice configuration from agent contract is used

**Check**:
- TTS uses `contract.voice.voice_id`
- STT uses `contract.voice.stt_provider` and `contract.voice.stt_model`
- Voice settings (stability, similarity_boost) are applied

### 3.3 Update System Prompt Generation

**File**: `backend/services/agent_service.py`

**Current**: `_generate_system_prompt()` generates prompt but doesn't include voice info

**Enhancement**: Add voice configuration details to system prompt (optional, for agent awareness)

**Code Update**:
```python
def _generate_system_prompt(self, contract: AgentContract) -> str:
    # ... existing code ...
    
    # Add voice configuration if present
    voice_section = ""
    if contract.voice:
        voice_section = f"""
VOICE CONFIGURATION:
- Provider: {contract.voice.provider}
- Voice ID: {contract.voice.voice_id}
- Language: {contract.voice.language}
- Speed: {contract.voice.speed}
- Stability: {contract.voice.stability}
"""
    
    return f"""...existing prompt...{voice_section}"""
```

---

## Phase 4: Testing & Validation

### 4.1 Test Voice Agent Creation

**Test Cases**:
1. Create voice agent WITH voice config → Should succeed
2. Create voice agent WITHOUT voice config → Should fail with clear error
3. Create conversational agent WITH voice_enabled=True but no voice → Should apply default
4. Create conversational agent WITH voice_enabled=True and voice → Should use provided voice
5. Create conversational agent WITHOUT voice → Should succeed (voice optional)

### 4.2 Test Agent Updates

**Test Cases**:
1. Update agent type to VOICE without voice → Should fail
2. Update voice_enabled to True without voice → Should fail
3. Update voice configuration → Should succeed
4. Remove voice from voice agent → Should fail

### 4.3 Test Filesystem Removal

**Test Cases**:
1. Create agent → Verify NO filesystem writes
2. Update agent → Verify NO filesystem writes
3. Get agent → Verify NO filesystem reads
4. Verify no errors from missing filesystem paths

### 4.4 Integration Tests

**Test Cases**:
1. Complete agent lifecycle (create → update → delete) without filesystem
2. Voice agent creation and usage in LiveKit
3. Voice configuration persistence across updates

---

## Phase 5: Documentation Updates

### 5.1 Update API Documentation

**File**: `backend/routers/agents.py`

**Changes**:
- Update docstrings to reflect voice requirements
- Remove filesystem references
- Add voice requirement examples

### 5.2 Update Architecture Documentation

**Files**:
- `docs/AGENT_CONTRACT_MANAGEMENT_REPORT.md`
- `docs/architecture/knowledgebase/AGENT_CREATION_STANDARD.md`

**Changes**:
- Mark filesystem storage as REMOVED
- Update voice configuration requirements
- Add voice validation examples

### 5.3 Update README

**File**: `README.md` or relevant setup docs

**Changes**:
- Remove any references to `backend/prompts/` directory
- Update voice configuration requirements

---

## Implementation Checklist

### Phase 1: Filesystem Removal
- [ ] Remove `_save_contract_file()` from `agent_service.py`
- [ ] Remove filesystem calls from `create_agent()`
- [ ] Remove filesystem calls from `update_agent()`
- [ ] Remove `validate_sync` parameter from `get_agent()`
- [ ] Remove filesystem validation code from `get_agent()`
- [ ] Delete `backend/services/contract_validator.py`
- [ ] Delete `backend/prompts/` directories
- [ ] Update docstrings in `agents.py` router

### Phase 2: Voice Configuration Fixes
- [ ] Enhance `validate_voice_for_voice_agents()` validator
- [ ] Update `create_agent()` endpoint voice validation
- [ ] Update `update_agent()` endpoint voice validation
- [ ] Add voice requirement checks in `AgentService.create_agent()`
- [ ] Add voice requirement checks in `AgentService.update_agent()`

### Phase 3: Voice Handling Verification
- [ ] Verify GuideAgent uses voice configuration
- [ ] Verify LiveKit services use voice configuration
- [ ] Update system prompt generation (optional enhancement)

### Phase 4: Testing
- [ ] Test voice agent creation scenarios
- [ ] Test agent update scenarios
- [ ] Test filesystem removal (no errors)
- [ ] Integration tests for complete lifecycle

### Phase 5: Documentation
- [ ] Update API docstrings
- [ ] Update architecture docs
- [ ] Update README/setup docs
- [ ] Mark filesystem decision as complete

---

## Files to Modify

### Delete
- `backend/services/contract_validator.py` (335 lines)
- `backend/prompts/dashboard-agent-001/` (directory)
- `backend/prompts/intake-agent-001/` (directory)

### Modify
- `backend/models/agent.py` (voice validator enhancement)
- `backend/services/agent_service.py` (remove filesystem code, add voice validation)
- `backend/routers/agents.py` (enhance voice validation, remove filesystem references)
- `docs/AGENT_CONTRACT_MANAGEMENT_REPORT.md` (update status)
- `docs/FILESYSTEM_STORAGE_DECISION.md` (mark complete)

### Verify (No Changes Expected)
- `backend/agents/guide_agent/guide_agent.py` (verify voice usage)
- `backend/services/therapy_livekit_service.py` (verify voice usage)
- `backend/services/livekit_service.py` (verify voice usage)

---

## Risk Assessment

### Low Risk
- Filesystem removal: No code reads from filesystem (confirmed)
- Voice validation: Adds safety checks, doesn't break existing flows

### Medium Risk
- Voice requirement enforcement: May break existing agents without voice
  - **Mitigation**: Check existing agents, add migration if needed
  - **Mitigation**: Provide clear error messages for users

### Testing Required
- All agent creation flows
- All agent update flows
- Voice agent usage in LiveKit
- Error handling for missing voice config

---

## Success Criteria

1. ✅ No filesystem writes during agent creation/updates
2. ✅ No filesystem reads during agent retrieval
3. ✅ Voice agents require voice configuration (validation error if missing)
4. ✅ Agents with `voice_enabled=True` require voice configuration
5. ✅ Clear error messages for missing voice configuration
6. ✅ All tests pass
7. ✅ Documentation updated
8. ✅ No breaking changes for existing valid agents

---

## Estimated Effort

- **Phase 1** (Filesystem Removal): 2-3 hours
- **Phase 2** (Voice Fixes): 3-4 hours
- **Phase 3** (Verification): 1-2 hours
- **Phase 4** (Testing): 2-3 hours
- **Phase 5** (Documentation): 1 hour

**Total**: 9-13 hours

---

## Notes

- Voice configuration is critical for voice agents - this fix ensures it's properly enforced
- Filesystem removal simplifies architecture and eliminates sync complexity
- All changes are backward compatible for existing valid agents
- Error messages should guide users to provide required voice configuration

---

**Plan Created**: 2025-01-15  
**Ready for Implementation**: Yes  
**Priority**: High

