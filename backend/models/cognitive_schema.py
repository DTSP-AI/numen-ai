"""
Cognitive Schema Models - Goal & Belief Assessment Framework

This module defines the CognitiveKernel and related assessment models
for deep goal/belief tracking in Guide agents.

Phase 1: Optional, additive-only implementation
These models are used when cognitive_kernel_ref is set in AgentContract
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid


# ============================================================================
# COGNITIVE KERNEL SCHEMA
# ============================================================================

class GoalAssessmentMethod(str, Enum):
    """Goal assessment methodologies"""
    GAS = "GAS"  # Goal Attainment Scaling
    IDEAL_ACTUAL = "ideal_actual"  # Ideal vs Actual rating
    BEHAVIOR_GAP = "behavior_gap"  # Intention-behavior discrepancy
    NARRATIVE_MAPPING = "narrative_mapping"  # Story-based goal mapping


class BeliefMappingMethod(str, Enum):
    """Belief mapping methodologies"""
    CAM = "CAM"  # Cognitive-Affective Mapping
    DOWNWARD_ARROW = "downward_arrow"  # Core belief excavation
    CONFLICT_SCORING = "conflict_scoring"  # Tension analysis
    BEHAVIORAL_AVOIDANCE = "behavioral_avoidance"  # Behavior-belief gap detection


class GoalAssessmentConfig(BaseModel):
    """Configuration for goal assessment protocols"""
    methods: List[GoalAssessmentMethod] = Field(
        default=[GoalAssessmentMethod.GAS, GoalAssessmentMethod.IDEAL_ACTUAL],
        description="Enabled goal assessment methods"
    )
    tracking: bool = Field(
        default=True,
        description="Enable longitudinal goal tracking"
    )
    reassessment_triggers: List[str] = Field(
        default=["significant_progress", "repeated_failure", "user_request"],
        description="Events that trigger goal reassessment"
    )


class BeliefMappingConfig(BaseModel):
    """Configuration for belief mapping protocols"""
    methods: List[BeliefMappingMethod] = Field(
        default=[BeliefMappingMethod.CAM, BeliefMappingMethod.CONFLICT_SCORING],
        description="Enabled belief mapping methods"
    )
    graph_storage: bool = Field(
        default=True,
        description="Store belief graphs in database"
    )
    analysis_enabled: bool = Field(
        default=True,
        description="Enable graph analysis (centrality, conflict detection)"
    )


class ReflexTriggerConfig(BaseModel):
    """Configuration for automatic reassessment triggers"""
    enabled: bool = Field(
        default=True,
        description="Enable automatic reflex triggers"
    )
    emotion_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Emotion conflict threshold (0-1) to trigger reassessment"
    )
    failure_threshold: int = Field(
        default=2,
        ge=1,
        description="Number of repeated failures before triggering intervention"
    )
    conflict_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Belief conflict score threshold for intervention"
    )


class MemoryIntegrationConfig(BaseModel):
    """Configuration for memory integration"""
    store_goal_vectors: bool = Field(default=True)
    store_belief_graphs: bool = Field(default=True)
    store_emotion_logs: bool = Field(default=True)


class CognitiveKernel(BaseModel):
    """
    Immutable Cognitive Kernel Schema

    Defines the goal/belief assessment framework for Guide agents.
    Once assigned to an agent, this schema determines assessment protocols.

    Phase 1: Optional field in AgentContract
    Phase 3: Will become immutable and override-protected
    """
    version: str = Field(
        default="v1.0",
        description="Cognitive kernel version (semver)"
    )

    goal_assessment: GoalAssessmentConfig = Field(
        default_factory=GoalAssessmentConfig,
        description="Goal assessment configuration"
    )

    belief_mapping: BeliefMappingConfig = Field(
        default_factory=BeliefMappingConfig,
        description="Belief mapping configuration"
    )

    reflex_triggers: ReflexTriggerConfig = Field(
        default_factory=ReflexTriggerConfig,
        description="Automatic trigger configuration"
    )

    memory_integration: MemoryIntegrationConfig = Field(
        default_factory=MemoryIntegrationConfig,
        description="Memory storage preferences"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "version": "v1.0",
                "goal_assessment": {
                    "methods": ["GAS", "ideal_actual"],
                    "tracking": True,
                    "reassessment_triggers": ["significant_progress", "repeated_failure"]
                },
                "belief_mapping": {
                    "methods": ["CAM", "conflict_scoring"],
                    "graph_storage": True,
                    "analysis_enabled": True
                },
                "reflex_triggers": {
                    "enabled": True,
                    "emotion_threshold": 0.7,
                    "failure_threshold": 2,
                    "conflict_threshold": 0.8
                },
                "memory_integration": {
                    "store_goal_vectors": True,
                    "store_belief_graphs": True,
                    "store_emotion_logs": True
                }
            }
        }


# ============================================================================
# GOAL ASSESSMENT MODELS
# ============================================================================

class GASLevel(int, Enum):
    """Goal Attainment Scaling levels"""
    MUCH_LESS = -2
    LESS = -1
    EXPECTED = 0
    MORE = 1
    MUCH_MORE = 2


class GoalCategory(str, Enum):
    """Goal categories"""
    CAREER = "career"
    HEALTH = "health"
    RELATIONSHIPS = "relationships"
    FINANCIAL = "financial"
    PERSONAL_GROWTH = "personal_growth"
    SPIRITUAL = "spiritual"
    CREATIVE = "creative"
    OTHER = "other"


class GoalAssessment(BaseModel):
    """
    Goal Assessment Model

    Tracks a single goal using GAS and Ideal vs Actual ratings
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    agent_id: str
    tenant_id: str

    # Goal identification
    goal_text: str = Field(..., description="Natural language goal description")
    goal_category: GoalCategory = Field(default=GoalCategory.OTHER)

    # GAS ratings
    gas_current_level: int = Field(
        default=-1,
        ge=-2,
        le=2,
        description="Current GAS level (-2 to +2)"
    )
    gas_expected_level: int = Field(
        default=0,
        description="Expected attainment level (baseline)"
    )
    gas_target_level: int = Field(
        default=2,
        description="Target level (stretch goal)"
    )

    # Ideal vs Actual
    ideal_state_rating: int = Field(
        ge=0,
        le=100,
        description="Ideal state rating (0-100)"
    )
    actual_state_rating: int = Field(
        ge=0,
        le=100,
        description="Current actual state rating (0-100)"
    )

    # Progress tracking
    initial_assessment_date: datetime = Field(default_factory=datetime.utcnow)
    last_reassessment_date: datetime = Field(default_factory=datetime.utcnow)
    reassessment_count: int = Field(default=0)

    # Metadata
    confidence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in goal clarity"
    )
    motivation_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="User motivation level"
    )

    # Behavioral tracking
    attempt_count: int = Field(default=0)
    success_count: int = Field(default=0)
    last_attempt_date: Optional[datetime] = None

    # Schema versioning
    schema_version: str = Field(default="v1.0")
    intake_depth: str = Field(default="standard")  # 'standard' or 'cognitive_extended'

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def progress_delta(self) -> int:
        """Calculate progress relative to expected level"""
        return self.gas_current_level - self.gas_expected_level

    @property
    def gap_score(self) -> int:
        """Calculate ideal-actual gap"""
        return self.ideal_state_rating - self.actual_state_rating


# ============================================================================
# BELIEF MAPPING MODELS
# ============================================================================

class BeliefNodeType(str, Enum):
    """Types of nodes in belief graph"""
    CORE_BELIEF = "core_belief"
    LIMITING_BELIEF = "limiting_belief"
    GOAL = "goal"
    EMOTION = "emotion"
    BEHAVIOR = "behavior"
    OUTCOME = "outcome"


class BeliefNode(BaseModel):
    """Single node in Cognitive-Affective Map"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str = Field(..., description="Node content/label")
    node_type: BeliefNodeType
    emotional_valence: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Emotional charge (-1 negative, 0 neutral, +1 positive)"
    )
    centrality: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Graph centrality score (computed)"
    )
    strength: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Belief strength/conviction"
    )


class BeliefEdgeRelationship(str, Enum):
    """Relationship types between belief nodes"""
    SUPPORTS = "supports"
    CONFLICTS = "conflicts"
    CAUSES = "causes"
    BLOCKS = "blocks"
    REINFORCES = "reinforces"


class BeliefEdge(BaseModel):
    """Edge connecting two nodes in belief graph"""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relationship: BeliefEdgeRelationship
    weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Relationship strength"
    )


class BeliefGraph(BaseModel):
    """
    Cognitive-Affective Map (CAM)

    Graph representation of user's belief system
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    agent_id: str
    tenant_id: str

    graph_name: str = Field(default="User Belief System")
    graph_version: int = Field(default=1)

    # Graph structure
    nodes: List[BeliefNode] = Field(default_factory=list)
    edges: List[BeliefEdge] = Field(default_factory=list)

    # Analysis metrics (computed)
    conflict_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall conflict/tension in belief system"
    )
    tension_nodes: List[str] = Field(
        default_factory=list,
        description="Node IDs with highest conflict"
    )
    core_beliefs: List[str] = Field(
        default_factory=list,
        description="Node IDs with highest centrality"
    )

    schema_version: str = Field(default="v1.0")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# COGNITIVE METRICS MODELS
# ============================================================================

class MetricType(str, Enum):
    """Types of cognitive metrics"""
    EMOTION_CONFLICT = "emotion_conflict"
    GOAL_PROGRESS = "goal_progress"
    BELIEF_SHIFT = "belief_shift"
    MOTIVATION_DROP = "motivation_drop"
    REPEATED_FAILURE = "repeated_failure"
    BREAKTHROUGH = "breakthrough"


class MetricCategory(str, Enum):
    """Metric categories"""
    EMOTIONAL = "emotional"
    BEHAVIORAL = "behavioral"
    COGNITIVE = "cognitive"


class CognitiveMetric(BaseModel):
    """
    Single cognitive metric measurement

    Used for tracking emotion conflicts, progress, and triggering interventions
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    agent_id: str
    tenant_id: str
    thread_id: Optional[str] = None

    # Metric classification
    metric_type: MetricType
    metric_category: MetricCategory

    # Metric values
    metric_value: float = Field(..., description="Primary metric value")
    threshold_value: Optional[float] = Field(
        None,
        description="Threshold for triggering action"
    )
    threshold_exceeded: bool = Field(default=False)

    # Context
    context_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (goal_id, belief_node_id, etc.)"
    )
    trigger_action: Optional[str] = Field(
        None,
        description="Recommended action if threshold exceeded"
    )

    # Timestamps
    measured_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = Field(default="v1.0")

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_default_cognitive_kernel() -> CognitiveKernel:
    """Get default CognitiveKernel v1.0 configuration"""
    return CognitiveKernel(
        version="v1.0",
        goal_assessment=GoalAssessmentConfig(
            methods=[GoalAssessmentMethod.GAS, GoalAssessmentMethod.IDEAL_ACTUAL],
            tracking=True,
            reassessment_triggers=["significant_progress", "repeated_failure", "user_request"]
        ),
        belief_mapping=BeliefMappingConfig(
            methods=[BeliefMappingMethod.CAM, BeliefMappingMethod.CONFLICT_SCORING],
            graph_storage=True,
            analysis_enabled=True
        ),
        reflex_triggers=ReflexTriggerConfig(
            enabled=True,
            emotion_threshold=0.7,
            failure_threshold=2,
            conflict_threshold=0.8
        ),
        memory_integration=MemoryIntegrationConfig(
            store_goal_vectors=True,
            store_belief_graphs=True,
            store_emotion_logs=True
        )
    )
