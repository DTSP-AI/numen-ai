"""
Quick Mem0 Integration Test
Tests the Mem0-based MemoryManager implementation
"""

import asyncio
import uuid
from services.memory_manager import MemoryManager, initialize_agent_memory


async def test_mem0_integration():
    """Test Mem0 integration end-to-end"""

    print("\n" + "="*60)
    print("MEM0 INTEGRATION TEST")
    print("="*60)

    # Test data
    tenant_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    print(f"\nTest IDs:")
    print(f"  Tenant: {tenant_id}")
    print(f"  Agent:  {agent_id}")
    print(f"  Thread: {thread_id}")
    print(f"  User:   {user_id}")

    try:
        # Test 1: Initialize agent memory
        print("\n[1/5] Testing agent memory initialization...")
        agent_contract = {
            "name": "Test Confidence Coach",
            "identity": {
                "short_description": "A test agent for Mem0 integration"
            },
            "traits": {
                "empathy": 90,
                "confidence": 85
            }
        }

        memory_manager = await initialize_agent_memory(
            agent_id=agent_id,
            tenant_id=tenant_id,
            agent_contract=agent_contract
        )
        print("   OK Agent memory initialized")

        # Test 2: Store user interaction
        print("\n[2/5] Testing interaction storage...")
        await memory_manager.store_interaction(
            role="user",
            content="I want to build confidence in public speaking",
            session_id=thread_id,
            user_id=user_id,
            metadata={"intent": "goal_setting"}
        )
        print("   OK User interaction stored")

        # Test 3: Store agent response
        print("\n[3/5] Testing agent response storage...")
        await memory_manager.store_interaction(
            role="assistant",
            content="Let's work on building your confidence step by step. Public speaking is a skill that improves with practice.",
            session_id=thread_id,
            user_id=user_id
        )
        print("   OK Agent response stored")

        # Test 4: Retrieve context with semantic search
        print("\n[4/5] Testing context retrieval...")
        context = await memory_manager.get_agent_context(
            user_input="How do I overcome stage fright?",
            session_id=thread_id,
            user_id=user_id,
            k=5
        )
        print(f"   OK Retrieved {len(context.retrieved_memories)} memories")
        print(f"   OK Confidence score: {context.confidence_score:.2f}")

        if context.retrieved_memories:
            print(f"\n   Top memory:")
            print(f"     Content: {context.retrieved_memories[0].get('content', '')[:80]}...")
            print(f"     Score: {context.retrieved_memories[0].get('score', 0):.2f}")

        # Test 5: Process full conversation turn
        print("\n[5/5] Testing conversation turn processing...")
        await memory_manager.process_interaction(
            user_input="What techniques can I use?",
            agent_response="Start with deep breathing exercises and visualization techniques. Practice in front of a mirror first.",
            session_id=thread_id,
            user_id=user_id
        )
        print("   OK Conversation turn processed")

        # Summary
        print("\n" + "="*60)
        print("ALL TESTS PASSED")
        print("="*60)
        print("\nMem0 integration is working correctly!")
        print(f"Namespace used: {memory_manager.namespace}")
        print(f"Thread namespace: {memory_manager.thread_namespace(thread_id)}")
        print("\nYou can now:")
        print("  1. Start the backend: uvicorn main:app --reload")
        print("  2. Create agents via API")
        print("  3. Interact with agents (using Mem0 memory)")
        print("\n")

        return True

    except Exception as e:
        print(f"\nTEST FAILED: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check MEM0_API_KEY in .env")
        print("  2. Verify internet connection")
        print("  3. Check Mem0 service status: https://status.mem0.ai")
        print("  4. Review error message above")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mem0_integration())
    exit(0 if success else 1)
