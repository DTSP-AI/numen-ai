# STACK 1ST PRINCIPLES GUARDRAIL

**Project:** HypnoAgent / Affirmation Application
**Purpose:** Ensure all development adheres to the approved technology stack
**Last Updated:** 2025-01-15

---

## TECHNOLOGY STACK - NON-NEGOTIABLE

### **Agent Orchestration / Behavior / Tools**
- **PRIMARY:** LangGraph (state machine, multi-agent workflows)
- **SECONDARY:** LangChain (tool integration, chains)
- **FORBIDDEN:** Custom orchestration, Crew AI, AutoGen, other frameworks

**Rules:**
- All agent workflows MUST use LangGraph StateGraph
- Agent tools MUST be LangChain-compatible
- NO custom orchestration logic outside LangGraph
- Agent state MUST be managed through typed dictionaries

### **Agent STT/TTS (Voice)**
- **VOICE INFRASTRUCTURE:** LiveKit (WebRTC rooms, real-time streaming)
- **SPEECH-TO-TEXT:** Deepgram (STT)
- **TEXT-TO-SPEECH:** ElevenLabs (TTS)
- **FORBIDDEN:** Twilio voice, AWS Polly, Google TTS, direct WebRTC

**Rules:**
- All voice features MUST use LiveKit rooms
- STT MUST use Deepgram API
- TTS MUST use ElevenLabs API
- NO direct browser WebRTC without LiveKit

### **Agent/User Memory & Infrastructure**
- **MEMORY:** Mem0 AI (user/agent memory, context retention)
- **DATABASE:** Supabase (PostgreSQL with RLS)
- **VECTOR STORE:** Supabase pgvector extension
- **FORBIDDEN:** Redis (removed), custom memory solutions, Pinecone, Chroma

**Rules:**
- All memory operations MUST use Mem0 SDK
- Database access MUST use Supabase client
- Vector storage MUST use Supabase pgvector
- NO Redis usage (deprecated)
- Multi-tenancy MUST use Supabase RLS policies

### **Frontend**
- **FRAMEWORK:** React (with TypeScript)
- **STYLING:** Tailwind CSS
- **ANIMATIONS:** Framer Motion
- **STATE:** React Context API or Zustand (lightweight)
- **FORBIDDEN:** Vue, Angular, Bootstrap, jQuery animations

**Rules:**
- All UI MUST use Tailwind utility classes
- Animations MUST use Framer Motion
- NO inline styles (except dynamic Framer Motion props)
- Components MUST be functional (no class components)

### **Backend**
- **FRAMEWORK:** FastAPI (Python 3.11+)
- **AUTH:** JWT tokens (implemented in backend/services/auth.py)
- **VALIDATION:** Pydantic V2
- **FORBIDDEN:** Flask, Django, Express.js

**Rules:**
- All endpoints MUST use FastAPI routers
- Request/response MUST use Pydantic models
- Auth MUST use JWT dependency injection
- NO session-based auth

---

## DECISION TREE: WHEN TO USE WHAT

### "I need to add agent behavior"
→ Use LangGraph StateGraph + LangChain tools
→ See: `backend/graph/graph.py`, `backend/agents/guide_agent/`

### "I need voice features"
→ Use LiveKit rooms + Deepgram STT + ElevenLabs TTS
→ See: `backend/routers/therapy.py` (voice endpoints)

### "I need to store user data"
→ Use Mem0 for memory, Supabase for persistent data
→ See: `backend/memoryManager/`, `backend/database.py`

### "I need UI animations"
→ Use Framer Motion with Tailwind
→ See: `frontend/src/components/`

### "I need authentication"
→ Use JWT tokens (backend/services/auth.py)
→ Frontend: Store token, send in Authorization header

---

## FORBIDDEN PATTERNS

### ❌ DO NOT:
1. **Use Redis** - Removed from architecture
2. **Bypass LangGraph** - All agent logic goes through StateGraph
3. **Custom WebRTC** - Use LiveKit exclusively
4. **Hardcode tenant IDs** - Use JWT-extracted user_id
5. **Skip Mem0** - Use it for all memory operations
6. **Inline styles** - Use Tailwind classes
7. **Session auth** - Use JWT tokens only
8. **SQL queries** - Use Supabase client methods
9. **Custom memory** - Use Mem0 SDK
10. **Non-LangChain tools** - Wrap external APIs in LangChain tools

---

## COMPLIANCE CHECKLIST

Before merging any PR, verify:

- [ ] Agent logic uses LangGraph StateGraph
- [ ] Voice features use LiveKit/Deepgram/ElevenLabs
- [ ] Memory uses Mem0 SDK
- [ ] Database uses Supabase client
- [ ] Frontend uses React + Tailwind + Framer Motion
- [ ] Auth uses JWT tokens
- [ ] No Redis references
- [ ] No hardcoded tenant IDs
- [ ] Pydantic models for all API contracts
- [ ] Multi-tenant RLS enforced

---

## ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────┐
│              FRONTEND (React)                   │
│  Tailwind CSS + Framer Motion + JWT Auth       │
└───────────────────┬─────────────────────────────┘
                    │ REST API (JWT in headers)
┌───────────────────▼─────────────────────────────┐
│           BACKEND (FastAPI)                     │
│  ┌─────────────────────────────────────────┐   │
│  │   LangGraph StateGraph (Orchestration)  │   │
│  │   ├─ GuideAgent (intake, therapy)       │   │
│  │   ├─ AffirmationAgent                   │   │
│  │   └─ ProtocolAgent                      │   │
│  └──────────────┬──────────────────────────┘   │
│                 │                               │
│  ┌──────────────▼──────────────────────────┐   │
│  │  LangChain Tools (integrations)         │   │
│  └──────────────┬──────────────────────────┘   │
└─────────────────┼─────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼────┐  ┌────▼─────┐  ┌───▼──────┐
│  Mem0  │  │ Supabase │  │ LiveKit  │
│   AI   │  │ Postgres │  │ + STT/TTS│
│ Memory │  │ pgvector │  │ Deepgram │
│        │  │   RLS    │  │ 11Labs   │
└────────┘  └──────────┘  └──────────┘
```

---

## VIOLATIONS: WHAT TO DO

If you find code that violates this guardrail:

1. **Flag immediately** - Do not merge
2. **Document the violation** - Note file + line number
3. **Propose fix** - Suggest Stack 1st Principles alternative
4. **Escalate if unsure** - Ask before making architectural changes

---

## UPDATES TO THIS GUARDRAIL

This document is **IMMUTABLE** unless approved by project lead.

To propose changes:
1. Create issue titled "GUARDRAIL CHANGE: [description]"
2. Provide justification for deviation
3. Wait for explicit approval
4. Update this document with change log entry

---

## CHANGE LOG

| Date       | Change                          | Reason                    |
|------------|---------------------------------|---------------------------|
| 2025-01-15 | Initial guardrail created       | E2E audit revealed drift |
