# HypnoAgent - Production-Grade Hypnotherapy Voice Agent

AI-powered manifestation and hypnotherapy voice agent with real-time voice streaming, LangGraph orchestration, and persistent memory.

## Architecture

### Dual-Agent System
- **IntakeAgent**: Collects user goals, tone preferences, and generates therapy contract
- **TherapyAgent**: Consumes contract and generates personalized hypnotherapy scripts

### Tech Stack
- **Backend**: FastAPI 0.115.0, LangGraph 0.2.27
- **Voice**: LiveKit 1.0.12, Deepgram 3.7.0 (STT), ElevenLabs 1.8.0 (TTS)
- **Memory**: Mem0 0.1.17, Qdrant 1.10.0
- **Frontend**: Next.js 14.2.7, Tailwind, shadcn/ui
- **Infrastructure**: Docker Compose, PostgreSQL, Redis

## Quick Start

### 1. Start Infrastructure Services

```bash
docker-compose up -d
```

This starts PostgreSQL, Redis, and Qdrant.

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys
```

Required API keys:
- OpenAI API key
- LiveKit credentials
- Deepgram API key
- ElevenLabs API key

### 3. Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs on `http://localhost:8000`

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`

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
├── infrastructure/
│   └── docker-compose.yml
│
└── CLAUDE.md            # Development guidance
```

## Workflow

1. **User fills IntakeForm** → goals, tone, session type
2. **IntakeAgent processes** → generates JSON contract
3. **Contract stored** → PostgreSQL + Mem0 preferences
4. **TherapyAgent consumes contract** → generates hypnotherapy script
5. **Script → ElevenLabs TTS** → streams to LiveKit room
6. **User hears audio** → real-time therapy session
7. **Session reflection stored** → Mem0 for future personalization

## API Endpoints

### Sessions
- `POST /api/sessions/` - Create new session
- `GET /api/sessions/{id}` - Get session details
- `PATCH /api/sessions/{id}/status` - Update status

### Contracts
- `POST /api/contracts/` - Create therapy contract
- `GET /api/contracts/{id}` - Get contract
- `GET /api/contracts/session/{session_id}` - Get by session

### Therapy
- `WS /api/therapy/session/{session_id}` - WebSocket for real-time session
- `GET /api/therapy/transcripts/{session_id}` - Get session transcripts

## Memory Architecture

### Mem0 Namespaces
- **User namespace**: Persistent preferences across sessions
- **Session namespace**: Ephemeral therapy session data

### Storage Layers
- **Qdrant**: Vector embeddings for semantic retrieval
- **PostgreSQL**: Structured session/contract/transcript data
- **Redis**: Session state and caching (TTL: 1 hour)

## Voice Pipeline

1. **User speaks** → LiveKit captures audio
2. **Deepgram STT** → transcribes to text
3. **LangGraph agent** → processes intent
4. **Agent generates response** → LLM
5. **ElevenLabs TTS** → synthesizes speech (Turbo v2 for <300ms latency)
6. **LiveKit streams audio** → user hears response

## Security & Compliance

- **HIPAA-ready**: Encrypted data at rest/transit
- **SOC2 audit logging**: All sessions logged
- **Enterprise TTS**: ElevenLabs enterprise tier
- **Session isolation**: No cross-session data leakage

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

## License

Private - Proprietary