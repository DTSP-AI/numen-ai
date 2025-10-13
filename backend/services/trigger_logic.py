"""
Trigger Logic - Reflex Engine for Cognitive Assessment

Phase 1: Opt-in reflex system that monitors cognitive metrics and
automatically triggers reassessment conversations when thresholds are exceeded.

This implements the strategy document's reflex trigger patterns:
- Emotion conflict threshold (default: 0.7)
- Repeated failure threshold (default: 2 failures)
- Belief conflict threshold (default: 0.8)

Usage:
    Only active when agent.reflex_triggers_enabled = True
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from database import get_pg_pool
from models.cognitive_schema import CognitiveKernel

logger = logging.getLogger(__name__)


class ReflexEngine:
    """
    Opt-in reflex engine for cognitive assessment triggers

    Monitors cognitive metrics and triggers interventions when thresholds are exceeded.

    Phase 1: Optional, requires explicit enable
    Phase 2: Default-on with opt-out
    Phase 3: Always-on for cognitive-enabled agents
    """

    def __init__(self, cognitive_kernel: CognitiveKernel):
        """
        Initialize reflex engine with cognitive kernel configuration

        Args:
            cognitive_kernel: CognitiveKernel configuration with trigger thresholds
        """
        self.kernel = cognitive_kernel
        self.triggers_enabled = cognitive_kernel.reflex_triggers.enabled
        self.emotion_threshold = cognitive_kernel.reflex_triggers.emotion_threshold
        self.failure_threshold = cognitive_kernel.reflex_triggers.failure_threshold
        self.conflict_threshold = cognitive_kernel.reflex_triggers.conflict_threshold

        logger.info(
            f"ReflexEngine initialized: "
            f"enabled={self.triggers_enabled}, "
            f"emotion_threshold={self.emotion_threshold}, "
            f"failure_threshold={self.failure_threshold}"
        )

    async def check_triggers(
        self,
        user_id: str,
        agent_id: str,
        tenant_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Check all trigger conditions and return list of triggered interventions

        Args:
            user_id: User UUID
            agent_id: Agent UUID
            tenant_id: Tenant UUID
            context: Optional context data (current interaction, goal_id, etc.)

        Returns:
            List of trigger dicts: [{"type": "emotion_conflict", "action": "...", "data": {...}}]
        """
        if not self.triggers_enabled:
            return []

        triggers_fired = []

        # Check emotion conflict
        emotion_trigger = await self._check_emotion_conflict(user_id, agent_id, tenant_id)
        if emotion_trigger:
            triggers_fired.append(emotion_trigger)

        # Check repeated failures
        failure_trigger = await self._check_repeated_failures(user_id, agent_id, tenant_id, context)
        if failure_trigger:
            triggers_fired.append(failure_trigger)

        # Check belief conflict
        conflict_trigger = await self._check_belief_conflict(user_id, agent_id, tenant_id)
        if conflict_trigger:
            triggers_fired.append(conflict_trigger)

        if triggers_fired:
            logger.info(f"🔔 {len(triggers_fired)} triggers fired for user {user_id}")

        return triggers_fired

    async def _check_emotion_conflict(
        self,
        user_id: str,
        agent_id: str,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Check if emotion conflict score exceeds threshold"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                # Get most recent emotion_conflict metric
                row = await conn.fetchrow("""
                    SELECT metric_value, context_data, measured_at
                    FROM cognitive_metrics
                    WHERE user_id = $1::uuid
                        AND agent_id = $2::uuid
                        AND tenant_id = $3::uuid
                        AND metric_type = 'emotion_conflict'
                    ORDER BY measured_at DESC
                    LIMIT 1
                """, user_id, agent_id, tenant_id)

                if not row:
                    return None

                metric_value = row["metric_value"]

                if metric_value >= self.emotion_threshold:
                    logger.warning(
                        f"⚠️ Emotion conflict threshold exceeded: "
                        f"{metric_value:.2f} >= {self.emotion_threshold}"
                    )

                    return {
                        "type": "emotion_conflict",
                        "severity": "high" if metric_value >= 0.9 else "medium",
                        "metric_value": metric_value,
                        "threshold": self.emotion_threshold,
                        "action": "Initiate belief reassessment conversation",
                        "prompt_template": "I notice some tension in your belief system. Would you like to explore what might be causing this conflict?",
                        "context": row["context_data"],
                        "measured_at": row["measured_at"].isoformat()
                    }

        except Exception as e:
            logger.error(f"Failed to check emotion conflict trigger: {e}")

        return None

    async def _check_repeated_failures(
        self,
        user_id: str,
        agent_id: str,
        tenant_id: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Check if user has repeated failures on a goal"""
        pool = get_pg_pool()

        try:
            # Check goal attempts vs successes in last 7 days
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT
                        id,
                        goal_text,
                        attempt_count,
                        success_count,
                        last_attempt_date
                    FROM goal_assessments
                    WHERE user_id = $1::uuid
                        AND agent_id = $2::uuid
                        AND tenant_id = $3::uuid
                        AND attempt_count > 0
                        AND last_attempt_date > NOW() - INTERVAL '7 days'
                """, user_id, agent_id, tenant_id)

                for row in rows:
                    attempt_count = row["attempt_count"]
                    success_count = row["success_count"]
                    failure_count = attempt_count - success_count

                    if failure_count >= self.failure_threshold:
                        logger.warning(
                            f"⚠️ Repeated failure detected: "
                            f"{failure_count} failures for goal '{row['goal_text'][:50]}'"
                        )

                        return {
                            "type": "repeated_failure",
                            "severity": "high" if failure_count >= 5 else "medium",
                            "goal_id": str(row["id"]),
                            "goal_text": row["goal_text"],
                            "failure_count": failure_count,
                            "threshold": self.failure_threshold,
                            "action": "Suggest breaking goal into smaller steps",
                            "prompt_template": f"I see you've been working on '{row['goal_text'][:50]}...' Let's break this down into smaller, more achievable steps.",
                            "last_attempt": row["last_attempt_date"].isoformat()
                        }

        except Exception as e:
            logger.error(f"Failed to check repeated failures trigger: {e}")

        return None

    async def _check_belief_conflict(
        self,
        user_id: str,
        agent_id: str,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Check if belief graph conflict score exceeds threshold"""
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                # Get most recent belief graph
                row = await conn.fetchrow("""
                    SELECT
                        id,
                        conflict_score,
                        tension_nodes,
                        updated_at
                    FROM belief_graphs
                    WHERE user_id = $1::uuid
                        AND agent_id = $2::uuid
                        AND tenant_id = $3::uuid
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, user_id, agent_id, tenant_id)

                if not row:
                    return None

                conflict_score = row["conflict_score"]

                if conflict_score >= self.conflict_threshold:
                    logger.warning(
                        f"⚠️ Belief conflict threshold exceeded: "
                        f"{conflict_score:.2f} >= {self.conflict_threshold}"
                    )

                    return {
                        "type": "belief_conflict",
                        "severity": "high" if conflict_score >= 0.95 else "medium",
                        "graph_id": str(row["id"]),
                        "conflict_score": conflict_score,
                        "threshold": self.conflict_threshold,
                        "tension_nodes": row["tension_nodes"],
                        "action": "Facilitate belief reconciliation dialogue",
                        "prompt_template": "I sense some conflicting beliefs that might be creating internal tension. Would you like to explore these together?",
                        "updated_at": row["updated_at"].isoformat()
                    }

        except Exception as e:
            logger.error(f"Failed to check belief conflict trigger: {e}")

        return None

    async def log_trigger_event(
        self,
        user_id: str,
        agent_id: str,
        tenant_id: str,
        trigger: Dict[str, Any]
    ):
        """
        Log trigger event to database for tracking and analysis

        Args:
            user_id: User UUID
            agent_id: Agent UUID
            tenant_id: Tenant UUID
            trigger: Trigger dictionary from check_triggers
        """
        from services.memory_manager import store_cognitive_metric

        try:
            await store_cognitive_metric(
                user_id=user_id,
                tenant_id=tenant_id,
                agent_id=agent_id,
                metric_type=f"trigger_{trigger['type']}",
                metric_value=trigger.get("metric_value", trigger.get("conflict_score", 1.0)),
                context_data={
                    "trigger_type": trigger["type"],
                    "severity": trigger.get("severity"),
                    "action_taken": trigger.get("action"),
                    "trigger_data": trigger
                },
                threshold_value=trigger.get("threshold")
            )

            logger.info(f"✅ Trigger event logged: {trigger['type']}")

        except Exception as e:
            logger.error(f"Failed to log trigger event: {e}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def create_reflex_engine(agent_contract: Dict[str, Any]) -> Optional[ReflexEngine]:
    """
    Create ReflexEngine from agent contract if cognitive assessment is enabled

    Args:
        agent_contract: Agent contract dictionary

    Returns:
        ReflexEngine instance or None if not enabled
    """
    # Check if reflex triggers are enabled
    if not agent_contract.get("reflex_triggers_enabled", False):
        return None

    # Get cognitive kernel config
    kernel_config = agent_contract.get("cognitive_kernel_config")
    if not kernel_config:
        # Use default kernel
        from models.cognitive_schema import get_default_cognitive_kernel
        kernel = get_default_cognitive_kernel()
    else:
        from models.cognitive_schema import CognitiveKernel
        kernel = CognitiveKernel(**kernel_config)

    # Only create if triggers are enabled in kernel
    if not kernel.reflex_triggers.enabled:
        return None

    return ReflexEngine(kernel)


async def check_and_handle_triggers(
    user_id: str,
    agent_id: str,
    tenant_id: str,
    agent_contract: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Check triggers and return list of intervention prompts

    Args:
        user_id: User UUID
        agent_id: Agent UUID
        tenant_id: Tenant UUID
        agent_contract: Agent contract dict
        context: Optional context

    Returns:
        List of intervention prompt strings
    """
    engine = await create_reflex_engine(agent_contract)
    if not engine:
        return []

    triggers = await engine.check_triggers(user_id, agent_id, tenant_id, context)

    intervention_prompts = []
    for trigger in triggers:
        # Log the trigger
        await engine.log_trigger_event(user_id, agent_id, tenant_id, trigger)

        # Get intervention prompt
        prompt = trigger.get("prompt_template", "Let's pause and reflect on your progress.")
        intervention_prompts.append(prompt)

    return intervention_prompts
