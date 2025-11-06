"""
Guide Agent Module

Complete guide-driven discovery and asset generation system.

Flow:
1. IntakeAgent creates immutable GuideContract (JSON)
2. GuideAgent loads contract and performs cognitive discovery
3. GuideAgent generates custom assets and strategy based on discovery

Components:
- GuideAgent - Main orchestrator (Phase 2)
- DiscoveryAgent - Cognitive discovery sub-agent (GAS, CAM, belief graphs)
- AffirmationAgent - Affirmation/hypnosis generation sub-agent
- ManifestationProtocolAgent - Daily schedule/protocol builder sub-agent
- TherapyAgent - Session planning sub-agent

Usage:
    from agents.guide_agent import GuideAgent, create_and_run_guide

    guide = GuideAgent(contract, memory)
    result = await guide.run_complete_flow(user_id, tenant_id, thread_id, goals)
"""

from agents.guide_agent.guide_agent import GuideAgent, create_and_run_guide
from agents.guide_agent.guide_sub_agents.discovery_agent import run_discovery
from agents.guide_agent.guide_sub_agents.affirmation_agent import AffirmationAgent
from agents.guide_agent.guide_sub_agents.manifestation_protocol_agent import ManifestationProtocolAgent

__all__ = [
    "GuideAgent",
    "create_and_run_guide",
    "run_discovery",
    "AffirmationAgent",
    "ManifestationProtocolAgent"
]
