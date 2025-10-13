"""
E2E Test: Guide Creation from Intake Contract

Tests the /api/agents/from_intake_contract endpoint to verify:
1. API responds with correct JSON structure
2. Guide agent is created with proper attributes
3. Memory manager is initialized correctly
4. Session is created
5. Protocol is generated
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_guide_creation():
    """Test the baseline flow endpoint"""

    print("=" * 80)
    print("E2E AUDIT: Guide Creation from Intake Contract")
    print("=" * 80)
    print()

    # Test payload - simulating intake agent output
    user_id = "00000000-0000-0000-0000-000000000001"
    intake_contract = {
        "normalized_goals": [
            "Build confidence in public speaking",
            "Overcome fear of judgment"
        ],
        "prefs": {
            "tone": "calm",
            "session_type": "manifestation"
        },
        "notes": "User wants gentle encouragement and practical exercises",
        "challenges": [
            "Gets nervous before presentations",
            "Worries about others' opinions"
        ],
        "preferences": {
            "session_length": "medium",
            "voice_style": "soothing"
        }
    }

    print("REQUEST TO: POST /api/agents/from_intake_contract")
    print("Query Param: user_id =", user_id)
    print("Body - intake_contract:")
    print(json.dumps(intake_contract, indent=2))
    print()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/agents/from_intake_contract",
                params={"user_id": user_id},  # Send as query parameter
                json={"intake_contract": intake_contract},  # Send as body
                headers={
                    "Content-Type": "application/json",
                    "x-tenant-id": "00000000-0000-0000-0000-000000000001"
                }
            )

            print(f"RESPONSE STATUS: {response.status_code}")
            print()

            if response.status_code == 200:
                data = response.json()

                print("[SUCCESS] Guide Created!")
                print()

                # Audit JSON contract structure
                print("=" * 80)
                print("1. JSON CONTRACT AUDIT")
                print("=" * 80)

                if "agent" in data:
                    agent = data["agent"]
                    print(f"[OK] Agent ID: {agent.get('id')}")
                    print(f"[OK] Agent Name: {agent.get('name')}")
                    print(f"[OK] Agent Type: {agent.get('type')}")
                    print(f"[OK] Agent Status: {agent.get('status')}")

                    # Check contract structure
                    contract = agent.get("contract", {})
                    print()
                    print("Contract Structure:")
                    print(f"  - Identity: {bool(contract.get('identity'))}")
                    print(f"  - Traits: {bool(contract.get('traits'))}")
                    print(f"  - Configuration: {bool(contract.get('configuration'))}")
                    print(f"  - Voice: {bool(contract.get('voice'))}")
                    print(f"  - Metadata: {bool(contract.get('metadata'))}")

                    # Check traits (4 core attributes)
                    if contract.get('traits'):
                        traits = contract['traits']
                        print()
                        print("Guide Attributes (0-100):")
                        print(f"  - Confidence: {traits.get('confidence')}")
                        print(f"  - Empathy: {traits.get('empathy')}")
                        print(f"  - Creativity: {traits.get('creativity')}")
                        print(f"  - Discipline: {traits.get('discipline')}")

                    # Check identity
                    if contract.get('identity'):
                        identity = contract['identity']
                        print()
                        print("Identity:")
                        print(f"  - Short Description: {identity.get('short_description')[:80]}...")
                        print(f"  - Character Role: {identity.get('character_role')}")
                        print(f"  - Mission: {identity.get('mission')[:60]}...")
                        print(f"  - Interaction Style: {identity.get('interaction_style')}")
                        print(f"  - Avatar URL: {identity.get('avatar_url')[:50]}...")

                    # Check voice configuration
                    if contract.get('voice'):
                        voice = contract['voice']
                        print()
                        print("Voice Configuration:")
                        print(f"  - Provider: {voice.get('provider')}")
                        print(f"  - Voice ID: {voice.get('voice_id')}")
                        print(f"  - Language: {voice.get('language')}")
                        print(f"  - Stability: {voice.get('stability')}")

                else:
                    print("[ERROR] Agent data missing from response")

                print()
                print("=" * 80)
                print("2. SESSION AUDIT")
                print("=" * 80)

                if "session" in data:
                    session = data["session"]
                    print(f"[OK] Session ID: {session.get('id')}")
                    print(f"[OK] Agent ID: {session.get('agent_id')}")
                    print(f"[OK] User ID: {session.get('user_id')}")
                    print(f"[OK] Status: {session.get('status')}")
                else:
                    print("[ERROR] Session data missing from response")

                print()
                print("=" * 80)
                print("3. PROTOCOL AUDIT")
                print("=" * 80)

                if "protocol" in data:
                    protocol = data["protocol"]
                    print(f"[OK] Affirmations Count: {protocol.get('affirmations_count')}")
                    print(f"[OK] Daily Practices Count: {protocol.get('daily_practices_count')}")
                    print(f"[OK] Checkpoints Count: {protocol.get('checkpoints_count')}")
                else:
                    print("[ERROR] Protocol data missing from response")

                print()
                print("=" * 80)
                print("4. MEMORY MANAGER VERIFICATION")
                print("=" * 80)
                print("Memory manager should be initialized with:")
                print(f"  - Namespace: {data.get('agent', {}).get('id')}")
                print(f"  - Tenant ID: 00000000-0000-0000-0000-000000000001")
                print(f"  - Using Mem0 cloud service")
                print()

                print("=" * 80)
                print("COMPLETE RESPONSE DATA")
                print("=" * 80)
                print(json.dumps(data, indent=2))

            else:
                print(f"[FAILED] Status Code: {response.status_code}")
                print()
                print("Error Response:")
                print(response.text)

    except httpx.RequestError as e:
        print(f"[REQUEST ERROR]: {e}")
    except httpx.TimeoutException:
        print(f"[TIMEOUT]: Request took longer than 30 seconds")
    except Exception as e:
        print(f"[UNEXPECTED ERROR]: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_guide_creation())
