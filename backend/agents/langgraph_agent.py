"""
LangGraph Agent - Production Agent Orchestration

Implements the standard agent interaction pattern with:
- Memory-aware context retrieval
- Trait-based behavioral modulation
- Structured response generation
- State management
"""

from typing import Dict, Any, TypedDict, Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import logging

from services.memory_manager import MemoryManager, MemoryContext
from services.trait_modulator import TraitModulator
from models.agent import AgentContract

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    Agent state for LangGraph workflow

    Tracks conversation context, agent config, and processing status
    """
    # Input
    agent_id: str
    tenant_id: str
    user_id: str
    thread_id: str
    input_text: str

    # Agent configuration
    agent_contract: Dict[str, Any]
    system_prompt: str

    # Memory context
    memory_context: MemoryContext
    retrieved_memories: list[Dict[str, Any]]
    recent_messages: list[Dict[str, Any]]

    # Processing
    llm_response: str
    response_text: str
    workflow_status: str

    # Metadata
    traits: Dict[str, int]
    configuration: Dict[str, Any]


class LangGraphAgent:
    """
    Production LangGraph agent with memory and trait modulation

    Architecture:
    1. Retrieve memory context (via Mem0)
    2. Build prompt with trait directives
    3. Invoke LLM
    4. Post-process response
    5. Update memory (via Mem0)
    """

    def __init__(self, memory_manager: MemoryManager, contract: AgentContract):
        """
        Initialize agent with memory manager and contract

        Args:
            memory_manager: Unified memory manager instance
            contract: Agent JSON contract
        """
        self.memory_manager = memory_manager
        self.contract = contract
        self.trait_modulator = TraitModulator()

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=contract.configuration.llm_model,
            temperature=contract.configuration.temperature,
            max_tokens=contract.configuration.max_tokens
        )

        # Build graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("build_prompt", self._build_prompt)
        workflow.add_node("invoke_llm", self._invoke_llm)
        workflow.add_node("post_process", self._post_process)

        # Define edges
        workflow.set_entry_point("retrieve_context")
        workflow.add_edge("retrieve_context", "build_prompt")
        workflow.add_edge("build_prompt", "invoke_llm")
        workflow.add_edge("invoke_llm", "post_process")
        workflow.add_edge("post_process", END)

        return workflow.compile()

    async def _retrieve_context(self, state: AgentState) -> Dict[str, Any]:
        """Node 1: Retrieve memory context for current interaction"""
        try:
            # Get memory context from memory manager
            memory_context = await self.memory_manager.get_agent_context(
                user_input=state["input_text"],
                session_id=state["thread_id"],
                user_id=state["user_id"]
            )

            logger.info(f"Retrieved {len(memory_context.retrieved_memories)} memories with confidence {memory_context.confidence_score:.2f}")

            return {
                "memory_context": memory_context,
                "retrieved_memories": memory_context.retrieved_memories,
                "recent_messages": memory_context.recent_messages,
                "workflow_status": "context_retrieved"
            }

        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return {
                "retrieved_memories": [],
                "recent_messages": [],
                "workflow_status": "context_retrieval_failed"
            }

    async def _build_prompt(self, state: AgentState) -> Dict[str, Any]:
        """Node 2: Build LLM prompt with system prompt, memory context, and user input"""
        try:
            # Get system prompt (already has trait directives)
            system_prompt = state["system_prompt"]

            # Build context section from retrieved memories
            context_section = self._format_memory_context(
                state["retrieved_memories"],
                state["recent_messages"]
            )

            # Combine into full prompt
            messages = [
                SystemMessage(content=system_prompt),
                SystemMessage(content=f"## RELEVANT CONTEXT FROM MEMORY:\n{context_section}"),
            ]

            # Add recent conversation history
            for msg in state["recent_messages"][-5:]:  # Last 5 messages
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg.get("content", "")))

            # Add current user input
            messages.append(HumanMessage(content=state["input_text"]))

            return {
                "workflow_status": "prompt_built",
                "_messages": messages  # Store for next node
            }

        except Exception as e:
            logger.error(f"Prompt building failed: {e}")
            return {"workflow_status": "prompt_build_failed"}

    def _format_memory_context(
        self,
        retrieved_memories: list[Dict[str, Any]],
        recent_messages: list[Dict[str, Any]]
    ) -> str:
        """Format memory context for LLM prompt"""
        sections = []

        if retrieved_memories:
            sections.append("**Relevant Past Memories:**")
            for i, memory in enumerate(retrieved_memories[:5], 1):
                content = memory.get("content", "")
                sections.append(f"{i}. {content}")

        if recent_messages:
            sections.append("\n**Recent Conversation:**")
            for msg in recent_messages[-3:]:
                role = msg.get("role", "").upper()
                content = msg.get("content", "")
                sections.append(f"{role}: {content}")

        return "\n".join(sections) if sections else "No prior context available."

    async def _invoke_llm(self, state: AgentState) -> Dict[str, Any]:
        """Node 3: Invoke LLM with constructed prompt"""
        try:
            messages = state.get("_messages", [])

            # Invoke LLM
            response = await self.llm.ainvoke(messages)
            llm_response = response.content

            logger.info(f"LLM response generated ({len(llm_response)} chars)")

            return {
                "llm_response": llm_response,
                "response_text": llm_response,  # Will be post-processed
                "workflow_status": "llm_invoked"
            }

        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return {
                "llm_response": "",
                "response_text": f"I apologize, but I'm having trouble generating a response right now. Please try again.",
                "workflow_status": "llm_invocation_failed"
            }

    async def _post_process(self, state: AgentState) -> Dict[str, Any]:
        """Node 4: Post-process LLM response"""
        try:
            response_text = state["llm_response"]

            # Optional: Apply any post-processing filters
            # - Remove markdown artifacts
            # - Ensure appropriate length
            # - Apply safety filters

            # For now, pass through
            final_response = response_text

            logger.info("Response post-processed successfully")

            return {
                "response_text": final_response,
                "workflow_status": "completed"
            }

        except Exception as e:
            logger.error(f"Post-processing failed: {e}")
            return {
                "response_text": state.get("llm_response", "Response processing error"),
                "workflow_status": "post_processing_failed"
            }

    async def ainvoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke the agent workflow

        Args:
            initial_state: Initial state with user input and config

        Returns:
            Final state with response_text and metadata
        """
        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            return final_state

        except Exception as e:
            logger.error(f"Agent workflow failed: {e}")
            return {
                "response_text": "I encountered an error processing your request. Please try again.",
                "workflow_status": "workflow_failed",
                "error": str(e)
            }


def build_agent_graph(
    memory_manager: MemoryManager,
    contract: AgentContract
) -> LangGraphAgent:
    """
    Factory function to build LangGraph agent

    Args:
        memory_manager: Mem0-based memory manager instance
        contract: Agent contract

    Returns:
        Compiled LangGraph agent ready for invocation
    """
    return LangGraphAgent(memory_manager, contract)
