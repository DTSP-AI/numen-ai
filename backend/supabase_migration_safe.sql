-- ============================================================
-- NUMEN AI - SAFE DATABASE MIGRATION
-- Preserves existing data while adding new schema
-- ============================================================
-- Run this in Supabase SQL Editor (Database > SQL Editor > New Query)
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- STEP 1: Create new tables (Agent Creation Standard)
-- ============================================================

-- Tenants table (multi-tenancy)
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users table (per-tenant users)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agents table (JSON contract storage)
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    owner_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0.0',
    contract JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    interaction_count INTEGER DEFAULT 0,
    last_interaction_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_tenant ON agents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);

-- Agent versions table (contract history)
CREATE TABLE IF NOT EXISTS agent_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    version VARCHAR(20) NOT NULL,
    contract JSONB NOT NULL,
    change_summary TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_versions_agent ON agent_versions(agent_id);

-- Threads table (conversation threads)
CREATE TABLE IF NOT EXISTS threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

CREATE INDEX IF NOT EXISTS idx_threads_agent ON threads(agent_id);
CREATE INDEX IF NOT EXISTS idx_threads_user ON threads(user_id);
CREATE INDEX IF NOT EXISTS idx_threads_tenant ON threads(tenant_id);
CREATE INDEX IF NOT EXISTS idx_threads_status ON threads(status);

-- Thread messages table (message persistence)
CREATE TABLE IF NOT EXISTS thread_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    feedback_score FLOAT,
    feedback_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_thread ON thread_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON thread_messages(created_at);

-- ============================================================
-- STEP 2: Create memory system
-- ============================================================

-- Memory embeddings table (replaces Qdrant)
CREATE TABLE IF NOT EXISTS memory_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    user_id UUID REFERENCES users(id),

    -- Memory content
    content TEXT NOT NULL,
    embedding vector(1536),

    -- Memory metadata
    namespace VARCHAR(255) NOT NULL,
    memory_type VARCHAR(50),
    metadata JSONB,

    -- Access tracking
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_tenant_agent ON memory_embeddings(tenant_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_memory_namespace ON memory_embeddings(namespace);
CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_embeddings(memory_type);

-- Vector similarity index (HNSW for fast search)
DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_memory_embedding
    ON memory_embeddings USING hnsw (embedding vector_cosine_ops);
EXCEPTION
    WHEN OTHERS THEN
        -- Fallback to ivfflat if HNSW not available
        CREATE INDEX IF NOT EXISTS idx_memory_embedding
        ON memory_embeddings USING ivfflat (embedding vector_cosine_ops);
END $$;

-- ============================================================
-- STEP 3: Alter existing tables (add missing columns)
-- ============================================================

-- Add columns to sessions table
DO $$
BEGIN
    -- Add agent_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'agent_id'
    ) THEN
        ALTER TABLE sessions ADD COLUMN agent_id UUID REFERENCES agents(id);
    END IF;

    -- Add tenant_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE sessions ADD COLUMN tenant_id UUID REFERENCES tenants(id);
    END IF;

    -- Add session_data if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'session_data'
    ) THEN
        ALTER TABLE sessions ADD COLUMN session_data JSONB;
    END IF;

    -- Add expires_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'expires_at'
    ) THEN
        ALTER TABLE sessions ADD COLUMN expires_at TIMESTAMP;
    END IF;
END $$;

-- Create indexes on sessions
CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- Fix sessions id column (ensure it has default)
DO $$
BEGIN
    ALTER TABLE sessions ALTER COLUMN id SET DEFAULT gen_random_uuid();
EXCEPTION
    WHEN OTHERS THEN NULL;
END $$;

-- Fix contracts id column
DO $$
BEGIN
    ALTER TABLE contracts ALTER COLUMN id SET DEFAULT gen_random_uuid();
EXCEPTION
    WHEN OTHERS THEN NULL;
END $$;

-- Fix transcripts id column
DO $$
BEGIN
    ALTER TABLE transcripts ALTER COLUMN id SET DEFAULT gen_random_uuid();
EXCEPTION
    WHEN OTHERS THEN NULL;
END $$;

-- Fix manifestation_protocols id column
DO $$
BEGIN
    ALTER TABLE manifestation_protocols ALTER COLUMN id SET DEFAULT gen_random_uuid();
EXCEPTION
    WHEN OTHERS THEN NULL;
END $$;

-- Fix protocol_checkpoints id column
DO $$
BEGIN
    ALTER TABLE protocol_checkpoints ALTER COLUMN id SET DEFAULT gen_random_uuid();
EXCEPTION
    WHEN OTHERS THEN NULL;
END $$;

-- ============================================================
-- STEP 4: Create Numen AI Pipeline tables
-- ============================================================

-- User Discovery Data (from IntakeAgent)
CREATE TABLE IF NOT EXISTS user_discovery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Discovery fields
    goals JSONB NOT NULL,
    limiting_beliefs JSONB,
    desired_outcomes JSONB,
    preferences JSONB,
    schedule_preference TEXT,

    -- Generated contract reference
    affirmation_agent_id UUID REFERENCES agents(id),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_discovery_user ON user_discovery(user_id);
CREATE INDEX IF NOT EXISTS idx_discovery_tenant ON user_discovery(tenant_id);

-- Affirmations (generated by AffirmationAgent)
CREATE TABLE IF NOT EXISTS affirmations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Content
    title TEXT,
    affirmation_text TEXT NOT NULL,
    category TEXT,
    tags TEXT[],

    -- Audio
    audio_url TEXT,
    audio_duration_seconds INT,
    voice_settings JSONB,

    -- Scheduling
    schedule_type TEXT,
    schedule_time TIME,
    schedule_days TEXT[],

    -- Analytics
    play_count INT DEFAULT 0,
    last_played_at TIMESTAMP,
    is_favorite BOOLEAN DEFAULT false,

    -- Metadata
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_affirmations_user ON affirmations(user_id);
CREATE INDEX IF NOT EXISTS idx_affirmations_schedule ON affirmations(schedule_type, schedule_time);
CREATE INDEX IF NOT EXISTS idx_affirmations_status ON affirmations(status);

-- Hypnosis Scripts (generated by AffirmationAgent)
CREATE TABLE IF NOT EXISTS hypnosis_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Content
    title TEXT NOT NULL,
    script_text TEXT NOT NULL,
    duration_minutes INT,
    pacing_markers JSONB,

    -- Audio
    audio_url TEXT,
    voice_settings JSONB,

    -- Metadata
    session_type TEXT,
    focus_area TEXT,

    -- Analytics
    play_count INT DEFAULT 0,
    last_played_at TIMESTAMP,
    completion_rate FLOAT,

    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scripts_user ON hypnosis_scripts(user_id);
CREATE INDEX IF NOT EXISTS idx_scripts_focus ON hypnosis_scripts(focus_area);

-- Scheduled Sessions
CREATE TABLE IF NOT EXISTS scheduled_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    affirmation_id UUID REFERENCES affirmations(id),
    script_id UUID REFERENCES hypnosis_scripts(id),

    -- Schedule
    scheduled_at TIMESTAMP NOT NULL,
    recurrence_rule TEXT,
    timezone TEXT DEFAULT 'UTC',

    -- Execution
    executed_at TIMESTAMP,
    execution_status TEXT,

    -- Notification
    notification_sent BOOLEAN DEFAULT false,
    notification_type TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheduled_pending ON scheduled_sessions(scheduled_at, execution_status);
CREATE INDEX IF NOT EXISTS idx_scheduled_user ON scheduled_sessions(user_id);

-- ============================================================
-- STEP 5: Row Level Security (RLS)
-- ============================================================

-- Enable RLS on new tables
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE thread_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_discovery ENABLE ROW LEVEL SECURITY;
ALTER TABLE affirmations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hypnosis_scripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_sessions ENABLE ROW LEVEL SECURITY;

-- Service role policies (allows backend full access)
-- Using DO blocks to skip if policy already exists
DO $$
BEGIN
    CREATE POLICY "Service role full access on tenants" ON tenants FOR ALL USING (auth.role() = 'service_role');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE POLICY "Service role full access on users" ON users FOR ALL USING (auth.role() = 'service_role');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE POLICY "Service role full access on agents" ON agents FOR ALL USING (auth.role() = 'service_role');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE POLICY "Service role full access on agent_versions" ON agent_versions FOR ALL USING (auth.role() = 'service_role');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE POLICY "Service role full access on threads" ON threads FOR ALL USING (auth.role() = 'service_role');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE POLICY "Service role full access on thread_messages" ON thread_messages FOR ALL USING (auth.role() = 'service_role');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE POLICY "Service role full access on memory_embeddings" ON memory_embeddings FOR ALL USING (auth.role() = 'service_role');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE POLICY "Service role full access on user_discovery" ON user_discovery FOR ALL USING (auth.role() = 'service_role');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE POLICY "Service role full access on affirmations" ON affirmations FOR ALL USING (auth.role() = 'service_role');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE POLICY "Service role full access on hypnosis_scripts" ON hypnosis_scripts FOR ALL USING (auth.role() = 'service_role');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE POLICY "Service role full access on scheduled_sessions" ON scheduled_sessions FOR ALL USING (auth.role() = 'service_role');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- STEP 6: Insert default test data
-- ============================================================

-- Default tenant
INSERT INTO tenants (id, name, slug, status)
VALUES ('00000000-0000-0000-0000-000000000001', 'Default Tenant', 'default', 'active')
ON CONFLICT (id) DO NOTHING;

-- Default user
INSERT INTO users (id, tenant_id, email, name, status)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'test@numen.ai',
    'Test User',
    'active'
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- VERIFICATION
-- ============================================================

SELECT 'Safe migration completed successfully!' AS status;

-- Show all tables
SELECT
    tablename,
    schemaname
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
