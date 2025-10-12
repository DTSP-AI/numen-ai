# Numen AI - AI-Powered Manifestation & Affirmation Platform

Production-grade platform combining FastAPI backend, Next.js frontend, and multi-agent AI orchestration for personalized affirmations, hypnotherapy scripts, and manifestation protocols with real-time voice interactions.

## Architecture

### Agent-First System
- **Contract-Based Agents**: JSON-defined agents with customizable personality traits
- **IntakeAgentV2**: Collects user goals and generates agent contracts
- **AffirmationAgent**: Generates personalized affirmations and scripts
- **ManifestationProtocolAgent**: Creates comprehensive manifestation protocols

### Tech Stack
- **Backend**: FastAPI 0.115+, LangGraph 0.2.27, Pydantic V2
- **Voice**: LiveKit 1.0.12, Deepgram 3.7.0 (STT), ElevenLabs 1.8.0 (TTS)
- **Memory**: Mem0 0.1.17 (cloud-based semantic memory)
- **Database**: PostgreSQL with pgvector (via Supabase)
- **Frontend**: Next.js 14.2.7, React 18, TailwindCSS, Radix UI, Framer Motion
- **Infrastructure**: Azure Container Apps, Docker Compose

## Quick Start

### 1. Start Infrastructure (Optional for Local Dev)

```bash
docker-compose up -d
```

This starts local PostgreSQL. For production, we use Supabase (managed PostgreSQL with pgvector).

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys
```

Required API keys:
- `OPENAI_API_KEY` - OpenAI GPT-4 for agent reasoning
- `MEM0_API_KEY` - Mem0 cloud memory service
- `ELEVENLABS_API_KEY` - ElevenLabs voice synthesis
- `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` - LiveKit real-time voice
- `DEEPGRAM_API_KEY` - Deepgram speech-to-text
- `SUPABASE_DB_URL` - Supabase PostgreSQL connection string

### 3. Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs on `http://localhost:8003` (see [PORT_ASSIGNMENT_LAW.md](docs/architecture/PORT_ASSIGNMENT_LAW.md))

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3003` (see [PORT_ASSIGNMENT_LAW.md](docs/architecture/PORT_ASSIGNMENT_LAW.md))

## Project Structure

```
.
├── backend/
│   ├── agents/          # IntakeAgent & TherapyAgent (LangGraph)
│   ├── services/        # LiveKit, Deepgram, ElevenLabs, Memory
│   ├── routers/         # FastAPI routes
│   ├── models/          # Pydantic schemas
│   ├── config.py        # Settings management
│   └── main.py          # FastAPI app
│
├── frontend/
│   ├── src/
│   │   ├── app/         # Next.js app router
│   │   ├── components/  # React components
│   │   ├── lib/         # API client & utilities
│   │   └── types/       # TypeScript types
│   └── package.json
│
├── docs/
│   ├── ARCHITECTURE.md              # Comprehensive architecture guide
│   └── architecture/                # Detailed documentation
│       ├── AGENT_CREATION_STANDARD.md
│       ├── CLAUDE.md
│       ├── E2E_PIPELINE_REPORT.md
│       ├── MEM0_MIGRATION_GUIDE.md
│       ├── ULTIMATE-11LABS-KB.md
│       └── ULTIMATE-LIVEKIT-KB.md
│
└── infrastructure/
    └── docker-compose.yml
```

## User Flow

1. **Discovery Questions** → User provides goals, preferences (IntakeForm)
2. **Agent Builder** → 7-step wizard to customize agent personality
   - Identity & Purpose
   - Personality Traits (9 sliders)
   - Communication Style
   - Voice Selection (8 ElevenLabs voices with preview)
   - Focus Areas
   - Philosophy & Approach
   - Advanced Settings
3. **Agent Creation** → POST /api/agents creates agent with JSON contract
4. **Chat Interface** → Real-time chat with agent (text or voice via LiveKit)
5. **Content Generation** → Agent generates affirmations, scripts, protocols
6. **Memory Persistence** → All interactions stored in Mem0 for future context

## API Endpoints

### Agents
- `POST /api/agents` - Create new agent with contract
- `GET /api/agents` - List all agents
- `GET /api/agents/{id}` - Get agent details
- `PATCH /api/agents/{id}` - Update agent contract

### Chat & Interaction
- `POST /api/chat/{agent_id}` - Send message to agent (streaming)
- `GET /api/threads/{agent_id}` - Get conversation threads

### Voice & Audio
- `GET /api/voices` - List available ElevenLabs voices
- `POST /api/voices/preview` - Generate voice preview
- `POST /api/voices/synthesize` - Text-to-speech synthesis

### Affirmations
- `POST /api/affirmations/generate` - Generate affirmations with protocol
- `GET /api/affirmations/user/{id}` - Get user affirmations

### LiveKit
- `POST /api/livekit/token` - Generate room access token

For complete API documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#api-endpoints)

## Memory Architecture

### Mem0 Cloud-Based Memory
- **Namespace Pattern**: `{tenant_id}:{agent_id}:{context}`
- **Semantic Search**: Automatic embedding generation and search
- **Persistent Storage**: Long-term memory across sessions
- **Multi-Tenant Isolation**: Complete data separation by tenant

### Storage Layers
- **Mem0**: Semantic memory with vector search
- **PostgreSQL**: Structured data (agents, threads, affirmations)
- **pgvector**: Vector embeddings (optional local search)

For details, see [docs/architecture/MEM0_MIGRATION_GUIDE.md](docs/architecture/MEM0_MIGRATION_GUIDE.md)

## Voice Pipeline

1. **User speaks** → LiveKit captures audio
2. **Deepgram STT** → transcribes to text
3. **LangGraph agent** → processes intent
4. **Agent generates response** → LLM
5. **ElevenLabs TTS** → synthesizes speech (Turbo v2 for <300ms latency)
6. **LiveKit streams audio** → user hears response

## Security & Compliance

- **Multi-Tenancy**: Complete tenant isolation via tenant_id
- **Data Encryption**: TLS 1.2+ in transit, AES-256 at rest (Supabase)
- **API Key Management**: Environment variables only
- **Memory Isolation**: Namespace-based memory separation (Mem0)
- **HIPAA/SOC2 Ready**: Architecture supports compliance (full implementation in progress)

For security guidelines, see [docs/architecture/SECURITY_QUICK_REFERENCE.md](docs/architecture/SECURITY_QUICK_REFERENCE.md)

## Development

### Running Tests
```bash
cd backend
pytest
```

### Linting
```bash
cd frontend
npm run lint
```

### Building for Production
```bash
cd frontend
npm run build
npm start
```

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Comprehensive system architecture
- **[AGENT_CREATION_STANDARD.md](docs/architecture/AGENT_CREATION_STANDARD.md)**: Agent lifecycle guide
- **[E2E_PIPELINE_REPORT.md](docs/architecture/E2E_PIPELINE_REPORT.md)**: End-to-end pipeline documentation
- **[CLAUDE.md](docs/architecture/CLAUDE.md)**: Claude Code integration guide
- **[ULTIMATE-11LABS-KB.md](docs/architecture/ULTIMATE-11LABS-KB.md)**: ElevenLabs integration
- **[ULTIMATE-LIVEKIT-KB.md](docs/architecture/ULTIMATE-LIVEKIT-KB.md)**: LiveKit integration

## Contributing

This is a private repository. For development guidance, see [docs/architecture/CLAUDE.md](docs/architecture/CLAUDE.md).

## License

Private - Proprietary