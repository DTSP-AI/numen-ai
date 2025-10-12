"""
Intake Router - Baseline Flow Entry Point

Processes user intake via IntakeAgent (LangGraph) and generates normalized intake contract.
"""

from fastapi import APIRouter, HTTPException, Request
import logging
import json

from models.schemas import IntakeRequest, IntakeContract
from agents.intake_agent import IntakeAgent
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Global intake agent instance
intake_agent = IntakeAgent()


class IntakeAssistRequest(BaseModel):
    """Request schema for AI text assistance"""
    text: str


class IntakeAssistResponse(BaseModel):
    """Response schema for AI text assistance"""
    suggestion: str


@router.post("/intake/process", response_model=IntakeContract)
async def process_intake(request: IntakeRequest):
    """
    Process user intake and generate normalized contract

    Flow:
    1. Receive user answers (goals, tone, session_type)
    2. Run through IntakeAgent (LangGraph) for normalization
    3. Return IntakeContract for guide creation

    Example Request:
    {
      "user_id": "uuid",
      "answers": {
        "goals": ["Build confidence", "Reduce anxiety"],
        "tone": "calm",
        "session_type": "manifestation"
      }
    }

    Example Response:
    {
      "normalized_goals": ["Build confidence", "Reduce anxiety"],
      "prefs": {
        "tone": "calm",
        "session_type": "manifestation"
      },
      "notes": "User seeks empowerment and stress relief"
    }
    """
    try:
        logger.info(f"Processing intake for user: {request.user_id}")

        # Extract answers
        answers = request.answers
        goals = answers.get("goals", [])
        tone = answers.get("tone", "calm")
        session_type = answers.get("session_type", "manifestation")

        # For baseline, directly normalize without full LangGraph flow
        # (IntakeAgent full conversational flow is for interactive sessions)
        # Here we do simple normalization

        # Normalize goals (clean, dedupe)
        normalized_goals = [
            goal.strip()
            for goal in goals
            if goal and goal.strip()
        ]

        if not normalized_goals:
            normalized_goals = ["Personal growth and manifestation"]

        # Build preferences dict
        prefs = {
            "tone": tone,
            "session_type": session_type
        }

        # Generate notes based on goals
        notes = f"User seeks: {', '.join(normalized_goals[:3])}. Preferred tone: {tone}. Session focus: {session_type}."

        intake_contract = IntakeContract(
            normalized_goals=normalized_goals,
            prefs=prefs,
            notes=notes
        )

        # Store intake contract in semantic memory
        try:
            from services.memory_manager import MemoryManager
            memory_manager = MemoryManager()
            await memory_manager.initialize()

            await memory_manager.embed_and_upsert(
                user_id=request.user_id,
                agent_id=None,  # No agent yet
                session_id=None,  # No session yet
                content=json.dumps(intake_contract.model_dump()),
                meta={"type": "intake_contract", "goals": normalized_goals}
            )

            logger.debug("Stored intake contract in semantic memory")
        except Exception as mem_error:
            logger.warning(f"Failed to store in memory: {mem_error}")
            # Non-blocking - continue even if memory storage fails

        logger.info(f"✅ Intake contract generated for user: {request.user_id}")
        return intake_contract

    except Exception as e:
        logger.error(f"Intake processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process intake: {str(e)}"
        )


@router.post("/intake/assist", response_model=IntakeAssistResponse)
async def intake_assist(request: IntakeAssistRequest):
    """
    AI-powered text refinement for intake form fields.

    Transforms raw user input into clear, structured, affirmative statements.

    Example Request:
    {
      "text": "i want be rich"
    }

    Example Response:
    {
      "suggestion": "I want to cultivate sustainable wealth and abundance."
    }
    """
    try:
        # Validate non-empty text
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text field cannot be empty"
            )

        # Call IntakeAgent to refine text
        refined_text = await intake_agent.refine_text(request.text)

        logger.info(f"✅ Text refined successfully")
        return IntakeAssistResponse(suggestion=refined_text)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text refinement failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refine text: {str(e)}"
        )
