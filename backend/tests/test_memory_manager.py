"""
Test Memory Manager: Thread + Semantic Memory

Validates memory insert and retrieval roundtrip.
"""

import pytest
import uuid


@pytest.mark.asyncio
async def test_memory_manager_initialization():
    """Test memory tables can be initialized"""
    from services.memory_manager import MemoryManager

    memory_manager = MemoryManager()
    await memory_manager.initialize()

    # If no exception, tables exist
    assert True


@pytest.mark.asyncio
async def test_embed_and_similar_roundtrip():
    """Test embedding upsert and similarity retrieval"""
    from services.memory_manager import MemoryManager

    memory_manager = MemoryManager()
    await memory_manager.initialize()

    test_user_id = "test-user-memory"
    test_agent_id = str(uuid.uuid4())
    test_session_id = str(uuid.uuid4())
    test_content = "User wants to build confidence and reduce anxiety"

    # Upsert content
    await memory_manager.embed_and_upsert(
        user_id=test_user_id,
        agent_id=test_agent_id,
        session_id=test_session_id,
        content=test_content,
        meta={"type": "test", "source": "pytest"}
    )

    # Retrieve similar
    results = await memory_manager.similar(
        user_id=test_user_id,
        agent_id=test_agent_id,
        session_id=test_session_id,
        query="confidence anxiety",
        k=5
    )

    # Should return at least the inserted content
    assert len(results) > 0
    assert any(test_content in result["content"] for result in results)


@pytest.mark.asyncio
async def test_record_turn():
    """Test thread memory turn recording"""
    from services.memory_manager import MemoryManager

    memory_manager = MemoryManager()
    await memory_manager.initialize()

    test_user_id = "test-user-turn"
    test_agent_id = str(uuid.uuid4())
    test_session_id = str(uuid.uuid4())

    # Record a turn
    await memory_manager.record_turn(
        user_id=test_user_id,
        agent_id=test_agent_id,
        session_id=test_session_id,
        turn_index=1,
        key="user_input",
        value_dict={"text": "Hello, guide me"}
    )

    # Retrieve context
    context = await memory_manager.context_for_planning(
        user_id=test_user_id,
        agent_id=test_agent_id,
        session_id=test_session_id
    )

    assert "thread_tail" in context
    assert len(context["thread_tail"]) > 0
    assert context["thread_tail"][0]["key"] == "user_input"
