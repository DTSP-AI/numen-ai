from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import TypedDict, List, Dict, Optional
import logging
import json

from config import settings

logger = logging.getLogger(__name__)


class ManifestationProtocolState(TypedDict):
    """State for Manifestation Protocol Agent"""
    user_id: str
    goal: str
    timeframe: str  # "7_days", "30_days", "90_days"
    commitment_level: str  # "light", "moderate", "intensive"
    protocol: Optional[Dict]
    daily_practices: List[Dict]
    affirmations: List[str]
    visualization_scripts: List[str]
    success_metrics: List[str]
    obstacles: List[Dict]
    accountability_checkpoints: List[Dict]


class ManifestationProtocolAgent:
    """
    Agent that creates structured, personalized manifestation protocols.

    Generates:
    - Daily practice schedule
    - Morning/evening routines
    - Affirmation sets
    - Visualization scripts
    - Progress tracking metrics
    - Obstacle identification & solutions
    - Accountability checkpoints
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build manifestation protocol workflow"""
        workflow = StateGraph(ManifestationProtocolState)

        # Protocol generation nodes
        workflow.add_node("analyze_goal", self._analyze_goal_node)
        workflow.add_node("design_daily_practices", self._design_daily_practices_node)
        workflow.add_node("create_affirmations", self._create_affirmations_node)
        workflow.add_node("generate_visualizations", self._generate_visualizations_node)
        workflow.add_node("define_metrics", self._define_metrics_node)
        workflow.add_node("identify_obstacles", self._identify_obstacles_node)
        workflow.add_node("set_checkpoints", self._set_checkpoints_node)
        workflow.add_node("compile_protocol", self._compile_protocol_node)

        # Build workflow
        workflow.set_entry_point("analyze_goal")
        workflow.add_edge("analyze_goal", "design_daily_practices")
        workflow.add_edge("design_daily_practices", "create_affirmations")
        workflow.add_edge("create_affirmations", "generate_visualizations")
        workflow.add_edge("generate_visualizations", "define_metrics")
        workflow.add_edge("define_metrics", "identify_obstacles")
        workflow.add_edge("identify_obstacles", "set_checkpoints")
        workflow.add_edge("set_checkpoints", "compile_protocol")
        workflow.add_edge("compile_protocol", END)

        return workflow.compile()

    def _analyze_goal_node(self, state: ManifestationProtocolState) -> ManifestationProtocolState:
        """Analyze the goal and break it down into components"""

        system_prompt = f"""You are an expert manifestation coach analyzing a user's goal.

Goal: {state['goal']}
Timeframe: {state['timeframe']}
Commitment Level: {state['commitment_level']}

Analyze this goal and identify:
1. Core desire (the emotional WHY)
2. Specific outcome (measurable result)
3. Identity shift required (who they need to become)
4. Key belief changes needed
5. Action domains (areas of life affected)

Return a JSON object with these keys."""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Analyze this goal deeply.")
        ])

        try:
            analysis = json.loads(response.content)
            state["protocol"] = {"analysis": analysis}
            logger.info(f"Goal analyzed for user {state['user_id']}")
        except:
            # Fallback if JSON parsing fails
            state["protocol"] = {"analysis": {"raw": response.content}}

        return state

    def _design_daily_practices_node(self, state: ManifestationProtocolState) -> ManifestationProtocolState:
        """Design daily manifestation practices"""

        commitment_hours = {
            "light": "15-30 minutes",
            "moderate": "30-60 minutes",
            "intensive": "1-2 hours"
        }

        system_prompt = f"""Design a daily manifestation practice schedule.

Goal: {state['goal']}
Timeframe: {state['timeframe']}
Daily Time Available: {commitment_hours[state['commitment_level']]}

Create a structured daily practice including:
1. Morning routine (first 10 mins after waking)
2. Midday check-in (5-10 mins)
3. Evening reflection (10-15 mins)
4. Optional: Deep practice sessions

Return JSON array of practice objects with:
- name: Practice name
- time: When to do it
- duration: How long
- instructions: Step-by-step
- purpose: Why it matters"""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Design the daily practice schedule.")
        ])

        try:
            practices = json.loads(response.content)
            state["daily_practices"] = practices if isinstance(practices, list) else []
        except:
            state["daily_practices"] = []

        logger.info(f"Daily practices designed: {len(state['daily_practices'])} practices")
        return state

    def _create_affirmations_node(self, state: ManifestationProtocolState) -> ManifestationProtocolState:
        """Generate personalized affirmation sets"""

        system_prompt = f"""Create powerful, personalized affirmations for this goal.

Goal: {state['goal']}
Analysis: {json.dumps(state['protocol'].get('analysis', {}))}

Create 3 affirmation sets (7-10 affirmations each):
1. IDENTITY SET: "I am..." statements (present tense, identity-based)
2. GRATITUDE SET: "I'm grateful for..." (as if already achieved)
3. ACTION SET: "I choose to..." (empowering action statements)

Rules:
- Use present tense
- Be specific and vivid
- Evoke emotion
- Include sensory details
- Make them believable yet stretching

Return JSON object with keys: identity, gratitude, action (each an array of strings)"""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Generate the affirmation sets.")
        ])

        try:
            affirmation_sets = json.loads(response.content)
            # Flatten into single list
            all_affirmations = []
            for key in ["identity", "gratitude", "action"]:
                all_affirmations.extend(affirmation_sets.get(key, []))
            state["affirmations"] = all_affirmations
        except:
            state["affirmations"] = []

        logger.info(f"Created {len(state['affirmations'])} affirmations")
        return state

    def _generate_visualizations_node(self, state: ManifestationProtocolState) -> ManifestationProtocolState:
        """Create guided visualization scripts"""

        system_prompt = f"""Create 3 guided visualization scripts for manifestation.

Goal: {state['goal']}

Create:
1. FUTURE SELF (5 mins): Vivid scene of life after achieving goal
2. PROCESS VISUALIZATION (3 mins): See yourself taking aligned actions
3. QUANTUM JUMP (2 mins): Brief, intense energetic activation

Each script should:
- Use present tense ("You see...", "You feel...")
- Include all 5 senses
- Build emotional intensity
- End with integration

Return JSON array of objects with: name, duration, script"""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Create the visualization scripts.")
        ])

        try:
            scripts = json.loads(response.content)
            state["visualization_scripts"] = [s.get("script", "") for s in scripts]
        except:
            state["visualization_scripts"] = []

        logger.info(f"Generated {len(state['visualization_scripts'])} visualization scripts")
        return state

    def _define_metrics_node(self, state: ManifestationProtocolState) -> ManifestationProtocolState:
        """Define success metrics and tracking methods"""

        system_prompt = f"""Define measurable success metrics for this manifestation goal.

Goal: {state['goal']}
Timeframe: {state['timeframe']}

Create metrics in 3 categories:
1. INNER SHIFTS (how you feel, think, believe)
2. EXTERNAL EVIDENCE (what shows up in your life)
3. BEHAVIORAL INDICATORS (actions you're taking)

Each metric should be:
- Observable
- Trackable weekly
- Specific
- Aligned with the goal

Return JSON array of metric strings."""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Define the success metrics.")
        ])

        try:
            metrics = json.loads(response.content)
            state["success_metrics"] = metrics if isinstance(metrics, list) else []
        except:
            state["success_metrics"] = []

        return state

    def _identify_obstacles_node(self, state: ManifestationProtocolState) -> ManifestationProtocolState:
        """Identify likely obstacles and create solutions"""

        system_prompt = f"""Identify the top 5 obstacles this person will likely face and provide solutions.

Goal: {state['goal']}
Commitment Level: {state['commitment_level']}

For each obstacle provide:
- obstacle: What will get in the way
- why_it_happens: Root cause
- reframe: New perspective on it
- solution: Practical action to overcome it
- affirmation: Power statement to use when it arises

Return JSON array of obstacle objects."""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Identify obstacles and solutions.")
        ])

        try:
            obstacles = json.loads(response.content)
            state["obstacles"] = obstacles if isinstance(obstacles, list) else []
        except:
            state["obstacles"] = []

        return state

    def _set_checkpoints_node(self, state: ManifestationProtocolState) -> ManifestationProtocolState:
        """Set accountability checkpoints throughout timeframe"""

        timeframe_days = {
            "7_days": 7,
            "30_days": 30,
            "90_days": 90
        }

        days = timeframe_days.get(state["timeframe"], 30)

        system_prompt = f"""Create accountability checkpoints for a {days}-day manifestation protocol.

Goal: {state['goal']}

Create checkpoints at strategic intervals:
- Day 3: Initial momentum check
- Day 7: Week 1 review
- Day 14: Mid-point assessment (if 30+ days)
- Day 30: Month milestone (if applicable)
- Final day: Completion review

Each checkpoint should include:
- day: Which day number
- title: Checkpoint name
- reflection_questions: 3-5 questions to ask yourself
- celebration: How to acknowledge progress
- adjustment: What to tweak if needed

Return JSON array of checkpoint objects."""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Create the accountability checkpoints.")
        ])

        try:
            checkpoints = json.loads(response.content)
            state["accountability_checkpoints"] = checkpoints if isinstance(checkpoints, list) else []
        except:
            state["accountability_checkpoints"] = []

        return state

    def _compile_protocol_node(self, state: ManifestationProtocolState) -> ManifestationProtocolState:
        """Compile everything into final protocol document"""

        protocol = {
            "meta": {
                "goal": state["goal"],
                "timeframe": state["timeframe"],
                "commitment_level": state["commitment_level"],
                "created_for": state["user_id"]
            },
            "analysis": state["protocol"].get("analysis", {}),
            "daily_practices": state["daily_practices"],
            "affirmations": {
                "all": state["affirmations"],
                "daily_rotation": self._create_rotation_schedule(state["affirmations"])
            },
            "visualizations": state["visualization_scripts"],
            "success_metrics": state["success_metrics"],
            "obstacles_and_solutions": state["obstacles"],
            "checkpoints": state["accountability_checkpoints"],
            "quick_start_guide": self._generate_quick_start(state)
        }

        state["protocol"] = protocol
        logger.info(f"Protocol compiled for user {state['user_id']}")

        return state

    def _create_rotation_schedule(self, affirmations: List[str]) -> Dict:
        """Create a weekly rotation schedule for affirmations"""
        if not affirmations:
            return {}

        # Split into daily sets
        daily_count = max(5, len(affirmations) // 7)
        rotation = {}

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for i, day in enumerate(days):
            start_idx = (i * daily_count) % len(affirmations)
            end_idx = start_idx + daily_count
            rotation[day] = affirmations[start_idx:end_idx]

        return rotation

    def _generate_quick_start(self, state: ManifestationProtocolState) -> Dict:
        """Generate a quick start guide for Day 1"""
        return {
            "day_1_checklist": [
                "Read through your complete protocol",
                "Set up your tracking system (journal, app, etc.)",
                "Do your first morning practice",
                "Write down your top 3 affirmations where you'll see them",
                "Complete your first visualization",
                "Set reminders for daily practices"
            ],
            "first_week_focus": "Building the habit. Consistency over perfection.",
            "emergency_motivation": "When you feel resistance, remember your WHY: " + state["goal"]
        }

    async def generate_protocol(
        self,
        user_id: str,
        goal: str,
        timeframe: str = "30_days",
        commitment_level: str = "moderate"
    ) -> Dict:
        """Generate complete manifestation protocol"""

        initial_state = {
            "user_id": user_id,
            "goal": goal,
            "timeframe": timeframe,
            "commitment_level": commitment_level,
            "protocol": None,
            "daily_practices": [],
            "affirmations": [],
            "visualization_scripts": [],
            "success_metrics": [],
            "obstacles": [],
            "accountability_checkpoints": []
        }

        result = await self.graph.ainvoke(initial_state)

        return result["protocol"]


# Helper function for easy access
async def create_manifestation_protocol(
    user_id: str,
    goal: str,
    timeframe: str = "30_days",
    commitment_level: str = "moderate"
) -> Dict:
    """
    Convenience function to create a manifestation protocol.

    Args:
        user_id: User identifier
        goal: The manifestation goal
        timeframe: "7_days", "30_days", or "90_days"
        commitment_level: "light", "moderate", or "intensive"

    Returns:
        Complete manifestation protocol dictionary
    """
    agent = ManifestationProtocolAgent()
    return await agent.generate_protocol(user_id, goal, timeframe, commitment_level)
