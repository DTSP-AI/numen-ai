Here is a **comprehensive prompt chain** to fully execute the **NEXT ACTIONS** checklist. This prompt is designed for Claude or a self-healing dev agent with access to your repo, test harness, and LangGraph runtime.

---

## 🧠 **Prompt Chain: Phase 1 Finalization + Phase 2 Readiness (Cognitive Layer)**

**Agent Name:** `CognitiveSystemOps_Executor`
**Purpose:** Execute the remaining post-implementation tasks for the Guide Cognitive Kernel infrastructure: improve OS safety, create test coverage, seed default belief maps, wire reflex triggers into LangGraph, and begin CAM visualizer scaffolding.

---

### 🟩 STEP 1 — Fix Platform-Safe Migration Script

````prompt
You’re reviewing `run_cognitive_migration.py`. Update the script to use `os.path.join()` and `__file__` so that it works across platforms (Windows, macOS, Linux).

Add a fallback check: if migration fails due to `asyncpg`, catch the exception and log it clearly with remediation steps.

Ensure path resolution works regardless of where the script is called from.

Use:

```python
base_dir = os.path.dirname(os.path.abspath(__file__))
sql_file_path = os.path.join(base_dir, '004_cognitive_assessment_tables.sql')
````

````

---

### 🟨 STEP 2 — Generate Cognitive Memory & Intake Test Files

```prompt
Create two test files under `tests/`:

1. `test_memory_cognitive.py`:
   - Mocks the `MemoryManager`
   - Calls `store_goal_assessment`, `store_belief_graph`, and `store_cognitive_metric` with dummy data
   - Asserts the correct `Mem0` storage calls and DB logging (mock `get_pg_pool`)

2. `test_cognitive_intake.py`:
   - Instantiates `IntakeAgentCognitive`
   - Mocks a cognitive intake scenario:
     - 2 goals with GAS scale
     - 3 belief nodes and 2 belief edges
     - One emotion conflict scenario
   - Validates the belief graph and goal vector output

Use `pytest + asyncio` compatible style and mock out DB + memory dependencies.
````

---

### 🟨 STEP 3 — Add `belief_graph_template.json`

````prompt
Create a file: `backend/assets/belief_graph_template.json`

It should contain a default set of starter nodes and edges for belief mapping. Structure:

```json
{
  "graph_name": "Default Belief Map",
  "nodes": [
    {
      "id": "n1",
      "label": "I’m not good enough",
      "node_type": "limiting_belief",
      "emotional_valence": -0.7
    },
    {
      "id": "n2",
      "label": "Success requires struggle",
      "node_type": "core_belief",
      "emotional_valence": -0.2
    }
  ],
  "edges": [
    {
      "source": "n1",
      "target": "n2",
      "relationship": "supports"
    }
  ]
}
````

Modify `intake_agent_cognitive.py` to auto-load this as fallback if user doesn’t provide beliefs in intake.

````

---

### 🟥 STEP 4 — Wire Reflex Trigger into LangGraph Runtime

```prompt
Modify `langgraph_agent.py` to include a **post-node reflex trigger hook**.

Steps:
- After each node execution (agent step), inspect `AgentState.cognitive_metrics`
- Import and call `check_reflex_trigger(agent_state)` from `trigger_logic.py`
- If a threshold is breached:
  - Inject a message into `AgentState.messages`
  - Log the trigger action in trace

Example:
```python
from services.trigger_logic import check_reflex_trigger

updated_state = check_reflex_trigger(agent_state)
return updated_state
````

This enables *autonomous activation* of reassessment, encouragement, or belief intervention steps during runtime.

````

---

### 🟩 STEP 5 — CAM Visualizer Block (ReactFlow Preferred)

```prompt
Design a React component for the CAM (Cognitive-Affective Mapping) Visualizer using ReactFlow.

Component: `CAMVisualizer.tsx`

Features:
- Nodes = beliefs (color-coded by emotional valence)
- Edge type = `supports` / `conflicts`
- Tooltip on hover = belief strength, type, associated goal
- Optional toggle to view "Tension Nodes" (conflict_score > 0.7)

Inputs:
```ts
type CAMNode = {
  id: string;
  label: string;
  node_type: "limiting_belief" | "core_belief" | "neutral";
  emotional_valence: number;
};

type CAMEdge = {
  source: string;
  target: string;
  relationship: "supports" | "conflicts";
};

<CAMVisualizer nodes={CAMNode[]} edges={CAMEdge[]} />
````

Display embedded in Guide dashboard or chat inspector view.

```

---

## 📦 Final Output from Prompt Chain

Once Claude or an agent executes this prompt chain, the system will include:

- Cross-platform-safe cognitive migration script ✅
- Full test coverage for memory and cognitive intake ✅
- Default belief graph for new users ✅
- LangGraph reflex hook for runtime reassessments ✅
- UI-ready CAM Visualizer (modular, embeddable) ✅

--