"""
DiscoveryAgent - Cognitive Discovery Sub-Agent for GuideAgent

This agent performs the cognitive discovery conversation that identifies:
- Goals (with GAS ratings)
- Limiting beliefs
- Desired outcomes
- Ideal vs Actual ratings
- Belief graph (CAM)

This is immutable GuideAgent logic that the JSON contract is layered on top of.
"""

import logging
from typing import Dict, Any, List
import uuid

logger = logging.getLogger(__name__)


def calculate_gas_ratings(goal_text: str) -> Dict[str, int]:
    """
    Calculate initial GAS ratings for a goal based on Goal Attainment Scaling research.

    GAS Scale (research-based):
    - -2: Current baseline/starting point
    - -1: Some progress towards goal
    - 0: Expected goal attainment (target outcome)
    - +1: Better than expected outcome
    - +2: Much better than expected (stretch goal)

    Args:
        goal_text: The user's goal text

    Returns:
        Dict with gas_current_level, gas_expected_level, gas_target_level,
        ideal_rating, actual_rating, and gap

    Reference: Goal Attainment Scaling is used in therapy/coaching to measure
    personalized goal achievement. See https://www.physio-pedia.com/Goal_Attainment_Scaling
    """
    # Standard GAS initial ratings based on research
    # During discovery phase: user starts at baseline (-2)
    # Expected attainment is the goal itself (0)
    # Stretch target is optimal outcome (+2)

    # Estimate initial actual_rating based on goal sentiment/urgency
    # More sophisticated implementation could use NLP sentiment analysis
    # For now, conservative baseline assumption: user is 30% towards ideal
    actual_rating_estimate = 30

    return {
        "gas_current_level": -2,      # Baseline: current state
        "gas_expected_level": 0,       # Expected: goal achievement
        "gas_target_level": 2,         # Target: optimal outcome
        "ideal_rating": 100,           # User's ideal state
        "actual_rating": actual_rating_estimate,  # Current estimated position
        "gap": 100 - actual_rating_estimate       # Gap to close
    }


async def run_discovery(
    user_id: str,
    tenant_id: str,
    guide_contract: Dict[str, Any],
    goals: List[str],
    limiting_beliefs: List[str],
    desired_outcomes: List[str]
) -> Dict[str, Any]:
    """
    Run cognitive discovery assessment

    This structures the discovery data that the GuideAgent uses
    to generate custom assets and strategy.

    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        guide_contract: GuideContract data (immutable base layer)
        goals: User's primary goals
        limiting_beliefs: Identified limiting beliefs
        desired_outcomes: Specific desired outcomes

    Returns:
        Dict with structured cognitive assessment data
    """

    logger.info(f"Running cognitive discovery for user {user_id}")

    # Structure cognitive data with GAS (Goal Attainment Scaling)
    # Uses research-based Goal Attainment Scaling from therapy/coaching literature
    cognitive_data = {
        "goals": [
            {
                "text": goal,
                **calculate_gas_ratings(goal)  # Apply research-based GAS ratings
            }
            for goal in goals
        ],
        "limiting_beliefs": [
            {
                "text": belief,
                "intensity": None,
                "linked_goals": []
            }
            for belief in limiting_beliefs
        ],
        "desired_outcomes": [
            {
                "text": outcome,
                "timeframe": None,
                "measurable_criteria": None
            }
            for outcome in desired_outcomes
        ],
        "cognitive_assessment": {
            "readiness_score": None,
            "emotional_tone": None,
            "focus_area": goals[0] if goals else None,
            "belief_graph": None
        }
    }

    logger.info(f"✅ Cognitive discovery complete: {len(goals)} goals, {len(limiting_beliefs)} beliefs")

    return {
        "cognitive_data": cognitive_data,
        "assessment_id": str(uuid.uuid4()),
        "user_id": user_id,
        "tenant_id": tenant_id
    }
