"""
Test script for Manifestation Protocol Agent

This demonstrates how to generate a complete, structured manifestation protocol.
"""

import asyncio
import json
from agents.manifestation_protocol_agent import create_manifestation_protocol


async def main():
    print("=" * 80)
    print("MANIFESTATION PROTOCOL GENERATOR")
    print("=" * 80)
    print()

    # Example 1: Career goal with moderate commitment
    print("Example 1: Career Manifestation")
    print("-" * 80)

    protocol1 = await create_manifestation_protocol(
        user_id="test-user-001",
        goal="Land my dream job as a Senior Software Engineer at a top tech company with $200k+ salary",
        timeframe="90_days",
        commitment_level="intensive"
    )

    print(f"Goal: {protocol1['meta']['goal']}")
    print(f"Timeframe: {protocol1['meta']['timeframe']}")
    print(f"Commitment: {protocol1['meta']['commitment_level']}")
    print()
    print(f"Daily Practices: {len(protocol1['daily_practices'])} practices")
    print(f"Affirmations: {len(protocol1['affirmations']['all'])} total")
    print(f"Visualizations: {len(protocol1['visualizations'])} scripts")
    print(f"Success Metrics: {len(protocol1['success_metrics'])} metrics")
    print(f"Obstacles Identified: {len(protocol1['obstacles_and_solutions'])}")
    print(f"Checkpoints: {len(protocol1['checkpoints'])}")
    print()

    # Show sample affirmations
    print("Sample Affirmations:")
    for i, aff in enumerate(protocol1['affirmations']['all'][:5], 1):
        print(f"  {i}. {aff}")
    print()

    # Show daily practices
    print("Daily Practices:")
    for practice in protocol1['daily_practices'][:3]:
        print(f"  • {practice['name']} ({practice['duration']})")
        print(f"    {practice['purpose']}")
    print()

    # Show first checkpoint
    if protocol1['checkpoints']:
        checkpoint = protocol1['checkpoints'][0]
        print(f"First Checkpoint: {checkpoint['title']} (Day {checkpoint['day']})")
        print(f"  Reflection Questions:")
        for q in checkpoint.get('reflection_questions', [])[:2]:
            print(f"    - {q}")
    print()

    # Example 2: Relationship goal with light commitment
    print("\n" + "=" * 80)
    print("Example 2: Relationship Manifestation")
    print("-" * 80)

    protocol2 = await create_manifestation_protocol(
        user_id="test-user-002",
        goal="Attract a loving, supportive romantic partner who shares my values and life vision",
        timeframe="30_days",
        commitment_level="moderate"
    )

    print(f"Goal: {protocol2['meta']['goal']}")
    print(f"Affirmations created: {len(protocol2['affirmations']['all'])}")
    print()

    # Show Monday's affirmations from rotation
    if 'Monday' in protocol2['affirmations']['daily_rotation']:
        print("Monday's Affirmation Set:")
        for aff in protocol2['affirmations']['daily_rotation']['Monday'][:3]:
            print(f"  • {aff}")
    print()

    # Show obstacles and solutions
    print("Identified Obstacles & Solutions:")
    for obstacle in protocol2['obstacles_and_solutions'][:2]:
        print(f"  Obstacle: {obstacle['obstacle']}")
        print(f"  Solution: {obstacle['solution']}")
        print(f"  Affirmation: \"{obstacle['affirmation']}\"")
        print()

    # Quick start guide
    print("Quick Start Guide:")
    for item in protocol2['quick_start_guide']['day_1_checklist']:
        print(f"  □ {item}")
    print()

    # Save protocols to JSON files for inspection
    with open('protocol_career_example.json', 'w') as f:
        json.dump(protocol1, f, indent=2)
        print("Saved full career protocol to: protocol_career_example.json")

    with open('protocol_relationship_example.json', 'w') as f:
        json.dump(protocol2, f, indent=2)
        print("Saved full relationship protocol to: protocol_relationship_example.json")

    print()
    print("=" * 80)
    print("Protocol generation complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
