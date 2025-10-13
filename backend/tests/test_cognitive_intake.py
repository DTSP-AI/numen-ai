"""
Test Suite for Cognitive Intake Agent

Tests IntakeAgentCognitive functionality:
- GAS rating collection
- Ideal vs Actual rating collection
- Belief graph construction
- Cognitive assessment saving

Uses pytest with asyncio and comprehensive mocking.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid
import json


@pytest.fixture
def mock_agent_contract():
    """Mock agent contract"""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Intake Agent",
        "type": "conversational",
        "identity": {
            "short_description": "Test cognitive intake agent",
            "mission": "Collect cognitive assessments"
        },
        "traits": {
            "empathy": 90,
            "confidence": 80
        },
        "configuration": {
            "llm_model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 500
        },
        "metadata": {
            "tenant_id": "tenant-123",
            "owner_id": "user-123"
        }
    }


@pytest.fixture
def mock_memory_manager():
    """Mock memory manager"""
    manager = Mock()
    manager.add_memory = AsyncMock()
    return manager


@pytest.fixture
def sample_intake_data():
    """Sample intake data"""
    return {
        "goals": ["Achieve financial abundance", "Build confidence in relationships"],
        "limiting_beliefs": [
            "Money is hard to earn",
            "I'm not confident enough",
            "Success requires sacrifice"
        ],
        "desired_outcomes": [
            "Earning $100k by year-end",
            "Speaking confidently at presentations"
        ]
    }


class TestGASRatingCollection:
    """Test Goal Attainment Scaling rating collection"""

    @pytest.mark.asyncio
    async def test_collect_gas_ratings_success(self, mock_agent_contract, mock_memory_manager, sample_intake_data):
        """Test successful GAS rating collection"""
        from models.agent import AgentContract
        from agents.intake_agent_cognitive import IntakeAgentCognitive

        contract = AgentContract(**mock_agent_contract)
        agent = IntakeAgentCognitive(contract, mock_memory_manager, enable_cognitive_assessment=True)

        gas_ratings = await agent.collect_gas_ratings(
            user_id="user-123",
            tenant_id="tenant-123",
            agent_id=contract.id,
            goals=sample_intake_data["goals"]
        )

        # Verify ratings for each goal
        assert len(gas_ratings) == len(sample_intake_data["goals"])

        for goal in sample_intake_data["goals"]:
            assert goal in gas_ratings
            rating = gas_ratings[goal]

            # Verify required fields
            assert "gas_current_level" in rating
            assert "gas_expected_level" in rating
            assert "gas_target_level" in rating
            assert "goal_category" in rating

            # Verify scale constraints
            assert -2 <= rating["gas_current_level"] <= 2
            assert -2 <= rating["gas_expected_level"] <= 2
            assert -2 <= rating["gas_target_level"] <= 2

    @pytest.mark.asyncio
    async def test_collect_gas_ratings_empty_goals(self, mock_agent_contract, mock_memory_manager):
        """Test GAS rating collection with no goals"""
        from models.agent import AgentContract
        from agents.intake_agent_cognitive import IntakeAgentCognitive

        contract = AgentContract(**mock_agent_contract)
        agent = IntakeAgentCognitive(contract, mock_memory_manager)

        gas_ratings = await agent.collect_gas_ratings(
            user_id="user-123",
            tenant_id="tenant-123",
            agent_id=contract.id,
            goals=[]
        )

        assert gas_ratings == {}

    @pytest.mark.asyncio
    async def test_goal_categorization(self, mock_agent_contract, mock_memory_manager):
        """Test automatic goal categorization"""
        from models.agent import AgentContract
        from agents.intake_agent_cognitive import IntakeAgentCognitive

        contract = AgentContract(**mock_agent_contract)
        agent = IntakeAgentCognitive(contract, mock_memory_manager)

        test_cases = [
            ("Earn more money", "financial"),
            ("Get a promotion at work", "career"),
            ("Lose 20 pounds", "health"),
            ("Find a romantic partner", "relationships"),
            ("Meditate daily", "spiritual"),
            ("Write a novel", "creative"),
            ("Build self-confidence", "personal_growth"),
            ("Random goal text", "other")
        ]

        for goal_text, expected_category in test_cases:
            category = agent._categorize_goal(goal_text)
            assert category == expected_category, f"Expected {expected_category} for '{goal_text}', got {category}"


class TestIdealActualRatings:
    """Test Ideal vs Actual rating collection"""

    @pytest.mark.asyncio
    async def test_collect_ideal_actual_ratings(self, mock_agent_contract, mock_memory_manager, sample_intake_data):
        """Test ideal/actual rating collection"""
        from models.agent import AgentContract
        from agents.intake_agent_cognitive import IntakeAgentCognitive

        contract = AgentContract(**mock_agent_contract)
        agent = IntakeAgentCognitive(contract, mock_memory_manager)

        ratings = await agent.collect_ideal_actual_ratings(sample_intake_data["goals"])

        # Verify ratings for each goal
        assert len(ratings) == len(sample_intake_data["goals"])

        for goal in sample_intake_data["goals"]:
            assert goal in ratings
            rating = ratings[goal]

            # Verify fields
            assert "ideal_state_rating" in rating
            assert "actual_state_rating" in rating

            # Verify range
            assert 0 <= rating["ideal_state_rating"] <= 100
            assert 0 <= rating["actual_state_rating"] <= 100

            # Verify ideal >= actual (creates gap)
            assert rating["ideal_state_rating"] >= rating["actual_state_rating"]


class TestBeliefGraphConstruction:
    """Test Cognitive-Affective Map construction"""

    @pytest.mark.asyncio
    async def test_build_belief_graph_success(self, mock_agent_contract, mock_memory_manager, sample_intake_data):
        """Test successful belief graph construction"""
        from models.agent import AgentContract
        from agents.intake_agent_cognitive import IntakeAgentCognitive

        contract = AgentContract(**mock_agent_contract)
        agent = IntakeAgentCognitive(contract, mock_memory_manager)

        belief_graph = await agent.build_belief_graph(
            user_id="user-123",
            tenant_id="tenant-123",
            agent_id=contract.id,
            goals=sample_intake_data["goals"],
            limiting_beliefs=sample_intake_data["limiting_beliefs"],
            desired_outcomes=sample_intake_data["desired_outcomes"]
        )

        # Verify graph structure
        assert "graph_name" in belief_graph
        assert "graph_version" in belief_graph
        assert "nodes" in belief_graph
        assert "edges" in belief_graph
        assert "conflict_score" in belief_graph
        assert "tension_nodes" in belief_graph
        assert "core_beliefs" in belief_graph

        # Verify nodes
        nodes = belief_graph["nodes"]
        expected_node_count = (
            len(sample_intake_data["goals"]) +
            len(sample_intake_data["limiting_beliefs"]) +
            len(sample_intake_data["desired_outcomes"])
        )
        assert len(nodes) == expected_node_count

        # Verify node types
        goal_nodes = [n for n in nodes if n["node_type"] == "goal"]
        belief_nodes = [n for n in nodes if n["node_type"] == "limiting_belief"]
        outcome_nodes = [n for n in nodes if n["node_type"] == "outcome"]

        assert len(goal_nodes) == len(sample_intake_data["goals"])
        assert len(belief_nodes) == len(sample_intake_data["limiting_beliefs"])
        assert len(outcome_nodes) == len(sample_intake_data["desired_outcomes"])

        # Verify edges
        edges = belief_graph["edges"]
        assert len(edges) > 0

        # Verify blocking edges (beliefs → goals)
        blocking_edges = [e for e in edges if e["relationship"] == "blocks"]
        assert len(blocking_edges) > 0

        # Verify supporting edges (goals → outcomes)
        supporting_edges = [e for e in edges if e["relationship"] == "causes"]
        assert len(supporting_edges) > 0

        # Verify conflict score
        assert 0.0 <= belief_graph["conflict_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_belief_graph_empty_inputs(self, mock_agent_contract, mock_memory_manager):
        """Test belief graph with minimal inputs"""
        from models.agent import AgentContract
        from agents.intake_agent_cognitive import IntakeAgentCognitive

        contract = AgentContract(**mock_agent_contract)
        agent = IntakeAgentCognitive(contract, mock_memory_manager)

        belief_graph = await agent.build_belief_graph(
            user_id="user-123",
            tenant_id="tenant-123",
            agent_id=contract.id,
            goals=["Single goal"],
            limiting_beliefs=[],
            desired_outcomes=[]
        )

        # Should still create graph structure
        assert "nodes" in belief_graph
        assert "edges" in belief_graph
        assert len(belief_graph["nodes"]) == 1  # Just the goal
        assert belief_graph["conflict_score"] == 0.0  # No blocking edges

    @pytest.mark.asyncio
    async def test_conflict_score_calculation(self, mock_agent_contract, mock_memory_manager):
        """Test conflict score increases with blocking edges"""
        from models.agent import AgentContract
        from agents.intake_agent_cognitive import IntakeAgentCognitive

        contract = AgentContract(**mock_agent_contract)
        agent = IntakeAgentCognitive(contract, mock_memory_manager)

        # More beliefs = higher conflict
        test_cases = [
            (1, 1, 0.15),  # 1 belief × 1 goal = ~0.15
            (3, 2, 0.45),  # 3 beliefs × 2 goals = ~0.45
            (5, 2, 0.75),  # 5 beliefs × 2 goals = ~0.75
        ]

        for belief_count, goal_count, expected_min_score in test_cases:
            goals = [f"Goal {i}" for i in range(goal_count)]
            beliefs = [f"Belief {i}" for i in range(belief_count)]

            graph = await agent.build_belief_graph(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id=contract.id,
                goals=goals,
                limiting_beliefs=beliefs,
                desired_outcomes=[]
            )

            assert graph["conflict_score"] >= expected_min_score - 0.1  # Allow tolerance


class TestCognitiveAssessmentSaving:
    """Test saving complete cognitive assessment"""

    @pytest.mark.asyncio
    async def test_save_cognitive_assessment_success(self, mock_agent_contract, mock_memory_manager, sample_intake_data):
        """Test successful saving of cognitive assessment"""
        from models.agent import AgentContract
        from agents.intake_agent_cognitive import IntakeAgentCognitive, CognitiveDiscoveryData

        contract = AgentContract(**mock_agent_contract)
        agent = IntakeAgentCognitive(contract, mock_memory_manager)

        # Build belief graph
        belief_graph = await agent.build_belief_graph(
            user_id="user-123",
            tenant_id="tenant-123",
            agent_id=contract.id,
            goals=sample_intake_data["goals"],
            limiting_beliefs=sample_intake_data["limiting_beliefs"],
            desired_outcomes=sample_intake_data["desired_outcomes"]
        )

        # Create cognitive data
        cognitive_data = CognitiveDiscoveryData(
            goals=sample_intake_data["goals"],
            limiting_beliefs=sample_intake_data["limiting_beliefs"],
            desired_outcomes=sample_intake_data["desired_outcomes"],
            goal_assessments={"Goal 1": {"gas_current_level": -1, "gas_target_level": 2, "goal_category": "other"}},
            ideal_actual_ratings={"Goal 1": {"ideal_state_rating": 100, "actual_state_rating": 40}},
            belief_nodes=belief_graph["nodes"],
            belief_edges=belief_graph["edges"],
            overall_confidence=0.7,
            overall_motivation=0.8
        )

        # Mock the storage functions
        with patch('agents.intake_agent_cognitive.store_goal_assessment', new_callable=AsyncMock) as mock_store_goal, \
             patch('agents.intake_agent_cognitive.store_belief_graph', new_callable=AsyncMock) as mock_store_graph, \
             patch('agents.intake_agent_cognitive.store_cognitive_metric', new_callable=AsyncMock) as mock_store_metric:

            mock_store_goal.return_value = str(uuid.uuid4())
            mock_store_graph.return_value = str(uuid.uuid4())

            created_ids = await agent.save_cognitive_assessment(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id=contract.id,
                cognitive_data=cognitive_data
            )

            # Verify returned IDs
            assert "goal_ids" in created_ids
            assert "graph_id" in created_ids
            assert len(created_ids["goal_ids"]) == 1
            assert created_ids["graph_id"] is not None

            # Verify storage functions were called
            assert mock_store_goal.called
            assert mock_store_graph.called


class TestFullCognitiveIntakeFlow:
    """Integration test for complete cognitive intake"""

    @pytest.mark.asyncio
    async def test_complete_cognitive_intake_flow(self, mock_agent_contract, sample_intake_data):
        """Test end-to-end cognitive intake flow"""
        with patch('agents.intake_agent_cognitive.store_goal_assessment', new_callable=AsyncMock) as mock_store_goal, \
             patch('agents.intake_agent_cognitive.store_belief_graph', new_callable=AsyncMock) as mock_store_graph, \
             patch('agents.intake_agent_cognitive.store_cognitive_metric', new_callable=AsyncMock) as mock_store_metric:

            mock_store_goal.return_value = str(uuid.uuid4())
            mock_store_graph.return_value = str(uuid.uuid4())

            from agents.intake_agent_cognitive import run_cognitive_intake

            result = await run_cognitive_intake(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_contract=mock_agent_contract,
                goals=sample_intake_data["goals"],
                limiting_beliefs=sample_intake_data["limiting_beliefs"],
                desired_outcomes=sample_intake_data["desired_outcomes"]
            )

            # Verify result structure
            assert "cognitive_data" in result
            assert "created_ids" in result
            assert "conflict_score" in result

            # Verify cognitive data
            cognitive_data = result["cognitive_data"]
            assert cognitive_data["goals"] == sample_intake_data["goals"]
            assert cognitive_data["limiting_beliefs"] == sample_intake_data["limiting_beliefs"]
            assert "goal_assessments" in cognitive_data
            assert "belief_nodes" in cognitive_data
            assert "belief_edges" in cognitive_data

            # Verify created IDs
            assert len(result["created_ids"]["goal_ids"]) == len(sample_intake_data["goals"])
            assert result["created_ids"]["graph_id"] is not None

            # Verify conflict score
            assert 0.0 <= result["conflict_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_high_conflict_scenario(self, mock_agent_contract):
        """Test scenario with high belief conflict"""
        many_beliefs = [f"Limiting belief {i}" for i in range(10)]

        with patch('agents.intake_agent_cognitive.store_goal_assessment', new_callable=AsyncMock) as mock_store_goal, \
             patch('agents.intake_agent_cognitive.store_belief_graph', new_callable=AsyncMock) as mock_store_graph, \
             patch('agents.intake_agent_cognitive.store_cognitive_metric', new_callable=AsyncMock) as mock_store_metric:

            mock_store_goal.return_value = str(uuid.uuid4())
            mock_store_graph.return_value = str(uuid.uuid4())

            from agents.intake_agent_cognitive import run_cognitive_intake

            result = await run_cognitive_intake(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_contract=mock_agent_contract,
                goals=["Goal 1", "Goal 2"],
                limiting_beliefs=many_beliefs,
                desired_outcomes=["Outcome 1"]
            )

            # Should have high conflict score
            assert result["conflict_score"] > 0.5

            # Should trigger conflict metric storage if threshold exceeded
            if result["conflict_score"] >= 0.8:
                mock_store_metric.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
