# Directory Structure & E2E Pipeline Report
**Generated:** 2025-10-03
**Version:** 2.0.0
**Status:** Production Architecture

---

## Executive Summary

This document provides a complete technical overview of the Affirmation Application's directory structure, end-to-end data flow, API architecture, and service integrations. The application is a full-stack AI-powered manifestation platform with voice synthesis, real-time chat, and personalized agent creation.

---

## Table of Contents

1. [Directory Structure](#1-directory-structure)
2. [E2E Pipeline Flow](#2-e2e-pipeline-flow)
3. [API Endpoints Map](#3-api-endpoints-map)
4. [Service Dependencies](#4-service-dependencies)
5. [Data Flow Diagrams](#5-data-flow-diagrams)
6. [Integration Points](#6-integration-points)

---

## 1. Directory Structure

### Root Structure

```
AffirmationApplication/
├── backend/                    # FastAPI + LangGraph backend
├── frontend/                   # Next.js 14 frontend
├── docs/                       # Architecture & documentation
├── infrastructure/             # Docker & deployment configs
├── .env                        # Environment variables
├── .gitignore
├── README.md
└── DESIGN_SYSTEM_LOCK.md      # Frontend design specifications
```

---

### Backend Architecture (`/backend`)

```
backend/
├── main.py                     # FastAPI app entry point
├── config.py                   # Environment configuration
├── database.py                 # PostgreSQL connection pool
│
├── agents/                     # LangGraph agent implementations
│   ├── __init__.py
│   ├── manifestation_protocol_agent.py    # Primary protocol generator
│   ├── therapy_agent.py                   # Therapy session handler
│   ├── intake_agent.py                    # User intake flow
│   ├── intake_agent_v2.py                 # Enhanced intake
│   └── affirmation_agent.py               # Affirmation generation
│
├── routers/                    # FastAPI route handlers
│   ├── __init__.py
│   ├── agents.py              # Agent CRUD (✅ PRIMARY)
│   ├── avatar.py              # Avatar generation/upload
│   ├── voices.py              # ElevenLabs voice selection
│   ├── chat.py                # Real-time chat sessions
│   ├── livekit.py             # LiveKit voice integration
│   ├── sessions.py            # Session management
│   ├── affirmations.py        # Affirmation CRUD
│   ├── protocols.py           # Protocol management
│   ├── dashboard.py           # Dashboard data aggregation
│   ├── therapy.py             # Therapy endpoints
│   └── contracts.py           # Contract operations
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── agent_service.py       # ✅ CORE: Agent lifecycle management
│   ├── audio_synthesis.py     # ElevenLabs TTS wrapper
│   ├── elevenlabs_service.py  # Voice synthesis service
│   ├── deepgram_service.py    # Speech-to-Text service
│   ├── livekit_service.py     # Real-time voice rooms
│   ├── memory.py              # Memory management
│   ├── unified_memory_manager.py  # Centralized memory
│   └── session_manager.py     # Session state handler
│
├── models/                     # Pydantic data models
│   ├── __init__.py
│   ├── agent.py               # ✅ Agent contract schemas
│   └── schemas.py             # Request/response schemas
│
├── scripts/                    # Utility scripts
│   ├── seed_data.py           # Database seeding
│   ├── test_supabase_connection.py
│   └── purge_test_agents.py   # Cleanup utility
│
├── backend/                    # Runtime directories
│   ├── audio_files/           # Generated TTS audio (mounted as /audio)
│   ├── avatars/               # Generated/uploaded avatars (mounted as /avatars)
│   └── prompts/               # Per-agent JSON contracts
│       └── {agent_id}/
│           ├── agent_contract.json
│           └── system_prompt.txt
│
└── test_*.py                   # Integration tests
```

**Key Backend Files:**

| File | Purpose | Lines | Critical |
|------|---------|-------|----------|
| `main.py` | FastAPI app, CORS, router registration | 106 | ✅ |
| `routers/agents.py` | Agent CRUD API, chat endpoint | 580 | ✅ |
| `services/agent_service.py` | Agent lifecycle, memory init, contract storage | 657 | ✅ |
| `agents/manifestation_protocol_agent.py` | LangGraph protocol generation | ~500 | ✅ |
| `routers/voices.py` | Voice discovery & preview | ~150 | ✅ |
| `routers/avatar.py` | Avatar generation (DALL·E 3) | ~120 | ⚠️ NEW |
| `services/audio_synthesis.py` | ElevenLabs TTS integration | ~200 | ✅ |

---

### Frontend Architecture (`/frontend`)

```
frontend/
├── package.json
├── tailwind.config.ts          # Tailwind + Kurzgesagt theme
├── next.config.ts              # Next.js configuration
│
├── public/                     # Static assets
│
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Landing page
│   │   ├── globals.css         # ✅ LOCKED: Global styles
│   │   │
│   │   ├── about/
│   │   │   └── page.tsx
│   │   ├── contact/
│   │   │   └── page.tsx
│   │   │
│   │   ├── create-agent/       # ✅ PRIMARY: Agent builder
│   │   │   └── page.tsx
│   │   │
│   │   ├── dashboard/          # ✅ PRIMARY: User dashboard
│   │   │   └── page.tsx
│   │   │
│   │   ├── chat/               # Real-time agent chat
│   │   │   ├── page.tsx        # Chat listing
│   │   │   └── [agentId]/
│   │   │       ├── page.tsx    # Active chat interface
│   │   │       └── layout.tsx
│   │   │
│   │   ├── affirmations/
│   │   │   └── page.tsx
│   │   │
│   │   └── creation/           # Legacy affirmation creation
│   │       └── page.tsx
│   │
│   ├── components/             # React components
│   │   ├── AgentBuilder.tsx           # ✅ LOCKED: 9-step wizard
│   │   ├── IntakeForm.tsx             # User discovery questions
│   │   ├── ChatInterface.tsx          # Real-time chat UI
│   │   ├── ChatSidebar.tsx            # Thread navigation
│   │   ├── MessageBubble.tsx          # Chat message display
│   │   ├── VoiceControls.tsx          # LiveKit voice controls
│   │   ├── AgentCard.tsx              # Agent preview card
│   │   ├── AffirmationCard.tsx        # Affirmation display
│   │   ├── ScriptPlayer.tsx           # Audio playback
│   │   ├── Navigation.tsx             # Site navigation
│   │   ├── HorizontalTabs.tsx         # Dashboard tabs
│   │   ├── DashboardStatCard.tsx      # Stats display
│   │   ├── ProtocolSummary.tsx        # Protocol preview
│   │   ├── PlanReview.tsx             # Plan consent UI
│   │   ├── DiscoveryQuestions.tsx     # Discovery flow
│   │   ├── TherapySession.tsx         # Therapy interface
│   │   ├── ScheduleCalendar.tsx       # Content scheduling
│   │   │
│   │   └── ui/                        # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── input.tsx
│   │       ├── label.tsx
│   │       ├── select.tsx
│   │       └── textarea.tsx
│   │
│   ├── lib/
│   │   ├── api.ts              # API client utilities
│   │   └── utils.ts            # Helper functions
│   │
│   └── types/
│       └── index.ts            # TypeScript type definitions
│
└── DESIGN_SYSTEM_LOCK.md       # ✅ CRITICAL: Design specifications
```

**Key Frontend Files:**

| File | Purpose | Lines | Critical |
|------|---------|-------|----------|
| `components/AgentBuilder.tsx` | 9-step agent creation wizard | ~1100 | ✅ |
| `app/dashboard/page.tsx` | Unified dashboard with tabs | ~400 | ✅ |
| `app/chat/[agentId]/page.tsx` | Live chat interface | ~600 | ✅ |
| `components/ChatInterface.tsx` | Chat UI with voice controls | ~500 | ✅ |
| `app/globals.css` | Kurzgesagt theme, glassmorphism | 130 | ✅ LOCKED |
| `DESIGN_SYSTEM_LOCK.md` | Design specifications | 350 | ✅ LOCKED |

---

### Documentation (`/docs`)

```
docs/
├── architecture/
│   ├── E2E_PIPELINE_REPORT.md          # ✅ Existing E2E docs
│   ├── CurrentCodeBasePrompt.md        # Project context for LLMs
│   ├── AUDIT_REPORT.md                 # Production readiness audit
│   ├── PRODUCTION_READINESS_AUDIT.yaml # Structured audit data
│   ├── PRODUCTION_READINESS_SUMMARY.md # Executive summary
│   ├── REMEDIATION_CHECKLIST.md        # Fix checklist
│   ├── ULTIMATE-11LABS-KB.md           # ElevenLabs integration guide
│   └── DIRECTORY_STRUCTURE_REPORT.md   # ⬅️ THIS FILE
│
├── audit/                              # Audit artifacts
└── setup/                              # Setup guides
```

---

## 2. E2E Pipeline Flow

### User Journey: Agent Creation → Affirmation Generation → Chat

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FULL E2E PIPELINE                          │
└─────────────────────────────────────────────────────────────────────┘

[1] USER LANDS ON HOMEPAGE
    ↓
    frontend/src/app/page.tsx
    ↓
    "Get Started" → /create-agent

[2] DISCOVERY QUESTIONS (Optional)
    ↓
    frontend/src/components/IntakeForm.tsx
    ↓
    localStorage.setItem('intakeData', {goals, tone, session_type})
    ↓
    Navigate to: /create-agent?userId={userId}

[3] AGENT BUILDER (9-Step Wizard)
    ↓
    frontend/src/components/AgentBuilder.tsx
    ├── Step 1: Identity & Purpose
    │   - Name, Roles (1-3), Mission
    ├── Step 2: Core Attributes (4 Traits)
    │   - Confidence, Empathy, Creativity, Discipline
    ├── Step 3: Voice Selection
    │   - GET /api/voices → 8 curated ElevenLabs voices
    │   - POST /api/voices/preview → Audio preview
    ├── Step 4: Avatar Creation
    │   - POST /api/avatar/generate (DALL·E 3)
    │   - POST /api/avatar/upload (Custom image)
    ├── Step 5: Communication Style
    │   - Interaction styles (1-3)
    ├── Step 6: Manifestation Focus Areas
    ├── Step 7: Philosophy & Approach
    ├── Step 8: Advanced Settings
    │   - LLM config, memory settings
    └── Step 9: Review & Create

[4] AGENT CREATION
    ↓
    POST /api/agents
    {
      name, type, identity, traits, configuration, voice, tags
    }
    ↓
    backend/routers/agents.py:create_agent()
    ↓
    backend/services/agent_service.py:create_agent()
    ├── INSERT INTO agents (contract JSONB)
    ├── Initialize memory namespace
    ├── Save backend/prompts/{agent_id}/agent_contract.json
    ├── Save backend/prompts/{agent_id}/system_prompt.txt
    └── CREATE default thread

    Response:
    {
      "status": "success",
      "agent": {
        "id": "uuid",
        "name": "...",
        "contract": {...}
      }
    }

[5] SESSION CREATION
    ↓
    POST /api/sessions
    {
      user_id, agent_id,
      metadata: { intake_data: {...} }
    }
    ↓
    backend/routers/sessions.py
    ↓
    INSERT INTO sessions (agent_id, session_data JSONB)

[6] DASHBOARD REDIRECT
    ↓
    Navigate to: /dashboard?agentId={agentId}&sessionId={sessionId}&success=true
    ↓
    frontend/src/app/dashboard/page.tsx
    ├── Display success message
    ├── Show agent voice configuration
    ├── Tabs: Overview | Affirmations | Scripts | Schedule
    └── Action: "Generate Affirmations"

[7] AFFIRMATION GENERATION (On-Demand)
    ↓
    POST /api/affirmations/generate
    {
      user_id, agent_id, session_id, count: 10
    }
    ↓
    backend/routers/affirmations.py
    ↓
    agents/manifestation_protocol_agent.py (LangGraph)
    ├── analyze_goal
    ├── design_daily_practices
    ├── create_affirmations
    ├── generate_visualizations
    ├── define_metrics
    ├── identify_obstacles
    ├── set_checkpoints
    └── compile_protocol

    Response:
    {
      "affirmations": [10 items],
      "protocol_summary": {
        "daily_practices": 4,
        "visualizations": 3,
        "success_metrics": 8,
        "checkpoints": 5
      }
    }
    ↓
    UPDATE sessions SET session_data = {manifestation_protocol}
    INSERT INTO affirmations (text, category, tags)

[8] AUDIO SYNTHESIS (On-Demand)
    ↓
    POST /api/affirmations/{id}/synthesize
    ↓
    backend/services/audio_synthesis.py
    ↓
    ElevenLabs API (TTS)
    ├── Use agent.contract.voice.voice_id
    ├── Generate audio file
    └── Save to backend/audio_files/{affirmation_id}.mp3
    ↓
    UPDATE affirmations SET audio_url = "/audio/{affirmation_id}.mp3"

[9] REAL-TIME CHAT (Active Agent Page)
    ↓
    Navigate to: /chat/{agentId}
    ↓
    frontend/src/app/chat/[agentId]/page.tsx
    ├── ChatInterface.tsx
    ├── ChatSidebar.tsx (thread list)
    ├── MessageBubble.tsx (message display)
    └── VoiceControls.tsx (LiveKit integration)

    User sends message:
    ↓
    POST /api/chat/sessions/{session_id}/messages
    {
      user_id, agent_id, message: "I want to build confidence"
    }
    ↓
    backend/routers/chat.py:send_chat_message()
    ↓
    backend/services/agent_service.py:process_chat_message()
    ├── Load agent contract
    ├── Get conversation history from memory
    ├── Process through LangGraph (future: use manifestation_protocol_agent)
    ├── INSERT INTO messages (user message)
    ├── INSERT INTO messages (agent response)
    └── Optional: Generate audio for agent response
    ↓
    Response:
    {
      "user_message": {...},
      "agent_response": {
        "content": "...",
        "audio_url": "/audio/{message_id}.mp3"
      }
    }
    ↓
    Frontend plays audio via <audio> element

[10] VOICE INTERACTION (LiveKit - Future)
    ↓
    POST /api/livekit/token
    ↓
    backend/routers/livekit.py
    ↓
    Create LiveKit room
    ├── Deepgram STT → Transcription
    ├── Agent processes in real-time
    ├── ElevenLabs TTS → Audio stream
    └── LiveKit → User audio playback
```

---

## 3. API Endpoints Map

### Complete API Reference

**Base URL:** `http://localhost:8000`

| Method | Endpoint | Purpose | Request | Response |
|--------|----------|---------|---------|----------|
| **AGENTS** |
| POST | `/api/agents` | Create agent from contract | AgentCreateRequest | `{status, agent}` |
| GET | `/api/agents` | List all agents (tenant-filtered) | Query params: status, type, limit, offset | `{total, agents[]}` |
| GET | `/api/agents/{agent_id}` | Get agent details | - | `{id, name, contract, ...}` |
| PATCH | `/api/agents/{agent_id}` | Update agent contract | AgentUpdateRequest | `{status, agent}` |
| DELETE | `/api/agents/{agent_id}` | Archive agent (soft delete) | - | `{status, message}` |
| POST | `/api/agents/{agent_id}/chat` | Chat with agent | `{message, thread_id?, metadata?}` | `{thread_id, response, metadata}` |
| GET | `/api/agents/{agent_id}/threads` | Get agent conversation threads | Query: limit | `{threads[]}` |
| GET | `/api/agents/{agent_id}/versions` | Get agent version history | Query: limit | `{versions[]}` |
| **VOICES** |
| GET | `/api/voices` | Get available ElevenLabs voices | - | `{total, voices[8]}` |
| POST | `/api/voices/preview` | Generate voice preview audio | `{voice_id, text}` | Audio file (audio/mpeg) |
| **AVATAR** |
| POST | `/api/avatar/generate` | Generate avatar with DALL·E 3 | `{prompt, style, size}` | `{avatar_url}` |
| POST | `/api/avatar/upload` | Upload custom avatar | FormData: file | `{avatar_url}` |
| **SESSIONS** |
| POST | `/api/sessions` | Create session | `{user_id, agent_id, metadata}` | `{id, agent_id, session_data, ...}` |
| GET | `/api/sessions/{session_id}` | Get session details | - | `{session}` |
| **AFFIRMATIONS** |
| POST | `/api/affirmations/generate` | Generate affirmations via LangGraph | `{user_id, agent_id, session_id, count}` | `{affirmations[], protocol_summary}` |
| GET | `/api/affirmations/user/{user_id}` | Get all user affirmations | - | `{affirmations[]}` |
| POST | `/api/affirmations/{id}/synthesize` | Generate TTS audio | `{voice_config?}` | `{audio_url}` |
| **CHAT** |
| POST | `/api/chat/sessions/{session_id}/messages` | Send chat message | `{user_id, agent_id, message}` | `{user_message, agent_response}` |
| GET | `/api/chat/sessions/{session_id}/messages` | Get chat history | - | `{messages[]}` |
| GET | `/api/chat/affirmations/agent/{agent_id}` | Get agent affirmations | - | `{affirmations[]}` |
| **DASHBOARD** |
| GET | `/api/dashboard/user/{user_id}` | Get dashboard data | - | `{stats, agents[], affirmations[], scripts[]}` |
| **LIVEKIT** |
| POST | `/api/livekit/token` | Generate LiveKit access token | `{room_name, participant_name}` | `{token, url}` |
| **HEALTH** |
| GET | `/health` | Health check | - | `{status, environment, version}` |

---

### Router → Service → Database Flow

```
┌──────────────────────────────────────────────────────────────┐
│                     REQUEST FLOW LAYERS                      │
└──────────────────────────────────────────────────────────────┘

[Frontend Request]
    ↓
[FastAPI Router]                    (routers/*.py)
    - Parse request
    - Extract headers (tenant_id, user_id)
    - Validate input with Pydantic
    ↓
[Business Logic Service]            (services/*.py)
    - Load agent contract
    - Initialize memory manager
    - Process with LangGraph
    - Update metrics
    ↓
[Database Layer]                    (database.py → PostgreSQL)
    - Execute SQL queries
    - Manage connection pool
    - Transaction handling
    ↓
[External Services]                 (ElevenLabs, OpenAI, LiveKit)
    - Voice synthesis
    - LLM inference
    - Real-time audio
    ↓
[Response Back to Frontend]
```

---

## 4. Service Dependencies

### Backend Service Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                    SERVICE ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────┘

main.py (FastAPI)
├── database.py (PostgreSQL Pool)
├── config.py (Settings)
│
├── ROUTERS
│   ├── agents.py
│   │   └── → agent_service.py
│   │       ├── → unified_memory_manager.py
│   │       ├── → database.py
│   │       └── → models/agent.py
│   │
│   ├── voices.py
│   │   └── → elevenlabs_service.py
│   │       └── → config.py (ELEVENLABS_API_KEY)
│   │
│   ├── avatar.py
│   │   └── → OpenAI DALL·E 3 API
│   │       └── → config.py (OPENAI_API_KEY)
│   │
│   ├── affirmations.py
│   │   ├── → manifestation_protocol_agent.py (LangGraph)
│   │   └── → audio_synthesis.py
│   │       └── → elevenlabs_service.py
│   │
│   ├── chat.py
│   │   └── → agent_service.py:process_chat_message()
│   │       └── → unified_memory_manager.py
│   │
│   └── livekit.py
│       ├── → livekit_service.py
│       ├── → deepgram_service.py (STT)
│       └── → elevenlabs_service.py (TTS)
│
└── AGENTS (LangGraph)
    ├── manifestation_protocol_agent.py
    │   └── → OpenAI GPT-4 (via LangChain)
    │
    ├── therapy_agent.py
    │   └── → OpenAI GPT-4
    │
    └── intake_agent_v2.py
        └── → OpenAI GPT-4
```

---

### External Service Integrations

| Service | Purpose | Used By | API Key Required |
|---------|---------|---------|------------------|
| **PostgreSQL (Supabase)** | Primary database, vector storage | All services | `SUPABASE_DB_URL` |
| **OpenAI GPT-4** | LLM inference for agents | LangGraph agents | `OPENAI_API_KEY` |
| **ElevenLabs** | Text-to-Speech synthesis | Voice preview, affirmation audio | `ELEVENLABS_API_KEY` |
| **DALL·E 3** | Avatar image generation | Avatar router | `OPENAI_API_KEY` |
| **LiveKit** | Real-time voice/video | Voice chat (future) | `LIVEKIT_*` |
| **Deepgram** | Speech-to-Text | Voice chat (future) | `DEEPGRAM_API_KEY` |

---

### Critical Environment Variables

```bash
# Database
SUPABASE_DB_URL=postgresql://postgres.xxx:pass@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# AI Services
OPENAI_API_KEY=sk-proj-...
ELEVENLABS_API_KEY=ssk_...

# Voice Services (Optional - for LiveKit integration)
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
DEEPGRAM_API_KEY=...

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## 5. Data Flow Diagrams

### Agent Creation Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│              AGENT CREATION DETAILED FLOW                    │
└──────────────────────────────────────────────────────────────┘

[Frontend: AgentBuilder.tsx]
    User completes 9 steps
    ↓
    Collects:
    - name: string
    - roles: string[] (1-3)
    - mission: string
    - traits: {confidence, empathy, creativity, discipline}
    - voice: Voice object from /api/voices
    - avatar_url: string (from DALL·E or upload)
    - interaction_styles: string[] (1-3)
    - focus_areas: string[]
    - philosophy: string
    - temperature: number
    - max_tokens: number
    ↓
    POST /api/agents
    {
      name,
      type: "conversational",
      identity: {
        short_description: "{roles} - {mission}",
        full_description: mission,
        character_role: roles[0],
        roles: roles[],
        mission,
        interaction_style: interaction_styles.join(', '),
        interaction_styles: interaction_styles[],
        avatar_url
      },
      traits: {confidence, empathy, creativity, discipline, ...},
      configuration: {
        llm_provider: "openai",
        llm_model: "gpt-4o-mini",
        max_tokens,
        temperature,
        memory_enabled: true,
        voice_enabled: true,
        tools_enabled: false,
        memory_k: 6,
        thread_window: 20
      },
      voice: {
        provider: "elevenlabs",
        voice_id: selectedVoice.id,
        language: "en-US",
        stability: 0.75,
        similarity_boost: 0.75,
        model: "eleven_turbo_v2"
      },
      tags: [...focus_areas, ...roles, philosophy]
    }

[Backend: routers/agents.py]
    create_agent() receives request
    ↓
    Validate & apply defaults:
    - If no voice but voice_enabled=true → default to Rachel
    - If no avatar → generate placeholder
    ↓
    Build AgentContract (Pydantic model)
    ↓
    Call agent_service.create_agent()

[Backend: services/agent_service.py]
    create_agent() executes:

    [1] INSERT INTO agents
        (id, tenant_id, owner_id, name, type, version,
         contract, status, interaction_count, last_interaction_at,
         created_at, updated_at)
        VALUES (uuid, tenant_id, owner_id, name, type, "1.0.0",
                contract_json, "active", 0, NULL, NOW(), NOW())

    [2] Initialize Memory
        unified_memory_manager.py
        ├── Create memory namespace: "agent_{agent_id}"
        └── Add system memory: "Agent initialized..."

    [3] Save Contract Files
        backend/prompts/{agent_id}/
        ├── agent_contract.json     (Full JSON contract)
        └── system_prompt.txt       (Generated from contract)

    [4] Create Default Thread
        INSERT INTO threads
        (id, agent_id, user_id, tenant_id, title, status,
         message_count, created_at, updated_at)
        VALUES (uuid, agent_id, user_id, tenant_id,
                "Default Thread", "active", 0, NOW(), NOW())

    ↓
    Return agent object to router

[Backend: routers/agents.py]
    Returns to frontend:
    {
      "status": "success",
      "message": "Agent 'Transformation Guide' created successfully",
      "agent": {
        "id": "uuid",
        "name": "Transformation Guide",
        "type": "conversational",
        "contract": { /* full contract */ },
        "status": "active",
        "created_at": "2025-10-03T..."
      }
    }

[Frontend: AgentBuilder.tsx]
    Receives response
    ↓
    Stores agentId, sessionId in state
    ↓
    router.push(`/dashboard?agentId=${agentId}&sessionId=${sessionId}&success=true`)
```

---

### Chat Interaction Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│              CHAT MESSAGE PROCESSING FLOW                    │
└──────────────────────────────────────────────────────────────┘

[Frontend: ChatInterface.tsx]
    User types: "I want to build confidence"
    ↓
    POST /api/chat/sessions/{session_id}/messages
    {
      user_id: "uuid",
      agent_id: "uuid",
      message: "I want to build confidence"
    }

[Backend: routers/chat.py]
    send_chat_message()
    ↓
    [1] Load session from database
        SELECT * FROM sessions WHERE id = session_id

    [2] Load agent from database
        SELECT * FROM agents WHERE id = agent_id

    [3] Store user message
        INSERT INTO messages
        (id, session_id, role, content, created_at)
        VALUES (uuid, session_id, "user", message, NOW())

    [4] Process with agent_service
        agent_service.process_chat_message(
          agent_id, session_id, message, session.session_data
        )

[Backend: services/agent_service.py]
    process_chat_message()
    ↓
    [1] Get or create memory manager
        if agent_id not in memory_managers:
            memory_managers[agent_id] = UnifiedMemoryManager(
                namespace=f"agent_{agent_id}"
            )

    [2] Store user message in memory
        memory_manager.add_memory(
          message,
          metadata={role: "user", session_id, timestamp}
        )

    [3] Get conversation history
        history = memory_manager.get_conversation_history(limit=10)

    [4] Generate response
        # Current: Simple intent detection
        # Future: Use manifestation_protocol_agent (LangGraph)
        response_text = _generate_response(message, history, context)

    [5] Store assistant response in memory
        memory_manager.add_memory(
          response_text,
          metadata={role: "assistant", session_id, timestamp}
        )

    [6] Return response
        return {
          "response": response_text,
          "assets_created": False,
          "context_updated": True
        }

[Backend: routers/chat.py]
    [7] Store agent message
        INSERT INTO messages
        (id, session_id, role, content, audio_url, created_at)
        VALUES (uuid, session_id, "agent", response_text,
                audio_url?, NOW())

    [8] Return to frontend
        {
          "user_message": {
            "id": "uuid",
            "role": "user",
            "content": "I want to build confidence",
            "timestamp": "2025-10-03T..."
          },
          "agent_response": {
            "id": "uuid",
            "role": "agent",
            "content": "That's wonderful...",
            "timestamp": "2025-10-03T...",
            "audio_url": "/audio/message_uuid.mp3"
          }
        }

[Frontend: ChatInterface.tsx]
    Receives response
    ↓
    Append messages to chat history
    ↓
    If audio_url exists:
        <audio src={audio_url} autoplay />
```

---

## 6. Integration Points

### Frontend ↔ Backend Integration

**API Client:** `frontend/src/lib/api.ts`

```typescript
const API_BASE_URL = "http://localhost:8000"

// Example: Create Agent
async function createAgent(agentData: AgentCreateRequest) {
  const response = await fetch(`${API_BASE_URL}/api/agents`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-tenant-id": "00000000-0000-0000-0000-000000000001",
      "x-user-id": "00000000-0000-0000-0000-000000000001"
    },
    body: JSON.stringify(agentData)
  })

  if (!response.ok) {
    throw new Error(`Agent creation failed: ${response.statusText}`)
  }

  return await response.json()
}

// Example: Get Voices
async function getVoices() {
  const response = await fetch(`${API_BASE_URL}/api/voices`)
  const data = await response.json()
  return data.voices
}
```

---

### Database Schema Integration

**Key Tables:**

```sql
-- Agents (Primary)
CREATE TABLE agents (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  owner_id UUID NOT NULL,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,
  version VARCHAR(20) DEFAULT '1.0.0',
  contract JSONB NOT NULL,         -- Full agent contract
  status VARCHAR(20) DEFAULT 'active',
  interaction_count INTEGER DEFAULT 0,
  last_interaction_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Sessions (Agent-created)
CREATE TABLE sessions (
  id UUID PRIMARY KEY,
  user_id TEXT NOT NULL,
  agent_id UUID REFERENCES agents(id),
  tenant_id UUID,
  status TEXT NOT NULL,
  room_name TEXT,
  session_data JSONB,              -- Includes manifestation_protocol
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Threads (Conversation threads)
CREATE TABLE threads (
  id UUID PRIMARY KEY,
  agent_id UUID NOT NULL,
  user_id UUID NOT NULL,
  tenant_id UUID NOT NULL,
  title VARCHAR(255),
  status VARCHAR(20) DEFAULT 'active',
  message_count INTEGER DEFAULT 0,
  last_message_at TIMESTAMP,
  context_summary TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Thread Messages
CREATE TABLE thread_messages (
  id UUID PRIMARY KEY,
  thread_id UUID NOT NULL REFERENCES threads(id),
  role VARCHAR(20) NOT NULL,       -- 'user' or 'assistant'
  content TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Messages (Chat sessions)
CREATE TABLE messages (
  id UUID PRIMARY KEY,
  session_id UUID NOT NULL REFERENCES sessions(id),
  role VARCHAR(20) NOT NULL,       -- 'user' or 'agent'
  content TEXT NOT NULL,
  audio_url TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Affirmations
CREATE TABLE affirmations (
  id UUID PRIMARY KEY,
  user_id UUID,
  agent_id UUID REFERENCES agents(id),
  affirmation_text TEXT NOT NULL,
  category VARCHAR(50),
  tags TEXT[],
  audio_url TEXT,
  audio_duration_seconds INTEGER,
  schedule_type VARCHAR(20),
  schedule_time TIME,
  play_count INTEGER DEFAULT 0,
  is_favorite BOOLEAN DEFAULT false,
  last_played_at TIMESTAMP,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### LangGraph Agent Integration

**ManifestationProtocolAgent Workflow:**

```python
# backend/agents/manifestation_protocol_agent.py

from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI

class ManifestationProtocolAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ProtocolState)

        # Add nodes (sequential workflow)
        workflow.add_node("analyze_goal", self.analyze_goal)
        workflow.add_node("design_daily_practices", self.design_daily_practices)
        workflow.add_node("create_affirmations", self.create_affirmations)
        workflow.add_node("generate_visualizations", self.generate_visualizations)
        workflow.add_node("define_metrics", self.define_metrics)
        workflow.add_node("identify_obstacles", self.identify_obstacles)
        workflow.add_node("set_checkpoints", self.set_checkpoints)
        workflow.add_node("compile_protocol", self.compile_protocol)

        # Define flow
        workflow.set_entry_point("analyze_goal")
        workflow.add_edge("analyze_goal", "design_daily_practices")
        workflow.add_edge("design_daily_practices", "create_affirmations")
        workflow.add_edge("create_affirmations", "generate_visualizations")
        workflow.add_edge("generate_visualizations", "define_metrics")
        workflow.add_edge("define_metrics", "identify_obstacles")
        workflow.add_edge("identify_obstacles", "set_checkpoints")
        workflow.add_edge("set_checkpoints", "compile_protocol")
        workflow.add_edge("compile_protocol", END)

        return workflow.compile()

    async def generate_protocol(self, user_input: dict):
        """
        Generate complete manifestation protocol

        Input:
        {
          "user_id": "uuid",
          "goal": "Build unshakeable confidence",
          "timeframe": "30_days",
          "commitment_level": "moderate"
        }

        Output:
        {
          "meta": {...},
          "analysis": {...},
          "daily_practices": [...],
          "affirmations": {
            "all": [...],
            "daily_rotation": {...}
          },
          "visualizations": [...],
          "success_metrics": [...],
          "obstacles_and_solutions": [...],
          "checkpoints": [...]
        }
        """
        result = await self.graph.ainvoke(user_input)
        return result["protocol"]
```

**Integration in Affirmations Router:**

```python
# backend/routers/affirmations.py

@router.post("/affirmations/generate")
async def generate_affirmations(request: GenerateRequest):
    # Initialize LangGraph agent
    protocol_agent = ManifestationProtocolAgent()

    # Generate protocol
    protocol = await protocol_agent.generate_protocol({
        "user_id": request.user_id,
        "goal": intake_data.get("goals", ["general"])[0],
        "timeframe": "30_days",
        "commitment_level": "moderate"
    })

    # Store in session
    await update_session_protocol(request.session_id, protocol)

    # Insert affirmations into database
    for affirmation_text in protocol["affirmations"]["all"]:
        await insert_affirmation(
            user_id=request.user_id,
            agent_id=request.agent_id,
            text=affirmation_text,
            category="manifestation"
        )

    return {
        "status": "success",
        "affirmations": protocol["affirmations"]["all"],
        "protocol_summary": {
            "daily_practices": len(protocol["daily_practices"]),
            "visualizations": len(protocol["visualizations"]),
            "success_metrics": len(protocol["success_metrics"]),
            "checkpoints": len(protocol["checkpoints"])
        }
    }
```

---

## Summary

### Architecture Highlights

1. **Agent-First Design**
   - Agents are autonomous entities with JSON contracts
   - All interactions flow through agent personality
   - Voice configuration embedded in contract

2. **9-Step Agent Creation**
   - Progressive disclosure UX
   - Voice preview before selection
   - Avatar generation with DALL·E 3
   - Complete personality customization

3. **LangGraph Orchestration**
   - ManifestationProtocolAgent generates structured protocols
   - 8-node sequential workflow
   - OpenAI GPT-4 powered

4. **Voice-First Experience**
   - 8 curated ElevenLabs voices
   - Preview playback in agent builder
   - Text-to-Speech for all content
   - LiveKit integration ready

5. **Real-Time Chat**
   - Persistent conversation threads
   - Memory-aware responses
   - Audio message playback
   - Session state management

6. **Design System Lock**
   - Locked CSS specifications
   - Framer Motion animations protected
   - Kurzgesagt theme consistency
   - No regressions allowed

---

### Critical File Paths Reference

**Backend Core:**
- `backend/main.py` - FastAPI entry point
- `backend/routers/agents.py` - Agent CRUD (PRIMARY)
- `backend/services/agent_service.py` - Agent lifecycle (CORE)
- `backend/agents/manifestation_protocol_agent.py` - LangGraph protocol generator

**Frontend Core:**
- `frontend/src/components/AgentBuilder.tsx` - 9-step wizard (LOCKED)
- `frontend/src/app/dashboard/page.tsx` - Unified dashboard
- `frontend/src/app/chat/[agentId]/page.tsx` - Real-time chat
- `frontend/src/app/globals.css` - Theme & styles (LOCKED)
- `frontend/DESIGN_SYSTEM_LOCK.md` - Design specifications (LOCKED)

**Documentation:**
- `docs/architecture/E2E_PIPELINE_REPORT.md` - Original E2E docs
- `docs/architecture/DIRECTORY_STRUCTURE_REPORT.md` - This file
- `docs/architecture/AUDIT_REPORT.md` - Production readiness

---

**End of Report**
