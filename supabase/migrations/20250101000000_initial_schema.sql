-- ============================================================================
-- Initial Schema Migration (Baseline from database.py)
-- Purpose: Establish all existing tables from inline schema
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- MULTI-TENANCY TABLES
-- ============================================================================

-- Tenants table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- AGENT SYSTEM TABLES
-- ============================================================================

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

-- ============================================================================
-- CONVERSATION TABLES
-- ============================================================================

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

-- ============================================================================
-- MEMORY SYSTEM (pgvector)
-- ============================================================================

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
CREATE INDEX IF NOT EXISTS idx_memory_embedding
ON memory_embeddings USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- SESSION MANAGEMENT
-- ============================================================================

-- Sessions table (replaces Redis)
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    agent_id UUID REFERENCES agents(id),
    tenant_id UUID REFERENCES tenants(id),
    status TEXT NOT NULL,
    room_name TEXT,

    -- Session state (replaces Redis)
    session_data JSONB,
    expires_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- Contracts table (session contracts, not agent contracts)
CREATE TABLE IF NOT EXISTS contracts (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    user_id TEXT NOT NULL,
    goals JSONB NOT NULL,
    tone TEXT NOT NULL,
    voice_id TEXT NOT NULL,
    session_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    speaker TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- MANIFESTATION PROTOCOLS (Legacy Numen AI)
-- ============================================================================

-- Manifestation protocols table
CREATE TABLE IF NOT EXISTS manifestation_protocols (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    goal TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    commitment_level TEXT NOT NULL,
    protocol_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Protocol checkpoints table
CREATE TABLE IF NOT EXISTS protocol_checkpoints (
    id UUID PRIMARY KEY,
    protocol_id UUID REFERENCES manifestation_protocols(id),
    checkpoint_day INTEGER NOT NULL,
    data JSONB NOT NULL,
    logged_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- USER DISCOVERY & AFFIRMATION PIPELINE
-- ============================================================================

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

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
