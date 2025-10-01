# Numen AI Agent Pipeline Architecture
**Contract-First Manifestation OS**

---

## 🎯 System Overview

Numen AI is a **memory-aware, agent-driven manifestation operating system** that combines:
- Manifestation psychology (Law of Attraction, Quantum Theory metaphors)
- Cognitive-Behavioral Therapy (CBT) principles
- Positive Psychology frameworks
- Hypnotherapy pacing and scripting
- Real-time voice synthesis with ElevenLabs
- Persistent memory and scheduling

All agents follow the **AGENT_CREATION_STANDARD** - 100% JSON contract-driven behavior.

---

## 🔁 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NUMEN AI PIPELINE                        │
└─────────────────────────────────────────────────────────────────┘

User Input
    ↓
┌───────────────────┐
│  INTAKE AGENT     │  Role: Prompt Engineer
│  (Discovery)      │  • Gathers goals, beliefs, outcomes, schedule
│                   │  • Validates user intent
│                   │  • Generates AffirmationAgent JSON contract
└─────────┬─────────┘
          │ JSON Contract
          ↓
┌───────────────────┐
│ AFFIRMATION AGENT │  Role: Manifestation Guide + Voice
│  (Generation)     │  • Created dynamically from contract
│                   │  • Generates affirmations, mantras, scripts
│                   │  • Applies psychology + hypnotherapy principles
│                   │  • Produces text + schedules
└─────────┬─────────┘
          │ Outputs (text + metadata)
          ↓
┌───────────────────┐
│  OUTPUT LAYER     │  • ElevenLabs voice synthesis
│  (Audio Synth)    │  • .mp3/.wav generation
│                   │  • Audio persistence
└─────────┬─────────┘
          │ Audio + Text + Schedule
          ↓
┌───────────────────┐
│ DASHBOARD AGENT   │  Role: Archivist + Editor
│  (Persistence)    │  • Stores all outputs
│                   │  • Displays affirmations, scripts, audio
│                   │  • Editing + replay capabilities
│                   │  • Thread management
└───────────────────┘
```

---

## 🧩 Agent Roles & Responsibilities

### 1. IntakeAgent (Prompt Engineer)

**Purpose**: Convert raw user discovery into a production-ready AffirmationAgent contract

**Responsibilities**:
- Conduct structured intake interview
- Extract goals, limiting beliefs, desired outcomes, preferences
- Validate psychological safety and user intent
- Generate comprehensive JSON contract for AffirmationAgent
- Store discovery data in user namespace

**Identity Traits**:
```json
{
  "creativity": 70,
  "empathy": 95,
  "assertiveness": 50,
  "formality": 40,
  "verbosity": 60,
  "confidence": 80
}
```

**Key Outputs**:
- User discovery data (JSON)
- AffirmationAgent JSON contract
- Initial thread context

---

### 2. AffirmationAgent (Manifestation Guide)

**Purpose**: Generate psychologically-grounded affirmations, mantras, and hypnosis scripts

**Responsibilities**:
- Create personalized affirmations based on user goals
- Generate mantras for reinforcement
- Write hypnotherapy scripts with proper pacing
- Apply Law of Attraction + Quantum Theory metaphors
- Integrate CBT/Positive Psychology principles
- Include scheduling metadata (morning/evening/weekly)
- Configure voice synthesis parameters

**Identity Traits**:
```json
{
  "creativity": 85,
  "empathy": 90,
  "assertiveness": 65,
  "formality": 45,
  "verbosity": 70,
  "confidence": 85,
  "safety": 95
}
```

**Psychological Frameworks Applied**:
1. **Law of Attraction**: Present-tense, positive affirmations
2. **Quantum Theory Metaphors**: Observer effect, energy alignment
3. **CBT**: Cognitive restructuring, thought replacement
4. **Positive Psychology**: Gratitude, strengths-based focus
5. **Hypnotherapy**: Repetition, pacing, deepening techniques

**Key Outputs**:
- Affirmations (text)
- Mantras (text)
- Hypnosis scripts (text with pacing markers)
- Scheduling data (frequency, time-of-day)
- Voice configuration (tone, pace, style)

---

### 3. DashboardAgent (Archivist + Editor)

**Purpose**: Manage persistence, display, and editing of all generated content

**Responsibilities**:
- Store all affirmations, scripts, audio files
- Display content in organized timeline/categories
- Enable editing and regeneration
- Manage scheduling and reminders
- Track usage analytics (plays, edits, favorites)
- Thread history management

**Identity Traits**:
```json
{
  "creativity": 40,
  "empathy": 70,
  "assertiveness": 60,
  "formality": 60,
  "verbosity": 50,
  "confidence": 75
}
```

**Key Functions**:
- Content CRUD operations
- Audio playback interface
- Schedule management
- Analytics dashboard
- Export capabilities (PDF, audio zip)

---

## 📦 JSON Contract Examples

### IntakeAgent Contract

```json
{
  "id": "intake-agent-001",
  "name": "IntakeAgent - Discovery Specialist",
  "type": "conversational",
  "version": "1.0.0",

  "identity": {
    "short_description": "Empathetic discovery specialist for manifestation coaching",
    "full_description": "A skilled interviewer who gently extracts user goals, limiting beliefs, and desired outcomes to create a personalized manifestation program. Trained in motivational interviewing and positive psychology.",
    "character_role": "Discovery Coach",
    "mission": "Gather comprehensive user data to engineer the perfect AffirmationAgent contract",
    "interaction_style": "Warm, curious, non-judgmental, encouraging, psychologically-informed"
  },

  "traits": {
    "creativity": 70,
    "empathy": 95,
    "assertiveness": 50,
    "humor": 40,
    "formality": 40,
    "verbosity": 60,
    "confidence": 80,
    "technicality": 30,
    "safety": 90
  },

  "configuration": {
    "llm_provider": "openai",
    "llm_model": "gpt-4",
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
    "voice_id": "warm-female-coach",
    "language": "en-US",
    "speed": 1.0,
    "stability": 0.75,
    "similarity_boost": 0.75
  },

  "metadata": {
    "tenant_id": "numen-ai-tenant",
    "owner_id": "system",
    "tags": ["intake", "discovery", "production"],
    "status": "active"
  }
}
```

---

### AffirmationAgent Contract (Generated by IntakeAgent)

```json
{
  "id": "affirmation-agent-{user_id}",
  "name": "AffirmationAgent - {User's Name} Manifestation Guide",
  "type": "voice",
  "version": "1.0.0",

  "identity": {
    "short_description": "Personalized manifestation guide for {specific_goal}",
    "full_description": "A nurturing guide specializing in {user_focus_area} manifestation, using Law of Attraction principles combined with evidence-based positive psychology to help {user_name} achieve {primary_goal}.",
    "character_role": "Manifestation Coach & Hypnotherapist",
    "mission": "Help {user_name} manifest {primary_goal} through daily affirmations, mantras, and hypnotherapy sessions",
    "interaction_style": "Soothing, confident, empowering, deeply affirming"
  },

  "traits": {
    "creativity": 85,
    "empathy": 90,
    "assertiveness": 65,
    "humor": 30,
    "formality": 45,
    "verbosity": 70,
    "confidence": 85,
    "technicality": 40,
    "safety": 95
  },

  "configuration": {
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "max_tokens": 1500,
    "temperature": 0.8,
    "memory_enabled": true,
    "voice_enabled": true,
    "tools_enabled": false
  },

  "voice": {
    "provider": "elevenlabs",
    "voice_id": "soothing-hypnotherapy",
    "language": "en-US",
    "speed": 0.9,
    "pitch": 1.0,
    "stability": 0.85,
    "similarity_boost": 0.80
  },

  "behavioral_directives": {
    "psychological_framework": "Law of Attraction + CBT + Positive Psychology",
    "affirmation_style": "present-tense, first-person, positive, specific",
    "hypnotherapy_techniques": ["progressive relaxation", "visualization", "repetition"],
    "content_themes": ["{user_goals}", "{limiting_beliefs_to_reframe}"],
    "scheduling": {
      "morning_affirmations": true,
      "evening_hypnosis": true,
      "weekly_review": true
    }
  },

  "metadata": {
    "tenant_id": "numen-ai-tenant",
    "owner_id": "{user_id}",
    "tags": ["affirmation", "manifestation", "personalized"],
    "status": "active",
    "user_context": {
      "goals": ["{goal_1}", "{goal_2}"],
      "limiting_beliefs": ["{belief_1}", "{belief_2}"],
      "preferred_schedule": "morning 7am, evening 9pm"
    }
  }
}
```

---

### DashboardAgent Contract

```json
{
  "id": "dashboard-agent-001",
  "name": "DashboardAgent - Content Manager",
  "type": "workflow",
  "version": "1.0.0",

  "identity": {
    "short_description": "Content management and persistence layer for manifestation outputs",
    "full_description": "A reliable archivist that stores, organizes, and serves all affirmations, scripts, and audio files. Provides editing, scheduling, and analytics capabilities.",
    "character_role": "Digital Archivist & Content Manager",
    "mission": "Ensure no manifestation content is lost; provide seamless access to all user outputs",
    "interaction_style": "Professional, organized, efficient, supportive"
  },

  "traits": {
    "creativity": 40,
    "empathy": 70,
    "assertiveness": 60,
    "formality": 60,
    "verbosity": 50,
    "confidence": 75,
    "technicality": 70,
    "safety": 85
  },

  "configuration": {
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",
    "max_tokens": 500,
    "temperature": 0.5,
    "memory_enabled": true,
    "voice_enabled": false,
    "tools_enabled": true
  },

  "capabilities": {
    "tools": ["database_query", "file_storage", "scheduler", "analytics"],
    "integrations": ["supabase", "elevenlabs", "calendar"]
  },

  "metadata": {
    "tenant_id": "numen-ai-tenant",
    "owner_id": "system",
    "tags": ["dashboard", "persistence", "production"],
    "status": "active"
  }
}
```

---

## 🗄️ Database Schema Extensions

### New Tables for Numen AI Pipeline

```sql
-- User Discovery Data (from IntakeAgent)
CREATE TABLE user_discovery (
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

-- Affirmations (generated by AffirmationAgent)
CREATE TABLE affirmations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Content
    title TEXT,
    affirmation_text TEXT NOT NULL,
    category TEXT, -- "morning", "evening", "emergency", "general"
    tags TEXT[],

    -- Audio
    audio_url TEXT,
    audio_duration_seconds INT,
    voice_settings JSONB,

    -- Scheduling
    schedule_type TEXT, -- "daily", "weekly", "monthly", "one-time"
    schedule_time TIME,
    schedule_days TEXT[], -- ["monday", "wednesday", "friday"]

    -- Analytics
    play_count INT DEFAULT 0,
    last_played_at TIMESTAMP,
    is_favorite BOOLEAN DEFAULT false,

    -- Metadata
    status TEXT DEFAULT 'active', -- "active", "archived", "draft"
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_affirmations_user ON affirmations(user_id);
CREATE INDEX idx_affirmations_schedule ON affirmations(schedule_type, schedule_time);
CREATE INDEX idx_affirmations_status ON affirmations(status);

-- Hypnosis Scripts (generated by AffirmationAgent)
CREATE TABLE hypnosis_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Content
    title TEXT NOT NULL,
    script_text TEXT NOT NULL,
    duration_minutes INT,
    pacing_markers JSONB, -- {"pause": [10, 25, 40], "deepen": [15, 30]}

    -- Audio
    audio_url TEXT,
    voice_settings JSONB,

    -- Metadata
    session_type TEXT, -- "induction", "deepening", "suggestion", "emergence"
    focus_area TEXT, -- "abundance", "health", "relationships", etc.

    -- Analytics
    play_count INT DEFAULT 0,
    last_played_at TIMESTAMP,
    completion_rate FLOAT, -- 0.0-1.0

    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scripts_user ON hypnosis_scripts(user_id);
CREATE INDEX idx_scripts_focus ON hypnosis_scripts(focus_area);

-- Scheduled Sessions
CREATE TABLE scheduled_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    affirmation_id UUID REFERENCES affirmations(id),
    script_id UUID REFERENCES hypnosis_scripts(id),

    -- Schedule
    scheduled_at TIMESTAMP NOT NULL,
    recurrence_rule TEXT, -- "FREQ=DAILY;BYHOUR=7", etc. (iCal format)
    timezone TEXT DEFAULT 'UTC',

    -- Execution
    executed_at TIMESTAMP,
    execution_status TEXT, -- "pending", "sent", "played", "skipped", "failed"

    -- Notification
    notification_sent BOOLEAN DEFAULT false,
    notification_type TEXT, -- "push", "email", "sms"

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scheduled_pending ON scheduled_sessions(scheduled_at, execution_status);
CREATE INDEX idx_scheduled_user ON scheduled_sessions(user_id);
```

---

## 🔧 Implementation Workflow

### Phase 1: Core Pipeline Setup

**1. Create Agent Contracts**
```bash
backend/prompts/intake-agent-001/agent_specific_prompt.json
backend/prompts/dashboard-agent-001/agent_specific_prompt.json
```

**2. Implement IntakeAgent Flow**
```python
# backend/services/intake_service.py
class IntakeService:
    async def conduct_discovery(user_id, tenant_id) -> dict:
        """Run intake interview with user"""

    async def generate_affirmation_agent_contract(discovery_data) -> AgentContract:
        """Convert discovery into AffirmationAgent JSON contract"""

    async def create_affirmation_agent(contract) -> AgentResponse:
        """Instantiate AffirmationAgent in database"""
```

**3. Implement AffirmationAgent Flow**
```python
# backend/services/affirmation_service.py
class AffirmationService:
    async def generate_affirmations(agent_id, user_id) -> List[Affirmation]:
        """Generate personalized affirmations"""

    async def generate_hypnosis_script(agent_id, user_id, focus_area) -> HypnosisScript:
        """Generate hypnotherapy script"""

    async def synthesize_audio(text, voice_config) -> str:
        """Generate audio via ElevenLabs"""
```

**4. Implement DashboardAgent Flow**
```python
# backend/services/dashboard_service.py
class DashboardService:
    async def get_user_affirmations(user_id) -> List[Affirmation]:
        """Retrieve all user affirmations"""

    async def get_user_scripts(user_id) -> List[HypnosisScript]:
        """Retrieve all hypnosis scripts"""

    async def update_content(content_id, updates) -> bool:
        """Edit affirmation or script"""

    async def track_playback(content_id):
        """Record audio playback event"""
```

---

### Phase 2: API Endpoints

```python
# backend/routers/numen.py

@router.post("/intake/start")
async def start_intake_session(user_id, tenant_id):
    """Begin intake interview"""

@router.post("/intake/complete")
async def complete_intake(discovery_data):
    """Process discovery data and create AffirmationAgent"""

@router.post("/affirmations/generate")
async def generate_affirmations(agent_id, user_id):
    """Generate new affirmations"""

@router.post("/scripts/generate")
async def generate_hypnosis_script(agent_id, user_id, focus_area):
    """Generate hypnotherapy script"""

@router.get("/dashboard/content")
async def get_dashboard_content(user_id):
    """Get all user content for dashboard"""

@router.patch("/content/{content_id}")
async def update_content(content_id, updates):
    """Edit content"""

@router.post("/content/{content_id}/play")
async def track_playback(content_id):
    """Record playback event"""
```

---

## 🎵 ElevenLabs Integration

```python
# backend/services/audio_synthesis.py
from elevenlabs import ElevenLabs, VoiceSettings

class AudioSynthesisService:
    def __init__(self):
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)

    async def synthesize_affirmation(
        self,
        text: str,
        voice_config: VoiceConfiguration
    ) -> str:
        """
        Generate audio from affirmation text
        Returns: S3/Supabase URL of .mp3 file
        """
        audio = self.client.generate(
            text=text,
            voice=voice_config.voice_id,
            model="eleven_turbo_v2",
            voice_settings=VoiceSettings(
                stability=voice_config.stability,
                similarity_boost=voice_config.similarity_boost,
                speed=voice_config.speed
            )
        )

        # Upload to storage
        audio_url = await self.upload_audio(audio, user_id, content_id)
        return audio_url

    async def synthesize_hypnosis_script(
        self,
        script_text: str,
        voice_config: VoiceConfiguration,
        pacing_markers: dict
    ) -> str:
        """
        Generate hypnosis audio with pacing
        Includes pauses, deepening cues, etc.
        """
        # Insert SSML for pacing
        ssml_text = self.apply_pacing_markers(script_text, pacing_markers)

        audio = self.client.generate(
            text=ssml_text,
            voice=voice_config.voice_id,
            model="eleven_multilingual_v2"
        )

        audio_url = await self.upload_audio(audio, user_id, script_id)
        return audio_url
```

---

## 📅 Scheduling System

```python
# backend/services/scheduler_service.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    async def schedule_affirmation(
        self,
        affirmation_id: str,
        user_id: str,
        schedule_type: str,
        schedule_time: str,
        schedule_days: List[str]
    ):
        """
        Schedule recurring affirmation playback
        Creates scheduled_sessions records
        """
        if schedule_type == "daily":
            # Every day at schedule_time
            self.scheduler.add_job(
                func=self.send_affirmation_reminder,
                trigger="cron",
                hour=schedule_time.hour,
                minute=schedule_time.minute,
                args=[affirmation_id, user_id]
            )

        elif schedule_type == "weekly":
            # Specific days of week
            self.scheduler.add_job(
                func=self.send_affirmation_reminder,
                trigger="cron",
                day_of_week=",".join(schedule_days),
                hour=schedule_time.hour,
                minute=schedule_time.minute,
                args=[affirmation_id, user_id]
            )

    async def send_affirmation_reminder(
        self,
        affirmation_id: str,
        user_id: str
    ):
        """
        Send push notification/email reminder
        Create scheduled_sessions record
        """
        # Record scheduled session
        await db.execute("""
            INSERT INTO scheduled_sessions (
                user_id, affirmation_id, scheduled_at, execution_status
            )
            VALUES ($1, $2, NOW(), 'sent')
        """, user_id, affirmation_id)

        # Send notification
        await notification_service.send_push(
            user_id,
            title="Time for Your Affirmation",
            body="Your daily manifestation practice is ready"
        )
```

---

## 🧪 Example User Flow

### Complete Numen AI Experience

```python
# Step 1: User starts intake
intake_session = await IntakeService.conduct_discovery(
    user_id="user-123",
    tenant_id="numen-ai"
)

# User provides:
# - Goals: "Financial abundance", "Career success"
# - Limiting beliefs: "Money is scarce", "I'm not good enough"
# - Schedule: Morning 7am, Evening 9pm

# Step 2: IntakeAgent generates AffirmationAgent contract
discovery_data = {
    "goals": ["Financial abundance", "Career success"],
    "limiting_beliefs": ["Money is scarce", "I'm not good enough"],
    "schedule": "7am, 9pm"
}

affirmation_agent_contract = await IntakeService.generate_affirmation_agent_contract(
    discovery_data
)

# Step 3: AffirmationAgent is created in database
affirmation_agent = await AgentService.create_agent(
    request=affirmation_agent_contract,
    tenant_id="numen-ai",
    owner_id="user-123"
)

# Step 4: AffirmationAgent generates content
affirmations = await AffirmationService.generate_affirmations(
    agent_id=affirmation_agent.id,
    user_id="user-123"
)

# Example output:
# [
#   {
#     "text": "I am a magnet for financial abundance and prosperity flows to me effortlessly",
#     "category": "morning",
#     "schedule_time": "07:00"
#   },
#   {
#     "text": "I deserve success and I am fully capable of achieving my career goals",
#     "category": "evening",
#     "schedule_time": "21:00"
#   }
# ]

# Step 5: Audio synthesis
for affirmation in affirmations:
    audio_url = await AudioSynthesisService.synthesize_affirmation(
        text=affirmation.text,
        voice_config=affirmation_agent.voice
    )
    affirmation.audio_url = audio_url
    await db.save(affirmation)

# Step 6: Schedule recurring playback
for affirmation in affirmations:
    await SchedulerService.schedule_affirmation(
        affirmation_id=affirmation.id,
        user_id="user-123",
        schedule_type="daily",
        schedule_time=affirmation.schedule_time
    )

# Step 7: User accesses dashboard
dashboard_content = await DashboardService.get_user_affirmations("user-123")
# Returns all affirmations with audio URLs, play counts, favorites
```

---

## ✅ Success Criteria

**Phase 1 Complete**:
- ✅ IntakeAgent contract created and stored
- ✅ Intake flow can generate AffirmationAgent contracts
- ✅ Database tables for discovery, affirmations, scripts created

**Phase 2 Complete**:
- ✅ AffirmationAgent can generate affirmations
- ✅ AffirmationAgent can generate hypnosis scripts
- ✅ ElevenLabs integration produces audio files

**Phase 3 Complete**:
- ✅ DashboardAgent displays all user content
- ✅ Scheduling system sends recurring reminders
- ✅ Analytics track plays, favorites, completion rates

**Production Ready**:
- ✅ End-to-end flow: Intake → Affirmation → Audio → Dashboard
- ✅ All agents 100% contract-driven (no hardcoded behavior)
- ✅ Multi-user support with tenant isolation
- ✅ Audio files stored and playable
- ✅ Scheduling working for recurring affirmations

---

**Next Steps**: Implement Phase 1 - Core pipeline setup with IntakeAgent and database schema updates.
