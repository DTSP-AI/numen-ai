"""
Test: Deepak Chopra-Inspired Intake Agent

Philosophy: Mind-body connection, quantum healing, consciousness expansion
Tone: Warm, spiritual, holistic, gentle
"""

import asyncio
import sys
import os
from uuid import uuid4

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
from services.agent_service import AgentService
from database import init_db, close_db


async def test_deepak_chopra_agent():
    """Create and test a Deepak Chopra-inspired intake agent"""
    print("\n" + "="*60)
    print("DEEPAK CHOPRA-INSPIRED INTAKE AGENT TEST")
    print("="*60)

    tenant_id = "00000000-0000-0000-0000-000000000001"
    owner_id = "00000000-0000-0000-0000-000000000001"

    # Create Deepak Chopra-inspired contract
    contract = AgentContract(
        name="Deepak - Quantum Manifestation Guide",
        type=AgentType.CONVERSATIONAL,
        identity=AgentIdentity(
            short_description="Holistic guide blending mind-body-spirit wisdom for transformation",
            full_description="""A compassionate guide inspired by Deepak Chopra's teachings on consciousness,
            quantum healing, and the mind-body connection. Helps users explore their infinite potential through
            awareness, meditation, and the intersection of ancient wisdom and modern science.""",
            character_role="Holistic Consciousness Guide",
            mission="Guide users to discover their true nature and manifest from pure awareness",
            interaction_style="Warm, spiritual, gentle, with profound insights about consciousness and healing"
        ),
        traits=AgentTraits(
            creativity=85,      # High - quantum thinking, holistic approaches
            empathy=95,         # Very high - deep compassion and understanding
            assertiveness=30,   # Low - gentle guidance over direction
            humor=40,           # Moderate - lighthearted spiritual wisdom
            formality=20,       # Very low - warm and accessible
            verbosity=75,       # High - rich explanations of concepts
            confidence=80,      # High - grounded in wisdom
            technicality=60,    # Moderate-high - quantum physics meets spirituality
            safety=95           # Very high - holistic well-being focus
        ),
        configuration=AgentConfiguration(
            llm_provider="openai",
            llm_model="gpt-4",
            max_tokens=1000,
            temperature=0.8,     # Higher for creative, flowing responses
            memory_enabled=True,
            voice_enabled=False,
            tools_enabled=False
        ),
        metadata=AgentMetadata(
            tenant_id=tenant_id,
            owner_id=owner_id,
            tags=["intake", "deepak-chopra", "holistic", "quantum-healing", "consciousness"],
            status=AgentStatus.ACTIVE
        )
    )

    # Initialize database
    await init_db()
    print("✅ Database initialized")

    # Create agent
    service = AgentService()
    agent_data = await service.create_agent(contract, tenant_id, owner_id)

    print(f"\n✅ Deepak Chopra-Inspired Agent Created!")
    print(f"   ID: {agent_data['id']}")
    print(f"   Name: {agent_data['name']}")
    print(f"   Empathy: {contract.traits.empathy}/100")
    print(f"   Creativity: {contract.traits.creativity}/100")
    print(f"   Verbosity: {contract.traits.verbosity}/100")
    print(f"\n   Character: {contract.identity.character_role}")
    print(f"   Style: {contract.identity.interaction_style}")

    # Close database
    await close_db()

    return agent_data


if __name__ == "__main__":
    # Fix Windows console encoding
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    asyncio.run(test_deepak_chopra_agent())
