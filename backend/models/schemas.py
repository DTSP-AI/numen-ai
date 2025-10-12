from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class SessionStatus(str, Enum):
    PENDING = "pending"
    INTAKE = "intake"
    THERAPY = "therapy"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionType(str, Enum):
    MANIFESTATION = "manifestation"
    ANXIETY_RELIEF = "anxiety_relief"
    SLEEP_HYPNOSIS = "sleep_hypnosis"
    CONFIDENCE = "confidence"
    HABIT_CHANGE = "habit_change"


class TonePreference(str, Enum):
    CALM = "calm"
    ENERGETIC = "energetic"
    AUTHORITATIVE = "authoritative"
    GENTLE = "gentle"
    EMPOWERING = "empowering"


# Request/Response Models
class SessionCreate(BaseModel):
    user_id: str


class SessionResponse(BaseModel):
    id: UUID
    user_id: str
    status: SessionStatus
    room_name: Optional[str] = None
    access_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ConsentUpdate(BaseModel):
    """User consent for plan and therapy"""
    consented: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ConsentResponse(BaseModel):
    """Response after consent update"""
    session_id: UUID
    consented: bool
    consented_at: Optional[datetime] = None
    message: str


class ContractCreate(BaseModel):
    session_id: UUID
    user_id: str
    goals: List[str]
    tone: TonePreference
    voice_id: str
    session_type: SessionType


class ContractResponse(BaseModel):
    id: UUID
    session_id: UUID
    user_id: str
    goals: List[str]
    tone: TonePreference
    voice_id: str
    session_type: SessionType
    created_at: datetime


class TranscriptEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    speaker: str  # "user" or "agent"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Agent State Models
class IntakeState(BaseModel):
    session_id: UUID
    user_id: str
    conversation_history: List[dict] = []
    goals: List[str] = []
    tone: Optional[TonePreference] = None
    voice_id: Optional[str] = None
    session_type: Optional[SessionType] = None
    contract_generated: bool = False


class TherapyState(BaseModel):
    session_id: UUID
    user_id: str
    contract: ContractResponse
    script: Optional[str] = None
    audio_chunks: List[bytes] = []
    transcript: List[TranscriptEntry] = []
    reflections: List[str] = []
    completed: bool = False


# Baseline Flow Models
class UserGuideControls(BaseModel):
    """4 user-facing guide customization controls (0-100 scale)"""
    guide_energy: int = Field(default=50, ge=0, le=100, description="Calm (0) ↔ Energetic (100)")
    coaching_style: int = Field(default=50, ge=0, le=100, description="Nurturing (0) ↔ Directive (100)")
    creative_expression: int = Field(default=50, ge=0, le=100, description="Practical (0) ↔ Imaginative (100)")
    communication_depth: int = Field(default=50, ge=0, le=100, description="Concise (0) ↔ Detailed (100)")


class IntakeRequest(BaseModel):
    """Request to process user intake"""
    user_id: str
    answers: dict  # {goals: list[str], tone: str, session_type: str}
    guide_controls: Optional[UserGuideControls] = None  # Optional user customization


class IntakeContract(BaseModel):
    """Normalized contract from IntakeAgent"""
    normalized_goals: List[str]
    prefs: dict  # {tone: str, session_type: str}
    notes: str = ""


class GuideAttributes(BaseModel):
    """4 core attributes for baseline"""
    confidence: int = Field(default=70, ge=0, le=100)
    empathy: int = Field(default=70, ge=0, le=100)
    creativity: int = Field(default=50, ge=0, le=100)
    discipline: int = Field(default=60, ge=0, le=100)


class GuideContract(BaseModel):
    """Guide agent contract from intake"""
    identity: dict
    roles: List[str]
    interaction_styles: List[str]
    attributes: GuideAttributes
    voice_id: Optional[str] = None
    avatar_url: Optional[str] = None


class CreateFromIntakeResponse(BaseModel):
    """Response from baseline agent creation"""
    agent: dict
    session: dict
    protocol: dict