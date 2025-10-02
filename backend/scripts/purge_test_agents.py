"""
Purge all test agents except Marcus Aurelius and Deepak Chopra agents
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_pg_pool, init_db, close_db


async def purge_test_agents():
    """Delete all agents except Marcus and Deepak"""
    print("\n" + "="*60)
    print("PURGING TEST AGENTS (Keeping Marcus & Deepak)")
    print("="*60)

    await init_db()
    pool = get_pg_pool()  # This is synchronous, not async

    async with pool.acquire() as conn:
        # First, show what we have
        agents = await conn.fetch("""
            SELECT id, name, created_at
            FROM agents
            ORDER BY created_at DESC
        """)

        print(f"\nFound {len(agents)} total agents:")
        for agent in agents:
            print(f"   - {agent['name']} (ID: {agent['id']})")

        # First, delete related data for agents we're removing
        agent_ids_to_delete = """
            SELECT id FROM agents
            WHERE name NOT LIKE '%Marcus%'
            AND name NOT LIKE '%Deepak%'
            AND name NOT LIKE '%Stoic%'
            AND name NOT LIKE '%Quantum%'
        """

        # Delete hypnosis_scripts
        scripts_result = await conn.execute(f"""
            DELETE FROM hypnosis_scripts
            WHERE agent_id IN ({agent_ids_to_delete})
        """)
        scripts_deleted = int(scripts_result.split()[-1])
        print(f"\nDeleted {scripts_deleted} hypnosis scripts")

        # Delete affirmations
        affirmations_result = await conn.execute(f"""
            DELETE FROM affirmations
            WHERE agent_id IN ({agent_ids_to_delete})
        """)
        affirmations_deleted = int(affirmations_result.split()[-1])
        print(f"Deleted {affirmations_deleted} affirmations")

        # Delete user_discovery references
        discovery_result = await conn.execute(f"""
            DELETE FROM user_discovery
            WHERE affirmation_agent_id IN ({agent_ids_to_delete})
        """)
        discovery_deleted = int(discovery_result.split()[-1])
        print(f"Deleted {discovery_deleted} user discovery records")

        # Delete memory embeddings
        mem_result = await conn.execute(f"""
            DELETE FROM memory_embeddings
            WHERE agent_id IN ({agent_ids_to_delete})
        """)
        mem_deleted = int(mem_result.split()[-1])
        print(f"Deleted {mem_deleted} memory embeddings")

        # Delete threads
        threads_result = await conn.execute(f"""
            DELETE FROM threads
            WHERE agent_id IN ({agent_ids_to_delete})
        """)
        threads_deleted = int(threads_result.split()[-1])
        print(f"Deleted {threads_deleted} threads")

        # Now delete the agents
        result = await conn.execute("""
            DELETE FROM agents
            WHERE name NOT LIKE '%Marcus%'
            AND name NOT LIKE '%Deepak%'
            AND name NOT LIKE '%Stoic%'
            AND name NOT LIKE '%Quantum%'
        """)

        deleted_count = int(result.split()[-1])

        print(f"\nDeleted {deleted_count} test agents")

        # Show remaining agents
        remaining = await conn.fetch("""
            SELECT id, name, created_at
            FROM agents
            ORDER BY created_at DESC
        """)

        print(f"\nRemaining agents ({len(remaining)}):")
        for agent in remaining:
            print(f"   - {agent['name']} (ID: {agent['id']})")

    await close_db()
    print("\n" + "="*60)
    print("CLEANUP COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(purge_test_agents())
