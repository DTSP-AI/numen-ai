"""
Agent Contract Models - JSON Contract-First Architecture

This module defines the complete agent JSON contract specification
following the AGENT_CREATION_STANDARD for universal AI agent systems.
"""

from pydantic import BaseModel, Field, validator, model_validator
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum
import uuid

# Conditional import to avoid circular dependency
if TYPE_CHECKING:
    from models.cognitive_schema import CognitiveKernel


class AgentType(str, Enum):
    """Agent type classification"""
    CONVERSATIONAL = "conversational"
    VOICE = "voice"
    WORKFLOW = "workflow"
    AUTONOMOUS = "autonomous"


class AgentStatus(str, Enum):
    """Agent lifecycle status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AgentTraits(BaseModel):
    """
    Agent personality traits (0-100 scale)

    These traits dynamically adjust agent behavior at runtime
    without code changes. Higher values intensify the trait.

    Core 4 attributes for Guide creation:
    - Confidence, Empathy, Creativity, Discipline
    """
    confidence: int = Field(
        ge=0, le=100, default=70,
        description="Certainty and authority in responses"
    )
    empathy: int = Field(
        ge=0, le=100, default=70,
        description="Emotional sensitivity and understanding"
    )
    creativity: int = Field(
        ge=0, le=100, default=50,
        description="Creative vs structured responses"
    )
    discipline: int = Field(
        ge=0, le=100, default=60,
        description="Structured and consistent approach"
    )
    # Additional traits (optional)
    assertiveness: int = Field(
        ge=0, le=100, default=50,
        description="Directive vs suggestive communication"
    )
    humor: int = Field(
        ge=0, le=100, default=30,
        description="Lighthearted vs serious tone"
    )
    formality: int = Field(
        ge=0, le=100, default=50,
        description="Formal vs casual language"
    )
    verbosity: int = Field(
        ge=0, le=100, default=50,
        description="Concise vs detailed responses"
    )
    spirituality: int = Field(
        ge=0, le=100, default=60,
        description="Spiritual awareness and connection"
    )
    supportiveness: int = Field(
        ge=0, le=100, default=80,
        description="Nurturing and encouraging presence"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "creativity": 75,
                "empathy": 90,
                "assertiveness": 60,
                "humor": 40,
                "formality": 30,
                "verbosity": 65,
                "confidence": 80,
                "spirituality": 70,
                "supportiveness": 90
            }
        }


class AgentIdentity(BaseModel):
    """
    Agent identity and character definition

    Defines who the agent is, their purpose, and how they interact.
    This is the core of the agent's personality and mission.
    """
    short_description: str = Field(
        ...,
        description="One-line agent purpose (max 100 chars)",
        max_length=100
    )
    full_description: Optional[str] = Field(
        default="",
        description="Detailed background and capabilities"
    )
    character_role: Optional[str] = Field(
        default="",
        description="Character archetype this agent embodies"
    )
    roles: List[str] = Field(
        default_factory=list,
        description="Guide roles (Stoic Sage, Manifestation Mentor, Life Coach, etc.)"
    )
    mission: Optional[str] = Field(
        default="",
        description="Primary objective and goals"
    )
    interaction_style: Optional[str] = Field(
        default="",
        description="Communication approach and manner"
    )
    interaction_styles: List[str] = Field(
        default_factory=list,
        description="Multiple interaction styles (Encouraging, Analytical, Compassionate, Direct)"
    )
    avatar_url: Optional[str] = Field(
        default=None,
        description="URL to agent avatar image (uploaded or AI-generated)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "short_description": "Empathetic hypnotherapy guide for manifestation",
                "full_description": "A warm, supportive hypnotherapist specializing in positive psychology and manifestation techniques",
                "character_role": "Compassionate Guide",
                "mission": "Help users manifest their goals through personalized hypnotherapy",
                "interaction_style": "Gentle, encouraging, and deeply empathetic"
            }
        }


class AgentConfiguration(BaseModel):
    """
    Agent runtime configuration

    Controls LLM behavior, memory settings, and capabilities.
    Can be adjusted per-agent without code changes.
    """
    # LLM settings
    llm_provider: str = Field(
        default="openai",
        description="LLM provider (openai, anthropic, xai, local)"
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="Model name/identifier"
    )
    max_tokens: int = Field(
        ge=50, le=4000, default=500,
        description="Maximum response tokens"
    )
    temperature: float = Field(
        ge=0.0, le=2.0, default=0.7,
        description="LLM temperature for randomness"
    )

    # Capability flags
    memory_enabled: bool = Field(
        default=True,
        description="Enable persistent memory"
    )
    voice_enabled: bool = Field(
        default=False,
        description="Enable voice capabilities"
    )
    tools_enabled: bool = Field(
        default=False,
        description="Enable tool use/function calling"
    )

    # Memory settings
    memory_k: int = Field(
        ge=1, le=20, default=6,
        description="Number of memories to retrieve per query"
    )
    thread_window: int = Field(
        ge=5, le=50, default=20,
        description="Recent messages to include in context"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "max_tokens": 800,
                "temperature": 0.8,
                "memory_enabled": True,
                "voice_enabled": True,
                "tools_enabled": False,
                "memory_k": 6,
                "thread_window": 20
            }
        }


class VoiceConfiguration(BaseModel):
    """
    Voice-specific configuration for voice agents

    Defines TTS/STT settings for real-time voice interactions.
    """
    # TTS settings
    provider: str = Field(
        default="elevenlabs",
        description="TTS provider (elevenlabs, azure, google)"
    )
    voice_id: str = Field(
        ...,
        description="Voice ID or name from provider"
    )
    language: str = Field(
        default="en-US",
        description="Language code (e.g., en-US, es-ES)"
    )
    speed: float = Field(
        ge=0.5, le=2.0, default=1.0,
        description="Speech speed multiplier"
    )
    pitch: float = Field(
        ge=0.5, le=2.0, default=1.0,
        description="Voice pitch adjustment"
    )
    stability: float = Field(
        ge=0.0, le=1.0, default=0.75,
        description="Voice stability (ElevenLabs)"
    )
    similarity_boost: float = Field(
        ge=0.0, le=1.0, default=0.75,
        description="Similarity boost (ElevenLabs)"
    )

    # STT settings
    stt_provider: str = Field(
        default="deepgram",
        description="STT provider (deepgram, azure, whisper)"
    )
    stt_model: str = Field(
        default="nova-2",
        description="STT model identifier"
    )
    stt_language: str = Field(
        default="en",
        description="STT language code"
    )
    vad_enabled: bool = Field(
        default=True,
        description="Enable voice activity detection"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "elevenlabs",
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "language": "en-US",
                "speed": 0.95,
                "stability": 0.75,
                "similarity_boost": 0.75,
                "stt_provider": "deepgram",
                "stt_model": "nova-2",
                "vad_enabled": True
            }
        }


class AgentMetadata(BaseModel):
    """
    Agent metadata and organizational info

    Manages multi-tenancy, ownership, and lifecycle status.
    """
    tenant_id: str = Field(
        ...,
        description="Organization/tenant UUID"
    )
    owner_id: str = Field(
        ...,
        description="User UUID of agent creator"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Organizational tags for filtering"
    )
    status: AgentStatus = Field(
        default=AgentStatus.ACTIVE,
        description="Agent lifecycle status"
    )


class AgentContract(BaseModel):
    """
    Complete agent JSON contract

    This is the single source of truth for agent identity, behavior,
    and configuration. All agent behavior is derived from this contract.

    Usage:
        # Create agent contract
        contract = AgentContract(
            name="My Agent",
            identity=AgentIdentity(short_description="..."),
            metadata=AgentMetadata(tenant_id="...", owner_id="...")
        )

        # Store in database
        db.agents.insert(contract.model_dump())

        # Load and use at runtime
        agent = load_agent_from_contract(contract)
    """
    # Core identity
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Agent UUID"
    )
    name: str = Field(
        ...,
        description="Agent display name"
    )
    type: AgentType = Field(
        default=AgentType.CONVERSATIONAL,
        description="Agent type classification"
    )
    version: str = Field(
        default="1.0.0",
        description="Contract version (semver)"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    # Contract components
    identity: AgentIdentity
    traits: AgentTraits = Field(
        default_factory=AgentTraits
    )
    configuration: AgentConfiguration = Field(
        default_factory=AgentConfiguration
    )
    voice: Optional[VoiceConfiguration] = None
    metadata: AgentMetadata

    # ========================================================================
    # PHASE 1: Optional Cognitive Assessment Layer
    # ========================================================================
    cognitive_kernel_ref: Optional[str] = Field(
        default=None,
        description="Reference to CognitiveKernel version (e.g., 'v1.0'). "
                    "When set, enables goal/belief assessment capabilities. "
                    "Phase 1: Optional. Phase 3: Will become immutable."
    )
    goal_assessment_enabled: bool = Field(
        default=False,
        description="Enable Goal Attainment Scaling (GAS) and goal tracking"
    )
    belief_mapping_enabled: bool = Field(
        default=False,
        description="Enable Cognitive-Affective Mapping (CAM) for belief systems"
    )
    reflex_triggers_enabled: bool = Field(
        default=False,
        description="Enable automatic reassessment triggers based on thresholds"
    )

    # Optional: Store full cognitive kernel config inline (alternative to ref)
    cognitive_kernel_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Inline CognitiveKernel configuration (alternative to cognitive_kernel_ref)"
    )

    @validator('type')
    def validate_type(cls, v):
        """Ensure agent type is valid"""
        if v not in AgentType.__members__.values():
            raise ValueError(f'type must be one of {list(AgentType.__members__.values())}')
        return v

    @model_validator(mode='after')
    def validate_voice_for_voice_agents(self):
        """Voice agents and agents with voice_enabled must have voice configuration"""
        # Check if voice is required
        requires_voice = (
            self.type == AgentType.VOICE or
            (self.configuration and self.configuration.voice_enabled)
        )

        if requires_voice and self.voice is None:
            raise ValueError(
                'Voice configuration is required for voice agents or when voice_enabled=True. '
                'Provide a VoiceConfiguration with at least voice_id and provider.'
            )
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "IntakeAgent - Manifestation Coach",
                "type": "voice",
                "version": "1.0.0",
                "identity": {
                    "short_description": "Empathetic intake specialist for hypnotherapy",
                    "mission": "Collect user goals and preferences with compassion"
                },
                "traits": {
                    "creativity": 60,
                    "empathy": 95,
                    "assertiveness": 40
                },
                "configuration": {
                    "llm_model": "gpt-4",
                    "temperature": 0.7,
                    "voice_enabled": True
                },
                "metadata": {
                    "tenant_id": "tenant-uuid",
                    "owner_id": "user-uuid",
                    "tags": ["production", "hypnotherapy"],
                    "status": "active"
                }
            }
        }


# API Request/Response Models

class AgentCreateRequest(BaseModel):
    """API request model for creating agents"""
    name: str = Field(..., description="Agent display name")
    type: AgentType = Field(default=AgentType.CONVERSATIONAL)
    identity: AgentIdentity
    traits: Optional[AgentTraits] = None
    configuration: Optional[AgentConfiguration] = None
    voice: Optional[VoiceConfiguration] = None
    tags: List[str] = Field(default_factory=list)


class AgentUpdateRequest(BaseModel):
    """API request model for updating agents"""
    name: Optional[str] = None
    identity: Optional[AgentIdentity] = None
    traits: Optional[AgentTraits] = None
    configuration: Optional[AgentConfiguration] = None
    voice: Optional[VoiceConfiguration] = None
    tags: Optional[List[str]] = None
    status: Optional[AgentStatus] = None


class AgentResponse(BaseModel):
    """API response model for agent details"""
    id: str
    name: str
    type: AgentType
    version: str
    identity: AgentIdentity
    traits: AgentTraits
    configuration: AgentConfiguration
    voice: Optional[VoiceConfiguration]
    status: AgentStatus
    interaction_count: int
    last_interaction_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
