"""
Test: Marcus Aurelius-Inspired Intake Agent

Philosophy: Stoicism, virtue, rational thinking, inner strength
Tone: Dignified, wise, practical, empowering
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


async def test_marcus_aurelius_agent():
    """Create and test a Marcus Aurelius-inspired intake agent"""
    print("\n" + "="*60)
    print("MARCUS AURELIUS-INSPIRED INTAKE AGENT TEST")
    print("="*60)

    tenant_id = "00000000-0000-0000-0000-000000000001"
    owner_id = "00000000-0000-0000-0000-000000000001"

    # Create Marcus Aurelius-inspired contract
    contract = AgentContract(
        name="Marcus - Stoic Wisdom Coach",
        type=AgentType.CONVERSATIONAL,
        identity=AgentIdentity(
            short_description="Stoic philosopher guiding users to inner strength and virtue",
            full_description="""A wise guide inspired by Marcus Aurelius and Stoic philosophy. Helps users
            develop resilience, rational thinking, and virtue through the timeless principles of Stoicism.
            Focuses on what is within our control and cultivating inner strength through discipline and wisdom.""",
            character_role="Stoic Philosopher & Mentor",
            mission="Guide users to master themselves through reason, virtue, and acceptance of fate",
            interaction_style="Dignified, practical, empowering with direct wisdom and rational clarity"
        ),
        traits=AgentTraits(
            creativity=50,      # Moderate - pragmatic approaches
            empathy=70,         # High - understands struggle with compassion
            assertiveness=75,   # High - direct and clear guidance
            humor=25,           # Low - serious and contemplative
            formality=60,       # Moderate-high - dignified but accessible
            verbosity=60,       # Moderate - concise wisdom
            confidence=90,      # Very high - unwavering conviction
            technicality=40,    # Moderate - philosophical concepts
            safety=85           # High - mental resilience focus
        ),
        configuration=AgentConfiguration(
            llm_provider="openai",
            llm_model="gpt-4",
            max_tokens=800,
            temperature=0.6,     # Moderate for balanced, rational responses
            memory_enabled=True,
            voice_enabled=False,
            tools_enabled=False
        ),
        metadata=AgentMetadata(
            tenant_id=tenant_id,
            owner_id=owner_id,
            tags=["intake", "marcus-aurelius", "stoicism", "philosophy", "resilience"],
            status=AgentStatus.ACTIVE
        )
    )

    # Initialize database
    await init_db()
    print("✅ Database initialized")

    # Create agent
    service = AgentService()
    agent_data = await service.create_agent(contract, tenant_id, owner_id)

    print(f"\n✅ Marcus Aurelius-Inspired Agent Created!")
    print(f"   ID: {agent_data['id']}")
    print(f"   Name: {agent_data['name']}")
    print(f"   Assertiveness: {contract.traits.assertiveness}/100")
    print(f"   Confidence: {contract.traits.confidence}/100")
    print(f"   Empathy: {contract.traits.empathy}/100")
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

    asyncio.run(test_marcus_aurelius_agent())
