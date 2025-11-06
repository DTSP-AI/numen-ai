# Asset Creation and Scheduling System for Guides

## Overview
This document outlines the complete architecture for Guides to create personalized assets (affirmations, hypnosis scripts, daily practices, visualizations) and schedule tailored plans based on the discovery conversation.

## System Architecture

### 1. Discovery → Asset Pipeline

```
IntakeAgentCognitive (Discovery)
    ↓
Goal Assessments + Belief Graphs
    ↓
AssetGenerationAgent
    ↓
Affirmations, Scripts, Practices, Visualizations
    ↓
SchedulingEngine
    ↓
Personalized Plan (Daily/Weekly Schedule)
```

---

## Phase 1: Asset Generation Agent

### Purpose
Generate personalized content assets tailored to user's goals, beliefs, and cognitive assessment data.

### Location
`backend/agents/asset_generation_agent.py`

### Key Features

#### 1. Multi-Asset Generator
```python
class AssetGenerationAgent:
    """
    Generates personalized assets from cognitive assessment data

    Assets:
    - Affirmations (identity, gratitude, action-based)
    - Hypnosis scripts (15-30 min guided sessions)
    - Daily practices (micro-habits, rituals)
    - Visualizations (guided imagery scenarios)
    - Progress checkpoints (weekly reflection prompts)
    """

    async def generate_from_discovery(
        self,
        user_id: str,
        tenant_id: str,
        agent_id: str,
        cognitive_data: CognitiveDiscoveryData,
        preferences: Dict[str, Any]
    ) -> GeneratedAssets:
        """
        Generate complete asset suite from discovery data

        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            agent_id: Guide agent UUID
            cognitive_data: From IntakeAgentCognitive
            preferences: User preferences (tone, intensity, schedule)

        Returns:
            GeneratedAssets with affirmations, scripts, practices, etc.
        """
```

#### 2. Affirmation Generation
```python
async def generate_affirmations(
    self,
    goals: List[str],
    belief_graph: Dict[str, Any],
    goal_assessments: Dict[str, Dict],
    count: int = 21  # 3 weeks of daily affirmations
) -> List[Affirmation]:
    """
    Generate affirmations that:
    1. Reinforce positive beliefs
    2. Counter limiting beliefs
    3. Support goal attainment
    4. Build on GAS current levels

    Types:
    - Identity affirmations ("I am...")
    - Gratitude affirmations ("I'm grateful for...")
    - Action affirmations ("I take action...")
    - Process affirmations ("I'm becoming...")
    """
```

#### 3. Hypnosis Script Generation
```python
async def generate_hypnosis_script(
    self,
    primary_goal: str,
    session_type: str,  # "deep_change", "anxiety_relief", "confidence_building"
    duration_minutes: int = 20,
    belief_graph: Dict[str, Any] = None
) -> HypnosisScript:
    """
    Generate complete hypnosis script with:
    - Induction phase (5 min)
    - Deepening phase (3 min)
    - Therapeutic suggestions (10 min)
    - Emergence phase (2 min)

    Includes:
    - Pacing markers for TTS
    - Embedded belief reframes
    - Goal-aligned visualizations
    """
```

#### 4. Daily Practice Generation
```python
async def generate_daily_practices(
    self,
    goals: List[str],
    commitment_level: str,  # "light", "moderate", "intensive"
    goal_categories: List[str]
) -> List[DailyPractice]:
    """
    Generate micro-practices (5-15 min each):

    Examples:
    - Morning intention setting (5 min)
    - Gratitude journaling (5 min)
    - Visualization practice (10 min)
    - Evening reflection (10 min)
    - Body scan meditation (15 min)
    """
```

---

## Phase 2: Scheduling Engine

### Purpose
Create personalized schedules that respect user's availability, commitment level, and optimal timing.

### Location
`backend/services/scheduling_engine.py`

### Key Features

#### 1. Schedule Builder
```python
class SchedulingEngine:
    """
    Builds personalized schedules from generated assets

    Considerations:
    - User's available time windows
    - Commitment level (light/moderate/intensive)
    - Goal priority and urgency
    - Optimal timing (morning/evening practices)
    - Variety and rotation
    """

    async def build_schedule(
        self,
        user_id: str,
        tenant_id: str,
        agent_id: str,
        assets: GeneratedAssets,
        preferences: SchedulePreferences
    ) -> PersonalizedSchedule:
        """
        Create complete schedule with:
        - Daily affirmation delivery times
        - Weekly hypnosis session slots
        - Daily practice assignments
        - Progress checkpoint dates
        - Reassessment triggers
        """
```

#### 2. Schedule Templates
```python
# Light Commitment (15-20 min/day)
LIGHT_SCHEDULE = {
    "morning": ["affirmation", "intention_setting"],  # 5 min
    "evening": ["affirmation", "reflection"]  # 5 min
}

# Moderate Commitment (30-45 min/day)
MODERATE_SCHEDULE = {
    "morning": ["affirmation", "visualization", "intention"],  # 15 min
    "midday": ["affirmation"],  # 2 min
    "evening": ["affirmation", "reflection", "gratitude"]  # 15 min
}

# Intensive Commitment (60+ min/day)
INTENSIVE_SCHEDULE = {
    "morning": ["affirmation", "meditation", "visualization", "intention"],  # 30 min
    "midday": ["affirmation", "micro_practice"],  # 10 min
    "evening": ["affirmation", "hypnosis_script", "reflection"]  # 30 min
}
```

#### 3. Recurrence Rules
```python
class RecurrenceEngine:
    """
    Generate iCal-compatible recurrence rules

    Patterns:
    - DAILY: Every day at specific time
    - WEEKDAYS: Monday-Friday only
    - CUSTOM: User-selected days
    - PROGRESSIVE: Gradually increase frequency
    """

    def create_recurrence(
        self,
        pattern: str,
        start_date: datetime,
        duration_days: int,
        time_slots: List[time]
    ) -> str:
        """Returns RRULE string for calendar integration"""
```

---

## Phase 3: Database Schema (Migration 005)

### New Tables

#### 1. `asset_library` - Generated Assets
```sql
CREATE TABLE asset_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Asset metadata
    asset_type VARCHAR(50) NOT NULL,  -- 'affirmation', 'script', 'practice', 'visualization'
    title VARCHAR(500),
    content TEXT NOT NULL,

    -- Context
    associated_goal_id UUID REFERENCES goal_assessments(id),
    belief_node_ids JSONB,  -- Link to belief graph nodes

    -- Delivery settings
    duration_seconds INT,
    optimal_time_of_day VARCHAR(20),  -- 'morning', 'afternoon', 'evening', 'night'
    energy_level VARCHAR(20),  -- 'calm', 'energizing', 'neutral'

    -- Audio synthesis
    audio_url TEXT,
    audio_duration_seconds INT,
    voice_settings JSONB,
    tts_provider VARCHAR(50),

    -- Usage tracking
    usage_count INT DEFAULT 0,
    last_used_at TIMESTAMP,
    effectiveness_score FLOAT,  -- User feedback

    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'archived', 'draft'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_asset_library_user ON asset_library(user_id);
CREATE INDEX idx_asset_library_type ON asset_library(asset_type);
CREATE INDEX idx_asset_library_goal ON asset_library(associated_goal_id);
CREATE INDEX idx_asset_library_status ON asset_library(status);
```

#### 2. `personalized_schedules` - User Plans
```sql
CREATE TABLE personalized_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Schedule metadata
    schedule_name VARCHAR(200),
    commitment_level VARCHAR(20),  -- 'light', 'moderate', 'intensive'
    duration_days INT,  -- Total plan duration

    -- Timeline
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    -- Schedule definition (JSONB for flexibility)
    daily_slots JSONB NOT NULL,  -- {morning: [asset_ids], evening: [asset_ids]}
    weekly_structure JSONB,  -- Week-by-week progression

    -- Linked assessments
    goal_assessment_ids JSONB,  -- Array of goal UUIDs
    belief_graph_id UUID REFERENCES belief_graphs(id),

    -- Progress tracking
    completion_percentage FLOAT DEFAULT 0.0,
    streak_days INT DEFAULT 0,
    missed_days INT DEFAULT 0,
    last_activity_date DATE,

    -- Reassessment triggers
    next_reassessment_date DATE,
    reassessment_frequency_days INT DEFAULT 14,  -- Reassess every 2 weeks

    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'paused', 'completed'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_schedules_user ON personalized_schedules(user_id);
CREATE INDEX idx_schedules_status ON personalized_schedules(status);
CREATE INDEX idx_schedules_dates ON personalized_schedules(start_date, end_date);
```

#### 3. `schedule_deliveries` - Daily Activity Log
```sql
CREATE TABLE schedule_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES personalized_schedules(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    asset_id UUID NOT NULL REFERENCES asset_library(id),

    -- Delivery timing
    scheduled_for TIMESTAMP NOT NULL,
    delivered_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Execution status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'delivered', 'completed', 'skipped', 'missed'

    -- User interaction
    engagement_duration_seconds INT,
    feedback_score INT,  -- 1-5 stars
    feedback_comment TEXT,

    -- Notification
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_type VARCHAR(50),  -- 'push', 'email', 'sms', 'in_app'

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_deliveries_schedule ON schedule_deliveries(schedule_id);
CREATE INDEX idx_deliveries_user ON schedule_deliveries(user_id);
CREATE INDEX idx_deliveries_scheduled ON schedule_deliveries(scheduled_for, status);
CREATE INDEX idx_deliveries_status ON schedule_deliveries(status);
```

---

## Phase 4: API Endpoints

### Location
`backend/routers/guide_assets.py`

### Endpoints

#### 1. Generate Assets from Discovery
```python
@router.post("/guides/{agent_id}/generate-assets")
async def generate_assets_from_discovery(
    agent_id: str,
    request: GenerateAssetsRequest,
    user_id: str = Header(None, alias="x-user-id"),
    tenant_id: str = Header(None, alias="x-tenant-id")
):
    """
    Generate complete asset suite from cognitive discovery data

    Body:
    {
        "discovery_session_id": "uuid",
        "preferences": {
            "commitment_level": "moderate",
            "preferred_times": ["08:00", "20:00"],
            "duration_days": 30,
            "focus_areas": ["confidence", "career"]
        }
    }

    Response:
    {
        "assets": {
            "affirmations": [...],  # 21 affirmations
            "scripts": [...],  # 3 hypnosis scripts
            "practices": [...],  # 5 daily practices
            "visualizations": [...]  # 3 visualization exercises
        },
        "schedule": {
            "id": "uuid",
            "daily_slots": {...},
            "weekly_structure": {...}
        },
        "summary": {
            "total_assets": 32,
            "estimated_daily_time": "30 minutes",
            "plan_duration": "30 days"
        }
    }
    """
```

#### 2. Get User Schedule
```python
@router.get("/users/{user_id}/schedule/current")
async def get_current_schedule(
    user_id: str,
    tenant_id: str = Header(None, alias="x-tenant-id")
):
    """
    Get user's active personalized schedule

    Response:
    {
        "schedule": {...},
        "today_activities": [...],
        "upcoming_activities": [...],
        "progress": {
            "completion_percentage": 67.5,
            "streak_days": 12,
            "next_checkpoint": "2025-10-20"
        }
    }
    """
```

#### 3. Get Today's Activities
```python
@router.get("/users/{user_id}/schedule/today")
async def get_today_activities(
    user_id: str,
    tenant_id: str = Header(None, alias="x-tenant-id")
):
    """
    Get all scheduled activities for today

    Response:
    {
        "date": "2025-10-13",
        "activities": [
            {
                "time": "08:00",
                "type": "affirmation",
                "asset": {...},
                "status": "pending",
                "duration_seconds": 60
            },
            ...
        ],
        "total_time_minutes": 30,
        "completed_count": 2,
        "pending_count": 3
    }
    """
```

#### 4. Mark Activity Complete
```python
@router.post("/schedule/deliveries/{delivery_id}/complete")
async def mark_activity_complete(
    delivery_id: str,
    request: CompleteActivityRequest
):
    """
    Mark scheduled activity as completed

    Body:
    {
        "completed_at": "2025-10-13T08:15:00Z",
        "engagement_duration_seconds": 90,
        "feedback_score": 5,
        "feedback_comment": "Very helpful today!"
    }

    Updates:
    - schedule_deliveries.status = 'completed'
    - asset_library.usage_count += 1
    - personalized_schedules.completion_percentage
    - Check and update streak_days
    """
```

---

## Phase 5: Integration Points

### 1. Post-Discovery Workflow
```python
# In backend/routers/intake.py

@router.post("/intake/complete")
async def complete_intake(request: CompleteIntakeRequest):
    """
    After discovery conversation completes:

    1. Run IntakeAgentCognitive to extract:
       - Goals (with GAS ratings)
       - Beliefs (graph structure)
       - Preferences (schedule, tone)

    2. Save cognitive assessment to DB

    3. Call AssetGenerationAgent to create:
       - 21 affirmations
       - 3 hypnosis scripts
       - 5 daily practices

    4. Call SchedulingEngine to create:
       - Personalized schedule
       - Daily delivery slots
       - Checkpoint dates

    5. Return complete plan to frontend
    """
```

### 2. Daily Delivery Scheduler
```python
# In backend/services/delivery_scheduler.py

class DeliveryScheduler:
    """
    Background task that runs every hour

    Checks:
    1. Pending deliveries for current hour
    2. Sends notifications (push, email, SMS)
    3. Updates delivery status
    4. Tracks missed activities
    5. Triggers reassessment if needed
    """

    async def process_pending_deliveries(self):
        """Process all deliveries scheduled for current hour"""

    async def send_notification(self, delivery: ScheduleDelivery):
        """Send push notification for scheduled activity"""

    async def check_reassessment_triggers(self, user_id: str):
        """Check if user needs cognitive reassessment"""
```

### 3. Progress Analytics
```python
# In backend/routers/analytics.py

@router.get("/users/{user_id}/progress")
async def get_user_progress(user_id: str):
    """
    Analytics dashboard showing:
    - Completion rates by asset type
    - Streak tracking
    - Goal progress (GAS level changes)
    - Belief conflict trends
    - Engagement patterns
    - Effectiveness scores
    """
```

---

## Phase 6: Frontend Integration

### Location
`frontend/src/components/Guide/`

### Components

#### 1. `AssetGallery.tsx`
- Display all generated assets
- Filter by type, goal, status
- Play audio, read scripts
- Mark favorites

#### 2. `DailySchedule.tsx`
- Show today's activities
- Mark activities complete
- Track streak
- View upcoming activities

#### 3. `ProgressDashboard.tsx`
- Completion statistics
- Goal progress charts
- Belief conflict trends
- Reassessment prompts

#### 4. `AssetPlayer.tsx`
- Audio playback for affirmations
- Guided script reading
- Timer for practices
- Completion tracking

---

## Implementation Checklist

### Database (Priority 1)
- [ ] Create `asset_library` table (migration 005)
- [ ] Create `personalized_schedules` table
- [ ] Create `schedule_deliveries` table
- [ ] Run migration and verify indexes

### Backend Services (Priority 1)
- [ ] Implement `AssetGenerationAgent` class
- [ ] Implement `SchedulingEngine` class
- [ ] Create asset generation prompts (templates)
- [ ] Wire asset generation into intake completion

### API Endpoints (Priority 2)
- [ ] POST `/guides/{agent_id}/generate-assets`
- [ ] GET `/users/{user_id}/schedule/current`
- [ ] GET `/users/{user_id}/schedule/today`
- [ ] POST `/schedule/deliveries/{delivery_id}/complete`
- [ ] GET `/users/{user_id}/assets`

### Background Tasks (Priority 2)
- [ ] Implement `DeliveryScheduler` service
- [ ] Set up hourly cron job
- [ ] Notification sending (push/email)
- [ ] Reassessment trigger checking

### Frontend (Priority 3)
- [ ] `AssetGallery` component
- [ ] `DailySchedule` component
- [ ] `ProgressDashboard` component
- [ ] `AssetPlayer` component
- [ ] Integration with Guide chat interface

### Testing (Priority 3)
- [ ] Test asset generation from discovery data
- [ ] Test schedule creation
- [ ] Test daily delivery flow
- [ ] Test completion tracking
- [ ] Test reassessment triggers

---

## Success Metrics

1. **Asset Quality**
   - Generated assets feel personalized and relevant
   - Users rate assets 4+ stars on average
   - Audio synthesis sounds natural

2. **Schedule Adherence**
   - Users complete 70%+ of scheduled activities
   - Maintain 7+ day streaks
   - Low "missed" activity rate

3. **Goal Progress**
   - GAS levels improve over 30 days
   - Users report progress at checkpoints
   - Belief conflict scores decrease

4. **Engagement**
   - Daily active usage 60%+
   - Asset variety prevents boredom
   - Users customize their schedule

---

## Future Enhancements

### Phase 7: Adaptive Scheduling
- ML-based optimal timing (when user is most engaged)
- Dynamic difficulty adjustment
- Content rotation based on effectiveness

### Phase 8: Social Features
- Share favorite affirmations
- Group challenges
- Accountability partners

### Phase 9: Advanced Analytics
- Sentiment analysis of user feedback
- Correlation between assets and goal progress
- Predictive reassessment triggers
