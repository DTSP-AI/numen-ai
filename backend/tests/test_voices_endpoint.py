"""
Test script for ElevenLabs voices endpoint
"""
import sys
import os

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.elevenlabs_service import ElevenLabsService

def test_get_voices():
    """Test fetching voices from ElevenLabs SDK"""
    print("\n" + "="*60)
    print("Testing ElevenLabs Voice Fetching")
    print("="*60)

    try:
        # Initialize service
        print("\n1. Initializing ElevenLabsService...")
        service = ElevenLabsService()
        print("   ✅ Service initialized")

        # Fetch voices
        print("\n2. Fetching voices from ElevenLabs API...")
        voices = service.get_available_voices()
        print(f"   ✅ Retrieved {len(voices)} voices")

        # Display sample voices
        print("\n3. Sample voices:")
        for voice in voices[:5]:
            print(f"\n   Voice: {voice['name']}")
            print(f"   ID: {voice['id']}")
            print(f"   Category: {voice.get('category', 'N/A')}")
            print(f"   Description: {voice.get('description', 'N/A')[:80]}")
            print(f"   Labels: {voice.get('labels', {})}")

        print("\n" + "="*60)
        print("✅ TEST PASSED - Voice fetching works!")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_get_voices()
    sys.exit(0 if success else 1)
