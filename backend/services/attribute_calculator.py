"""
Attribute Calculator - Dynamic Trait Calculation from Intake Data

Analyzes user's intake responses to recommend optimal agent trait values
instead of using hardcoded defaults.

Architecture:
- LLM-powered trait recommendation
- Session type awareness
- Tone preference integration
- Goal analysis for personality alignment
"""

from typing import Dict, List, Optional
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from models.agent import AgentTraits
from models.schemas import IntakeContract, UserGuideControls
from config import settings

logger = logging.getLogger(__name__)


class AttributeCalculator:
    """
    Calculate optimal agent attributes from intake data

    Uses LLM to analyze:
    - Session type (manifestation vs anxiety_relief vs confidence_building)
    - Tone preference (calm vs energetic vs authoritative)
    - User goals and communication style
    - Explicit preferences
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-5-nano",
            temperature=0.3,  # Lower temp for consistent recommendations
            api_key=settings.openai_api_key
        )

    def map_user_controls_to_traits(
        self,
        user_controls: UserGuideControls,
        session_type: Optional[str] = None
    ) -> AgentTraits:
        """
        Map 4 user-facing controls to 10 backend traits

        Args:
            user_controls: User's guide customization preferences
            session_type: Optional session type for auto-calculation of hidden traits

        Returns:
            AgentTraits with all 10 traits calculated
        """

        # === USER CONTROL 1: Guide Energy (Calm ↔ Energetic) ===
        # Maps to: Assertiveness, Confidence (inverse at extremes), Formality (inverse)
        energy = user_controls.guide_energy

        # Assertiveness: Direct linear mapping
        assertiveness = energy

        # Confidence: High at both extremes (calm confidence vs energetic confidence)
        # U-shaped curve: high at 0-20 (calm certainty), dip at 40-60, high at 80-100 (energetic conviction)
        if energy <= 30:
            confidence = 75  # Calm, grounded confidence
        elif energy <= 60:
            confidence = 65  # Moderate confidence
        else:
            confidence = 80  # Energetic, dynamic confidence

        # Formality: Inverse relationship (calm = more formal, energetic = less formal)
        formality = 100 - energy

        # === USER CONTROL 2: Coaching Style (Nurturing ↔ Directive) ===
        # Maps to: Empathy (inverse), Discipline (direct), Supportiveness (inverse)
        coaching = user_controls.coaching_style

        # Empathy: Inverse linear (nurturing = high empathy, directive = moderate)
        empathy = 100 - int(coaching * 0.4)  # Range: 60-100

        # Discipline: Direct linear mapping
        discipline = coaching

        # Supportiveness: Inverse relationship
        supportiveness = 100 - int(coaching * 0.2)  # Range: 80-100

        # === USER CONTROL 3: Creative Expression (Practical ↔ Imaginative) ===
        # Maps to: Creativity (direct), Spirituality (correlated)
        expression = user_controls.creative_expression

        # Creativity: Direct linear mapping
        creativity = expression

        # Spirituality: Correlated (practical = evidence-based, imaginative = spiritual)
        spirituality = expression

        # === USER CONTROL 4: Communication Depth (Concise ↔ Detailed) ===
        # Maps to: Verbosity (direct)
        depth = user_controls.communication_depth

        # Verbosity: Direct linear mapping
        verbosity = depth

        # === BACKEND-ONLY TRAIT: Humor ===
        # Always low for manifestation/hypnotherapy (25-35 range)
        humor = 30

        # === AUTO-ADJUST BASED ON SESSION TYPE (if provided) ===
        if session_type:
            if session_type == "anxiety_relief":
                # Override for anxiety: maximize empathy, minimize assertiveness
                empathy = max(empathy, 85)
                assertiveness = min(assertiveness, 40)
                supportiveness = 95

            elif session_type == "confidence_building":
                # Override for confidence: boost confidence and discipline
                confidence = max(confidence, 80)
                discipline = max(discipline, 70)
                assertiveness = max(assertiveness, 65)

            elif session_type == "manifestation":
                # Boost spirituality and creativity for manifestation
                spirituality = max(spirituality, 65)
                creativity = max(creativity, 60)

        logger.info(f"Mapped user controls to traits: energy={energy}, coaching={coaching}, expression={expression}, depth={depth}")

        return AgentTraits(
            confidence=confidence,
            empathy=empathy,
            creativity=creativity,
            discipline=discipline,
            assertiveness=assertiveness,
            humor=humor,
            formality=formality,
            verbosity=verbosity,
            spirituality=spirituality,
            supportiveness=supportiveness
        )

    async def calculate_optimal_attributes(
        self,
        intake_contract: IntakeContract,
        user_history: Optional[Dict] = None,
        user_controls: Optional[UserGuideControls] = None
    ) -> AgentTraits:
        """
        Calculate optimal trait values based on intake data

        Args:
            intake_contract: User's intake responses
            user_history: Optional past interaction data
            user_controls: Optional user customization (if provided, overrides AI calculation)

        Returns:
            AgentTraits with personalized values
        """

        # PRIORITY 1: User explicitly set controls (highest priority)
        if user_controls:
            logger.info("Using user-provided guide controls for trait calculation")
            return self.map_user_controls_to_traits(
                user_controls,
                session_type=intake_contract.prefs.get("session_type")
            )

        # PRIORITY 2: AI-calculated traits from intake data
        try:
            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(intake_contract, user_history)

            # Invoke LLM
            messages = [
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=analysis_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            traits_text = response.content

            # Parse LLM response into trait values
            traits = self._parse_trait_values(traits_text)

            logger.info(f"Calculated traits for session_type={intake_contract.session_type}: {traits}")

            return AgentTraits(**traits)

        except Exception as e:
            logger.error(f"Attribute calculation failed: {e}")
            # Fallback to session-type based defaults
            return self._get_session_type_defaults(intake_contract.session_type)

    def _get_system_prompt(self) -> str:
        """System prompt for trait calculation LLM"""
        return """You are an expert AI personality architect. Your task is to analyze user intake data and recommend optimal agent trait values (0-100 scale) for a personalized AI guide.

TRAIT DEFINITIONS:
- Confidence (0-100): Certainty and authority in responses
  - Low (0-30): Tentative, deferential
  - Moderate (31-60): Balanced, collaborative
  - High (61-85): Assertive, directive
  - Very High (86-100): Absolutely certain, commanding

- Empathy (0-100): Emotional sensitivity and understanding
  - Low (0-30): Task-focused, minimal emotional processing
  - Moderate (31-60): Acknowledges feelings appropriately
  - High (61-85): Deeply validating, compassionate
  - Very High (86-100): Profoundly attuned, nurturing

- Creativity (0-100): Creative vs structured responses
  - Low (0-30): Linear, evidence-based, conventional
  - Moderate (31-60): Balanced structure with some creativity
  - High (61-85): Imaginative, uses metaphors
  - Very High (86-100): Highly novel, unconventional approaches

- Discipline (0-100): Structured and consistent approach
  - Low (0-30): Fluid, intuitive, spontaneous
  - Moderate (31-60): Flexible structure
  - High (61-85): Organized, accountable
  - Very High (86-100): Rigorous, systematic, enforcement-oriented

YOUR TASK:
Analyze the user's intake data and recommend trait values that will create the most effective, personalized guide for their specific needs and preferences.

OUTPUT FORMAT:
confidence: <value 0-100>
empathy: <value 0-100>
creativity: <value 0-100>
discipline: <value 0-100>
assertiveness: <value 0-100>
humor: <value 0-100>
formality: <value 0-100>
verbosity: <value 0-100>
spirituality: <value 0-100>
supportiveness: <value 0-100>

Include brief reasoning for each value (2-3 sentences).
"""

    def _build_analysis_prompt(
        self,
        intake: IntakeContract,
        user_history: Optional[Dict]
    ) -> str:
        """Build prompt for LLM analysis"""
        sections = []

        sections.append(f"**Session Type:** {intake.session_type}")
        sections.append(f"**Tone Preference:** {intake.tone}")

        if intake.goals:
            goals_text = "\n".join([f"- {g}" for g in intake.goals])
            sections.append(f"**User Goals:**\n{goals_text}")

        if intake.challenges:
            challenges_text = "\n".join([f"- {c}" for c in intake.challenges])
            sections.append(f"**Challenges:**\n{challenges_text}")

        if intake.preferences:
            prefs = intake.preferences
            sections.append(f"**Preferences:**")
            if prefs.communication_style:
                sections.append(f"- Communication style: {prefs.communication_style}")
            if prefs.session_pace:
                sections.append(f"- Session pace: {prefs.session_pace}")

        if user_history:
            sections.append(f"**Past Interactions:** {user_history.get('summary', 'None')}")

        return "\n\n".join(sections)

    def _parse_trait_values(self, llm_response: str) -> Dict[str, int]:
        """Parse LLM response into trait dictionary"""
        import re

        traits = {}
        trait_names = [
            "confidence", "empathy", "creativity", "discipline",
            "assertiveness", "humor", "formality", "verbosity",
            "spirituality", "supportiveness"
        ]

        for trait in trait_names:
            # Look for pattern: "trait: value"
            pattern = rf"{trait}:\s*(\d+)"
            match = re.search(pattern, llm_response, re.IGNORECASE)

            if match:
                value = int(match.group(1))
                # Clamp to 0-100
                value = max(0, min(100, value))
                traits[trait] = value
            else:
                # Fallback to default
                traits[trait] = self._get_trait_default(trait)

        return traits

    def _get_trait_default(self, trait: str) -> int:
        """Get default value for a trait"""
        defaults = {
            "confidence": 70,
            "empathy": 70,
            "creativity": 50,
            "discipline": 60,
            "assertiveness": 50,
            "humor": 30,
            "formality": 50,
            "verbosity": 50,
            "spirituality": 60,
            "supportiveness": 80
        }
        return defaults.get(trait, 50)

    def _get_session_type_defaults(self, session_type: str) -> AgentTraits:
        """
        Fallback: Get trait defaults based on session type

        Used when LLM analysis fails
        """
        if session_type == "manifestation":
            return AgentTraits(
                confidence=75,      # Higher confidence for manifestation
                empathy=65,
                creativity=70,      # More creative for visualization
                discipline=65,      # Moderate discipline for practice
                assertiveness=60,
                humor=40,
                formality=40,
                verbosity=60,
                spirituality=75,    # Higher spirituality for manifestation
                supportiveness=80
            )

        elif session_type == "anxiety_relief":
            return AgentTraits(
                confidence=60,
                empathy=85,         # Very high empathy for anxiety
                creativity=50,
                discipline=50,      # Lower discipline, more fluid
                assertiveness=40,   # Less assertive, more gentle
                humor=25,
                formality=30,       # More casual for comfort
                verbosity=55,
                spirituality=60,
                supportiveness=90   # Maximum supportiveness
            )

        elif session_type == "confidence_building":
            return AgentTraits(
                confidence=85,      # Model high confidence
                empathy=70,
                creativity=60,
                discipline=70,      # Higher discipline for growth
                assertiveness=70,   # More directive
                humor=45,
                formality=50,
                verbosity=55,
                spirituality=50,
                supportiveness=75
            )

        else:
            # Default balanced traits
            return AgentTraits()

    async def refine_attributes_from_feedback(
        self,
        current_traits: AgentTraits,
        feedback: str,
        adjustment_magnitude: float = 0.15
    ) -> AgentTraits:
        """
        Refine traits based on user feedback

        Args:
            current_traits: Current trait values
            feedback: User feedback text
            adjustment_magnitude: How much to adjust (0.0-1.0)

        Returns:
            Adjusted AgentTraits
        """
        # Analyze feedback for trait adjustments
        messages = [
            SystemMessage(content="""Analyze user feedback and recommend trait adjustments.

Output format (only changed traits):
trait_name: +10 (increase) or -15 (decrease)
reasoning: brief explanation
"""),
            HumanMessage(content=f"Current traits: {current_traits.model_dump()}\n\nUser feedback: {feedback}")
        ]

        response = await self.llm.ainvoke(messages)
        adjustments = self._parse_trait_adjustments(response.content)

        # Apply adjustments
        current_dict = current_traits.model_dump()

        for trait, delta in adjustments.items():
            if trait in current_dict:
                current_value = current_dict[trait]
                adjustment = int(delta * adjustment_magnitude)
                new_value = max(0, min(100, current_value + adjustment))
                current_dict[trait] = new_value

        return AgentTraits(**current_dict)

    def _parse_trait_adjustments(self, llm_response: str) -> Dict[str, int]:
        """Parse adjustment deltas from LLM response"""
        import re

        adjustments = {}
        # Look for pattern: "trait: +10" or "trait: -15"
        pattern = r"(\w+):\s*([+-]?\d+)"
        matches = re.findall(pattern, llm_response)

        for trait, delta in matches:
            if trait in ["confidence", "empathy", "creativity", "discipline",
                        "assertiveness", "humor", "formality", "verbosity",
                        "spirituality", "supportiveness"]:
                adjustments[trait] = int(delta)

        return adjustments


# Singleton instance
calculator = AttributeCalculator()


async def calculate_guide_attributes(
    intake_contract: IntakeContract,
    user_history: Optional[Dict] = None,
    user_controls: Optional[UserGuideControls] = None
) -> AgentTraits:
    """
    Convenience function to calculate guide attributes

    Args:
        intake_contract: User's intake responses
        user_history: Optional past interaction data
        user_controls: Optional user customization controls

    Returns:
        Optimized AgentTraits
    """
    return await calculator.calculate_optimal_attributes(intake_contract, user_history, user_controls)


def map_user_controls(
    user_controls: UserGuideControls,
    session_type: Optional[str] = None
) -> AgentTraits:
    """
    Synchronous convenience function to map user controls to traits

    Args:
        user_controls: User's 4 guide customization preferences
        session_type: Optional session type for context-aware adjustments

    Returns:
        Complete AgentTraits with all 10 traits
    """
    return calculator.map_user_controls_to_traits(user_controls, session_type)
