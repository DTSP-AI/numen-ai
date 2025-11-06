# HypnoAgent Clean Architecture

**Last Updated**: 2025-01-15
**Status**: Refactored - Contract-First, Graph-Orchestrated

---

## Core Principles

1. **Contract-First**: All agents driven by JSON contracts
2. **Graph-Orchestrated**: `graph.py` manages ALL workflow orchestration
3. **Memory-Managed**: Shared MemoryManager across all agents
4. **Sub-Agent Pattern**: GuideAgent orchestrates specialized sub-agents
5. **Stack-First**: Use Supabase, Mem0, LangGraph before custom solutions

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERACTION                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   INTAKE AGENT                               │
│  • Collects discovery data (goals, beliefs, outcomes)       │
│  • Uses own JSON contract for personality                   │
│  • Outputs → GuideContract JSON                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   GUIDE AGENT                                │
│  • Loads GuideContract (immutable base layer)               │
│  • Runs discovery conversation with user                    │
│  • Orchestrates sub-agents via graph.py                     │
│  • Uses shared MemoryManager                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                ┌──────┴──────┐
                ▼             ▼
        ┌──────────────┐  ┌──────────────┐
        │ AFFIRMATION  │  │ PROTOCOL     │
        │ SUB-AGENT    │  │ SUB-AGENT    │
        │              │  │              │
        │ Generates:   │  │ Generates:   │
        │ • Affirmations│  │ • Daily plan │
        │ • Scripts    │  │ • Checkpoints│
        │ • Mantras    │  │ • Schedule   │
        └──────┬───────┘  └──────┬───────┘
               │                 │
               └────────┬────────┘
                        ▼
            ┌─────────────────────┐
            │   MEMORY MANAGER    │
            │   (Mem0 + pgvector) │
            └─────────────────────┘
```

---

## File Structure

### Core Orchestration
```
backend/
  graph/
    graph.py                    # AgentState, workflow builder
                               # MANAGES ALL ORCHESTRATION

  memoryManager/
    memory_manager.py           # MemoryManager class
                               # Shared across all agents
```

### Agents (Contract-First)
```
backend/agents/
  intake_agent/
    intake_agent.py            # IntakeAgent class
                              # Loads own contract
                              # Outputs GuideContract

  guide_agent/
    guide_agent.py             # GuideAgent class
                              # Loads GuideContract
                              # Orchestrates sub-agents

    guide_sub_agents/
      affirmation_agent.py     # Creates affirmations
      manifestation_protocol_agent.py  # Creates protocols
      discovery_agent.py       # Cognitive discovery
      therapy_agent.py         # (Future)
```

### Service Layer
```
backend/services/
  agent_service.py             # AgentService class
                              # Invokes GuideAgent
                              # Does NOT build graphs

  trait_modulator.py           # Trait-based behavior
  trigger_logic.py             # Cognitive triggers
  contract_validator.py        # Contract validation
```

---

## How It Works

### 1. IntakeAgent Creates GuideContract

**Input**: User discovery data
**Process**:
- Loads its own AgentContract for personality
- Collects: goals, limiting beliefs, desired outcomes, preferences
- Uses LLM to generate optimal traits
- Outputs complete GuideContract JSON

**Output**: GuideContract stored in database

```python
# backend/agents/intake_agent/intake_agent.py
class IntakeAgent:
    def __init__(self, contract: AgentContract, memory: MemoryManager):
        self.contract = contract  # IntakeAgent's own personality
        self.memory = memory
        self.graph = self._build_graph()  # Uses graph.py

    async def process_message(self, message: str) -> GuideContract:
        # Runs discovery conversation
        # Returns GuideContract JSON
```

### 2. GuideAgent Orchestrates Everything

**Input**: GuideContract + User interaction
**Process**:
- Loads immutable GuideContract from database
- Runs discovery conversation (via graph.py)
- Orchestrates sub-agents (Affirmation, Protocol)
- All sub-agents share MemoryManager

**Output**: Complete asset package (affirmations, protocols, audio)

```python
# backend/agents/guide_agent/guide_agent.py
class GuideAgent:
    def __init__(self, contract: AgentContract, memory: MemoryManager):
        self.contract = contract  # GuideContract
        self.memory = memory      # Shared memory

        # Build workflow using graph.py
        self.graph = build_agent_workflow(
            retrieve_context_fn=self._load_guide_context,
            build_prompt_fn=self._perform_discovery,
            invoke_llm_fn=self._generate_assets,
            post_process_fn=self._synthesize_audio,
            check_cognitive_triggers_fn=self._embed_and_store
        )

    async def _generate_assets(self, state):
        # Initialize sub-agents
        affirmation_agent = AffirmationAgent(self.contract, self.memory)
        protocol_agent = ManifestationProtocolAgent()

        # Generate assets
        affirmations = await affirmation_agent.generate(...)
        protocol = await protocol_agent.generate(...)

        return {"affirmations": affirmations, "protocol": protocol}
```

### 3. graph.py Manages Orchestration

**Purpose**: Single source of truth for workflow structure

```python
# backend/graph/graph.py
class AgentState(TypedDict):
    """Unified state for ALL agents"""
    agent_id: str
    tenant_id: str
    user_id: str
    thread_id: str
    input_text: str
    agent_contract: Dict[str, Any]
    memory_context: MemoryContext
    # ... all state fields

def build_agent_workflow(
    retrieve_context_fn,
    build_prompt_fn,
    invoke_llm_fn,
    post_process_fn,
    check_cognitive_triggers_fn
) -> StateGraph:
    """Build LangGraph workflow with custom node functions"""
    workflow = StateGraph(AgentState)

    # Add nodes (provided by agent)
    workflow.add_node("retrieve_context", retrieve_context_fn)
    workflow.add_node("build_prompt", build_prompt_fn)
    workflow.add_node("invoke_llm", invoke_llm_fn)
    workflow.add_node("post_process", post_process_fn)
    workflow.add_node("check_cognitive_triggers", check_cognitive_triggers_fn)

    # Define flow (managed by graph.py)
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "build_prompt")
    workflow.add_edge("build_prompt", "invoke_llm")
    workflow.add_edge("invoke_llm", "post_process")
    workflow.add_edge("post_process", "check_cognitive_triggers")
    workflow.add_edge("check_cognitive_triggers", END)

    return workflow.compile()
```

### 4. AgentService Invokes GuideAgent

**Purpose**: Service layer between API and agents

```python
# backend/services/agent_service.py
class AgentService:
    async def process_interaction(
        self, agent_id, tenant_id, user_id, user_input, thread_id
    ):
        # 1. Load agent contract
        agent = await self.get_agent(agent_id, tenant_id)
        contract = AgentContract(**agent["contract"])

        # 2. Get memory manager
        memory_manager = await self._get_memory_manager(agent_id, tenant_id, contract)

        # 3. Create GuideAgent with contract + memory
        guide_agent = GuideAgent(contract=contract, memory=memory_manager)

        # 4. GuideAgent orchestrates everything via graph.py
        result = await guide_agent.graph.ainvoke({
            "agent_id": agent_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "thread_id": thread_id,
            "input_text": user_input,
            "guide_contract": contract.model_dump()
        })

        return result
```

---

## Sub-Agent Pattern

All sub-agents follow the same pattern:

```python
class AffirmationAgent:
    """Sub-agent for creating affirmations"""

    def __init__(self, contract: AgentContract, memory: MemoryManager):
        self.contract = contract  # GuideContract (shared)
        self.memory = memory      # MemoryManager (shared)
        # No graph - sub-agents don't orchestrate, they execute

    async def generate_daily_content(self, user_id, discovery_id):
        # Use contract traits to shape affirmations
        # Use memory to retrieve context
        # Return affirmations, scripts, mantras
```

**Key Points**:
- Sub-agents receive GuideContract (shared personality)
- Sub-agents receive MemoryManager (shared context)
- Sub-agents do NOT build graphs (they're invoked by GuideAgent)
- Sub-agents create specific assets (affirmations, protocols, etc.)

---

## Contract-First Approach

Every agent is driven by its JSON contract:

```json
{
  "id": "uuid",
  "name": "Marcus Aurelius Guide",
  "type": "voice",
  "identity": {
    "short_description": "Stoic guide for resilience",
    "character_role": "Stoic Philosopher",
    "mission": "Help you build unshakeable inner strength",
    "interaction_style": "Calm, wise, grounded"
  },
  "traits": {
    "empathy": 85,
    "confidence": 95,
    "creativity": 70,
    "formality": 60
  },
  "configuration": {
    "llm_model": "gpt-4",
    "temperature": 0.7,
    "memory_enabled": true
  },
  "voice": {
    "provider": "elevenlabs",
    "voice_id": "..."
  }
}
```

**How Contracts Are Used**:
1. **IntakeAgent** has its own contract (defines its personality during discovery)
2. **IntakeAgent** creates GuideContract (based on user discovery)
3. **GuideAgent** loads GuideContract (immutable base layer)
4. **Sub-agents** receive GuideContract (shared personality)

---

## Memory Manager Pattern

Single MemoryManager instance shared across agent + sub-agents:

```python
# Created once per agent interaction
memory_manager = MemoryManager(
    tenant_id=tenant_id,
    agent_id=agent_id,
    agent_traits=contract.traits.model_dump()
)

# Shared with GuideAgent
guide_agent = GuideAgent(contract=contract, memory=memory_manager)

# Shared with sub-agents (inside GuideAgent)
affirmation_agent = AffirmationAgent(contract=contract, memory=self.memory)
```

**Benefits**:
- Context shared across all agents
- Semantic memory via Mem0
- Vector search via pgvector
- Coherent conversation history

---

## What Was Removed

### ❌ `langgraph_agent.py` - DELETED
**Why**: Named after stack, not function. Redundant node implementations.

**Before**:
```python
from agents.langgraph_agent import build_agent_graph
graph = build_agent_graph(memory_manager, contract)
```

**After**:
```python
from agents.guide_agent.guide_agent import GuideAgent
guide_agent = GuideAgent(contract=contract, memory=memory_manager)
result = await guide_agent.graph.ainvoke(state)
```

---

## Key Design Decisions

### 1. Why graph.py manages orchestration
- **Single source of truth** for workflow structure
- Agents provide node functions (what to do)
- graph.py provides flow structure (when to do it)
- Easier to debug (all edges defined in one place)

### 2. Why GuideAgent orchestrates sub-agents
- **Hierarchical organization** - clear responsibilities
- GuideAgent knows the full workflow
- Sub-agents focus on specific tasks
- Shared contract + memory = coherent behavior

### 3. Why contract-first
- **Immutable base layer** - predictable behavior
- Agents can be versioned and rolled back
- Easy to A/B test different personalities
- Clear separation of configuration vs. code

### 4. Why shared MemoryManager
- **Context consistency** across all sub-agents
- Single source of truth for conversation history
- Efficient (one Mem0 instance per agent interaction)
- Enables semantic search across all assets

---

## Testing the Architecture

### Unit Tests
```python
# Test individual agents with mock contracts
def test_intake_agent_generates_guide_contract():
    contract = IntakeAgentContract(...)
    memory = MockMemoryManager()
    agent = IntakeAgent(contract, memory)

    result = await agent.process_message("I want confidence")
    assert result.affirmation_agent_contract is not None

# Test sub-agents with shared memory
def test_affirmation_agent_uses_shared_memory():
    guide_contract = GuideContract(...)
    memory = MemoryManager(...)
    agent = AffirmationAgent(guide_contract, memory)

    affirmations = await agent.generate_daily_content(...)
    assert len(affirmations) > 0
```

### Integration Tests
```python
# Test complete flow: Intake → Guide → Assets
async def test_complete_flow():
    # 1. Intake creates GuideContract
    intake = IntakeAgent(...)
    guide_contract = await intake.complete_discovery(...)

    # 2. Guide creates assets
    guide = GuideAgent(contract=guide_contract, memory=...)
    result = await guide.run_complete_flow(...)

    # 3. Verify assets created
    assert result["affirmations"]
    assert result["manifestation_protocol"]
    assert result["audio_assets"]
```

---

## Architecture Benefits

✅ **Clear Separation of Concerns**
- graph.py = orchestration
- GuideAgent = coordination
- Sub-agents = execution

✅ **Contract-Driven Behavior**
- All agents use JSON contracts
- Easy to version and test
- Predictable personalities

✅ **Memory Coherence**
- Shared MemoryManager
- Context across all sub-agents
- Semantic search works globally

✅ **Stack-First**
- Uses LangGraph for workflows
- Uses Mem0 for memory
- Uses pgvector for embeddings
- No custom orchestration needed

✅ **Testable**
- Mock contracts easily
- Test sub-agents in isolation
- Integration tests prove flow

---

## Next Steps

1. ✅ Remove `langgraph_agent.py` - DONE
2. ✅ Refactor `agent_service.py` to use GuideAgent - DONE
3. ⏳ Add comprehensive tests for each agent
4. ⏳ Document sub-agent contracts
5. ⏳ Add observability (log workflow transitions)

---

## Quick Reference

**Create an agent interaction**:
```python
# Service layer
service = AgentService()
result = await service.process_interaction(
    agent_id="uuid",
    tenant_id="uuid",
    user_id="uuid",
    user_input="Help me build confidence",
    thread_id="uuid"
)
```

**Behind the scenes**:
```
AgentService
  → Loads GuideContract from database
  → Creates MemoryManager
  → Creates GuideAgent(contract, memory)
  → GuideAgent.graph.ainvoke(state)
    → graph.py orchestrates nodes
    → GuideAgent._generate_assets()
      → Creates AffirmationAgent(contract, memory)
      → Creates ProtocolAgent()
      → Returns assets
  → Stores results in database
```

---

**Architecture Status**: ✅ Clean, Contract-First, Graph-Orchestrated
