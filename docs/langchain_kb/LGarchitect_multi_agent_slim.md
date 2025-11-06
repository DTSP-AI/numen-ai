### LGarchitect Multi-Agent

#### Hierarchical Tool Swarm Orchestration via LangGraph

**Overview:**
- Design and execute hierarchical swarm systems using LangGraph and LangChain.
- Build modular, multi-agent workflows with a top-level supervisor, mid-level subgraph supervisors, and specialized worker agents.

**Components:**
1. **Top-Level Supervisor:** Routes user requests between distinct subgraphs (e.g., Research Team, Document Team).
2. **Mid-Level Subgraph Supervisors:** Delegate tasks among internal worker nodes using structured LLM outputs.
3. **Specialized Worker Agents:** Execute specific roles using tools like web scraping, Tavily search, document editing, and Python REPL.

**Core Requirements:**
- Use StateGraph abstraction with custom State schemas for shared memory across nodes.
- Explicit state transitions back to the relevant supervisor after task completion.
- Support dynamic branching (goto) and recursive streaming (graph.stream()).
- Ensure safe, modular, and scoped tool execution.
- Compose agents as nested LangGraph graphs for hierarchical delegation.
- Persist memory using LangGraph-compatible state objects and support recursion.

**System Stack:**
- langchain==0.3.23
- langgraph==0.3.31
- OpenAI, PGVector, SQLAlchemy, Streamlit, Python REPL.

**Behavioral Expectation:**
- Each node acts as a self-contained reasoning unit:
  - Accepts shared state.
  - Executes task using its defined toolset.
  - Returns updated state.
  - Reports back to its supervisor.

**Final Output:**
- A functioning multi-agent LangGraph application capable of executing nested workflows, routing decisions via LLM-based supervisors, and dynamically resolving tool calls within a structured message-passing graph.

**Example Notebook:**
- **Research Team:** Uses search engine and web scraping tools.
- **Document Writing Team:** Uses file-access tools for document creation and editing.

**Utilities:**
- Create worker agents and subgraph supervisors to simplify graph composition.
- Use LangGraph's prebuilt `create_react_agent` for agent node simplification.

**Graph Construction:**
- Define nodes and edges for control flow.
- Use conditional edges for dynamic routing.
- Set entry points and compile graphs for execution.

**Execution:**
- Stream tasks through the graph with specified recursion limits.
- Monitor and adjust based on task complexity and worker availability.

This structured approach enables efficient orchestration of complex, multi-agent workflows, leveraging the power of LLMs and LangGraph's hierarchical capabilities.