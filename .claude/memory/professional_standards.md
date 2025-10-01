# Professional Architecture Standards - PERMANENT MEMORY

## Core Principles

### 1. Single Entry Point
- **ONE main.py per application** - Never create main_simple.py, main_protocol_only.py, or any variants
- Entry point must be in the standard location: `backend/main.py` or `src/main.py`
- All application initialization happens in a single lifespan manager

### 2. Proper Directory Structure
```
project/
├── backend/              # Backend code
│   ├── main.py          # SINGLE entry point
│   ├── config.py        # Configuration
│   ├── database.py      # Database setup
│   ├── models/          # Data models
│   ├── routers/         # API routes
│   ├── services/        # Business logic
│   └── agents/          # Agent implementations
├── frontend/            # Frontend code
├── docs/                # ALL documentation
│   ├── architecture/    # Architecture docs
│   ├── setup/          # Setup guides
│   └── audit/          # Audit reports
├── tests/              # Test files
├── .env                # Environment config
├── README.md           # Project overview
└── CLAUDE.md           # Claude instructions
```

### 3. Documentation Organization
- **NO excessive markdown files in root** - Maximum 3-4 core files (README.md, CLAUDE.md, spec files)
- All other docs go in `docs/` with proper subdirectories
- Never create duplicate summary/implementation/status files
- Consolidate related information into single comprehensive docs

### 4. File Naming Conventions
- Use snake_case for Python: `session_manager.py`, `memory.py`
- Use kebab-case for docs: `streamlined-architecture.md`
- Never append suffixes like `_v2`, `_new`, `_old`, `_simple`, `_protocol_only`
- Update existing files instead of creating variants

### 5. Service Architecture
- One service per concern: `memory.py` (NOT memory.py + unified_memory_manager.py)
- Keep backward compatibility by updating existing interfaces
- Use dependency injection, not multiple implementations
- If refactoring, update the original file, don't create alternatives

### 6. Configuration Management
- Single `.env` file for all environment variables
- Single `config.py` for settings management
- No duplicate config files per environment
- Use environment variable to switch between dev/staging/prod

### 7. Database Migrations
- Use proper migration tools (Alembic for Python)
- Never create multiple schema files
- Version migrations sequentially
- One source of truth for schema

### 8. API Routing
- Organize routes by domain: `sessions.py`, `agents.py`, `therapy.py`
- Include all routers in main.py
- No duplicate route files or alternate APIs
- Use API versioning if breaking changes needed: `/api/v1/`, `/api/v2/`

### 9. Testing Structure
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── e2e/           # End-to-end tests
```
- Never create test files in root or scattered locations
- Group by test type, not by feature

### 10. Error Prevention Checklist

**Before creating any file, ask:**
- [ ] Does this file already exist? → Update it instead
- [ ] Is this a variant of an existing file? → Refactor the original
- [ ] Does this belong in a subdirectory? → Place it there
- [ ] Will this create confusion? → Don't create it
- [ ] Is this documentation? → Put in docs/

**Before creating documentation, ask:**
- [ ] Can this be added to existing docs? → Update existing
- [ ] Is this a duplicate summary? → Consolidate
- [ ] Will this clutter the root? → Use docs/
- [ ] Is this temporary debug info? → Don't commit it

## Anti-Patterns to NEVER Repeat

### ❌ NEVER DO:
1. Create `main_simple.py`, `main_v2.py`, `main_old.py` variants
2. Create multiple implementation summaries with timestamps
3. Create debug summary files in root
4. Create temporary test files that get committed
5. Rename core services (e.g., memory.py → unified_memory_manager.py)
6. Create documentation files for every change
7. Create alternate implementations instead of refactoring
8. Use generic names like `temp.py`, `test.py`, `new.py`
9. Create files outside established directory structure
10. Commit files like `nul`, empty files, or OS artifacts

### ✅ ALWAYS DO:
1. Update existing files instead of creating variants
2. Use proper directory structure from day one
3. Consolidate documentation into organized docs/
4. Follow established naming conventions
5. One entry point, one config, one truth
6. Refactor code, don't duplicate it
7. Use migrations for schema changes
8. Keep root directory clean (< 5 files)
9. Ask "Does this already exist?" before creating
10. Follow the principle: **"When in doubt, consolidate"**

## Enforcement

This is **permanent memory**. Every file creation, every refactor, every documentation update must adhere to these standards. No exceptions.

**Commit this to permanent memory**: Professional architecture is not optional—it is the foundation of maintainable, scalable software.
