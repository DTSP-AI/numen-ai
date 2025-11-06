# Filesystem Contract Storage - Decision Document

**Date**: 2025-11-05
**Updated**: 2025-11-06
**Status**: ✅ **REMOVED** - Successfully eliminated
**Impact**: Low - No functionality loss

---

## Executive Summary

The filesystem contract storage (`backend/prompts/{agent_id}/`) is **redundant** and should be removed in favor of database-only storage. This will simplify the architecture and eliminate sync complexity.

## Current Architecture

### What Exists Today

1. **Database Storage** (PRIMARY)
   - `agents` table stores complete JSON contract in `contract` JSONB column
   - Single source of truth
   - Full CRUD operations
   - Tenant isolation enforced

2. **Filesystem Storage** (REDUNDANT)
   - Location: `backend/prompts/{agent_id}/`
   - Files created:
     - `agent_contract.json` - Copy of database contract
     - `system_prompt.txt` - Generated from contract
   - Code: `agent_service.py:544-565` (`_save_contract_to_filesystem()`)
   - Sync validation: `contract_validator.py` (335 lines)

### Usage Analysis

**Writes to filesystem:**
- `agent_service.py:_save_contract_to_filesystem()` - Called after agent creation
- Never fails agent creation (errors logged but not raised)

**Reads from filesystem:**
- ❌ **NONE FOUND** - No code reads from `backend/prompts/`
- All agent loading happens from database

**Validation:**
- `contract_validator.py:validate_agent_sync()` - Only called when `validate_sync=True`
- Currently not used in production flow (validate_sync defaults to False)

---

## Analysis

### Problems with Filesystem Storage

1. **Redundancy**
   - Duplicates data already in database
   - No functional benefit

2. **Sync Complexity**
   - 335 lines of validation code
   - Potential for database ↔ filesystem divergence
   - Adds failure points

3. **Multi-Tenant Issues**
   - Filesystem lacks tenant isolation
   - All contracts in single directory structure
   - Security concern for multi-tenant deployments

4. **Scalability**
   - File I/O overhead on each agent creation
   - Directory management complexity
   - No cloud-native storage benefits

### Benefits of Database-Only

1. **Simplicity**
   - Single source of truth
   - No sync validation needed
   - Remove 335 lines of code

2. **Security**
   - Tenant isolation via PostgreSQL RLS policies
   - Centralized access control

3. **Performance**
   - No filesystem I/O
   - Database caching effective
   - Better for containerized environments

4. **Cloud-Native**
   - No persistent volume requirements
   - Easier horizontal scaling
   - Container-friendly

---

## Recommendation

### ✅ Remove Filesystem Storage

**Rationale:**
- No code reads from filesystem
- Database is already the source of truth
- Simplifies architecture
- Eliminates sync complexity
- Better multi-tenant security

### Implementation Plan

#### Phase 1: Mark as Deprecated (✅ COMPLETE)
- Document decision in this file
- Add deprecation warnings to code
- Update architecture documentation

#### Phase 2: Code Cleanup (Recommended for next sprint)
1. Remove `_save_contract_to_filesystem()` from `agent_service.py`
2. Remove `contract_validator.py` (335 lines)
3. Remove filesystem validation from `get_agent()`
4. Remove `backend/prompts/` directory references
5. Update tests to not check filesystem

**Estimated effort**: 1-2 hours
**Risk**: Very low (no reads from filesystem)
**Breaking changes**: None

#### Phase 3: Cleanup Existing Files (Optional)
- Remove existing `backend/prompts/{agent_id}/` directories
- Add to `.gitignore` if not already present

---

## Alternative: Keep for Debugging

**If we want to keep for debugging purposes:**

1. Make it explicitly optional
2. Only enable via environment variable: `ENABLE_CONTRACT_FILESYSTEM_DEBUG=true`
3. Never validate sync (remove contract_validator.py)
4. Log warnings when enabled
5. Document as debug-only feature

**Verdict**: Not recommended - database queries are easier for debugging

---

## Stack Compliance

✅ **Removing filesystem storage aligns with Stack 1st Principles:**
- PostgreSQL (Supabase) handles all persistence
- No unnecessary abstractions
- Simpler architecture
- Cloud-native design

---

## Decision

**APPROVED**: Remove filesystem contract storage in next sprint

**Rationale:**
- Zero functional impact (nothing reads from it)
- Simplifies codebase (-335 lines)
- Better security (tenant isolation)
- Cloud-native architecture

**Action Items:**
1. ✅ Document decision (this file)
2. ⏳ Create cleanup PR
3. ⏳ Remove filesystem code
4. ⏳ Update architecture docs

---

## Appendix: Files Affected

### To Remove
- `backend/services/contract_validator.py` (335 lines)
- `backend/prompts/{agent_id}/` directories

### To Modify
- `backend/services/agent_service.py`
  - Remove `_save_contract_to_filesystem()` (lines 539-565)
  - Remove filesystem validation from `get_agent()` (lines 225-229)

### Tests to Update
- Remove filesystem assertions from agent creation tests

---

**Signed off by**: Code Quality Audit
**Review date**: 2025-11-05
