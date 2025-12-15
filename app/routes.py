from fastapi import APIRouter, HTTPException
from app.models.tracking import (
    SetCurrentLessonRequest,
    ClearCurrentLessonRequest,
    CurrentLessonResponse
)
from app.services.tracking_service import TrackingService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/tracking",
    tags=["Tracking"]
)

# Initialize tracking service
tracking_service = TrackingService()


@router.get(
    '/health',
    tags=["Health"],
    summary="Health Check",
    description="Check if Tracking Service is running"
)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "tracking-service",
        "version": "1.0.0"
    }


@router.post('/lesson/enter')
async def enter_lesson(request: SetCurrentLessonRequest):
    """
    Set user's current lesson when they enter a lesson page

    Use case: When user navigates to a lesson page and starts learning
    This allows chatbot to know the context and answer questions about current lesson
    """
    try:
        result = tracking_service.set_current_lesson(
            user_id=request.user_id,
            lesson_id=request.lesson_id,
            serie_id=request.serie_id,
            lesson_title=request.lesson_title
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error entering lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/lesson/exit')
async def exit_lesson(request: ClearCurrentLessonRequest):
    """
    Clear user's current lesson when they exit lesson page

    Use case: When user navigates away from lesson page (back to explore, series list, etc.)
    Chatbot will know user is not in any specific lesson context
    """
    try:
        result = tracking_service.clear_current_lesson(user_id=request.user_id)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exiting lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/user/{user_id}/current', response_model=CurrentLessonResponse)
async def get_current_lesson(user_id: str):
    """
    Get user's current lesson

    Use case: Chatbot calls this to check if user is in a lesson
    - If user is in lesson -> chatbot can answer questions about current lesson
    - If user is NOT in lesson (None) -> chatbot tells user to navigate to a lesson first

    Returns:
        - CurrentLessonResponse with lesson info if user is in a lesson
        - CurrentLessonResponse with is_in_lesson=False if user is not in any lesson
    """
    try:
        current = tracking_service.get_current_lesson(user_id)

        if current is None:
            # User is not in any lesson (exploring, browsing, etc.)
            return CurrentLessonResponse(
                user_id=user_id,
                is_in_lesson=False
            )

        # User is in a lesson
        return CurrentLessonResponse(
            user_id=current["user_id"],
            lesson_id=current["lesson_id"],
            serie_id=current["serie_id"],
            lesson_title=current.get("lesson_title"),
            last_updated=current["last_updated"],
            is_in_lesson=True
        )

    except Exception as e:
        logger.error(f"Error getting current lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))
