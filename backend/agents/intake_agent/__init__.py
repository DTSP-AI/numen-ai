"""
Intake Agent Module

Single unified intake agent for user discovery and Guide contract generation.

Usage:
    from agents.intake_agent import IntakeAgent

    # Basic intake
    intake = IntakeAgent(contract, memory)
    state = await intake.process_message(session_id, user_id, tenant_id, message)
    agent_id = await intake.save_discovery_and_create_agent(state)
"""

from agents.intake_agent.intake_agent import (
    IntakeAgent,
    IntakeAgentState,
    DiscoveryData
)

__all__ = [
    "IntakeAgent",
    "IntakeAgentState",
    "DiscoveryData"
]
