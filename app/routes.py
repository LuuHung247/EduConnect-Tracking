from fastapi import APIRouter, HTTPException
from app.models.tracking import (
    SetCurrentLessonRequest,
    ClearCurrentLessonRequest,
    UpdateFocusRequest,
    CurrentLessonResponse
)
from app.services.tracking_service import TrackingService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/api/tracking",
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
    Add/update lesson for a browser tab when user enters a lesson page

    Use case: When user navigates to a lesson page in any browser tab
    This allows tracking multiple lessons across tabs
    The lesson is automatically set as current (focused)
    """
    try:
        result = tracking_service.set_current_lesson(
            user_id=request.user_id,
            lesson_id=request.lesson_id,
            serie_id=request.serie_id,
            tab_id=request.tab_id,
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
    Remove lesson from a specific browser tab when user exits/closes tab

    Use case: When user navigates away from lesson or closes a tab
    If other tabs have lessons open, the most recently active tab becomes current
    If no tabs remain, all tracking is cleared
    """
    try:
        result = tracking_service.clear_current_lesson(
            user_id=request.user_id,
            tab_id=request.tab_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exiting lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/lesson/focus')
async def update_lesson_focus(request: UpdateFocusRequest):
    """
    Update which browser tab is currently focused

    Use case: When user switches between browser tabs (window focus event)
    This updates current_lesson to the focused tab's lesson
    Chatbot will use the focused lesson's context for answers
    """
    try:
        result = tracking_service.update_focus(
            user_id=request.user_id,
            tab_id=request.tab_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating focus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/user/{user_id}/current')
async def get_current_lesson(user_id: str):
    """
    Get user's current lesson (focused tab) and all active lessons

    Use case: Chatbot calls this to check lesson context
    - Returns the currently focused lesson
    - Also returns all active lessons across tabs
    - Chatbot uses focused lesson for context

    Returns:
        - CurrentLessonResponse with:
          - Current lesson (focused tab)
          - All active lessons across tabs
          - Total number of active tabs
    """
    try:
        current = tracking_service.get_current_lesson(user_id)

        if current is None:
            # User is not in any lesson (exploring, browsing, etc.)
            return CurrentLessonResponse(
                user_id=user_id,
                is_in_lesson=False,
                active_lessons=[],
                total_active_tabs=0
            )

        # User is in a lesson
        # Note: lesson_data is included in response but not in Pydantic model
        # This allows chatbot to receive full lesson details without changing model
        response_data = {
            "user_id": current["user_id"],
            "lesson_id": current["lesson_id"],
            "serie_id": current["serie_id"],
            "lesson_title": current.get("lesson_title"),
            "last_updated": current["last_updated"],
            "is_in_lesson": True,
            "active_lessons": current.get("active_lessons", []),
            "total_active_tabs": current.get("total_active_tabs", 0)
        }

        # Add lesson_data if available (for chatbot context)
        if "lesson_data" in current:
            response_data["lesson_data"] = current["lesson_data"]

        return response_data

    except Exception as e:
        logger.error(f"Error getting current lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))
