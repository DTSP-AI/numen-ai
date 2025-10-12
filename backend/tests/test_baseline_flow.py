"""
Test Baseline Flow: Intake → Guide → Session + Protocol

Happy path validation for baseline compliance.
"""

import pytest
import json
from httpx import AsyncClient

# Note: These are integration tests that require database setup
# Run with: pytest backend/tests/test_baseline_flow.py


@pytest.mark.asyncio
async def test_intake_process():
    """Test POST /api/intake/process"""
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/intake/process",
            json={
                "user_id": "test-user-123",
                "answers": {
                    "goals": ["Build confidence", "Reduce anxiety"],
                    "tone": "calm",
                    "session_type": "manifestation"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "normalized_goals" in data
        assert "prefs" in data
        assert len(data["normalized_goals"]) >= 1
        assert data["prefs"]["tone"] == "calm"


@pytest.mark.asyncio
async def test_baseline_flow_complete():
    """
    Test complete baseline flow:
    1. Process intake
    2. Create guide from intake
    3. Verify session exists
    4. Verify protocol exists
    5. Verify memory tables populated
    """
    from main import app
    from database import get_pg_pool

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Process intake
        intake_response = await client.post(
            "/api/intake/process",
            json={
                "user_id": "test-user-baseline",
                "answers": {
                    "goals": ["Test goal"],
                    "tone": "calm",
                    "session_type": "manifestation"
                }
            }
        )

        assert intake_response.status_code == 200
        intake_contract = intake_response.json()

        # Step 2: Create guide from intake
        guide_response = await client.post(
            "/api/agents/from_intake_contract",
            json={
                "user_id": "test-user-baseline",
                "intake_contract": intake_contract
            }
        )

        assert guide_response.status_code == 200
        result = guide_response.json()

        # Verify structure
        assert "agent" in result
        assert "session" in result
        assert "protocol" in result

        agent_id = result["agent"]["id"]
        session_id = result["session"]["id"]

        # Step 3: Verify session exists in database
        pool = get_pg_pool()
        async with pool.acquire() as conn:
            session_row = await conn.fetchrow("""
                SELECT id, session_data FROM sessions WHERE id = $1::uuid
            """, session_id)

            assert session_row is not None
            session_data = session_row["session_data"]

            # Step 4: Verify protocol exists in session_data
            assert "manifestation_protocol" in session_data
            protocol = session_data["manifestation_protocol"]
            assert "affirmations" in protocol

            # Step 5: Verify memory tables populated
            thread_count = await conn.fetchval("""
                SELECT COUNT(*) FROM thread_memory WHERE session_id = $1::uuid
            """, session_id)

            semantic_count = await conn.fetchval("""
                SELECT COUNT(*) FROM semantic_memory WHERE session_id = $1::uuid
            """, session_id)

            # At least one memory entry should exist
            assert (thread_count + semantic_count) > 0


def test_baseline_compliance():
    """
    Baseline flow exit criteria validation

    ✅ Intake Agent → Guide Agent handoff works
    ✅ Guide Agent created with persisted contract
    ✅ Guide Agent auto-creates Session
    ✅ Session includes generated Manifestation Strategy
    """
    # This test documents compliance - actual checks in test_baseline_flow_complete
    pass
