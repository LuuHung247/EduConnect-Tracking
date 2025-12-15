from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ActiveLesson(BaseModel):
    """Active lesson in a browser tab"""
    lesson_id: str = Field(..., description="Lesson ID")
    serie_id: str = Field(..., description="Serie ID")
    lesson_title: Optional[str] = Field(None, description="Lesson title")
    tab_id: str = Field(..., description="Unique tab identifier")
    last_active: datetime = Field(..., description="Last time this tab was active")


class SetCurrentLessonRequest(BaseModel):
    """Request to set user's current lesson with tab tracking"""
    user_id: str = Field(..., description="User ID", example="user123")
    lesson_id: str = Field(..., description="Lesson ID", example="lesson456")
    serie_id: str = Field(..., description="Serie ID", example="serie789")
    lesson_title: Optional[str] = Field(None, description="Lesson title", example="Introduction to Python")
    tab_id: str = Field(..., description="Unique browser tab ID", example="tab_abc123")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "lesson_id": "lesson456",
                "serie_id": "serie789",
                "lesson_title": "Introduction to Python",
                "tab_id": "tab_abc123"
            }
        }


class ClearCurrentLessonRequest(BaseModel):
    """Request to clear user's lesson for a specific tab"""
    user_id: str = Field(..., description="User ID", example="user123")
    tab_id: str = Field(..., description="Browser tab ID to remove", example="tab_abc123")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "tab_id": "tab_abc123"
            }
        }


class UpdateFocusRequest(BaseModel):
    """Request to update which tab/lesson is currently focused"""
    user_id: str = Field(..., description="User ID", example="user123")
    tab_id: str = Field(..., description="Tab ID that gained focus", example="tab_abc123")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "tab_id": "tab_abc123"
            }
        }


class CurrentLessonResponse(BaseModel):
    """Response for current lesson (focused tab)"""
    user_id: str = Field(..., description="User ID")
    lesson_id: Optional[str] = Field(None, description="Current lesson ID (focused tab)")
    serie_id: Optional[str] = Field(None, description="Current serie ID")
    lesson_title: Optional[str] = Field(None, description="Lesson title")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    is_in_lesson: bool = Field(False, description="Whether user is currently in a lesson")
    active_lessons: List[dict] = Field(default_factory=list, description="All active lessons across tabs")
    total_active_tabs: int = Field(0, description="Total number of tabs with active lessons")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "name": "User with multiple tabs",
                    "value": {
                        "user_id": "user123",
                        "lesson_id": "lesson456",
                        "serie_id": "serie789",
                        "lesson_title": "Introduction to Python",
                        "last_updated": "2025-12-15T10:35:00Z",
                        "is_in_lesson": True,
                        "active_lessons": [
                            {
                                "lesson_id": "lesson123",
                                "serie_id": "serie111",
                                "lesson_title": "Advanced JavaScript",
                                "tab_id": "tab_001",
                                "last_active": "2025-12-15T10:30:00Z"
                            },
                            {
                                "lesson_id": "lesson456",
                                "serie_id": "serie789",
                                "lesson_title": "Introduction to Python",
                                "tab_id": "tab_002",
                                "last_active": "2025-12-15T10:35:00Z"
                            }
                        ],
                        "total_active_tabs": 2
                    }
                },
                {
                    "name": "User not in lesson",
                    "value": {
                        "user_id": "user123",
                        "lesson_id": None,
                        "serie_id": None,
                        "lesson_title": None,
                        "last_updated": None,
                        "is_in_lesson": False,
                        "active_lessons": [],
                        "total_active_tabs": 0
                    }
                }
            ]
        }
