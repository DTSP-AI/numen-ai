<!-- f745223c-247e-4db5-98bf-1b9143ec2e49 8a1130d5-e5de-430c-9901-915d99f52f89 -->
# Code Quality Analysis & Resolution Plan

## Objective

Systematically analyze the codebase to identify and resolve:

1. Placeholders/pseudocode/hypothetical code
2. Syntax errors
3. Redundant code
4. Overengineering or Stack 1st violations
5. Unused imports

## Analysis Categories

### 1. Placeholders & Pseudocode

**Known Issues Found:**

#### Issue 1.1: ElevenLabs Integration TODO (MEDIUM)

- **File:** `backend/agents/guide_agent/guide_agent.py:292`
- **Issue:** `# TODO: Integrate ElevenLabs SDK` with placeholder audio URLs
- **Status:** Audio service exists but not integrated in GuideAgent
- **Resolution:** Replace placeholder with `audio_service.synthesize_affirmation()` calls

#### Issue 1.2: GAS Rating System Placeholder (LOW)

- **File:** `backend/agents/guide_agent/guide_sub_agents/discovery_agent.py:54`
- **Issue:** `"gas_rating": None,  # TODO: Implement GAS rating system`
- **Status:** Intentional placeholder, doesn't break flow
- **Resolution:** Keep as-is (documented feature gap) OR implement basic GAS rating using LLM

#### Issue 1.3: Therapy Router Placeholder Response (MEDIUM)

- **File:** `backend/routers/therapy.py:101, 194`
- **Issue:** Placeholder text responses instead of actual agent calls
- **Status:** Router disabled, but has pseudocode
- **Resolution:** Either implement properly or remove placeholder code

#### Issue 1.4: ChatInterface LiveKit TODO (LOW)

- **File:** `frontend/src/components/ChatInterface.tsx:149`
- **Issue:** `// TODO: Implement LiveKit voice connection`
- **Status:** Feature gap
- **Resolution:** Implement or remove comment

#### Issue 1.5: Dashboard Q&A TODO (LOW)

- **File:** `frontend/src/app/dashboard/page.tsx:190`
- **Issue:** `// TODO: Implement Q&A flow with guide`
- **Status:** Feature gap
- **Resolution:** Implement or remove comment

### 2. Syntax Errors

**Files to Check:**

- All Python files in `backend/` for syntax errors
- All TypeScript files in `frontend/src/` for syntax errors
- Run `python -m py_compile` on all Python files
- Run TypeScript compiler check

**Known Issues:**

- None found in initial scan (affirmations.py compiles successfully)

### 3. Redundant Code

#### Issue 3.1: Duplicate Memory Manager Cache (MEDIUM)

- **File:** `backend/services/agent_service.py:27-74`
- **Issue:** `LRUMemoryCache` class exists, but also maintains `memory_managers` dict
- **Resolution:** Remove redundant `memory_managers` alias, use only cache

#### Issue 3.2: Redundant Temperature Defaults (LOW)

- **Files:** Multiple files set `temperature=0.7` as default
- **Issue:** Hardcoded values instead of using contract defaults
- **Resolution:** Use contract.configuration.temperature consistently

#### Issue 3.3: Duplicate Tenant ID Fallback Logic (LOW)

- **Files:** Multiple routers have identical tenant_id fallback code
- **Resolution:** Create shared helper function

### 4. Stack 1st Principle Violations

#### Issue 4.1: Audio Duration Calculation Bug (HIGH)

- **File:** `backend/services/audio_synthesis.py:205`
- **Issue:** `estimated_duration_seconds = (len(audio_url) * 60) // (150 * 5)` - calculates from URL length, not text
- **Violation:** Logic error, not stack violation
- **Resolution:** Fix calculation to use text length

#### Issue 4.2: Direct SQL Queries (MEDIUM)

- **Files:** Multiple routers use direct SQL instead of Supabase client methods
- **Status:** Current architecture uses asyncpg directly (acceptable per Stack 1st)
- **Resolution:** Document as acceptable pattern OR migrate to Supabase client

#### Issue 4.3: Redis References Removed (GOOD)

- **Status:** ✅ Already cleaned up - Redis removed, using PostgreSQL

### 5. Unused Imports

**Files to Analyze:**

- `backend/routers/intake.py` - Check `json` import usage
- `backend/routers/therapy.py` - Check all imports
- `backend/agents/guide_agent/guide_agent.py` - Check imports
- `backend/services/agent_service.py` - Check imports

**Analysis Method:**

- Use `grep` to find import statements
- Check if imported symbols are used in file
- Mark for deletion if unused
- Mark for implementation if logic is missing

## Resolution Strategy

### Phase 1: Critical Fixes (HIGH Priority)

1. Fix audio duration calculation bug (Issue 4.1)
2. Integrate ElevenLabs in GuideAgent (Issue 1.1)
3. Remove redundant memory manager code (Issue 3.1)

### Phase 2: Code Cleanup (MEDIUM Priority)

4. Remove redundant tenant_id fallback duplication (Issue 3.3)
5. Clean up therapy router placeholders (Issue 1.3)
6. Remove unused imports across codebase

### Phase 3: Feature Completeness (LOW Priority)

7. Implement GAS rating system (Issue 1.2) OR document as future feature
8. Implement LiveKit voice connection (Issue 1.4)
9. Implement Q&A flow (Issue 1.5)

## Implementation Details

### Resolution 1.1: Integrate ElevenLabs in GuideAgent

**File:** `backend/agents/guide_agent/guide_agent.py`

- Replace placeholder URLs with actual `audio_service.synthesize_affirmation()` calls
- Use agent's voice configuration from contract
- Handle errors gracefully

### Resolution 3.1: Remove Redundant Memory Cache

**File:** `backend/services/agent_service.py`

- Remove `self.memory_managers = self.memory_cache.cache` line
- Update all references to use `self.memory_cache` directly

### Resolution 4.1: Fix Audio Duration Calculation

**File:** `backend/services/audio_synthesis.py:205`

- Change from: `(len(audio_url) * 60) // (150 * 5)`
- Change to: Calculate from text length or actual audio duration
- Use: `len(text.split()) * 60 / 150` (words per minute estimate)

### Resolution: Unused Imports

- Create script to detect unused imports
- Remove confirmed unused imports
- Keep imports that are needed for type hints or future implementation

## Compliance Checks

All resolutions must:

- ✅ Use LangGraph for agent orchestration (no custom state machines)
- ✅ Use Mem0 for memory operations
- ✅ Use Supabase/PostgreSQL for database
- ✅ Use ElevenLabs for TTS
- ✅ Use FastAPI routers and Pydantic models
- ✅ Follow Agent Creation Standard patterns
- ✅ Maintain contract-first architecture

## Output Deliverables

1. **Code Quality Report** (`CODE_QUALITY_REPORT.md`)

- Detailed findings by category
- Severity levels (Critical, High, Medium, Low)
- File locations and line numbers

2. **Resolution Implementation**

- Fixed code files
- Removed redundant code
- Cleaned up imports
- Integrated placeholders

3. **Updated Documentation**

- Notes on intentional placeholders (GAS rating)
- Architecture decisions (direct SQL usage)
- Feature gaps documented

### To-dos

- [ ] Create backend/scripts/e2e_diagnostic.py with all test functions for environment, API endpoints, data flow, and known issue checks
- [ ] Add helper functions for API requests, database validation, and report generation
- [ ] Implement checks for documented breaking issues from BREAKING_ISSUES_RESOLUTION.md
- [ ] Add markdown report generation with detailed findings, severity levels, and recommendations
- [ ] Run the diagnostic tool to verify it works and produces accurate reports