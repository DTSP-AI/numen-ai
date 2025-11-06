# HypnoAgent - Quick Start Guide

Get the HypnoAgent application running on your local machine in **5 minutes**.

---

## Prerequisites

Before you begin, make sure you have:

- ✅ **Python 3.11+** installed ([Download](https://www.python.org/downloads/))
- ✅ **Node.js 18+** installed ([Download](https://nodejs.org/))
- ✅ **OpenAI API key** ([Get key](https://platform.openai.com/api-keys))

**Database Options (choose one):**
- ✅ **Supabase Cloud** (free tier) - [Sign up](https://supabase.com/) (recommended for quick start)
- ✅ **Supabase Local** - Docker-based local instance (ports 54321/54322) - [Install CLI](https://supabase.com/docs/guides/cli)
- ✅ **Local PostgreSQL** - If you prefer traditional setup (port 5432)

---

## Step 1: Install Dependencies (2 minutes)

Open your terminal and run the installation script:

**Windows:**
```bash
scripts\install.bat
```

**Mac/Linux:**
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

This will:
- Install all Python packages (25 packages)
- Install all npm packages (30 packages)
- Create necessary directories
- Copy `.env.example` to `.env`

---

## Step 2: Configure Environment (2 minutes)

Edit the `.env` file in the project root with your credentials:

### Required (app won't start without these):

**Option A: Supabase Cloud (Recommended)**
```bash
# From Supabase Dashboard → Settings → Database
SUPABASE_DB_URL=postgresql://postgres.xxx:[PASSWORD]@xxx.pooler.supabase.com:6543/postgres

# From Supabase Dashboard → Settings → API
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# From OpenAI Dashboard
OPENAI_API_KEY=sk-proj-...
```

**Option B: Supabase Local (Docker)**
```bash
# Start Supabase local first
supabase start

# Then use local connection (ports 54321/54322)
SUPABASE_DB_URL=postgresql://postgres:postgres@localhost:54322/postgres
SUPABASE_URL=http://localhost:54321
SUPABASE_KEY=<anon-key-from-supabase-start-output>

# From OpenAI Dashboard
OPENAI_API_KEY=sk-proj-...
```

**Option C: Local PostgreSQL**
```bash
# If you have PostgreSQL installed locally (port 5432)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=hypnoagent
POSTGRES_PASSWORD=your-password
POSTGRES_DB=hypnoagent

# From OpenAI Dashboard
OPENAI_API_KEY=sk-proj-...
```

### Optional (app works without these):

```bash
# For voice synthesis (optional)
ELEVENLABS_API_KEY=...

# For speech-to-text (optional)
DEEPGRAM_API_KEY=...

# For real-time voice (optional)
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=API...
LIVEKIT_API_SECRET=...
```

**Note**: The app will run without the optional keys - features gracefully degrade.

---

## Step 3: Start Development Servers (1 minute)

Run the startup script:

**Windows:**
```bash
scripts\dev.bat
```

**Mac/Linux:**
```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

This will start:
- ✅ Backend on **http://localhost:8003** (fixed port)
- ✅ Frontend on **http://localhost:3003** (auto-fallback to 3004 if occupied)

**Port Assignment Law:**
See [docs/architecture/PORT_ASSIGNMENT_LAW.md](docs/architecture/PORT_ASSIGNMENT_LAW.md) for complete port specifications.

---

## Step 4: Verify Setup (30 seconds)

### Check Backend Health
Open your browser or use curl:
```bash
curl http://localhost:8003/health
```

You should see:
```json
{
  "status": "healthy",
  "services": {
    "database": {"status": "connected"},
    "openai": {"status": "configured"},
    ...
  }
}
```

### Access Points
- **Frontend**: http://localhost:3003
- **API Docs**: http://localhost:8003/docs (Swagger UI)
- **Health Check**: http://localhost:8003/health

---

## Step 5: Test the Application

### Create a User
```bash
curl -X POST http://localhost:8003/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "name": "Test User"
  }'
```

### Use the Frontend
1. Open http://localhost:3003
2. Click "Get Started" to register/login
3. Go through the intake flow to create a Guide
4. Start chatting with your Guide!

---

## Troubleshooting

### Backend won't start
**Error**: "OPENAI_API_KEY is not set"
- Check that `.env` exists in project root
- Verify `OPENAI_API_KEY` is set in `.env`
- Restart backend

**Error**: "SUPABASE_DB_URL is not set"
- Get connection string from Supabase dashboard
- Use **Session mode** connection string (not transaction mode)
- Update `.env` and restart

### Frontend won't start
**Error**: "Cannot find module..."
- Run: `cd frontend && npm install`
- Restart frontend

### Health check shows "degraded"
- This is OK if you only have required services configured
- Check which services are missing in the health response
- Add API keys for optional services if needed

---

## What Works Without Optional Services

| Feature | Without ElevenLabs | Without Deepgram | Without LiveKit |
|---------|-------------------|------------------|-----------------|
| Text Chat | ✅ Works | ✅ Works | ✅ Works |
| Guide Creation | ✅ Works | ✅ Works | ✅ Works |
| Memory | ✅ Works | ✅ Works | ✅ Works |
| Authentication | ✅ Works | ✅ Works | ✅ Works |
| Voice Synthesis | ❌ Disabled | ✅ Works | ✅ Works |
| Voice Input | ✅ Works | ❌ Disabled | ✅ Works |
| Real-time Voice | ✅ Works | ✅ Works | ❌ Disabled |

**Bottom line**: You can fully test the core application with just Supabase + OpenAI.

---

## Next Steps

- **Detailed Setup**: See [docs/LOCAL_SETUP_GUIDE.md](docs/LOCAL_SETUP_GUIDE.md)
- **Architecture**: See [docs/CurrentCodeBasePrompt.md](docs/CurrentCodeBasePrompt.md)
- **Testing Report**: See [docs/LOCAL_TESTING_READY_REPORT.md](docs/LOCAL_TESTING_READY_REPORT.md)

---

## Need Help?

1. Check the health endpoint: http://localhost:8003/health
2. Review backend logs in terminal
3. Verify all required env vars are set
4. Consult [docs/LOCAL_SETUP_GUIDE.md](docs/LOCAL_SETUP_GUIDE.md) for detailed troubleshooting

---

**That's it!** You should now have HypnoAgent running locally. Happy testing! 🚀
