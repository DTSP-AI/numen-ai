# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**hypno-voice-agent** is a production-grade Manifestation/Hypnotherapy Voice Agent built with real-time voice streaming, LangGraph orchestration, and persistent memory.

### Stack
- **Backend**: FastAPI 0.115.0, LangGraph 0.2.27, LiveKit 1.0.12, Deepgram 3.7.0, ElevenLabs 1.8.0
- **Frontend**: Next.js 14.2.7, Tailwind, shadcn/ui, Radix, Framer Motion
- **Memory**: Mem0 0.1.17, Qdrant 1.10.0
- **Infrastructure**: Docker Compose, Azure Container Apps, PostgreSQL, Redis

## Architecture

### Agent System

**IntakeAgent**
- Collects user goals, preferred tone, and voice preferences
- Outputs a JSON contract consumed by TherapyAgent
- I/O: Voice + Chat via LiveKit, Deepgram STT, ElevenLabs TTS (neutral voice)
- Memory: Stores user preferences in Mem0 with namespaced storage

**TherapyAgent**
- Acts as hypnotherapist, consuming the contract from IntakeAgent
- Generates personalized hypnotherapy scripts
- I/O: Real-time audio streaming + transcript export capability
- Memory: Session storage and reflections stored in Mem0

### Workflow
1. IntakeAgent collects information → outputs JSON contract
2. TherapyAgent consumes contract → generates script → streams audio

### Real-Time Voice Pipeline
- **LiveKit**: WebRTC transport for low-latency voice
- **Deepgram**: Speech-to-Text with streaming support
- **ElevenLabs**: Text-to-Speech (Turbo v2 / Flash for low latency, enterprise tier)

### Memory Architecture
- **Mem0**: Persistent memory layer for user preferences and session reflections
- **Qdrant**: Vector database backing Mem0 for semantic retrieval
- **PostgreSQL**: Structured data storage
- **Redis**: Session state and caching

### Security & Compliance
- SOC2 and HIPAA-ready architecture
- ElevenLabs enterprise TTS for voice compliance
- Secure handling of sensitive health data

## Development Commands

### Backend (FastAPI + LangGraph)
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload

# Run tests
pytest

# Run single test
pytest path/to/test.py::test_function_name
```

### Frontend (Next.js)
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run production build
npm start

# Run tests
npm test

# Lint
npm run lint
```

### Infrastructure
```bash
# Start all services (Qdrant, PostgreSQL, Redis)
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose up --build
```

## Key Design Patterns

### LangGraph Agent Orchestration
- IntakeAgent and TherapyAgent are implemented as LangGraph nodes
- State is passed between agents via JSON contracts
- Graph state includes conversation history, user preferences, and session metadata

### Memory Namespacing
- Mem0 uses namespaces to separate user preferences from session data
- User namespace: persistent across sessions
- Session namespace: ephemeral, cleared after therapy session

### LiveKit Integration
- Room-based architecture: one room per therapy session
- Track management: separate audio tracks for STT and TTS
- Agent connects as participant for voice streaming

### Voice Pipeline
- Deepgram streams transcripts to LangGraph agent
- Agent generates responses via LangChain/LangGraph
- ElevenLabs streams synthesized audio back via LiveKit
- Full duplex: user can interrupt agent mid-sentence

## Critical Considerations

### Latency Optimization
- Use ElevenLabs Flash or Turbo v2 models for sub-300ms TTS
- Stream audio chunks immediately (don't wait for full completion)
- Implement voice activity detection (VAD) for natural turn-taking

### Session Management
- Each therapy session creates new LiveKit room
- Session state persists in Redis with TTL
- Transcripts exported to storage after session completion

### Error Handling
- Graceful degradation if voice services fail (fallback to text)
- Retry logic for transient API failures
- User notification for critical service outages