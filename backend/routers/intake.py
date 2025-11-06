"""
Intake Router - Baseline Flow Entry Point

Processes user intake via IntakeAgent (LangGraph) and generates normalized intake contract.
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from models.schemas import IntakeRequest, IntakeContract
from dependencies import get_tenant_id, get_user_id
# from agents.intake_agent import IntakeAgent  # Not needed for intake/assist endpoint
from pydantic import BaseModel
from openai import OpenAI
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# OpenAI client for AI assist endpoint
# Check both lowercase and uppercase env var names for consistency
_openai_api_key = settings.openai_api_key or settings.OPENAI_API_KEY
openai_client = OpenAI(api_key=_openai_api_key)


class IntakeAssistRequest(BaseModel):
    """Request schema for AI text assistance"""
    text: str


class IntakeAssistResponse(BaseModel):
    """Response schema for AI text assistance"""
    suggestion: str


@router.post("/intake/process", response_model=IntakeContract)
async def process_intake(
    request: IntakeRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
):
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
        # Use user_id from dependency or fallback to request
        if not user_id and request.user_id:
            user_id = request.user_id
        
        logger.info(f"Processing intake for user: {user_id}, tenant: {tenant_id}")

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
        # NOTE: Skipping memory storage at intake stage - will be stored when agent is created
        # MemoryManager requires agent_id which doesn't exist yet during intake
        try:
            # For now, skip memory storage until agent is created
            # The agent creation process will handle storing intake data
            logger.debug("Skipping memory storage at intake - will be stored during agent creation")
        except Exception as mem_error:
            logger.warning(f"Memory storage skipped: {mem_error}")
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

        # Use OpenAI to refine text
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Polish and improve this user input for a manifestation intake form. Make it clear, positive, and actionable. Keep it concise."},
                {"role": "user", "content": request.text}
            ],
            max_tokens=200
        )
        refined_text = response.choices[0].message.content

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
