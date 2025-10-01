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