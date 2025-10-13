"""
Test Suite for Cognitive Memory Functions

Tests the cognitive assessment storage functions in memory_manager.py:
- store_goal_assessment()
- store_belief_graph()
- store_cognitive_metric()

Uses pytest with asyncio and mocks for DB and Mem0 dependencies.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import uuid

# Mock asyncpg before import
asyncpg_mock = Mock()


@pytest.fixture
def mock_pg_pool():
    """Mock PostgreSQL connection pool"""
    pool = AsyncMock()
    conn = AsyncMock()

    # Mock connection acquisition
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None

    # Mock execute and fetch
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)

    return pool, conn


@pytest.fixture
def mock_memory_manager():
    """Mock MemoryManager instance"""
    manager = Mock()
    manager.add_memory = AsyncMock()
    manager.user_namespace = Mock(return_value="tenant:agent:user:user-123")
    return manager


@pytest.fixture
def sample_goal_assessment():
    """Sample goal assessment data"""
    return {
        "goal_text": "Achieve financial abundance",
        "goal_category": "financial",
        "gas_current_level": -1,
        "gas_expected_level": 0,
        "gas_target_level": 2,
        "ideal_state_rating": 100,
        "actual_state_rating": 40,
        "confidence_score": 0.7,
        "motivation_score": 0.8,
        "intake_depth": "cognitive_extended"
    }


@pytest.fixture
def sample_belief_graph():
    """Sample belief graph data"""
    return {
        "graph_name": "Test Belief System",
        "graph_version": 1,
        "nodes": [
            {
                "id": "node-1",
                "label": "I'm not good enough",
                "node_type": "limiting_belief",
                "emotional_valence": -0.7,
                "centrality": 0.8,
                "strength": 0.9
            },
            {
                "id": "node-2",
                "label": "Financial abundance",
                "node_type": "goal",
                "emotional_valence": 0.9,
                "centrality": 0.9,
                "strength": 0.8
            }
        ],
        "edges": [
            {
                "source": "node-1",
                "target": "node-2",
                "relationship": "blocks",
                "weight": 0.7
            }
        ],
        "conflict_score": 0.45,
        "tension_nodes": ["node-1"],
        "core_beliefs": ["node-2"]
    }


class TestStoreGoalAssessment:
    """Test goal assessment storage"""

    @pytest.mark.asyncio
    async def test_store_goal_assessment_success(self, mock_pg_pool, mock_memory_manager, sample_goal_assessment):
        """Test successful goal assessment storage"""
        pool, conn = mock_pg_pool

        with patch('services.memory_manager.get_pg_pool', return_value=pool), \
             patch('services.memory_manager.MemoryManager', return_value=mock_memory_manager):

            from services.memory_manager import store_goal_assessment

            goal_id = await store_goal_assessment(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id="agent-123",
                goal_assessment=sample_goal_assessment
            )

            # Verify goal_id was generated
            assert goal_id is not None
            assert isinstance(goal_id, str)

            # Verify database insert was called
            conn.execute.assert_called_once()
            call_args = conn.execute.call_args[0]
            assert "INSERT INTO goal_assessments" in call_args[0]

            # Verify Mem0 storage was called
            mock_memory_manager.add_memory.assert_called_once()
            mem0_call = mock_memory_manager.add_memory.call_args
            assert "Goal:" in mem0_call.kwargs["content"]
            assert mem0_call.kwargs["memory_type"] == "goal_assessment"

    @pytest.mark.asyncio
    async def test_store_goal_assessment_db_error(self, mock_pg_pool, sample_goal_assessment):
        """Test handling of database errors"""
        pool, conn = mock_pg_pool
        conn.execute.side_effect = Exception("Database connection failed")

        with patch('services.memory_manager.get_pg_pool', return_value=pool):
            from services.memory_manager import store_goal_assessment

            with pytest.raises(Exception) as exc_info:
                await store_goal_assessment(
                    user_id="user-123",
                    tenant_id="tenant-123",
                    agent_id="agent-123",
                    goal_assessment=sample_goal_assessment
                )

            assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_store_goal_assessment_defaults(self, mock_pg_pool, mock_memory_manager):
        """Test goal assessment with minimal data (uses defaults)"""
        pool, conn = mock_pg_pool

        minimal_assessment = {
            "goal_text": "Test goal",
            "goal_category": "other"
        }

        with patch('services.memory_manager.get_pg_pool', return_value=pool), \
             patch('services.memory_manager.MemoryManager', return_value=mock_memory_manager):

            from services.memory_manager import store_goal_assessment

            goal_id = await store_goal_assessment(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id="agent-123",
                goal_assessment=minimal_assessment
            )

            assert goal_id is not None
            conn.execute.assert_called_once()


class TestStoreBeliefGraph:
    """Test belief graph storage"""

    @pytest.mark.asyncio
    async def test_store_belief_graph_success(self, mock_pg_pool, mock_memory_manager, sample_belief_graph):
        """Test successful belief graph storage"""
        pool, conn = mock_pg_pool

        with patch('services.memory_manager.get_pg_pool', return_value=pool), \
             patch('services.memory_manager.MemoryManager', return_value=mock_memory_manager):

            from services.memory_manager import store_belief_graph

            graph_id = await store_belief_graph(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id="agent-123",
                belief_graph=sample_belief_graph
            )

            # Verify graph_id was generated
            assert graph_id is not None
            assert isinstance(graph_id, str)

            # Verify database insert was called
            conn.execute.assert_called_once()
            call_args = conn.execute.call_args[0]
            assert "INSERT INTO belief_graphs" in call_args[0]

            # Verify JSONB serialization in call
            assert len(call_args) > 1  # Has parameters

            # Verify Mem0 storage was called
            mock_memory_manager.add_memory.assert_called_once()
            mem0_call = mock_memory_manager.add_memory.call_args
            assert "Limiting beliefs identified:" in mem0_call.kwargs["content"]
            assert mem0_call.kwargs["memory_type"] == "belief_graph"

    @pytest.mark.asyncio
    async def test_store_belief_graph_empty_nodes(self, mock_pg_pool, mock_memory_manager):
        """Test belief graph with no nodes/edges"""
        pool, conn = mock_pg_pool

        empty_graph = {
            "graph_name": "Empty Graph",
            "graph_version": 1,
            "nodes": [],
            "edges": [],
            "conflict_score": 0.0,
            "tension_nodes": [],
            "core_beliefs": []
        }

        with patch('services.memory_manager.get_pg_pool', return_value=pool), \
             patch('services.memory_manager.MemoryManager', return_value=mock_memory_manager):

            from services.memory_manager import store_belief_graph

            graph_id = await store_belief_graph(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id="agent-123",
                belief_graph=empty_graph
            )

            assert graph_id is not None
            conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_belief_graph_high_conflict(self, mock_pg_pool, mock_memory_manager, sample_belief_graph):
        """Test belief graph with high conflict score"""
        pool, conn = mock_pg_pool

        # Set high conflict score
        sample_belief_graph["conflict_score"] = 0.9

        with patch('services.memory_manager.get_pg_pool', return_value=pool), \
             patch('services.memory_manager.MemoryManager', return_value=mock_memory_manager):

            from services.memory_manager import store_belief_graph

            graph_id = await store_belief_graph(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id="agent-123",
                belief_graph=sample_belief_graph
            )

            assert graph_id is not None

            # Should extract limiting beliefs from nodes
            mem0_call = mock_memory_manager.add_memory.call_args
            assert "I'm not good enough" in mem0_call.kwargs["content"] or "Limiting beliefs" in mem0_call.kwargs["content"]


class TestStoreCognitiveMetric:
    """Test cognitive metric storage"""

    @pytest.mark.asyncio
    async def test_store_cognitive_metric_success(self, mock_pg_pool):
        """Test successful cognitive metric storage"""
        pool, conn = mock_pg_pool

        with patch('services.memory_manager.get_pg_pool', return_value=pool):
            from services.memory_manager import store_cognitive_metric

            metric_id = await store_cognitive_metric(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id="agent-123",
                metric_type="emotion_conflict",
                metric_value=0.75,
                context_data={"goal_id": "goal-123"},
                threshold_value=0.7
            )

            # Verify metric_id was generated
            assert metric_id is not None
            assert isinstance(metric_id, str)

            # Verify database insert was called
            conn.execute.assert_called_once()
            call_args = conn.execute.call_args[0]
            assert "INSERT INTO cognitive_metrics" in call_args[0]

    @pytest.mark.asyncio
    async def test_store_cognitive_metric_threshold_exceeded(self, mock_pg_pool):
        """Test metric with threshold exceeded"""
        pool, conn = mock_pg_pool

        with patch('services.memory_manager.get_pg_pool', return_value=pool):
            from services.memory_manager import store_cognitive_metric

            metric_id = await store_cognitive_metric(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id="agent-123",
                metric_type="repeated_failure",
                metric_value=3.0,
                threshold_value=2.0
            )

            assert metric_id is not None

            # Verify threshold_exceeded was set to True
            call_args = conn.execute.call_args[0]
            # The 9th parameter should be threshold_exceeded (True)
            assert call_args[9] == True  # threshold_exceeded

    @pytest.mark.asyncio
    async def test_store_cognitive_metric_no_threshold(self, mock_pg_pool):
        """Test metric without threshold"""
        pool, conn = mock_pg_pool

        with patch('services.memory_manager.get_pg_pool', return_value=pool):
            from services.memory_manager import store_cognitive_metric

            metric_id = await store_cognitive_metric(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id="agent-123",
                metric_type="goal_progress",
                metric_value=0.5
            )

            assert metric_id is not None
            conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_metric_category_mapping(self, mock_pg_pool):
        """Test that metric types are correctly mapped to categories"""
        pool, conn = mock_pg_pool

        test_cases = [
            ("emotion_conflict", "emotional"),
            ("motivation_drop", "emotional"),
            ("repeated_failure", "behavioral"),
            ("goal_progress", "behavioral"),
            ("belief_shift", "cognitive"),
            ("unknown_type", "emotional")  # default
        ]

        with patch('services.memory_manager.get_pg_pool', return_value=pool):
            from services.memory_manager import store_cognitive_metric, _get_metric_category

            for metric_type, expected_category in test_cases:
                category = _get_metric_category(metric_type)
                assert category == expected_category, f"Expected {expected_category} for {metric_type}, got {category}"

    @pytest.mark.asyncio
    async def test_trigger_action_mapping(self, mock_pg_pool):
        """Test that trigger actions are correctly determined"""
        pool, conn = mock_pg_pool

        with patch('services.memory_manager.get_pg_pool', return_value=pool):
            from services.memory_manager import _get_trigger_action

            # Threshold not exceeded
            action = _get_trigger_action("emotion_conflict", False)
            assert action is None

            # Threshold exceeded
            action = _get_trigger_action("emotion_conflict", True)
            assert action == "Initiate belief reassessment conversation"

            action = _get_trigger_action("repeated_failure", True)
            assert action == "Suggest breaking goal into smaller steps"

            action = _get_trigger_action("unknown_type", True)
            assert action == "Review with user"


class TestIntegration:
    """Integration tests for cognitive memory functions"""

    @pytest.mark.asyncio
    async def test_full_cognitive_assessment_flow(self, mock_pg_pool, mock_memory_manager, sample_goal_assessment, sample_belief_graph):
        """Test complete flow: goal assessment + belief graph + metrics"""
        pool, conn = mock_pg_pool

        with patch('services.memory_manager.get_pg_pool', return_value=pool), \
             patch('services.memory_manager.MemoryManager', return_value=mock_memory_manager):

            from services.memory_manager import (
                store_goal_assessment,
                store_belief_graph,
                store_cognitive_metric
            )

            # 1. Store goal assessment
            goal_id = await store_goal_assessment(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id="agent-123",
                goal_assessment=sample_goal_assessment
            )
            assert goal_id is not None

            # 2. Store belief graph
            graph_id = await store_belief_graph(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id="agent-123",
                belief_graph=sample_belief_graph
            )
            assert graph_id is not None

            # 3. Store cognitive metric
            metric_id = await store_cognitive_metric(
                user_id="user-123",
                tenant_id="tenant-123",
                agent_id="agent-123",
                metric_type="emotion_conflict",
                metric_value=0.75,
                context_data={"goal_id": goal_id, "graph_id": graph_id},
                threshold_value=0.7
            )
            assert metric_id is not None

            # Verify all three DB calls were made
            assert conn.execute.call_count == 3

            # Verify Mem0 storage was called twice (goal + graph)
            assert mock_memory_manager.add_memory.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
