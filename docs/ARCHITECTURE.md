# Numen AI - Architecture Documentation
**Last Updated:** 2025-10-11
**Version:** 2.0
**Status:** Production-Ready

---

## Executive Summary

**Numen AI** is a production-grade AI-powered manifestation and affirmation platform that combines FastAPI backend, Next.js frontend, and multi-agent AI orchestration. The platform enables users to create personalized AI agents that generate affirmations, hypnotherapy scripts, and manifestation protocols using voice-enabled real-time interactions.

### Core Capabilities
- **Agent-First Architecture**: JSON contract-based agent creation and lifecycle management
- **Real-Time Voice**: LiveKit + Deepgram (STT) + ElevenLabs (TTS) integration
- **Persistent Memory**: Mem0 cloud-based semantic memory with multi-tenant isolation
- **Content Generation**: AI-generated affirmations, scripts, and manifestation protocols
- **Multi-Tenant Ready**: Complete tenant isolation with PostgreSQL + pgvector

---

## Table of Contents

1. [Technology Stack](#technology-stack)
2. [System Architecture](#system-architecture)
3. [Agent System](#agent-system)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Frontend Architecture](#frontend-architecture)
7. [Memory System](#memory-system)
8. [Voice Pipeline](#voice-pipeline)
9. [Security & Compliance](#security--compliance)
10. [Deployment](#deployment)

---

## Technology Stack

### Backend
- **Framework:** FastAPI 0.115+ (Python 3.11+)
- **AI/LLM:** LangChain, LangGraph 0.2.27, OpenAI GPT-4
- **Database:** PostgreSQL with pgvector extension (via Supabase)
- **Memory:** Mem0 0.1.17 (cloud-based semantic memory)
- **Voice Services:**
  - **TTS:** ElevenLabs 1.8.0
  - **STT:** Deepgram 3.7.0
  - **Real-Time:** LiveKit 1.0.12
- **Validation:** Pydantic V2
- **Storage:** Supabase Storage (avatars, audio files)

### Frontend
- **Framework:** Next.js 14.2.7 (App Router)
- **UI:** React 18, TailwindCSS, Radix UI, shadcn/ui
- **Animations:** Framer Motion
- **Voice:** @livekit/components-react, livekit-client
- **State:** React hooks (localStorage for discovery data)
- **TypeScript:** Strict mode enabled

### Infrastructure
- **Hosting:** Azure Container Apps / Docker Compose
- **Database:** Supabase PostgreSQL (with pgvector)
- **Version Control:** Git
- **Ports:** Backend 8003, Frontend 3003 (see PORT_ASSIGNMENT_LAW.md)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Landing   │  │ Agent Builder│  │  Chat Interface  │   │
│  │     Page    │→ │  (7 Steps)   │→ │   + Voice Lab   │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (Port 3003 → 8003)
┌────────────────────────▼────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Routers   │  │  Services   │  │      Agents         │ │
│  │ (13 files)  │→ │ (13 files)  │→ │ (LangGraph-based)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┬────────────────┐
         │               │               │                │
         ▼               ▼               ▼                ▼
┌──────────────┐ ┌────────────┐ ┌─────────────┐ ┌─────────────┐
│  PostgreSQL  │ │    Mem0    │ │  ElevenLabs │ │   LiveKit   │
│  (Supabase)  │ │  (Memory)  │ │    (TTS)    │ │   (Voice)   │
└──────────────┘ └────────────┘ └─────────────┘ └─────────────┘
```

### Architecture Principles

1. **Agent-First Design**: Agents are the primary actors that create sessions and generate content
2. **Contract-Based Configuration**: All agent behavior defined via JSON contracts (no hardcoded personalities)
3. **Multi-Tenant by Default**: All data isolated by tenant_id
4. **Memory-Persistent**: Every interaction stored in Mem0 for semantic retrieval
5. **Voice-Native**: Real-time voice streaming with sub-300ms latency
6. **Type-Safe**: Pydantic (backend) + TypeScript (frontend) for compile-time safety

---

## Agent System

### Contract-First Agent Architecture

Every agent is defined by a JSON contract that specifies its identity, personality traits, configuration, and capabilities. This contract is stored in the database and filesystem, enabling dynamic runtime behavior without code changes.

#### Agent Contract Structure

```json
{
  "id": "uuid",
  "name": "Transformation Guide",
  "type": "conversational",
  "version": "1.0.0",
  "identity": {
    "short_description": "Empowering Coach - Help users manifest their potential",
    "full_description": "I am a compassionate guide specializing in...",
    "character_role": "Empowering Coach",
    "mission": "Help users manifest their highest potential",
    "roles": ["Guide", "Coach", "Mentor"],
    "interaction_styles": ["Warm", "Supportive", "Empowering"]
  },
  "traits": {
    "confidence": 70,
    "empathy": 80,
    "creativity": 60,
    "discipline": 55,
    "playfulness": 40,
    "directness": 50,
    "supportiveness": 85,
    "spirituality": 65,
    "intellectualism": 60
  },
  "configuration": {
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",
    "max_tokens": 800,
    "temperature": 0.7,
    "memory_enabled": true,
    "voice_enabled": true,
    "tools_enabled": false,
    "memory_k": 6,
    "thread_window": 20
  },
  "voice": {
    "provider": "elevenlabs",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "name": "Rachel",
    "language": "en-US",
    "stability": 0.75,
    "similarity_boost": 0.75,
    "model": "eleven_turbo_v2"
  },
  "metadata": {
    "tenant_id": "uuid",
    "owner_id": "uuid",
    "tags": ["manifestation", "hypnotherapy", "empowerment"]
  }
}
```

#### Agent Lifecycle

```
1. User Discovery Flow
   ↓ (localStorage: goals, tone, preferences)
2. Agent Builder (7 Steps)
   - Identity & Purpose
   - Personality Traits (9 sliders)
   - Communication Style
   - Voice Selection (8 curated ElevenLabs voices)
   - Focus Areas
   - Philosophy & Approach
   - Advanced Settings
   ↓
3. POST /api/agents (create agent with contract)
   ↓
4. Agent Service:
   - Validate contract (Pydantic)
   - Create database record
   - Initialize Mem0 memory namespace
   - Save contract to filesystem (backend/prompts/{agent_id}/)
   - Create default thread
   ↓
5. Agent ready for interactions
```

### Key Agents

| Agent | File | Purpose | Status |
|-------|------|---------|--------|
| **IntakeAgentV2** | `intake_agent_v2.py` | Contract-first intake flow | ✅ Active |
| **AffirmationAgent** | `affirmation_agent.py` | Content generation (affirmations, scripts) | ✅ Active |
| **ManifestationProtocolAgent** | `manifestation_protocol_agent.py` | Protocol generation (8-node LangGraph workflow) | ✅ Active |
| **LangGraphAgent** | `langgraph_agent.py` | Generic agent builder utility | ✅ Active |

---

## Database Schema

### Core Tables (AGENT_CREATION_STANDARD)

```sql
-- Multi-Tenancy
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent System
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    owner_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- conversational, voice, workflow, autonomous
    version VARCHAR(20) DEFAULT '1.0.0',
    contract JSONB NOT NULL,  -- Full agent contract
    status VARCHAR(20) DEFAULT 'active',
    interaction_count INTEGER DEFAULT 0,
    last_interaction_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agents_tenant ON agents(tenant_id);
CREATE INDEX idx_agents_status ON agents(status);

-- Conversation Threads
CREATE TABLE threads (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES agents(id),
    user_id UUID NOT NULL REFERENCES users(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    title VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP,
    context_summary TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_threads_agent ON threads(agent_id);
CREATE INDEX idx_threads_user ON threads(user_id);

CREATE TABLE thread_messages (
    id UUID PRIMARY KEY,
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB,
    feedback_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_thread ON thread_messages(thread_id);
```

### Application-Specific Tables

```sql
-- Discovery & Intake
CREATE TABLE user_discovery (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    goals JSONB,
    limiting_beliefs JSONB,
    desired_outcomes JSONB,
    affirmation_agent_id UUID REFERENCES agents(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Generated Content
CREATE TABLE affirmations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    affirmation_text TEXT NOT NULL,
    category VARCHAR(50),
    tags TEXT[],
    audio_url TEXT,
    audio_duration_seconds INTEGER,
    schedule_type VARCHAR(20),  -- daily, weekly, null
    schedule_time TIME,
    play_count INTEGER DEFAULT 0,
    is_favorite BOOLEAN DEFAULT false,
    last_played_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE hypnosis_scripts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    title VARCHAR(500),
    script_text TEXT NOT NULL,
    duration_minutes INTEGER,
    audio_url TEXT,
    pacing_markers JSONB,  -- Timestamps for emphasis, pauses
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sessions (for LiveKit voice sessions)
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    agent_id UUID REFERENCES agents(id),
    tenant_id UUID REFERENCES tenants(id),
    status TEXT NOT NULL,  -- active, completed, cancelled
    room_name TEXT,
    session_data JSONB,  -- Stores intake_data and protocol
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Relationship Diagram

```
tenants (multi-tenant root)
  ├── users
  └── agents
       ├── threads
       │    └── thread_messages
       ├── affirmations
       ├── hypnosis_scripts
       └── sessions
```

---

## API Endpoints

### Agent Management

```
POST   /api/agents               Create new agent
GET    /api/agents               List all agents (tenant-filtered)
GET    /api/agents/{id}          Get agent details
PATCH  /api/agents/{id}          Update agent contract
DELETE /api/agents/{id}          Archive agent (soft delete)
```

### Voice & Audio

```
GET    /api/voices               List available ElevenLabs voices
POST   /api/voices/preview       Generate voice preview audio
POST   /api/voices/validate      Validate voice_id exists
POST   /api/voices/synthesize    Synthesize text to speech
```

### Chat & Interaction

```
POST   /api/chat/{agent_id}      Send message to agent (streaming)
WS     /ws/chat/{agent_id}       WebSocket for real-time chat
GET    /api/threads/{agent_id}   Get conversation threads
```

### Intake & Discovery

```
POST   /api/intake/baseline      Submit baseline intake data
POST   /api/intake/discovery     Submit discovery questions
GET    /api/intake/user/{id}     Get user intake data
```

### LiveKit Voice

```
POST   /api/livekit/token        Generate LiveKit room token
GET    /api/livekit/rooms        List active rooms
```

### Affirmations

```
POST   /api/affirmations/generate    Generate affirmations with protocol
GET    /api/affirmations/user/{id}   Get user affirmations
POST   /api/affirmations/{id}/synthesize  Generate audio
PATCH  /api/affirmations/{id}        Update affirmation
```

### Avatar Generation

```
POST   /api/avatar/generate      Generate DALL-E agent avatar
GET    /api/avatar/{agent_id}    Get agent avatar URL
```

---

## Frontend Architecture

### Page Structure (Next.js App Router)

```
src/app/
├── page.tsx                    # Landing page
├── create-agent/
│   └── page.tsx               # Agent builder (7-step wizard)
├── chat/
│   └── [agentId]/
│       ├── page.tsx           # Agent chat interface
│       └── layout.tsx         # Chat layout with sidebar
├── voice-lab/
│   └── page.tsx               # Voice testing & selection
├── affirmations/
│   └── page.tsx               # Affirmation library
├── dashboard/
│   └── page.tsx               # User dashboard
└── creation/
    └── page.tsx               # Content creation flow
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **ChatInterface** | `ChatInterface.tsx` | Main chat UI with message bubbles, streaming |
| **VoiceControls** | `VoiceControls.tsx` | LiveKit audio controls (mute, unmute, disconnect) |
| **AgentBuilder** | `AgentBuilder.tsx` | 7-step agent customization wizard |
| **GuideCustomization** | `GuideCustomization.tsx` | User-facing 4-control customization |
| **DiscoveryQuestions** | `DiscoveryQuestions.tsx` | Structured intake questions |
| **IntakeForm** | `IntakeForm.tsx` | Initial discovery flow |
| **ChatSidebar** | `ChatSidebar.tsx` | Agent/conversation switcher |
| **ScriptPlayer** | `ScriptPlayer.tsx` | Audio playback with progress |

### API Client

```typescript
// src/lib/api.ts
const API_URL = 'http://localhost:8003'

export const api = {
  // Agents
  async createAgent(contract: AgentContract): Promise<Agent>
  async getAgents(): Promise<Agent[]>
  async getAgent(agentId: string): Promise<Agent>

  // Chat
  async sendMessage(agentId: string, message: string): Promise<Response>

  // Voices
  async getVoices(): Promise<Voice[]>
  async previewVoice(voiceId: string, text: string): Promise<Blob>

  // Affirmations
  async generateAffirmations(data: GenerateRequest): Promise<Affirmation[]>
}
```

### User Flow

```
1. User lands on homepage
   ↓
2. Fills discovery questions (IntakeForm)
   - Goals, tone preferences, session type
   - Stored in localStorage
   ↓
3. Redirected to Agent Builder (/create-agent)
   - 7-step wizard
   - Voice selection with preview
   - Personality trait customization
   ↓
4. Agent created (POST /api/agents)
   ↓
5. Redirected to chat interface (/chat/[agentId])
   - Real-time chat with agent
   - Optional voice interaction via LiveKit
   ↓
6. Dashboard (/dashboard)
   - View affirmations
   - Manage agents
   - Analytics
```

---

## Memory System

### Mem0 Architecture

**Mem0** is a cloud-based semantic memory service that provides persistent, searchable memory for AI agents. Unlike local vector stores (FAISS, Qdrant), Mem0 handles embedding generation, storage, and semantic search as a managed service.

#### Memory Manager Implementation

```python
# backend/services/memory_manager.py

class MemoryManager:
    """Mem0-backed memory manager for agents"""

    def __init__(self, tenant_id: str, agent_id: str, agent_traits: Dict):
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.namespace = f"{tenant_id}:{agent_id}"
        self.client = MemoryClient(api_key=MEM0_API_KEY)

    async def store_interaction(self, role: str, content: str, session_id: str):
        """Persist a message to Mem0"""
        await self.client.store(
            namespace=self.namespace,
            session_id=session_id,
            role=role,
            content=content,
            metadata={"traits": self.agent_traits}
        )

    async def get_agent_context(self, user_input: str, session_id: str, k: int = 5):
        """Retrieve top-k relevant memories"""
        results = await self.client.search(
            namespace=self.namespace,
            query=user_input,
            session_id=session_id,
            limit=k
        )

        memories = [r["content"] for r in results]
        avg_score = sum(r["score"] for r in results) / max(len(results), 1)

        return {
            "memories": memories,
            "confidence_score": avg_score
        }
```

#### Namespace Pattern

```
{tenant_id}:{agent_id}                          # Agent-level memory
{tenant_id}:{agent_id}:thread:{thread_id}       # Thread-specific memory
{tenant_id}:{agent_id}:user:{user_id}           # User-specific memory
```

#### Memory Storage Strategy

1. **Mem0 Cloud**: Long-term semantic memory, searchable across sessions
2. **PostgreSQL thread_messages**: Recent conversation history (last 20 messages)
3. **Hybrid Retrieval**: Combine recent messages + semantic memories for context

---

## Voice Pipeline

### Real-Time Voice Architecture

```
User speaks
  ↓
[LiveKit] Captures audio stream
  ↓
[Deepgram STT] Transcribes to text (streaming)
  ↓
[Agent Service] Processes message
  ├─ Load agent contract
  ├─ Get memory context (Mem0)
  └─ Generate response (LangGraph + GPT-4)
  ↓
[ElevenLabs TTS] Synthesizes speech (Turbo v2 - <300ms latency)
  ↓
[LiveKit] Streams audio back to user
  ↓
User hears response
```

### ElevenLabs Voice Selection

**8 Curated Voices** (see ULTIMATE-11LABS-KB.md for details):

| Voice | ID | Gender | Accent | Use Case |
|-------|--------|--------|--------|----------|
| Rachel | `21m00Tcm4TlvDq8ikWAM` | Female | American | Anxiety relief, calm guidance |
| Adam | `pNInz6obpgDQGcFmaJgB` | Male | American | Confidence building, motivation |
| Bella | `EXAVITQu4vr4xnSDxMaL` | Female | American | Structured guidance, habit change |
| Domi | `AZnzlk1XvdvUeBnXmlld` | Female | American | Meditation, gentle support |
| Daria | `4E7B5qJZD5JKiZJpkDQn` | Female | American | Manifestation, empowerment |
| Josh | `TxGEqnHWrfWFTfGW9XjX` | Male | American | Daily affirmations, support |
| Charlie | `IKne3meq5aSn9XLyUdCD` | Male | Australian | Stress relief, calm |
| Daniel | `onwK4e9ZLuTAKqWW03F9` | Male | British | Executive coaching, authority |

### LiveKit Integration

```typescript
// frontend/src/components/VoiceControls.tsx

import { useRoomContext, useLocalParticipant } from '@livekit/components-react'

function VoiceControls() {
  const { audioTrack } = useLocalParticipant()

  const toggleMute = () => {
    audioTrack?.setMuted(!audioTrack.isMuted)
  }

  return (
    <button onClick={toggleMute}>
      {audioTrack?.isMuted ? 'Unmute' : 'Mute'}
    </button>
  )
}
```

---

## Security & Compliance

### Authentication (Planned)
- **Current**: Demo mode with hardcoded user ID (`00000000-0000-0000-0000-000000000001`)
- **Planned**: Supabase Auth with JWT tokens

### Multi-Tenancy
- All tables include `tenant_id` column
- Row-Level Security (RLS) policies in Supabase
- Namespace isolation in Mem0

### API Key Management
- Environment variables only (no hardcoded keys)
- Pydantic Settings with case-insensitive fallback:
  ```python
  openai_api_key: Optional[str] = None
  OPENAI_API_KEY: Optional[str] = None  # Fallback
  ```

### Data Privacy
- User data encrypted at rest (Supabase default)
- TLS 1.2+ for all API communication
- Mem0 data isolated by namespace

### HIPAA/SOC2 Readiness
- **Note**: Current disclaimers reference HIPAA/SOC2 compliance, but full implementation requires:
  - Audit logging for all data access
  - Data retention policies
  - User data export/deletion endpoints
  - Business Associate Agreements (BAAs)

---

## Deployment

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8003

# Frontend
cd frontend
npm install
npm run dev  # Runs on port 3003
```

### Environment Variables

```bash
# Backend (.env)
SUPABASE_DB_URL=postgresql://...
OPENAI_API_KEY=sk-...
MEM0_API_KEY=...
ELEVENLABS_API_KEY=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
DEEPGRAM_API_KEY=...

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8003
```

### Port Assignment (PORT_ASSIGNMENT_LAW.md)
- **Backend**: 8003
- **Frontend**: 3003
- **Reason**: Avoid conflicts with common ports (8000, 3000)

### Production Deployment
- **Backend**: Azure Container Apps / Docker
- **Frontend**: Vercel / Azure Static Web Apps
- **Database**: Supabase (managed PostgreSQL)
- **Memory**: Mem0 (managed cloud service)

---

## Related Documentation

- **[AGENT_CREATION_STANDARD.md](architecture/AGENT_CREATION_STANDARD.md)**: Comprehensive agent lifecycle guide
- **[CurrentCodeBasePrompt.md](architecture/CurrentCodeBasePrompt.md)**: Development context for Claude Code
- **[CLAUDE.md](architecture/CLAUDE.md)**: Claude Code integration guide
- **[E2E_PIPELINE_REPORT.md](architecture/E2E_PIPELINE_REPORT.md)**: End-to-end pipeline documentation
- **[PORT_ASSIGNMENT_LAW.md](architecture/PORT_ASSIGNMENT_LAW.md)**: Port assignment standards
- **[SECURITY_QUICK_REFERENCE.md](architecture/SECURITY_QUICK_REFERENCE.md)**: Security best practices
- **[ULTIMATE-11LABS-KB.md](architecture/ULTIMATE-11LABS-KB.md)**: ElevenLabs integration guide
- **[ULTIMATE-LIVEKIT-KB.md](architecture/ULTIMATE-LIVEKIT-KB.md)**: LiveKit integration guide
- **[MEM0_MIGRATION_GUIDE.md](architecture/MEM0_MIGRATION_GUIDE.md)**: Memory system migration guide

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-10-11 | Consolidated architecture documentation, removed redundant files |
| 1.1 | 2025-10-02 | Added voice selection, agent builder updates |
| 1.0 | 2025-10-01 | Initial architecture documentation |

---

**Maintained by**: Numen AI Development Team
**Questions**: Refer to documentation above or review source code in `/backend` and `/frontend`
