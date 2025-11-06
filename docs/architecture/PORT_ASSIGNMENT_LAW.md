# Port Assignment Law
**Status**: ENFORCED
**Last Updated**: 2025-01-15

---

## Overview

This document defines the **immutable port assignments** for the HypnoAgent application. These ports are hardcoded in the codebase and must not be changed without updating all references.

---

## Port Allocation Table

| Service | Primary Port | Fallback Port | Protocol | Status |
|---------|--------------|---------------|----------|--------|
| **Backend (FastAPI)** | 8003 | 8004 | HTTP | Required |
| **Frontend (Next.js)** | 3003 | 3004 | HTTP | Required |
| **Supabase (Local)** | 54321 | - | HTTP | Optional |
| **Supabase DB (Local)** | 54322 | - | PostgreSQL | Optional |
| **PostgreSQL (Local)** | 5432 | - | PostgreSQL | Deprecated |
| **Redis (Local)** | 6379 | - | TCP | Deprecated |
| **Qdrant (Local)** | 6333 | - | HTTP | Deprecated |

---

## Port Assignment Rules

### 1. Backend (FastAPI) - Ports 8003-8004

**Primary**: 8003
**Fallback**: 8004

**Enforcement Location:**
```python
# backend/main.py:212
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,  # HARDCODED - DO NOT CHANGE
        reload=settings.environment == "development"
    )
```

**CORS Configuration:**
```python
# backend/main.py:90
allow_origins=[
    "http://localhost:3000",  # Legacy
    "http://localhost:3001",  # Legacy
    "http://localhost:3002",  # Legacy
    "http://localhost:3003"   # Current frontend port
]
```

**Why 8003?**
- Port 8000-8002 reserved for other local services
- 8003 is the standard port for HypnoAgent backend
- All documentation references this port
- All scripts reference this port

**Startup Command:**
```bash
# Correct
uvicorn main:app --host 0.0.0.0 --port 8003 --reload

# Incorrect - DO NOT USE
uvicorn main:app  # Defaults to 8000
```

---

### 2. Frontend (Next.js) - Ports 3003-3004

**Primary**: 3003
**Fallback**: 3004

**Enforcement Location:**
```javascript
// frontend/start-dev.js:6
const PREFERRED_PORTS = [3003, 3004];
```

**API Configuration:**
```typescript
// frontend/src/lib/api.ts:1
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003'
```

**Why 3003?**
- Port 3000-3002 reserved for other Next.js projects
- 3003 is the standard port for HypnoAgent frontend
- Matches backend CORS configuration
- Auto-recovers if port occupied (tries 3004)

**Startup Command:**
```bash
# Correct (automatic port selection)
npm run dev  # Uses start-dev.js

# Manual (if needed)
npm run dev:direct -- -p 3003
```

**Port Selection Logic:**
1. Check if 3003 is available → Use 3003
2. If 3003 occupied, check 3004 → Use 3004
3. If both occupied, kill process on 3003 → Use 3003

---

### 3. Supabase Local (Docker) - Ports 54321-54322

**Supabase Studio**: 54321 (HTTP)
**PostgreSQL**: 54322 (TCP)

**Why Supabase Local?**
- For developers without Supabase cloud accounts
- Full local development environment
- pgvector extension included
- Replaces local PostgreSQL setup

**Startup Command:**
```bash
# Using Supabase CLI
supabase start

# Studio: http://localhost:54321
# Database: postgresql://postgres:postgres@localhost:54322/postgres
```

**Connection String:**
```bash
# Local Supabase
SUPABASE_DB_URL=postgresql://postgres:postgres@localhost:54322/postgres

# Supabase Cloud (production)
SUPABASE_DB_URL=postgresql://postgres.xxx:[PASSWORD]@xxx.pooler.supabase.com:6543/postgres
```

**Note:** Port 54322 is Supabase's default for local PostgreSQL. Do not use standard port 5432 to avoid conflicts.

---

### 4. Deprecated Services (No Longer Used)

#### PostgreSQL Local (5432) - DEPRECATED
**Status**: ❌ No longer used
**Reason**: Replaced by Supabase (cloud or local)
**Migration**: Use Supabase cloud or `supabase start` for local

#### Redis (6379) - DEPRECATED
**Status**: ❌ No longer used
**Reason**: Replaced by PostgreSQL sessions table
**Migration**: Sessions stored in `sessions` table in PostgreSQL

#### Qdrant (6333) - DEPRECATED
**Status**: ❌ No longer used
**Reason**: Replaced by Supabase pgvector + Mem0
**Migration**:
- Vector search → Supabase pgvector
- Semantic memory → Mem0 cloud

**docker-compose.yml Status:**
The existing `docker-compose.yml` contains Redis and Qdrant services but these are **deprecated** and should not be used. The file is retained for reference only.

---

## Environment Variable Configuration

### Backend (.env)
```bash
# API URL configuration (not needed - backend doesn't call itself)
# If needed for internal services:
# BACKEND_URL=http://localhost:8003

# No PORT variable needed - hardcoded in main.py
```

### Frontend (.env.local)
```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8003

# No PORT variable needed - managed by start-dev.js
```

---

## Port Conflict Resolution

### If Port 8003 (Backend) is Occupied

**Check what's using it:**
```bash
# Windows
netstat -ano | findstr :8003

# Mac/Linux
lsof -i :8003
```

**Kill the process:**
```bash
# Windows
taskkill /PID <PID> /F

# Mac/Linux
kill -9 <PID>
```

**Or use different port (update all references):**
```bash
# Start backend on 8004
uvicorn main:app --host 0.0.0.0 --port 8004 --reload

# Update frontend API URL
export NEXT_PUBLIC_API_URL=http://localhost:8004

# Update CORS in backend/main.py
allow_origins=["http://localhost:3003", "http://localhost:3004"]
```

### If Port 3003 (Frontend) is Occupied

**Automatic Resolution:**
The `start-dev.js` script automatically:
1. Detects port 3003 is occupied
2. Tries port 3004
3. If both occupied, kills process on 3003
4. Starts on available port

**Manual Resolution:**
```bash
# Check what's using it
# Windows
netstat -ano | findstr :3003

# Mac/Linux
lsof -i :3003

# Kill the process
# Windows
taskkill /PID <PID> /F

# Mac/Linux
kill -9 <PID>
```

---

## Quick Start Port Verification

### Step 1: Check Backend
```bash
curl http://localhost:8003/health

# Expected:
# {"status": "healthy", "version": "1.0.0"}
```

### Step 2: Check Frontend
```bash
curl http://localhost:3003

# Expected:
# HTML response from Next.js
```

### Step 3: Check Supabase Local (if using)
```bash
curl http://localhost:54321

# Expected:
# Supabase Studio UI
```

---

## Port Testing Matrix

| Test | Command | Expected Result |
|------|---------|----------------|
| Backend Health | `curl http://localhost:8003/health` | `{"status": "healthy"}` |
| Backend Docs | Open `http://localhost:8003/docs` | Swagger UI |
| Frontend | Open `http://localhost:3003` | Next.js app |
| Supabase Studio | Open `http://localhost:54321` | Supabase UI |

---

## Integration with Scripts

### Install Script (scripts/install.bat, scripts/install.sh)
- Does not modify ports
- Copies .env.example to .env
- User must verify ports in .env

### Dev Script (scripts/dev.bat, scripts/dev.sh)
```bash
# Starts backend on port 8003
cd backend && uvicorn main:app --host 0.0.0.0 --port 8003 --reload &

# Starts frontend on port 3003/3004 (automatic)
cd frontend && npm run dev
```

---

## Compliance Checklist

When modifying the codebase, ensure:

- [ ] Backend always starts on port 8003
- [ ] Frontend prefers port 3003, falls back to 3004
- [ ] CORS includes `http://localhost:3003`
- [ ] API_URL defaults to `http://localhost:8003`
- [ ] Health check accessible at `http://localhost:8003/health`
- [ ] Documentation references correct ports
- [ ] Scripts use correct ports
- [ ] No hardcoded localhost:3000 or localhost:8000

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User Browser                                                │
│  http://localhost:3003                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14)                                       │
│  Port: 3003 (primary) / 3004 (fallback)                     │
│  Protocol: HTTP                                              │
└────────────────┬────────────────────────────────────────────┘
                 │ API Calls
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                           │
│  Port: 8003                                                  │
│  Protocol: HTTP                                              │
│  Endpoints: /health, /api/*, /docs                          │
└────────────────┬────────────────────────────────────────────┘
                 │
      ┌──────────┼──────────┐
      ▼          ▼          ▼
   ┌─────┐   ┌──────┐   ┌─────┐
   │OpenAI│   │Supabase│   │Mem0│
   │ API │   │Cloud or│   │Cloud│
   │     │   │ Local  │   │     │
   └─────┘   │54321/2 │   └─────┘
             └────────┘
```

---

## Supabase Local Setup (Optional)

For developers who want to run everything locally:

### Install Supabase CLI
```bash
# Mac
brew install supabase/tap/supabase

# Windows (Scoop)
scoop install supabase

# Or npm
npm install -g supabase
```

### Start Supabase Local
```bash
# In project root
supabase init  # First time only
supabase start

# Output shows:
# API URL: http://localhost:54321
# DB URL: postgresql://postgres:postgres@localhost:54322/postgres
# Studio URL: http://localhost:54321
```

### Update .env
```bash
# Use local Supabase
SUPABASE_DB_URL=postgresql://postgres:postgres@localhost:54322/postgres
SUPABASE_URL=http://localhost:54321
SUPABASE_KEY=<anon-key-from-supabase-start-output>
```

### Stop Supabase Local
```bash
supabase stop
```

---

## Port Change Procedure (Emergency Only)

If you absolutely must change ports (not recommended):

### 1. Update Backend Port
```python
# backend/main.py:212
port=8003  # Change to new port
```

### 2. Update CORS
```python
# backend/main.py:90
allow_origins=["http://localhost:3003"]  # Update if frontend port changes
```

### 3. Update Frontend API URL
```typescript
// frontend/src/lib/api.ts:1
const API_URL = 'http://localhost:NEW_PORT'
```

### 4. Update Frontend Preferred Ports
```javascript
// frontend/start-dev.js:6
const PREFERRED_PORTS = [NEW_PORT, NEW_PORT + 1];
```

### 5. Update All Documentation
- QUICK_START.md
- LOCAL_SETUP_GUIDE.md
- E2E_TESTING_READINESS_REPORT.md
- This file (PORT_ASSIGNMENT_LAW.md)

### 6. Update Scripts
- scripts/dev.bat
- scripts/dev.sh
- scripts/install.bat
- scripts/install.sh

### 7. Notify Team
Create a notification about the port change and update all developer environments.

---

## Frequently Asked Questions

**Q: Why not use default ports (3000 for Next.js, 8000 for FastAPI)?**
A: To avoid conflicts with other common development tools and allow multiple projects to run simultaneously.

**Q: Can I use environment variables for ports?**
A: Not recommended. Hardcoded ports ensure consistency across environments and prevent configuration drift.

**Q: What if I'm already using port 8003?**
A: Use port conflict resolution procedures above. Temporarily use 8004 and update configuration.

**Q: Why does frontend have two ports but backend only one?**
A: Frontend auto-recovers with fallback port. Backend typically runs as single instance.

**Q: Do I need Supabase local or can I use cloud?**
A: Either works. Cloud is recommended for simplicity. Local is for offline development.

**Q: What happened to Redis and Qdrant?**
A: Deprecated in stack-first refactor. Redis → PostgreSQL sessions, Qdrant → Supabase pgvector + Mem0.

---

## Summary

| Component | Port | Required | Alternative |
|-----------|------|----------|-------------|
| Backend | 8003 | Yes | 8004 (emergency) |
| Frontend | 3003 | Yes | 3004 (auto-fallback) |
| Supabase Local | 54321/54322 | No | Cloud Supabase |
| PostgreSQL | 5432 | No | Use Supabase |
| Redis | 6379 | No | Deprecated |
| Qdrant | 6333 | No | Deprecated |

**Golden Rule**: Never change ports unless absolutely necessary, and if you do, update ALL references.

---

**Last Updated**: 2025-01-15
**Enforced By**: Code, Scripts, Documentation
**Compliance**: Mandatory for all developers
