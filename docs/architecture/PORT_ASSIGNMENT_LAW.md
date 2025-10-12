# Port Assignment Law - MANDATORY

**Date:** October 8, 2025
**Status:** ✅ LAW ENFORCED

---

## THE LAW

```
FRONTEND: 3003 or 3004
BACKEND:  8003 or 8004

NO EXCEPTIONS.
```

---

## Port Assignments

### Frontend (Next.js)
- **Primary Port:** `3003`
- **Fallback Port:** `3004`
- **Command:** `npm run dev` (auto-selects available port)
- **Access:** `http://localhost:3003`

### Backend (FastAPI)
- **Primary Port:** `8003`
- **Fallback Port:** `8004`
- **Command:** `uvicorn main:app --host 0.0.0.0 --port 8003 --reload`
- **Access:** `http://localhost:8003`
- **Docs:** `http://localhost:8003/docs`

---

## Why This Matters

**Convention Over Configuration:**
- Clear separation between frontend and backend
- Easy to remember: 3xxx = Frontend, 8xxx = Backend
- Avoids port conflicts
- Consistent across all environments

**Historical Context:**
- Default Next.js port: 3000 (conflicts with other projects)
- Default FastAPI/uvicorn port: 8000 (conflicts with common services)
- Solution: Offset by 3 for this project

---

## Environment Configuration

### Frontend `.env.local`

```bash
# Next.js runs on 3003 or 3004
NEXT_PUBLIC_API_URL=http://localhost:8003
```

### Backend `.env`

```bash
# FastAPI runs on 8003 or 8004
# No port config needed (specified in run command)
```

---

## Development Commands

### Start Frontend (Port 3003)

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
> next dev -p 3003
ready - started server on 0.0.0.0:3003
```

### Start Backend (Port 8003)

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

**Expected Output:**
```
INFO: Uvicorn running on http://0.0.0.0:8003 (Press CTRL+C to quit)
INFO: Application startup complete.
```

---

## Frontend API Configuration

### Current Files Using Backend URL

**File:** `frontend/src/components/AgentBuilder.tsx`

```typescript
// Line 142: Load voices
const response = await fetch("http://localhost:8003/api/voices")

// Line 155: Voice preview
const response = await fetch("http://localhost:8003/api/voices/preview", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ voice_id: voiceId, text: "..." })
})

// Line 188: Avatar generation
const response = await fetch("http://localhost:8003/api/avatar/generate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ prompt: avatarPrompt })
})

// Line 375: Create agent
const agentResponse = await fetch("http://localhost:8003/api/agents", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "x-tenant-id": "00000000-0000-0000-0000-000000000001",
    "x-user-id": userId
  },
  body: JSON.stringify(agentRequest)
})

// Line 398: Create session
const sessionResponse = await fetch("http://localhost:8003/api/sessions", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ user_id: userId, agent_id: agentId })
})
```

**Status:** ✅ All hardcoded to `localhost:8003`

---

## Port Conflict Resolution

### If Port 8003 is Occupied

```bash
# Check what's using the port
netstat -ano | findstr :8003

# Kill the process (Windows)
taskkill /PID <PID> /F

# Or use fallback port 8004
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

### If Port 3003 is Occupied

```bash
# Check what's using the port
netstat -ano | findstr :3003

# Kill the process (Windows)
taskkill /PID <PID> /F

# Or Next.js will auto-increment to 3004
npm run dev
```

---

## Compliance Checklist

Before committing code:

- [ ] Backend runs on `8003` or `8004` ONLY
- [ ] Frontend runs on `3003` or `3004` ONLY
- [ ] All `fetch()` calls use `http://localhost:8003` (or env var)
- [ ] No hardcoded `localhost:8000` anywhere
- [ ] No hardcoded `localhost:3000` anywhere
- [ ] README documents correct ports

---

## Violations

### ❌ NEVER DO THIS

```bash
# WRONG - Frontend on backend port
npm run dev -p 8003

# WRONG - Backend on frontend port
uvicorn main:app --port 3003

# WRONG - Using default ports
uvicorn main:app --port 8000
npm run dev  # (defaults to 3000)
```

### ✅ ALWAYS DO THIS

```bash
# RIGHT - Backend on 8003
uvicorn main:app --host 0.0.0.0 --port 8003 --reload

# RIGHT - Frontend on 3003
npm run dev -p 3003
```

---

## Production Deployment

**Note:** This port law applies to **local development only**.

**Production ports:**
- Frontend: Standard HTTP (80) or HTTPS (443)
- Backend: Behind reverse proxy (nginx/traefik)
- No direct port exposure

---

## Summary

```
┌─────────────────────────────────────────┐
│  DEVELOPMENT PORT ASSIGNMENTS           │
├─────────────────────────────────────────┤
│  Frontend (Next.js)                     │
│    Primary:  3003                       │
│    Fallback: 3004                       │
├─────────────────────────────────────────┤
│  Backend (FastAPI)                      │
│    Primary:  8003                       │
│    Fallback: 8004                       │
└─────────────────────────────────────────┘

THE LAW: 3xxx = Frontend, 8xxx = Backend
```

**Last Updated:** October 8, 2025

---

**THE LAW IS ABSOLUTE. THE LAW IS ENFORCED. ✅**
