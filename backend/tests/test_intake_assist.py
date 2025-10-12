"""
Tests for /api/intake/assist endpoint
"""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_intake_assist_success():
    """Test successful text refinement"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/intake/assist",
            json={"text": "i want be rich"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "suggestion" in data
        assert len(data["suggestion"]) > 0
        assert data["suggestion"] != "i want be rich"  # Should be refined


@pytest.mark.asyncio
async def test_intake_assist_empty_text():
    """Test that empty text returns 400"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/intake/assist",
            json={"text": ""}
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_intake_assist_whitespace_only():
    """Test that whitespace-only text returns 400"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/intake/assist",
            json={"text": "   "}
        )

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_intake_assist_preserves_intent():
    """Test that AI preserves user's original intent"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/intake/assist",
            json={"text": "need confidence"}
        )

        assert response.status_code == 200
        data = response.json()
        suggestion = data["suggestion"].lower()
        # Should contain key intent words
        assert "confidence" in suggestion or "confident" in suggestion
