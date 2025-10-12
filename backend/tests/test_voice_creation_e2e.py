"""
End-to-End Voice Creation Pipeline Tests
=========================================

Tests per-user voice creation, filtering, and preview functionality.
Run with: pytest tests/test_voice_creation_e2e.py -v
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import io

from main import app
from services.elevenlabs_service import ElevenLabsService


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_elevenlabs_client():
    """Mock ElevenLabs SDK client"""
    mock = MagicMock()

    # Mock voices.get_all() response
    mock_voice1 = Mock()
    mock_voice1.voice_id = "system-voice-1"
    mock_voice1.name = "System Voice 1"
    mock_voice1.category = "general"
    mock_voice1.labels = {}  # No owner_id = system voice
    mock_voice1.preview_url = "https://example.com/preview1.mp3"

    mock_voice2 = Mock()
    mock_voice2.voice_id = "user-voice-1"
    mock_voice2.name = "User Voice 1"
    mock_voice2.category = "custom"
    mock_voice2.labels = {"owner_id": "test-user-123", "source": "numen"}
    mock_voice2.preview_url = None

    mock_voice3 = Mock()
    mock_voice3.voice_id = "other-user-voice"
    mock_voice3.name = "Other User Voice"
    mock_voice3.category = "custom"
    mock_voice3.labels = {"owner_id": "other-user-456", "source": "numen"}
    mock_voice3.preview_url = None

    mock_voices_response = Mock()
    mock_voices_response.voices = [mock_voice1, mock_voice2, mock_voice3]
    mock.voices.get_all.return_value = mock_voices_response

    # Mock voices.add() response
    mock_new_voice = Mock()
    mock_new_voice.voice_id = "new-voice-id"
    mock_new_voice.name = "Test Voice"
    mock_new_voice.description = "Test voice description"
    mock_new_voice.category = "custom"
    mock.voices.add.return_value = mock_new_voice

    # Mock generate() for preview
    mock.generate.return_value = iter([b"fake_audio_data"])

    return mock


class TestVoiceFiltering:
    """Test per-user voice filtering logic"""

    def test_get_voices_without_user_id_shows_system_only(self, client, mock_elevenlabs_client):
        """System voices visible to all, custom voices hidden without user_id"""
        with patch('services.elevenlabs_service.ElevenLabs', return_value=mock_elevenlabs_client):
            response = client.get("/api/voices")

            assert response.status_code == 200
            data = response.json()

            # Should only show system voice (no owner_id)
            assert data["total"] == 1
            assert data["voices"][0]["id"] == "system-voice-1"
            assert data["voices"][0]["name"] == "System Voice 1"

    def test_get_voices_with_user_id_shows_system_plus_owned(self, client, mock_elevenlabs_client):
        """User sees system voices + their own custom voices"""
        with patch('services.elevenlabs_service.ElevenLabs', return_value=mock_elevenlabs_client):
            response = client.get(
                "/api/voices",
                headers={"x-user-id": "test-user-123"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should show system voice + user's custom voice (not other user's)
            assert data["total"] == 2
            voice_ids = [v["id"] for v in data["voices"]]
            assert "system-voice-1" in voice_ids
            assert "user-voice-1" in voice_ids
            assert "other-user-voice" not in voice_ids

    def test_get_voices_filters_other_users_voices(self, client, mock_elevenlabs_client):
        """User cannot see other users' custom voices"""
        with patch('services.elevenlabs_service.ElevenLabs', return_value=mock_elevenlabs_client):
            response = client.get(
                "/api/voices",
                headers={"x-user-id": "other-user-456"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should show system voice + other user's voice (not test user's)
            voice_ids = [v["id"] for v in data["voices"]]
            assert "system-voice-1" in voice_ids
            assert "other-user-voice" in voice_ids
            assert "user-voice-1" not in voice_ids


class TestVoiceCreation:
    """Test voice creation endpoint and scoping"""

    def test_create_voice_without_user_id_returns_401(self, client):
        """Voice creation requires x-user-id header"""
        fake_file = io.BytesIO(b"fake_audio_data")

        response = client.post(
            "/api/voices/create",
            data={"name": "Test Voice", "description": "Test"},
            files={"files": ("test.mp3", fake_file, "audio/mpeg")}
        )

        assert response.status_code == 401
        assert "x-user-id" in response.json()["detail"].lower()

    def test_create_voice_with_user_id_succeeds(self, client, mock_elevenlabs_client):
        """Voice creation works with valid user_id"""
        with patch('services.elevenlabs_service.ElevenLabs', return_value=mock_elevenlabs_client):
            fake_file = io.BytesIO(b"fake_audio_data")

            response = client.post(
                "/api/voices/create",
                headers={"x-user-id": "test-user-123"},
                data={"name": "Test Voice", "description": "Test description"},
                files={"files": ("test.mp3", fake_file, "audio/mpeg")}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "success"
            assert data["voice"]["voice_id"] == "new-voice-id"
            assert data["voice"]["name"] == "Test Voice"

            # Verify ElevenLabs SDK was called with owner_id label
            mock_elevenlabs_client.voices.add.assert_called_once()
            call_kwargs = mock_elevenlabs_client.voices.add.call_args.kwargs
            assert call_kwargs["labels"]["owner_id"] == "test-user-123"
            assert call_kwargs["labels"]["source"] == "numen"

    def test_create_voice_with_multiple_files(self, client, mock_elevenlabs_client):
        """Voice creation accepts multiple audio files"""
        with patch('services.elevenlabs_service.ElevenLabs', return_value=mock_elevenlabs_client):
            file1 = io.BytesIO(b"fake_audio_1")
            file2 = io.BytesIO(b"fake_audio_2")

            response = client.post(
                "/api/voices/create",
                headers={"x-user-id": "test-user-123"},
                data={"name": "Multi-File Voice"},
                files=[
                    ("files", ("test1.mp3", file1, "audio/mpeg")),
                    ("files", ("test2.wav", file2, "audio/wav"))
                ]
            )

            assert response.status_code == 200
            assert response.json()["status"] == "success"


class TestVoicePreview:
    """Test voice preview endpoint"""

    def test_voice_preview_returns_audio(self, client, mock_elevenlabs_client):
        """Voice preview generates and returns MP3 audio"""
        with patch('services.elevenlabs_service.ElevenLabs', return_value=mock_elevenlabs_client):
            response = client.post(
                "/api/voices/preview",
                json={
                    "voice_id": "system-voice-1",
                    "text": "Test preview"
                }
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/mpeg"
            assert b"fake_audio_data" in response.content

    def test_voice_preview_without_service_returns_503(self, client):
        """Voice preview fails gracefully when service unavailable"""
        with patch('routers.voices.get_elevenlabs_service', return_value=None):
            response = client.post(
                "/api/voices/preview",
                json={
                    "voice_id": "test-voice",
                    "text": "Test"
                }
            )

            assert response.status_code == 503


class TestElevenLabsService:
    """Test ElevenLabsService directly"""

    @pytest.mark.asyncio
    async def test_get_available_voices_filters_correctly(self, mock_elevenlabs_client):
        """Service layer filters voices by owner_id"""
        with patch('services.elevenlabs_service.ElevenLabs', return_value=mock_elevenlabs_client):
            service = ElevenLabsService()

            # Test with user_id
            voices = service.get_available_voices(user_id="test-user-123")
            assert len(voices) == 2  # System + user's voice

            # Test without user_id
            voices_no_user = service.get_available_voices(user_id=None)
            assert len(voices_no_user) == 1  # Only system voice

    @pytest.mark.asyncio
    async def test_create_voice_sets_owner_label(self, mock_elevenlabs_client):
        """Voice creation tags voice with owner_id"""
        with patch('services.elevenlabs_service.ElevenLabs', return_value=mock_elevenlabs_client):
            service = ElevenLabsService()

            mock_file = Mock()
            mock_file.file = io.BytesIO(b"audio")

            result = await service.create_voice(
                name="Test Voice",
                files=[mock_file],
                user_id="test-user-456",
                description="Test"
            )

            assert result["voice_id"] == "new-voice-id"

            # Verify labels were set correctly
            call_kwargs = mock_elevenlabs_client.voices.add.call_args.kwargs
            assert call_kwargs["labels"]["owner_id"] == "test-user-456"


# Integration test requiring real ElevenLabs API (skip in CI)
@pytest.mark.skipif(
    True,  # Set to False to run with real API key
    reason="Requires real ElevenLabs API key and creates actual voices"
)
class TestRealAPIIntegration:
    """Real API tests (skip in CI, run manually)"""

    @pytest.mark.asyncio
    async def test_real_voice_creation_flow(self):
        """
        Manual test for real ElevenLabs API

        Requirements:
        - Valid ELEVENLABS_API_KEY in .env
        - Test audio file at tests/fixtures/sample.mp3
        """
        from config import settings

        service = ElevenLabsService()

        # Create test voice
        with open("tests/fixtures/sample.mp3", "rb") as f:
            mock_file = Mock()
            mock_file.file = f

            result = await service.create_voice(
                name="Pytest Test Voice",
                files=[mock_file],
                user_id="pytest-test-user",
                description="Automated test voice"
            )

            assert result["voice_id"]
            voice_id = result["voice_id"]

            # Verify voice appears in filtered list
            voices = service.get_available_voices(user_id="pytest-test-user")
            voice_ids = [v["id"] for v in voices]
            assert voice_id in voice_ids

            # Clean up: delete test voice
            # (ElevenLabs SDK doesn't have delete yet, manual cleanup required)
            print(f"Created test voice: {voice_id} - Please delete manually")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
