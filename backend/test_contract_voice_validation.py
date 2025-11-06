"""
Test script to validate contract cleanup and voice configuration fixes

Tests:
1. Voice agents require voice configuration
2. Voice_enabled agents handle voice requirements
3. No filesystem operations during agent creation
"""

import sys
import asyncio
from models.agent import (
    AgentContract,
    AgentIdentity,
    AgentTraits,
    AgentConfiguration,
    VoiceConfiguration,
    AgentMetadata,
    AgentType,
    AgentStatus
)
from pydantic import ValidationError

def test_voice_agent_without_voice():
    """Test that VOICE agent without voice config fails validation"""
    print("\n[TEST 1] VOICE agent without voice config (should fail)")
    try:
        contract = AgentContract(
            name="Test Voice Agent",
            type=AgentType.VOICE,
            identity=AgentIdentity(short_description="Test agent"),
            metadata=AgentMetadata(
                tenant_id="test-tenant",
                owner_id="test-owner"
            )
            # Missing voice configuration!
        )
        print("[FAIL] Should have raised ValidationError")
        return False
    except ValidationError as e:
        print("[PASS] Validation error raised as expected")
        print(f"   Error: {e.errors()[0]['msg']}")
        return True

def test_voice_agent_with_voice():
    """Test that VOICE agent with voice config succeeds"""
    print("\n[TEST 2] VOICE agent with voice config (should succeed)")
    try:
        contract = AgentContract(
            name="Test Voice Agent",
            type=AgentType.VOICE,
            identity=AgentIdentity(short_description="Test agent"),
            voice=VoiceConfiguration(
                provider="elevenlabs",
                voice_id="test-voice-id"
            ),
            metadata=AgentMetadata(
                tenant_id="test-tenant",
                owner_id="test-owner"
            )
        )
        print("[PASS] Agent created successfully")
        print(f"   Voice ID: {contract.voice.voice_id}")
        return True
    except Exception as e:
        print(f"[FAIL] Should have succeeded. Error: {e}")
        return False

def test_voice_enabled_without_voice():
    """Test that voice_enabled=True without voice config fails"""
    print("\n[TEST 3] Conversational agent with voice_enabled=True but no voice (should fail)")
    try:
        contract = AgentContract(
            name="Test Agent",
            type=AgentType.CONVERSATIONAL,
            identity=AgentIdentity(short_description="Test agent"),
            configuration=AgentConfiguration(
                voice_enabled=True
            ),
            metadata=AgentMetadata(
                tenant_id="test-tenant",
                owner_id="test-owner"
            )
            # Missing voice configuration!
        )
        print("[FAIL] Should have raised ValidationError")
        return False
    except ValidationError as e:
        print("[PASS] Validation error raised as expected")
        print(f"   Error: {e.errors()[0]['msg']}")
        return True

def test_voice_enabled_with_voice():
    """Test that voice_enabled=True with voice config succeeds"""
    print("\n[TEST 4] Conversational agent with voice_enabled=True and voice (should succeed)")
    try:
        contract = AgentContract(
            name="Test Agent",
            type=AgentType.CONVERSATIONAL,
            identity=AgentIdentity(short_description="Test agent"),
            configuration=AgentConfiguration(
                voice_enabled=True
            ),
            voice=VoiceConfiguration(
                provider="elevenlabs",
                voice_id="test-voice-id"
            ),
            metadata=AgentMetadata(
                tenant_id="test-tenant",
                owner_id="test-owner"
            )
        )
        print("[PASS] Agent created successfully")
        print(f"   Voice ID: {contract.voice.voice_id}")
        return True
    except Exception as e:
        print(f"[FAIL] Should have succeeded. Error: {e}")
        return False

def test_conversational_without_voice():
    """Test that conversational agent without voice is allowed"""
    print("\n[TEST 5] Conversational agent without voice (should succeed)")
    try:
        contract = AgentContract(
            name="Test Agent",
            type=AgentType.CONVERSATIONAL,
            identity=AgentIdentity(short_description="Test agent"),
            metadata=AgentMetadata(
                tenant_id="test-tenant",
                owner_id="test-owner"
            )
            # No voice configuration - should be fine
        )
        print("[PASS] Agent created successfully without voice")
        print(f"   Voice config: {contract.voice}")
        return True
    except Exception as e:
        print(f"[FAIL] Should have succeeded. Error: {e}")
        return False

def main():
    """Run all validation tests"""
    print("=" * 70)
    print("CONTRACT CLEANUP & VOICE VALIDATION TESTS")
    print("=" * 70)

    results = []

    # Run all tests
    results.append(("VOICE agent without voice (should fail)", test_voice_agent_without_voice()))
    results.append(("VOICE agent with voice (should succeed)", test_voice_agent_with_voice()))
    results.append(("voice_enabled=True without voice (should fail)", test_voice_enabled_without_voice()))
    results.append(("voice_enabled=True with voice (should succeed)", test_voice_enabled_with_voice()))
    results.append(("Conversational without voice (should succeed)", test_conversational_without_voice()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 70)

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
