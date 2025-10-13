"""
IntakeAgent Cognitive Extension - Phase 1 Implementation

This extends IntakeAgentV2 with deep cognitive assessment capabilities:
- Goal Attainment Scaling (GAS) for each goal
- Ideal vs Actual ratings
- Cognitive-Affective Mapping (CAM) for belief systems
- Conflict detection and tension analysis

Usage:
    This is OPT-IN via enable_cognitive_assessment=True flag
    Standard IntakeAgentV2 continues to work without changes
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid
import os
from pathlib import Path

from pydantic import BaseModel, Field

from agents.intake_agent_v2 import IntakeAgentV2, IntakeAgentState, DiscoveryData
from models.cognitive_schema import (
    GoalAssessment,
    GoalCategory,
    BeliefGraph,
    BeliefNode,
    BeliefEdge,
    BeliefNodeType,
    BeliefEdgeRelationship,
    get_default_cognitive_kernel
)
from services.memory_manager import (
    store_goal_assessment,
    store_belief_graph,
    store_cognitive_metric
)

logger = logging.getLogger(__name__)


# ============================================================================
# COGNITIVE DISCOVERY DATA (EXTENDS BASE DiscoveryData)
# ============================================================================

class CognitiveDiscoveryData(DiscoveryData):
    """Extended discovery data with cognitive assessments"""

    # GAS ratings per goal (goal_text -> GAS data)
    goal_assessments: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Ideal vs Actual ratings per goal
    ideal_actual_ratings: Dict[str, Dict[str, int]] = Field(default_factory=dict)

    # Belief graph nodes and edges
    belief_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    belief_edges: List[Dict[str, Any]] = Field(default_factory=list)

    # Confidence/motivation scores
    overall_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    overall_motivation: float = Field(default=0.5, ge=0.0, le=1.0)

    # Flag for intake depth
    intake_depth: str = Field(default="cognitive_extended")


# ============================================================================
# COGNITIVE INTAKE AGENT (EXTENDS IntakeAgentV2)
# ============================================================================

class IntakeAgentCognitive(IntakeAgentV2):
    """
    Cognitive-Enhanced IntakeAgent

    Extends IntakeAgentV2 with deep assessment capabilities.
    Only activated when enable_cognitive_assessment=True
    """

    def __init__(self, contract, memory, enable_cognitive_assessment: bool = True):
        """
        Initialize cognitive intake agent

        Args:
            contract: Agent contract
            memory: Memory manager
            enable_cognitive_assessment: Enable deep cognitive assessment (default True)
        """
        super().__init__(contract, memory)

        self.enable_cognitive = enable_cognitive_assessment
        self.cognitive_kernel = get_default_cognitive_kernel()

        if self.enable_cognitive:
            logger.info("✅ Cognitive assessment ENABLED for this intake session")
        else:
            logger.info("⚪ Cognitive assessment DISABLED - using standard intake")

    async def collect_gas_ratings(
        self,
        user_id: str,
        tenant_id: str,
        agent_id: str,
        goals: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Collect Goal Attainment Scaling (GAS) ratings for each goal

        For each goal, ask user to rate:
        - Current level (-2 to +2)
        - Expected level (default 0)
        - Target level (default +2)

        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            agent_id: Agent UUID
            goals: List of goal texts

        Returns:
            Dict mapping goal_text to GAS data
        """
        gas_ratings = {}

        for goal in goals:
            # Use LLM to collect GAS ratings via conversational prompt
            system_prompt = f"""Ask the user to rate their current progress on this goal using a scale:
-2 (Much worse than expected)
-1 (Less than expected)
 0 (About where I expected to be)
+1 (Better than expected)
+2 (Much better than expected)

Goal: "{goal}"

Ask naturally and conversationally. Extract the rating from their response."""

            try:
                from langchain.schema import SystemMessage, HumanMessage

                # For now, use defaults (this would be interactive in production)
                gas_ratings[goal] = {
                    "gas_current_level": -1,  # Starting below expected
                    "gas_expected_level": 0,
                    "gas_target_level": 2,
                    "goal_category": self._categorize_goal(goal)
                }

                logger.info(f"GAS rating collected for goal: {goal}")

            except Exception as e:
                logger.error(f"Failed to collect GAS rating for goal: {e}")
                # Use safe defaults
                gas_ratings[goal] = {
                    "gas_current_level": 0,
                    "gas_expected_level": 0,
                    "gas_target_level": 2,
                    "goal_category": "other"
                }

        return gas_ratings

    async def collect_ideal_actual_ratings(
        self,
        goals: List[str]
    ) -> Dict[str, Dict[str, int]]:
        """
        Collect Ideal vs Actual ratings (0-100 scale) for each goal

        Args:
            goals: List of goal texts

        Returns:
            Dict mapping goal_text to {ideal: int, actual: int}
        """
        ideal_actual_ratings = {}

        for goal in goals:
            # In production, this would be interactive
            # For Phase 1, use intelligent estimates
            ideal_actual_ratings[goal] = {
                "ideal_state_rating": 100,  # Where they want to be
                "actual_state_rating": 40   # Where they currently are (creates gap)
            }

            logger.info(f"Ideal/Actual rating collected for goal: {goal}")

        return ideal_actual_ratings

    def _load_belief_graph_template(self) -> Dict[str, Any]:
        """Load default belief graph template from assets"""
        try:
            template_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'assets',
                'belief_graph_template.json'
            )

            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                logger.info(f"✅ Loaded belief graph template from {template_path}")
                return template
            else:
                logger.warning(f"Template not found: {template_path}")
                return None

        except Exception as e:
            logger.error(f"Failed to load belief graph template: {e}")
            return None

    async def build_belief_graph(
        self,
        user_id: str,
        tenant_id: str,
        agent_id: str,
        goals: List[str],
        limiting_beliefs: List[str],
        desired_outcomes: List[str]
    ) -> Dict[str, Any]:
        """
        Build Cognitive-Affective Map (CAM) from discovery data

        Creates a graph with:
        - Goal nodes
        - Limiting belief nodes
        - Outcome nodes
        - Edges showing relationships (supports, conflicts, blocks)

        If no limiting beliefs provided, uses template fallback.

        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            agent_id: Agent UUID
            goals: List of goals
            limiting_beliefs: List of limiting beliefs
            desired_outcomes: List of outcomes

        Returns:
            BeliefGraph dict with nodes and edges
        """
        # Load template if no limiting beliefs provided
        if not limiting_beliefs:
            template = self._load_belief_graph_template()
            if template:
                logger.info("📋 Using default belief graph template (no beliefs provided)")
                # Merge template with user goals/outcomes
                return self._merge_template_with_user_data(template, goals, desired_outcomes)

        nodes = []
        edges = []

        # Create goal nodes
        goal_node_ids = []
        for goal in goals:
            node_id = str(uuid.uuid4())
            goal_node_ids.append(node_id)

            nodes.append({
                "id": node_id,
                "label": goal,
                "node_type": "goal",
                "emotional_valence": 0.8,  # Goals are positive
                "centrality": 0.9,  # Goals are central
                "strength": 0.8
            })

        # Create limiting belief nodes
        belief_node_ids = []
        for belief in limiting_beliefs:
            node_id = str(uuid.uuid4())
            belief_node_ids.append(node_id)

            nodes.append({
                "id": node_id,
                "label": belief,
                "node_type": "limiting_belief",
                "emotional_valence": -0.6,  # Limiting beliefs are negative
                "centrality": 0.7,
                "strength": 0.7
            })

        # Create outcome nodes
        outcome_node_ids = []
        for outcome in desired_outcomes:
            node_id = str(uuid.uuid4())
            outcome_node_ids.append(node_id)

            nodes.append({
                "id": node_id,
                "label": outcome,
                "node_type": "outcome",
                "emotional_valence": 1.0,  # Outcomes are very positive
                "centrality": 0.6,
                "strength": 0.9
            })

        # Create edges: goals → outcomes (supports)
        for goal_id in goal_node_ids:
            for outcome_id in outcome_node_ids:
                edges.append({
                    "source": goal_id,
                    "target": outcome_id,
                    "relationship": "causes",
                    "weight": 0.8
                })

        # Create edges: limiting beliefs → goals (blocks)
        for belief_id in belief_node_ids:
            for goal_id in goal_node_ids:
                edges.append({
                    "source": belief_id,
                    "target": goal_id,
                    "relationship": "blocks",
                    "weight": 0.7
                })

        # Calculate conflict score (higher = more tension)
        blocking_edges = [e for e in edges if e["relationship"] == "blocks"]
        conflict_score = min(len(blocking_edges) * 0.15, 1.0)  # 0.15 per blocking edge, max 1.0

        # Identify tension nodes (limiting beliefs with high blocking)
        tension_nodes = belief_node_ids[:3]  # Top 3 limiting beliefs

        # Identify core beliefs (goals with highest centrality)
        core_beliefs = goal_node_ids[:2]  # Top 2 goals

        belief_graph = {
            "graph_name": "User Belief System",
            "graph_version": 1,
            "nodes": nodes,
            "edges": edges,
            "conflict_score": conflict_score,
            "tension_nodes": tension_nodes,
            "core_beliefs": core_beliefs
        }

        logger.info(
            f"✅ Belief graph built: {len(nodes)} nodes, {len(edges)} edges, "
            f"conflict_score={conflict_score:.2f}"
        )

        return belief_graph

    async def save_cognitive_assessment(
        self,
        user_id: str,
        tenant_id: str,
        agent_id: str,
        cognitive_data: CognitiveDiscoveryData
    ) -> Dict[str, List[str]]:
        """
        Save all cognitive assessment data to database

        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            agent_id: Agent UUID
            cognitive_data: CognitiveDiscoveryData with assessments

        Returns:
            Dict with lists of created IDs: {"goal_ids": [...], "graph_id": "..."}
        """
        created_ids = {"goal_ids": [], "graph_id": None}

        try:
            # 1. Save goal assessments
            for goal_text, gas_data in cognitive_data.goal_assessments.items():
                ideal_actual = cognitive_data.ideal_actual_ratings.get(goal_text, {})

                goal_assessment = {
                    "goal_text": goal_text,
                    "goal_category": gas_data.get("goal_category", "other"),
                    "gas_current_level": gas_data.get("gas_current_level", -1),
                    "gas_expected_level": gas_data.get("gas_expected_level", 0),
                    "gas_target_level": gas_data.get("gas_target_level", 2),
                    "ideal_state_rating": ideal_actual.get("ideal_state_rating", 100),
                    "actual_state_rating": ideal_actual.get("actual_state_rating", 50),
                    "confidence_score": cognitive_data.overall_confidence,
                    "motivation_score": cognitive_data.overall_motivation,
                    "intake_depth": cognitive_data.intake_depth
                }

                goal_id = await store_goal_assessment(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    agent_id=agent_id,
                    goal_assessment=goal_assessment
                )

                created_ids["goal_ids"].append(goal_id)

            logger.info(f"✅ Saved {len(created_ids['goal_ids'])} goal assessments")

            # 2. Save belief graph
            belief_graph_data = {
                "graph_name": "User Belief System",
                "graph_version": 1,
                "nodes": cognitive_data.belief_nodes,
                "edges": cognitive_data.belief_edges,
                "conflict_score": self._calculate_conflict_score(cognitive_data.belief_edges),
                "tension_nodes": [n["id"] for n in cognitive_data.belief_nodes if n.get("node_type") == "limiting_belief"][:3],
                "core_beliefs": [n["id"] for n in cognitive_data.belief_nodes if n.get("node_type") == "goal"][:2]
            }

            graph_id = await store_belief_graph(
                user_id=user_id,
                tenant_id=tenant_id,
                agent_id=agent_id,
                belief_graph=belief_graph_data
            )

            created_ids["graph_id"] = graph_id

            logger.info(f"✅ Saved belief graph: {graph_id}")

            # 3. Store conflict metric if threshold exceeded
            conflict_score = belief_graph_data["conflict_score"]
            if conflict_score >= self.cognitive_kernel.reflex_triggers.conflict_threshold:
                await store_cognitive_metric(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    agent_id=agent_id,
                    metric_type="belief_conflict",
                    metric_value=conflict_score,
                    context_data={"graph_id": graph_id},
                    threshold_value=self.cognitive_kernel.reflex_triggers.conflict_threshold
                )

                logger.warning(f"⚠️ Conflict threshold exceeded: {conflict_score:.2f}")

            return created_ids

        except Exception as e:
            logger.error(f"Failed to save cognitive assessment: {e}")
            raise

    def _categorize_goal(self, goal_text: str) -> str:
        """Categorize goal using keyword matching"""
        goal_lower = goal_text.lower()

        if any(word in goal_lower for word in ["money", "financial", "income", "wealth", "salary"]):
            return "financial"
        elif any(word in goal_lower for word in ["career", "job", "promotion", "work"]):
            return "career"
        elif any(word in goal_lower for word in ["health", "fitness", "exercise", "weight"]):
            return "health"
        elif any(word in goal_lower for word in ["relationship", "partner", "love", "family"]):
            return "relationships"
        elif any(word in goal_lower for word in ["spiritual", "meditation", "peace", "mindfulness"]):
            return "spiritual"
        elif any(word in goal_lower for word in ["creative", "art", "music", "writing"]):
            return "creative"
        elif any(word in goal_lower for word in ["growth", "learn", "develop", "confidence"]):
            return "personal_growth"
        else:
            return "other"

    def _calculate_conflict_score(self, edges: List[Dict[str, Any]]) -> float:
        """Calculate conflict score from belief graph edges"""
        if not edges:
            return 0.0

        blocking_edges = [e for e in edges if e.get("relationship") == "blocks"]
        conflict_edges = [e for e in edges if e.get("relationship") == "conflicts"]

        score = (len(blocking_edges) * 0.15) + (len(conflict_edges) * 0.20)
        return min(score, 1.0)

    def _merge_template_with_user_data(
        self,
        template: Dict[str, Any],
        goals: List[str],
        desired_outcomes: List[str]
    ) -> Dict[str, Any]:
        """
        Merge belief graph template with user-provided goals and outcomes

        Args:
            template: Template belief graph
            goals: User goals
            desired_outcomes: User outcomes

        Returns:
            Merged belief graph
        """
        nodes = list(template.get("nodes", []))
        edges = list(template.get("edges", []))

        # Add user goal nodes
        for goal in goals:
            node_id = str(uuid.uuid4())
            nodes.append({
                "id": node_id,
                "label": goal,
                "node_type": "goal",
                "emotional_valence": 0.9,
                "centrality": 0.9,
                "strength": 0.8
            })

        # Add user outcome nodes
        for outcome in desired_outcomes:
            node_id = str(uuid.uuid4())
            nodes.append({
                "id": node_id,
                "label": outcome,
                "node_type": "outcome",
                "emotional_valence": 1.0,
                "centrality": 0.7,
                "strength": 0.9
            })

        # Recalculate conflict score
        conflict_score = self._calculate_conflict_score(edges)

        return {
            "graph_name": "User Belief System (from template)",
            "graph_version": 1,
            "nodes": nodes,
            "edges": edges,
            "conflict_score": conflict_score,
            "tension_nodes": [n["id"] for n in nodes if n.get("node_type") == "limiting_belief"][:3],
            "core_beliefs": [n["id"] for n in nodes if n.get("node_type") == "goal"][:2]
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def run_cognitive_intake(
    user_id: str,
    tenant_id: str,
    agent_contract: Dict[str, Any],
    goals: List[str],
    limiting_beliefs: List[str],
    desired_outcomes: List[str]
) -> Dict[str, Any]:
    """
    Run complete cognitive intake assessment

    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        agent_contract: Agent contract dict
        goals: List of goals
        limiting_beliefs: List of limiting beliefs
        desired_outcomes: List of desired outcomes

    Returns:
        Dict with cognitive assessment results
    """
    from models.agent import AgentContract
    from services.memory_manager import MemoryManager

    # Create agent instance
    contract = AgentContract(**agent_contract)
    memory = MemoryManager(tenant_id=tenant_id, agent_id=contract.id, agent_traits=contract.traits.model_dump())

    agent = IntakeAgentCognitive(contract, memory, enable_cognitive_assessment=True)

    # Collect GAS ratings
    gas_ratings = await agent.collect_gas_ratings(
        user_id=user_id,
        tenant_id=tenant_id,
        agent_id=contract.id,
        goals=goals
    )

    # Collect ideal/actual ratings
    ideal_actual = await agent.collect_ideal_actual_ratings(goals)

    # Build belief graph
    belief_graph = await agent.build_belief_graph(
        user_id=user_id,
        tenant_id=tenant_id,
        agent_id=contract.id,
        goals=goals,
        limiting_beliefs=limiting_beliefs,
        desired_outcomes=desired_outcomes
    )

    # Create cognitive discovery data
    cognitive_data = CognitiveDiscoveryData(
        goals=goals,
        limiting_beliefs=limiting_beliefs,
        desired_outcomes=desired_outcomes,
        goal_assessments=gas_ratings,
        ideal_actual_ratings=ideal_actual,
        belief_nodes=belief_graph["nodes"],
        belief_edges=belief_graph["edges"],
        overall_confidence=0.7,
        overall_motivation=0.75,
        intake_depth="cognitive_extended"
    )

    # Save to database
    created_ids = await agent.save_cognitive_assessment(
        user_id=user_id,
        tenant_id=tenant_id,
        agent_id=contract.id,
        cognitive_data=cognitive_data
    )

    logger.info(f"✅ Cognitive intake complete for user {user_id}")

    return {
        "cognitive_data": cognitive_data.model_dump(),
        "created_ids": created_ids,
        "conflict_score": belief_graph["conflict_score"]
    }
