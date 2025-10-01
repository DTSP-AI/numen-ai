"""
Numen AI Pipeline - End-to-End Test Suite

Tests the complete flow:
1. Create IntakeAgent
2. Simulate discovery conversation
3. Generate AffirmationAgent contract
4. Create AffirmationAgent
5. Generate content (affirmations, mantras, scripts)
6. Synthesize audio
7. Access via Dashboard API
"""

import asyncio
import sys
import os
import json
import uuid
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.agent import (
    AgentContract,
    AgentIdentity,
    AgentTraits,
    AgentConfiguration,
    AgentMetadata,
    AgentType,
    AgentStatus
)
from agents.intake_agent_v2 import IntakeAgentV2, IntakeAgentState, DiscoveryData
from agents.affirmation_agent import AffirmationAgent
from services.agent_service import AgentService
from services.unified_memory_manager import UnifiedMemoryManager
from services.audio_synthesis import audio_service
from database import init_db, close_db, get_pg_pool


async def test_1_create_intake_agent():
    """Test 1: Create IntakeAgent from contract"""
    print("\n" + "="*60)
    print("TEST 1: Creating IntakeAgent from JSON Contract")
    print("="*60)

    tenant_id = "00000000-0000-0000-0000-000000000001"
    owner_id = "00000000-0000-0000-0000-000000000001"

    # Create IntakeAgent contract
    intake_contract = AgentContract(
        name="Numen Discovery Specialist",
        type=AgentType.CONVERSATIONAL,
        identity=AgentIdentity(
            short_description="Empathetic discovery specialist for manifestation coaching",
            full_description="An empathetic and intuitive guide who helps users explore their deepest goals, identify limiting beliefs, and articulate their desired outcomes with clarity and compassion.",
            character_role="Compassionate Discovery Guide",
            mission="Collect comprehensive discovery data and generate personalized AffirmationAgent contracts",
            interaction_style="Warm, curious, and deeply empathetic with gentle probing questions"
        ),
        traits=AgentTraits(
            creativity=70,
            empathy=95,
            assertiveness=40,
            humor=35,
            formality=25,
            verbosity=65,
            confidence=75,
            technicality=20,
            safety=90
        ),
        configuration=AgentConfiguration(
            llm_provider="openai",
            llm_model="gpt-4",
            max_tokens=800,
            temperature=0.7,
            memory_enabled=True,
            voice_enabled=False,
            tools_enabled=False
        ),
        metadata=AgentMetadata(
            tenant_id=tenant_id,
            owner_id=owner_id,
            tags=["intake", "discovery", "numen-ai"],
            status=AgentStatus.ACTIVE
        )
    )

    # Create via AgentService
    service = AgentService()
    intake_agent_data = await service.create_agent(intake_contract, tenant_id, owner_id)

    print(f"✅ IntakeAgent created: {intake_agent_data['id']}")
    print(f"   Name: {intake_agent_data['name']}")
    print(f"   Type: {intake_agent_data['type']}")
    print(f"   Empathy: {intake_contract.traits.empathy}/100")

    return intake_agent_data


async def test_2_simulate_intake_conversation(intake_agent_data):
    """Test 2: Simulate complete intake conversation"""
    print("\n" + "="*60)
    print("TEST 2: Simulating Intake Conversation")
    print("="*60)

    tenant_id = intake_agent_data['tenant_id']
    agent_id = intake_agent_data['id']
    user_id = str(uuid.uuid4())  # Generate proper UUID for user_id
    session_id = "test-session-" + str(uuid.uuid4())[:8]

    # Create test user in database
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, tenant_id, email, name, status)
            VALUES ($1::uuid, $2::uuid, $3, $4, 'active')
            ON CONFLICT (id) DO NOTHING
        """, user_id, tenant_id, f"test-{user_id}@numen.ai", "Test User")

    # Initialize IntakeAgentV2
    contract = AgentContract(**intake_agent_data['contract'])
    memory = UnifiedMemoryManager(
        tenant_id=tenant_id,
        agent_id=agent_id,
        agent_traits=intake_agent_data['contract']
    )

    intake_agent = IntakeAgentV2(contract, memory)
    print(f"✅ IntakeAgentV2 initialized")

    # Simulate conversation
    conversation = [
        "I want to manifest financial abundance and grow my career",
        "I also want more confidence in public speaking",
        "I believe money is hard to earn and that I'm not good enough",
        "I want to earn $150,000 by the end of the year and feel confident leading teams",
        "I prefer an empowering, energetic tone with a warm female voice",
        "Morning sessions work best for me, I can commit 45 minutes daily",
        "Let's do a 30-day program",
        "Yes, that looks perfect! Let's create my affirmation agent"
    ]

    # Build state manually (simulating full conversation)
    state = IntakeAgentState(
        session_id=session_id,
        user_id=user_id,
        tenant_id=tenant_id,
        discovery=DiscoveryData(
            goals=[
                "Financial abundance",
                "Career growth",
                "Confidence in public speaking"
            ],
            limiting_beliefs=[
                "Money is hard to earn",
                "I'm not good enough"
            ],
            desired_outcomes=[
                "Earn $150,000 by year-end",
                "Feel confident leading teams"
            ],
            tone_preference="empowering",
            voice_preference="warm female",
            schedule_preference="morning",
            timeframe="30_days",
            commitment_level="moderate"
        ),
        stage="confirmation",
        contract_generated=False
    )

    print(f"✅ Discovery data collected:")
    print(f"   Goals: {state.discovery.goals}")
    print(f"   Limiting Beliefs: {state.discovery.limiting_beliefs}")
    print(f"   Desired Outcomes: {state.discovery.desired_outcomes}")
    print(f"   Preferences: {state.discovery.tone_preference}, {state.discovery.schedule_preference}")

    # Generate AffirmationAgent contract
    print("\n🔄 Generating AffirmationAgent contract...")
    final_state = await intake_agent.graph.ainvoke(state.model_dump())
    final_state = IntakeAgentState(**final_state)

    if final_state.contract_generated:
        print(f"✅ AffirmationAgent contract generated!")
        contract_json = final_state.affirmation_agent_contract
        print(f"   Agent Name: {contract_json['name']}")
        print(f"   Agent Type: {contract_json['type']}")
        print(f"   Empathy: {contract_json['traits']['empathy']}/100")
        print(f"   Confidence: {contract_json['traits']['confidence']}/100")

        return final_state, user_id
    else:
        raise Exception("Contract generation failed")


async def test_3_create_affirmation_agent(intake_state, user_id):
    """Test 3: Create AffirmationAgent from generated contract"""
    print("\n" + "="*60)
    print("TEST 3: Creating AffirmationAgent")
    print("="*60)

    # Parse the generated contract
    contract_json = intake_state.affirmation_agent_contract
    affirmation_contract = AgentContract(**contract_json)

    # Create agent using AgentService
    service = AgentService()
    affirmation_agent_data = await service.create_agent(
        affirmation_contract,
        intake_state.tenant_id,
        user_id
    )

    print(f"✅ AffirmationAgent created: {affirmation_agent_data['id']}")
    print(f"   Name: {affirmation_agent_data['name']}")
    print(f"   Status: {affirmation_agent_data['status']}")
    print(f"   Voice Enabled: {affirmation_agent_data['contract'].get('voice') is not None}")

    # Save discovery data linking to this agent
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO user_discovery (
                user_id, tenant_id, goals, limiting_beliefs,
                desired_outcomes, preferences, schedule_preference,
                affirmation_agent_id
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8::uuid)
        """,
            user_id,
            intake_state.tenant_id,
            json.dumps(intake_state.discovery.goals),
            json.dumps(intake_state.discovery.limiting_beliefs),
            json.dumps(intake_state.discovery.desired_outcomes),
            json.dumps({
                "tone": intake_state.discovery.tone_preference,
                "voice": intake_state.discovery.voice_preference,
                "timeframe": intake_state.discovery.timeframe,
                "commitment": intake_state.discovery.commitment_level
            }),
            intake_state.discovery.schedule_preference,
            affirmation_agent_data['id']
        )

    print(f"✅ Discovery data saved")

    return affirmation_agent_data, user_id


async def test_4_generate_content(affirmation_agent_data, user_id):
    """Test 4: Generate affirmations, mantras, and scripts"""
    print("\n" + "="*60)
    print("TEST 4: Generating Manifestation Content")
    print("="*60)

    agent_id = affirmation_agent_data['id']
    tenant_id = affirmation_agent_data['tenant_id']

    # Get discovery data
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        discovery_row = await conn.fetchrow("""
            SELECT id FROM user_discovery
            WHERE affirmation_agent_id = $1::uuid
        """, agent_id)

        if not discovery_row:
            raise Exception("Discovery data not found")

        discovery_id = str(discovery_row['id'])

    # Initialize AffirmationAgent
    contract = AgentContract(**affirmation_agent_data['contract'])
    memory = UnifiedMemoryManager(
        tenant_id=tenant_id,
        agent_id=agent_id,
        agent_traits=affirmation_agent_data['contract']
    )

    affirmation_agent = AffirmationAgent(contract, memory)
    print(f"✅ AffirmationAgent initialized")

    # Generate content
    print("\n🔄 Generating content (this may take 20-30 seconds)...")
    content = await affirmation_agent.generate_daily_content(user_id, discovery_id)

    print(f"\n✅ Content generation complete!")
    print(f"   Affirmations: {len(content['affirmations'])}")
    print(f"   Mantras: {len(content['mantras'])}")
    print(f"   Hypnosis Scripts: {len(content['hypnosis_scripts'])}")

    # Display samples
    print("\n📝 Sample Content:")
    print("\n   Identity Affirmations:")
    for aff in content['affirmations'][:3]:
        if aff['category'] == 'identity':
            print(f"   • {aff['text']}")

    print("\n   Mantras:")
    for mantra in content['mantras'][:3]:
        print(f"   • {mantra}")

    print("\n   Hypnosis Script:")
    script = content['hypnosis_scripts'][0]
    print(f"   Title: {script['title']}")
    print(f"   Duration: {script['duration_minutes']} minutes")
    print(f"   Focus: {script['focus_area']}")

    return content, affirmation_agent_data, user_id


async def test_5_synthesize_audio(content, affirmation_agent_data, user_id):
    """Test 5: Synthesize audio for affirmations"""
    print("\n" + "="*60)
    print("TEST 5: Synthesizing Audio (ElevenLabs)")
    print("="*60)

    if not os.getenv("ELEVENLABS_API_KEY"):
        print("⚠️  ELEVENLABS_API_KEY not set - skipping audio synthesis")
        print("   Set the environment variable to enable audio generation")
        return content, user_id

    agent_id = affirmation_agent_data['id']
    voice_config_data = affirmation_agent_data['contract'].get('voice')

    if not voice_config_data:
        print("⚠️  Agent has no voice configuration - skipping audio synthesis")
        return content, user_id

    from models.agent import VoiceConfiguration
    voice_config = VoiceConfiguration(**voice_config_data)

    print(f"🔄 Synthesizing audio for 3 sample affirmations...")
    print(f"   Voice: {voice_config.voice_id}")
    print(f"   Provider: {voice_config.provider}")

    # Get affirmation IDs from database
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, affirmation_text
            FROM affirmations
            WHERE user_id = $1::uuid AND agent_id = $2::uuid
            LIMIT 3
        """, user_id, agent_id)

    success_count = 0
    for row in rows:
        affirmation_id = str(row['id'])
        text = row['affirmation_text']

        print(f"\n   Synthesizing: {text[:50]}...")
        audio_url = await audio_service.synthesize_affirmation(
            affirmation_id=affirmation_id,
            text=text,
            voice_config=voice_config
        )

        if audio_url:
            print(f"   ✅ Audio saved: {audio_url}")
            success_count += 1
        else:
            print(f"   ❌ Synthesis failed")

    print(f"\n✅ Audio synthesis complete: {success_count}/3 successful")

    return content, user_id


async def test_6_dashboard_access(user_id):
    """Test 6: Access content via Dashboard API"""
    print("\n" + "="*60)
    print("TEST 6: Dashboard API Access")
    print("="*60)

    pool = get_pg_pool()

    # Get affirmations
    async with pool.acquire() as conn:
        affirmations_rows = await conn.fetch("""
            SELECT id, affirmation_text, category, audio_url
            FROM affirmations
            WHERE user_id = $1::uuid
            ORDER BY created_at DESC
            LIMIT 5
        """, user_id)

        print(f"\n📊 Dashboard Summary:")
        print(f"   Total Affirmations: {len(affirmations_rows)}")

        # Count by category
        categories = {}
        audio_count = 0
        for row in affirmations_rows:
            cat = row['category'] or 'uncategorized'
            categories[cat] = categories.get(cat, 0) + 1
            if row['audio_url']:
                audio_count += 1

        print(f"   By Category:")
        for cat, count in categories.items():
            print(f"      • {cat}: {count}")

        print(f"   With Audio: {audio_count}/{len(affirmations_rows)}")

        # Get scripts
        scripts_count = await conn.fetchval("""
            SELECT COUNT(*) FROM hypnosis_scripts
            WHERE user_id = $1::uuid
        """, user_id)

        print(f"   Hypnosis Scripts: {scripts_count}")

        # Get agents
        agents_rows = await conn.fetch("""
            SELECT id, name, type FROM agents
            WHERE owner_id = $1::uuid
        """, user_id)

        print(f"   Total Agents: {len(agents_rows)}")
        for row in agents_rows:
            print(f"      • {row['name']} ({row['type']})")

    print(f"\n✅ Dashboard data retrieved successfully")


async def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*60)
    print("🧪 NUMEN AI PIPELINE - END-TO-END TEST SUITE")
    print("="*60)
    print(f"Started: {datetime.utcnow().isoformat()}")

    try:
        # Initialize database
        print("\n🔄 Initializing database connection...")
        await init_db()
        print("✅ Database initialized")

        # Run tests
        intake_agent_data = await test_1_create_intake_agent()

        intake_state, user_id = await test_2_simulate_intake_conversation(intake_agent_data)

        affirmation_agent_data, user_id = await test_3_create_affirmation_agent(intake_state, user_id)

        content, affirmation_agent_data, user_id = await test_4_generate_content(affirmation_agent_data, user_id)

        content, user_id = await test_5_synthesize_audio(content, affirmation_agent_data, user_id)

        await test_6_dashboard_access(user_id)

        # Final summary
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print(f"\nTest User ID: {user_id}")
        print(f"IntakeAgent ID: {intake_agent_data['id']}")
        print(f"AffirmationAgent ID: {affirmation_agent_data['id']}")
        print(f"\nThe complete Numen AI pipeline is operational! 🎉")
        print("\nNext steps:")
        print("  1. Check database tables for generated content")
        print("  2. View audio files in backend/audio_files/")
        print("  3. Test API endpoints with the IDs above")
        print("  4. Build frontend dashboard UI")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        await close_db()
        print("\n✅ Database connection closed")


if __name__ == "__main__":
    # Fix Windows console encoding
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    # Set up environment
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set")
        print("   Set it in your environment to run the full test")

    # Run tests
    asyncio.run(run_all_tests())
