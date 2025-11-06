"""
LangGraph Workflow Definition - Single Source of Truth

This module defines the agent conversation graph used across all agents.
Each agent uses this same workflow with different configurations (traits, prompts, etc.)

Graph Flow:
1. retrieve_context - Get memory context from Mem0
2. build_prompt - Construct LLM prompt with system prompt + memory
3. invoke_llm - Call LLM with constructed prompt
4. post_process - Clean up and format response
5. check_cognitive_triggers - Check reflex triggers and inject interventions
"""

from typing import Dict, Any, Callable, TypedDict
from langgraph.graph import StateGraph, END
import logging

from memoryManager.memory_manager import MemoryContext

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

    # Cognitive assessment (optional)
    cognitive_triggers: list[str]  # Intervention prompts from reflex engine
    trigger_fired: bool

    # Metadata
    traits: Dict[str, int]
    configuration: Dict[str, Any]


def build_agent_workflow(
    retrieve_context_fn: Callable,
    build_prompt_fn: Callable,
    invoke_llm_fn: Callable,
    post_process_fn: Callable,
    check_cognitive_triggers_fn: Callable
) -> StateGraph:
    """
    Build the standard agent workflow graph.

    This function creates the LangGraph workflow that all agents use.
    Each agent provides its own implementation of the node functions,
    but the graph structure remains the same.

    Args:
        retrieve_context_fn: Function to retrieve memory context
        build_prompt_fn: Function to build LLM prompt
        invoke_llm_fn: Function to invoke LLM
        post_process_fn: Function to post-process response
        check_cognitive_triggers_fn: Function to check cognitive triggers

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(AgentState)

    # Define nodes
    workflow.add_node("retrieve_context", retrieve_context_fn)
    workflow.add_node("build_prompt", build_prompt_fn)
    workflow.add_node("invoke_llm", invoke_llm_fn)
    workflow.add_node("post_process", post_process_fn)
    workflow.add_node("check_cognitive_triggers", check_cognitive_triggers_fn)

    # Define edges (linear flow)
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "build_prompt")
    workflow.add_edge("build_prompt", "invoke_llm")
    workflow.add_edge("invoke_llm", "post_process")
    workflow.add_edge("post_process", "check_cognitive_triggers")
    workflow.add_edge("check_cognitive_triggers", END)

    return workflow.compile()


def build_simple_graph(node_functions: Dict[str, Callable]) -> StateGraph:
    """
    Simplified builder that accepts a dictionary of node functions.

    Args:
        node_functions: Dictionary mapping node names to functions:
            - "retrieve_context"
            - "build_prompt"
            - "invoke_llm"
            - "post_process"
            - "check_cognitive_triggers"

    Returns:
        Compiled LangGraph workflow
    """
    return build_agent_workflow(
        retrieve_context_fn=node_functions["retrieve_context"],
        build_prompt_fn=node_functions["build_prompt"],
        invoke_llm_fn=node_functions["invoke_llm"],
        post_process_fn=node_functions["post_process"],
        check_cognitive_triggers_fn=node_functions["check_cognitive_triggers"]
    )
