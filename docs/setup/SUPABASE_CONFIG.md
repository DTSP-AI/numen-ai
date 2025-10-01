# Supabase Configuration Guide for Numen AI

## Overview

Numen AI now uses **Supabase** as the PostgreSQL database backend for the AGENT_CREATION_STANDARD implementation. This guide will help you configure the connection.

---

## Step 1: Get Your Supabase Credentials

### 1.1 Create Supabase Project (if not already done)

1. Go to [supabase.com](https://supabase.com)
2. Sign in or create an account
3. Click "New Project"
4. Fill in:
   - **Name**: `numen-ai` (or your preferred name)
   - **Database Password**: Choose a strong password (save it!)
   - **Region**: Choose closest to your users
   - **Pricing Plan**: Free tier is sufficient for development

### 1.2 Get Connection String

Once your project is created:

1. Go to **Settings** → **Database**
2. Scroll to **Connection String** section
3. Choose **Connection Pooling** (recommended for production)
4. Select **Transaction** mode
5. Copy the connection string (format: `postgresql://postgres.xxx:[PASSWORD]@xxx.supabase.co:5432/postgres`)

**Important**: Replace `[PASSWORD]` with your actual database password!

---

## Step 2: Update Your `.env` File

Add these lines to your `C:\AI_src\AffirmationApplication\.env` file:

```bash
# === SUPABASE CONFIGURATION ===

# Supabase Database Connection (Direct Connection)
SUPABASE_DB_URL=postgresql://postgres.xxx:[YOUR-PASSWORD]@xxx.pooler.supabase.com:5432/postgres

# Supabase API (for admin operations)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here

# === OPTIONAL: Keep for local development fallback ===
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_USER=hypnoagent
# POSTGRES_PASSWORD=
# POSTGRES_DB=hypnoagent
```

### Where to find each value:

**SUPABASE_DB_URL**:
- Settings → Database → Connection String → Transaction mode
- Format: `postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres`

**SUPABASE_URL**:
- Settings → API → Project URL
- Format: `https://xxxxxxxxxxxx.supabase.co`

**SUPABASE_KEY**:
- Settings → API → Project API keys → `anon` `public` key
- Format: Long JWT token starting with `eyJ...`

---

## Step 3: Verify Connection

The `database.py` file is already configured to use Supabase. It will:

1. Check for `SUPABASE_DB_URL` first
2. If found, connect to Supabase
3. If not found, fall back to local PostgreSQL

### Test the connection:

```bash
# From backend directory
cd C:\AI_src\AffirmationApplication\backend

# Run the seed script (this will also test connection)
python scripts/seed_data.py
```

You should see:
```
✅ All database tables initialized (AGENT_CREATION_STANDARD compliant)
✅ Created tenant: [UUID]
✅ Created user: [UUID]
```

---

## Step 4: Verify Tables in Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to **Table Editor**
3. You should see these new tables:
   - `tenants`
   - `users`
   - `agents`
   - `agent_versions`
   - `threads`
   - `thread_messages`
   - Plus existing: `sessions`, `contracts`, `transcripts`, etc.

---

## Supabase Features We're Using

### 1. **PostgreSQL Database**
- Full PostgreSQL 15 compatibility
- JSONB support for agent contracts
- Foreign keys and indexes

### 2. **Connection Pooling**
- Pgbouncer for efficient connection management
- Transaction mode for FastAPI compatibility

### 3. **Real-time (Future)**
- Can enable real-time subscriptions for live agent updates
- Useful for monitoring agent interactions in dashboard

### 4. **Row Level Security (RLS) - Recommended for Production**
Once you move to production, enable RLS:

```sql
-- Enable RLS on all tables
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE thread_messages ENABLE ROW LEVEL SECURITY;

-- Create policy for tenant isolation
CREATE POLICY "Tenants can only access their own agents"
ON agents
FOR ALL
USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

---

## Connection String Formats

### Direct Connection (for migrations/scripts):
```
postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres
```

### Connection Pooling (recommended for app):
```
postgresql://postgres.xxx:[PASSWORD]@xxx.pooler.supabase.com:5432/postgres
```

**Use connection pooling** for your FastAPI application!

---

## Troubleshooting

### Issue: "connection refused"
**Solution**: Check your IP is allowed in Supabase Network Restrictions
- Settings → Database → Network Restrictions
- Add your IP or disable for development

### Issue: "password authentication failed"
**Solution**: Double-check your password in the connection string
- Make sure to replace `[PASSWORD]` with actual password
- No brackets in final string

### Issue: "SSL required"
**Solution**: Supabase requires SSL by default
- The `asyncpg` connection includes SSL automatically
- For local tools, add `?sslmode=require` to connection string

### Issue: "too many connections"
**Solution**: You've hit connection limit
- Free tier: 60 connections
- Use connection pooling URL instead of direct connection

---

## Security Best Practices

1. **Never commit `.env` to git**
   - Already in `.gitignore`
   - Use environment variables in production

2. **Use different databases for dev/staging/prod**
   - Create separate Supabase projects
   - Update `SUPABASE_DB_URL` per environment

3. **Rotate API keys regularly**
   - Especially the service role key (if used)
   - Supabase → Settings → API → Revoke & Generate New

4. **Enable Row Level Security (RLS) in production**
   - Prevents cross-tenant data leakage
   - See example policies above

---

## Next Steps

Once Supabase is configured:

1. ✅ Run seed script: `python backend/scripts/seed_data.py`
2. ✅ Create default agents: `python backend/scripts/create_default_agents.py`
3. ✅ Start backend: `python backend/main.py`
4. ✅ Test agent creation via API

---

## Environment Variables Summary

Add to `.env`:

```bash
# Supabase PostgreSQL
SUPABASE_DB_URL=postgresql://postgres.xxx:[PASSWORD]@xxx.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Existing services (keep these)
OPENAI_API_KEY=sk-...
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...

# Qdrant (for Mem0 vector storage)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis (for session state)
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

**Ready to go!** Once you've added your Supabase credentials, run the seed script to initialize the database.
