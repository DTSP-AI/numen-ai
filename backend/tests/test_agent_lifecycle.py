"""
Agent Lifecycle Tests - Comprehensive Test Suite

Tests complete agent lifecycle following Agent Creation Standard:
1. Create agent from JSON contract
2. Initialize memory namespace
3. Save contract to filesystem
4. Create default thread
5. Process agent interactions
6. Update agent with versioning
7. Delete (archive) agent
"""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any

from models.agent import (
    AgentContract, AgentIdentity, AgentTraits, AgentConfiguration,
    AgentMetadata, AgentType, AgentStatus
)
from services.agent_service import AgentService
from services.contract_validator import ContractValidator
from database import init_db, get_pg_pool


# Fixtures

@pytest.fixture(scope="module")
async def db():
    """Initialize database for testing"""
    await init_db()
    yield
    # Cleanup handled by transaction rollback

@pytest.fixture
def tenant_id():
    """Generate test tenant ID"""
    return str(uuid.uuid4())

@pytest.fixture
def user_id():
    """Generate test user ID"""
    return str(uuid.uuid4())

@pytest.fixture
async def test_tenant(tenant_id):
    """Create test tenant in database"""
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO tenants (id, name, slug, status)
            VALUES ($1::uuid, 'Test Tenant', 'test-tenant', 'active')
            ON CONFLICT (id) DO NOTHING
        """, tenant_id)
    yield tenant_id

@pytest.fixture
async def test_user(user_id, tenant_id, test_tenant):
    """Create test user in database"""
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, tenant_id, email, name, status)
            VALUES ($1::uuid, $2::uuid, 'test@example.com', 'Test User', 'active')
            ON CONFLICT (id) DO NOTHING
        """, user_id, tenant_id)
    yield user_id

@pytest.fixture
def sample_contract():
    """Sample agent contract for testing"""
    return AgentContract(
        name="Test Agent - Manifestation Coach",
        type=AgentType.CONVERSATIONAL,
        identity=AgentIdentity(
            short_description="Test agent for validation",
            full_description="A test agent for comprehensive lifecycle testing",
            character_role="Test Coach",
            mission="Test agent capabilities thoroughly",
            interaction_style="Professional and thorough"
        ),
        traits=AgentTraits(
            creativity=75,
            empathy=60,
            confidence=80,
            discipline=65,
            assertiveness=55,
            humor=40,
            formality=50,
            verbosity=50,
            spirituality=60,
            supportiveness=70
        ),
        configuration=AgentConfiguration(
            llm_model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=500,
            memory_enabled=True,
            voice_enabled=False,
            tools_enabled=False
        ),
        metadata=AgentMetadata(
            tenant_id="",  # Will be set in test
            owner_id="",  # Will be set in test
            tags=["test", "manifestation"],
            status=AgentStatus.ACTIVE
        )
    )


# Test 1: Agent Creation

@pytest.mark.asyncio
async def test_agent_creation_complete_flow(db, test_tenant, test_user, tenant_id, user_id, sample_contract):
    """Test complete agent creation flow"""
    service = AgentService()

    # Set metadata
    sample_contract.metadata.tenant_id = tenant_id
    sample_contract.metadata.owner_id = user_id

    # Create agent
    agent = await service.create_agent(
        contract=sample_contract,
        tenant_id=tenant_id,
        owner_id=user_id
    )

    # Verify database record
    assert agent["id"] == sample_contract.id
    assert agent["name"] == sample_contract.name
    assert agent["status"] == AgentStatus.ACTIVE.value
    assert agent["tenant_id"] == tenant_id
    assert agent["owner_id"] == user_id

    # Verify contract stored
    assert agent["contract"]["name"] == sample_contract.name
    assert agent["contract"]["traits"]["creativity"] == 75
    assert agent["contract"]["traits"]["empathy"] == 60
    assert agent["contract"]["traits"]["discipline"] == 65  # Core attribute

    # Verify filesystem JSON exists
    import os
    contract_path = f"backend/prompts/{sample_contract.id}/agent_contract.json"
    assert os.path.exists(contract_path), "Filesystem contract should exist"

    prompt_path = f"backend/prompts/{sample_contract.id}/system_prompt.txt"
    assert os.path.exists(prompt_path), "System prompt should exist"

    # Cleanup
    await service.delete_agent(sample_contract.id, tenant_id)


# Test 2: Agent Retrieval

@pytest.mark.asyncio
async def test_agent_retrieval(db, test_tenant, test_user, tenant_id, user_id, sample_contract):
    """Test agent retrieval with tenant validation"""
    service = AgentService()

    sample_contract.metadata.tenant_id = tenant_id
    sample_contract.metadata.owner_id = user_id

    # Create agent
    created = await service.create_agent(sample_contract, tenant_id, user_id)

    # Retrieve agent
    agent = await service.get_agent(sample_contract.id, tenant_id)

    assert agent is not None
    assert agent["id"] == sample_contract.id
    assert agent["name"] == sample_contract.name

    # Try to retrieve with wrong tenant (should fail)
    wrong_tenant = str(uuid.uuid4())
    agent_wrong = await service.get_agent(sample_contract.id, wrong_tenant)
    assert agent_wrong is None, "Should not retrieve agent with wrong tenant"

    # Cleanup
    await service.delete_agent(sample_contract.id, tenant_id)


# Test 3: Agent Update with Versioning

@pytest.mark.asyncio
async def test_agent_update_with_versioning(db, test_tenant, test_user, tenant_id, user_id, sample_contract):
    """Test agent update creates version snapshot"""
    service = AgentService()

    sample_contract.metadata.tenant_id = tenant_id
    sample_contract.metadata.owner_id = user_id

    # Create agent
    await service.create_agent(sample_contract, tenant_id, user_id)

    # Update agent
    updates = {
        "traits": {
            "creativity": 90,  # Changed from 75
            "empathy": 85     # Changed from 60
        },
        "change_summary": "Increased creativity and empathy"
    }

    updated_agent = await service.update_agent(sample_contract.id, tenant_id, updates)

    assert updated_agent is not None
    assert updated_agent["contract"]["traits"]["creativity"] == 90
    assert updated_agent["contract"]["traits"]["empathy"] == 85

    # Verify version snapshot created
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        versions = await conn.fetch("""
            SELECT version, contract, change_summary
            FROM agent_versions
            WHERE agent_id = $1::uuid
            ORDER BY created_at DESC
        """, sample_contract.id)

        assert len(versions) >= 1, "Version snapshot should exist"
        snapshot = versions[0]
        assert snapshot["contract"]["traits"]["creativity"] == 75  # Original value
        assert snapshot["change_summary"] == "Increased creativity and empathy"

    # Cleanup
    await service.delete_agent(sample_contract.id, tenant_id)


# Test 4: Agent Interaction

@pytest.mark.asyncio
async def test_agent_interaction_flow(db, test_tenant, test_user, tenant_id, user_id, sample_contract):
    """Test complete agent-user interaction"""
    service = AgentService()

    sample_contract.metadata.tenant_id = tenant_id
    sample_contract.metadata.owner_id = user_id

    # Create agent
    await service.create_agent(sample_contract, tenant_id, user_id)

    # Process interaction
    result = await service.process_interaction(
        agent_id=sample_contract.id,
        tenant_id=tenant_id,
        user_id=user_id,
        user_input="Hello, I want to manifest abundance in my life.",
        metadata={"source": "test"}
    )

    # Verify response
    assert "thread_id" in result
    assert "response" in result
    assert result["response"] != "", "Response should not be empty"
    assert result["agent_id"] == sample_contract.id

    # Verify thread created
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        thread = await conn.fetchrow("""
            SELECT id, agent_id, message_count
            FROM threads
            WHERE id = $1::uuid
        """, result["thread_id"])

        assert thread is not None
        assert thread["message_count"] == 2  # User + assistant message

    # Verify messages stored
    async with pool.acquire() as conn:
        messages = await conn.fetch("""
            SELECT role, content
            FROM thread_messages
            WHERE thread_id = $1::uuid
            ORDER BY created_at ASC
        """, result["thread_id"])

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello, I want to manifest abundance in my life."
        assert messages[1]["role"] == "assistant"

    # Verify interaction count updated
    updated_agent = await service.get_agent(sample_contract.id, tenant_id)
    assert updated_agent["interaction_count"] == 1

    # Cleanup
    await service.delete_agent(sample_contract.id, tenant_id)


# Test 5: Thread Persistence Across Interactions

@pytest.mark.asyncio
async def test_thread_persistence(db, test_tenant, test_user, tenant_id, user_id, sample_contract):
    """Test thread persistence across multiple interactions"""
    service = AgentService()

    sample_contract.metadata.tenant_id = tenant_id
    sample_contract.metadata.owner_id = user_id

    await service.create_agent(sample_contract, tenant_id, user_id)

    # First interaction
    result1 = await service.process_interaction(
        agent_id=sample_contract.id,
        tenant_id=tenant_id,
        user_id=user_id,
        user_input="First message"
    )

    thread_id = result1["thread_id"]

    # Second interaction (same thread)
    result2 = await service.process_interaction(
        agent_id=sample_contract.id,
        tenant_id=tenant_id,
        user_id=user_id,
        user_input="Second message",
        thread_id=thread_id
    )

    # Verify same thread used
    assert result2["thread_id"] == thread_id

    # Verify message count
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        thread = await conn.fetchrow("""
            SELECT message_count FROM threads WHERE id = $1::uuid
        """, thread_id)

        assert thread["message_count"] == 4  # 2 user + 2 assistant

    # Cleanup
    await service.delete_agent(sample_contract.id, tenant_id)


# Test 6: Contract Sync Validation

@pytest.mark.asyncio
async def test_contract_sync_validation(db, test_tenant, test_user, tenant_id, user_id, sample_contract):
    """Test filesystem-database contract synchronization"""
    service = AgentService()
    validator = ContractValidator()

    sample_contract.metadata.tenant_id = tenant_id
    sample_contract.metadata.owner_id = user_id

    await service.create_agent(sample_contract, tenant_id, user_id)

    # Validate sync (should pass)
    result = await validator.validate_agent_contract(sample_contract.id)
    assert result["valid"] is True

    # Modify filesystem contract (simulate desync)
    import json
    contract_path = f"backend/prompts/{sample_contract.id}/agent_contract.json"
    with open(contract_path, 'r') as f:
        fs_contract = json.load(f)

    fs_contract["traits"]["creativity"] = 999  # Invalid modification

    with open(contract_path, 'w') as f:
        json.dump(fs_contract, f, indent=2)

    # Validate sync (should fail)
    with pytest.raises(Exception):
        await validator.validate_agent_contract(sample_contract.id, auto_repair=False)

    # Validate with auto-repair (should fix)
    result_repaired = await validator.validate_agent_contract(sample_contract.id, auto_repair=True)
    assert result_repaired["valid"] is True
    assert result_repaired.get("repaired") is True

    # Verify filesystem repaired
    with open(contract_path, 'r') as f:
        repaired_contract = json.load(f)

    assert repaired_contract["traits"]["creativity"] == 75  # Original value restored

    # Cleanup
    await service.delete_agent(sample_contract.id, tenant_id)


# Test 7: Trait Modulation in System Prompt

@pytest.mark.asyncio
async def test_trait_modulation_in_prompt(sample_contract):
    """Test that system prompts include trait-specific behavioral directives"""
    from services.agent_service import AgentService

    service = AgentService()
    system_prompt = service._generate_system_prompt(sample_contract)

    # Verify trait modulation present
    assert "BEHAVIORAL DIRECTIVES" in system_prompt
    assert "Confidence" in system_prompt
    assert "Empathy" in system_prompt
    assert "Creativity" in system_prompt
    assert "Discipline" in system_prompt

    # Verify specific directives based on trait values
    # Confidence: 80 (high) should have specific language
    assert "certainty" in system_prompt.lower() or "conviction" in system_prompt.lower()

    # Empathy: 60 (moderate-high) should acknowledge feelings
    assert "emotional" in system_prompt.lower() or "feeling" in system_prompt.lower()


# Test 8: Multi-Tenancy Isolation

@pytest.mark.asyncio
async def test_multi_tenancy_isolation(db, sample_contract):
    """Test that agents are isolated by tenant"""
    service = AgentService()

    tenant1 = str(uuid.uuid4())
    tenant2 = str(uuid.uuid4())
    user1 = str(uuid.uuid4())
    user2 = str(uuid.uuid4())

    # Create tenants
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO tenants (id, name, slug, status)
            VALUES ($1::uuid, 'Tenant 1', 'tenant-1', 'active'), ($2::uuid, 'Tenant 2', 'tenant-2', 'active')
            ON CONFLICT DO NOTHING
        """, tenant1, tenant2)

        await conn.execute("""
            INSERT INTO users (id, tenant_id, email, name, status)
            VALUES ($1::uuid, $2::uuid, 'user1@example.com', 'User 1', 'active'),
                   ($3::uuid, $4::uuid, 'user2@example.com', 'User 2', 'active')
            ON CONFLICT DO NOTHING
        """, user1, tenant1, user2, tenant2)

    # Create agent for tenant1
    sample_contract.metadata.tenant_id = tenant1
    sample_contract.metadata.owner_id = user1
    await service.create_agent(sample_contract, tenant1, user1)

    # Try to access from tenant2 (should fail)
    agent_from_tenant2 = await service.get_agent(sample_contract.id, tenant2)
    assert agent_from_tenant2 is None, "Agent should not be accessible to different tenant"

    # Access from correct tenant (should succeed)
    agent_from_tenant1 = await service.get_agent(sample_contract.id, tenant1)
    assert agent_from_tenant1 is not None

    # Cleanup
    await service.delete_agent(sample_contract.id, tenant1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
