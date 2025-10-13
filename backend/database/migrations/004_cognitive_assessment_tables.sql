-- ============================================================================
-- Migration 004: Cognitive Assessment Tables (Phase 1)
-- Purpose: Add goal/belief assessment infrastructure for Guide agents
-- Strategy: Additive only - no breaking changes to existing tables
-- ============================================================================

-- ============================================================================
-- 1. GOAL ASSESSMENTS (Goal Attainment Scaling)
-- ============================================================================
CREATE TABLE IF NOT EXISTS goal_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,

    -- Goal identification
    goal_text TEXT NOT NULL,
    goal_category VARCHAR(100),  -- career, health, relationships, financial, personal_growth

    -- GAS (Goal Attainment Scaling) -2 to +2 scale
    gas_current_level INT CHECK (gas_current_level BETWEEN -2 AND 2),
    gas_expected_level INT DEFAULT 0,  -- 0 = expected attainment
    gas_target_level INT DEFAULT 2,    -- +2 = much more than expected

    -- Ideal vs Actual ratings (0-100)
    ideal_state_rating INT CHECK (ideal_state_rating BETWEEN 0 AND 100),
    actual_state_rating INT CHECK (actual_state_rating BETWEEN 0 AND 100),

    -- Progress tracking
    initial_assessment_date TIMESTAMP DEFAULT NOW(),
    last_reassessment_date TIMESTAMP DEFAULT NOW(),
    reassessment_count INT DEFAULT 0,

    -- Metadata
    confidence_score FLOAT DEFAULT 0.5,  -- 0-1 confidence in goal clarity
    motivation_score FLOAT DEFAULT 0.5,  -- 0-1 user motivation level

    -- Behavioral tracking
    attempt_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    last_attempt_date TIMESTAMP,

    -- Schema versioning
    schema_version VARCHAR(20) DEFAULT 'v1.0',
    intake_depth VARCHAR(50) DEFAULT 'standard',  -- 'standard' or 'cognitive_extended'

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_goal_assessments_user ON goal_assessments(user_id);
CREATE INDEX idx_goal_assessments_agent ON goal_assessments(agent_id);
CREATE INDEX idx_goal_assessments_tenant ON goal_assessments(tenant_id);
CREATE INDEX idx_goal_assessments_category ON goal_assessments(goal_category);

-- ============================================================================
-- 2. BELIEF GRAPHS (Cognitive-Affective Mapping)
-- ============================================================================
CREATE TABLE IF NOT EXISTS belief_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,

    -- Graph identification
    graph_name VARCHAR(200) DEFAULT 'User Belief System',
    graph_version INT DEFAULT 1,

    -- Graph data (JSONB for flexibility)
    nodes JSONB NOT NULL,  -- Array of {id, label, type, emotional_valence, centrality}
    edges JSONB NOT NULL,  -- Array of {source, target, relationship, weight}

    -- Analysis metrics
    conflict_score FLOAT DEFAULT 0.0,  -- 0-1 overall tension in belief system
    tension_nodes JSONB,  -- Array of node IDs with high conflict
    core_beliefs JSONB,    -- Array of node IDs with highest centrality

    -- Schema versioning
    schema_version VARCHAR(20) DEFAULT 'v1.0',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_belief_graphs_user ON belief_graphs(user_id);
CREATE INDEX idx_belief_graphs_agent ON belief_graphs(agent_id);
CREATE INDEX idx_belief_graphs_tenant ON belief_graphs(tenant_id);

-- ============================================================================
-- 3. COGNITIVE METRICS (Emotional conflict, progress tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cognitive_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    thread_id UUID,  -- Optional link to conversation thread

    -- Metric type
    metric_type VARCHAR(100) NOT NULL,  -- emotion_conflict, goal_progress, belief_shift, etc.
    metric_category VARCHAR(100),       -- emotional, behavioral, cognitive

    -- Metric values
    metric_value FLOAT NOT NULL,        -- Primary metric value
    threshold_value FLOAT,              -- Threshold for triggering action
    threshold_exceeded BOOLEAN DEFAULT FALSE,

    -- Context
    context_data JSONB,  -- Additional context (e.g., which goal, which belief node)
    trigger_action VARCHAR(200),  -- Action to take if threshold exceeded

    -- Timestamps
    measured_at TIMESTAMP DEFAULT NOW(),

    -- Schema versioning
    schema_version VARCHAR(20) DEFAULT 'v1.0',

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cognitive_metrics_user ON cognitive_metrics(user_id);
CREATE INDEX idx_cognitive_metrics_agent ON cognitive_metrics(agent_id);
CREATE INDEX idx_cognitive_metrics_tenant ON cognitive_metrics(tenant_id);
CREATE INDEX idx_cognitive_metrics_type ON cognitive_metrics(metric_type);
CREATE INDEX idx_cognitive_metrics_threshold ON cognitive_metrics(threshold_exceeded);
CREATE INDEX idx_cognitive_metrics_measured ON cognitive_metrics(measured_at);

-- ============================================================================
-- 4. COGNITIVE SCHEMA VERSIONS (Optional, for kernel versioning)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cognitive_schema_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(20) UNIQUE NOT NULL,  -- e.g., 'v1.0', 'v1.1'

    -- Schema definition
    schema_definition JSONB NOT NULL,  -- Full CognitiveKernel JSON spec

    -- Metadata
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW(),
    deprecated_at TIMESTAMP
);

-- Insert default CognitiveKernel v1.0
INSERT INTO cognitive_schema_versions (version, schema_definition, description, is_default, is_active)
VALUES (
    'v1.0',
    '{
        "version": "v1.0",
        "goal_assessment": {
            "methods": ["GAS", "ideal_actual", "behavior_gap"],
            "tracking": true,
            "reassessment_triggers": ["significant_progress", "repeated_failure", "user_request"]
        },
        "belief_mapping": {
            "methods": ["CAM", "downward_arrow", "conflict_scoring"],
            "graph_storage": true,
            "analysis_enabled": true
        },
        "reflex_triggers": {
            "enabled": true,
            "emotion_threshold": 0.7,
            "failure_threshold": 2,
            "conflict_threshold": 0.8
        },
        "memory_integration": {
            "store_goal_vectors": true,
            "store_belief_graphs": true,
            "store_emotion_logs": true
        }
    }'::jsonb,
    'Default Cognitive Kernel v1.0 - Foundational goal/belief assessment framework',
    TRUE,
    TRUE
)
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- 5. EXTEND user_discovery TABLE (Non-breaking)
-- ============================================================================
-- Add optional cognitive assessment flags to existing user_discovery table
ALTER TABLE user_discovery
ADD COLUMN IF NOT EXISTS cognitive_assessment_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS gas_scores JSONB,  -- Store initial GAS ratings
ADD COLUMN IF NOT EXISTS belief_graph_id UUID REFERENCES belief_graphs(id),
ADD COLUMN IF NOT EXISTS intake_depth VARCHAR(50) DEFAULT 'standard';

-- ============================================================================
-- 6. HELPER VIEWS (Optional, for easy querying)
-- ============================================================================

-- View: Active goals with current progress
CREATE OR REPLACE VIEW active_goals_progress AS
SELECT
    ga.id,
    ga.user_id,
    ga.agent_id,
    ga.goal_text,
    ga.goal_category,
    ga.gas_current_level,
    ga.gas_expected_level,
    ga.gas_target_level,
    (ga.gas_current_level - ga.gas_expected_level) AS progress_delta,
    ga.actual_state_rating,
    ga.ideal_state_rating,
    (ga.ideal_state_rating - ga.actual_state_rating) AS gap_score,
    ga.confidence_score,
    ga.motivation_score,
    ga.reassessment_count,
    ga.updated_at
FROM goal_assessments ga
WHERE ga.gas_current_level < ga.gas_target_level
ORDER BY ga.updated_at DESC;

-- View: High-conflict beliefs requiring attention
CREATE OR REPLACE VIEW high_conflict_beliefs AS
SELECT
    bg.id,
    bg.user_id,
    bg.agent_id,
    bg.graph_name,
    bg.conflict_score,
    bg.tension_nodes,
    bg.core_beliefs,
    bg.updated_at
FROM belief_graphs bg
WHERE bg.conflict_score > 0.7
ORDER BY bg.conflict_score DESC;

-- View: Triggered cognitive alerts
CREATE OR REPLACE VIEW cognitive_alerts AS
SELECT
    cm.id,
    cm.user_id,
    cm.agent_id,
    cm.metric_type,
    cm.metric_value,
    cm.threshold_value,
    cm.trigger_action,
    cm.context_data,
    cm.measured_at
FROM cognitive_metrics cm
WHERE cm.threshold_exceeded = TRUE
    AND cm.measured_at > NOW() - INTERVAL '7 days'
ORDER BY cm.measured_at DESC;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- This migration is backward-compatible and additive only.
-- Existing agents will continue to function without cognitive assessment.
-- New agents with cognitive_kernel_ref will utilize these tables.
-- ============================================================================
