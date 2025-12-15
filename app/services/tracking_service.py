from datetime import datetime, timezone
from typing import Optional, Dict, List
from app.utils.mongodb import get_db
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class TrackingService:
    """
    Service to track user's current lesson across multiple browser tabs with focus tracking

    Database Schema:
    {
        user_id: "user123",
        active_lessons: [
            {
                lesson_id: "lesson_A",
                serie_id: "serie_1",
                lesson_title: "Intro to Python",
                tab_id: "tab_uuid_1",
                last_active: "2025-12-15T10:30:00Z"
            }
        ],
        current_lesson: {  # Most recently focused lesson
            lesson_id: "lesson_B",
            serie_id: "serie_2",
            lesson_title: "Advanced JS",
            tab_id: "tab_uuid_2"
        },
        last_updated: "2025-12-15T10:35:00Z"
    }
    """

    def __init__(self):
        self._client, self._db = get_db()
        self._tracking_collection = self._db["current_lesson_tracking"]
        self._lessons_collection = self._db["lessons"]
        self._create_indexes()

    def _create_indexes(self):
        """Create MongoDB indexes"""
        try:
            # Unique index on user_id
            self._tracking_collection.create_index("user_id", unique=True)
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    def _fetch_lesson_details(self, serie_id: str, lesson_id: str) -> Optional[Dict]:
        """Fetch full lesson details from database for AI chatbot context"""
        try:
            lesson = self._lessons_collection.find_one({
                "_id": ObjectId(lesson_id),
                "lesson_serie": serie_id
            })

            if not lesson:
                logger.warning(f"Lesson not found: {lesson_id} in serie {serie_id}")
                return None

            # Return lesson data with all fields needed for chatbot
            return {
                "lesson_title": lesson.get("lesson_title"),
                "lesson_description": lesson.get("lesson_description"),
                "lesson_serie": lesson.get("lesson_serie"),
                "lesson_video": lesson.get("lesson_video"),
                "lesson_transcript": lesson.get("lesson_transcript"),
                "transcript_status": lesson.get("transcript_status"),
                "lesson_documents": lesson.get("lesson_documents", []),
                "createdAt": lesson.get("createdAt"),
                "updatedAt": lesson.get("updatedAt"),
                "lesson_summary": lesson.get("lesson_summary"),
                "lesson_timeline": lesson.get("lesson_timeline")
            }
        except Exception as e:
            logger.error(f"Error fetching lesson details: {e}")
            return None

    def set_current_lesson(
        self,
        user_id: str,
        lesson_id: str,
        serie_id: str,
        tab_id: str,
        lesson_title: Optional[str] = None
    ) -> Dict:
        """
        Add or update lesson for a specific browser tab
        This is called when user opens a lesson page in a tab
        Automatically sets this as the current (focused) lesson
        """
        try:
            now = datetime.now(timezone.utc)

            new_lesson = {
                "lesson_id": lesson_id,
                "serie_id": serie_id,
                "lesson_title": lesson_title,
                "tab_id": tab_id,
                "last_active": now
            }

            # Get existing tracking document
            tracking = self._tracking_collection.find_one({"user_id": user_id})

            if tracking:
                # Update existing document
                active_lessons = tracking.get("active_lessons", [])

                # Remove old entry for this tab if exists
                active_lessons = [l for l in active_lessons if l.get("tab_id") != tab_id]

                # Add new lesson for this tab
                active_lessons.append(new_lesson)

                # Update document
                self._tracking_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "active_lessons": active_lessons,
                            "current_lesson": new_lesson,  # Set as current (focused)
                            "last_updated": now
                        }
                    }
                )
            else:
                # Create new document
                self._tracking_collection.insert_one({
                    "user_id": user_id,
                    "active_lessons": [new_lesson],
                    "current_lesson": new_lesson,
                    "last_updated": now
                })

            logger.info(f"Set current lesson for user {user_id} tab {tab_id}: {lesson_id}")

            return {
                "success": True,
                "message": "Current lesson set successfully",
                "data": {
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "serie_id": serie_id,
                    "lesson_title": lesson_title,
                    "tab_id": tab_id
                }
            }

        except Exception as e:
            logger.error(f"Error setting current lesson: {e}")
            return {
                "success": False,
                "message": f"Failed to set current lesson: {str(e)}"
            }

    def update_focus(self, user_id: str, tab_id: str) -> Dict:
        """
        Update which tab is currently focused
        This is called when user switches between tabs (window focus event)
        """
        try:
            now = datetime.now(timezone.utc)

            # Get existing tracking
            tracking = self._tracking_collection.find_one({"user_id": user_id})

            if not tracking:
                return {
                    "success": False,
                    "message": "No tracking data found for user"
                }

            active_lessons = tracking.get("active_lessons", [])

            # Find the lesson for this tab
            focused_lesson = None
            for lesson in active_lessons:
                if lesson.get("tab_id") == tab_id:
                    lesson["last_active"] = now
                    focused_lesson = lesson
                    break

            if not focused_lesson:
                return {
                    "success": False,
                    "message": "Tab not found in active lessons"
                }

            # Update current_lesson and last_active timestamp
            self._tracking_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "active_lessons": active_lessons,
                        "current_lesson": focused_lesson,
                        "last_updated": now
                    }
                }
            )

            logger.info(f"Updated focus for user {user_id} to tab {tab_id}")

            return {
                "success": True,
                "message": "Focus updated successfully",
                "data": focused_lesson
            }

        except Exception as e:
            logger.error(f"Error updating focus: {e}")
            return {
                "success": False,
                "message": f"Failed to update focus: {str(e)}"
            }

    def get_current_lesson(self, user_id: str) -> Optional[Dict]:
        """
        Get user's current lesson (focused tab) with full lesson details for chatbot
        Returns None if user is not in any lesson
        Chatbot uses this to know what lesson context to use
        """
        try:
            tracking = self._tracking_collection.find_one({"user_id": user_id})

            if not tracking or not tracking.get("current_lesson"):
                logger.info(f"User {user_id} is not in any lesson")
                return None

            current = tracking["current_lesson"]
            active_lessons = tracking.get("active_lessons", [])

            # Convert datetime objects to strings for JSON serialization
            active_lessons_serializable = []
            for lesson in active_lessons:
                lesson_copy = lesson.copy()
                if isinstance(lesson_copy.get("last_active"), datetime):
                    lesson_copy["last_active"] = lesson_copy["last_active"].isoformat()
                active_lessons_serializable.append(lesson_copy)

            result = {
                "user_id": tracking["user_id"],
                "lesson_id": current.get("lesson_id"),
                "serie_id": current.get("serie_id"),
                "lesson_title": current.get("lesson_title"),
                "last_updated": tracking.get("last_updated"),
                "active_lessons": active_lessons_serializable,
                "total_active_tabs": len(active_lessons)
            }

            # Fetch full lesson details for AI chatbot context
            lesson_id = current.get("lesson_id")
            serie_id = current.get("serie_id")

            if lesson_id and serie_id:
                lesson_details = self._fetch_lesson_details(serie_id, lesson_id)
                if lesson_details:
                    result["lesson_data"] = lesson_details
                    logger.info(f"Enriched tracking response with lesson details for {lesson_id}")

            return result

        except Exception as e:
            logger.error(f"Error getting current lesson: {e}")
            return None

    def clear_current_lesson(self, user_id: str, tab_id: str) -> Dict:
        """
        Remove lesson from a specific tab (when user closes/navigates away from tab)
        If this was the focused tab, automatically focus the most recent tab
        """
        try:
            tracking = self._tracking_collection.find_one({"user_id": user_id})

            if not tracking:
                return {
                    "success": True,
                    "message": "No tracking data found"
                }

            active_lessons = tracking.get("active_lessons", [])

            # Remove lesson for this tab
            active_lessons = [l for l in active_lessons if l.get("tab_id") != tab_id]

            if len(active_lessons) == 0:
                # No more active lessons, delete entire document
                self._tracking_collection.delete_one({"user_id": user_id})
                logger.info(f"Cleared all lessons for user {user_id}")
                return {
                    "success": True,
                    "message": "All lessons cleared"
                }
            else:
                # Still have active lessons, update current_lesson to most recent
                most_recent = max(active_lessons, key=lambda x: x.get("last_active", datetime.min))

                self._tracking_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "active_lessons": active_lessons,
                            "current_lesson": most_recent,
                            "last_updated": datetime.now(timezone.utc)
                        }
                    }
                )

                logger.info(f"Cleared lesson for user {user_id} tab {tab_id}, {len(active_lessons)} tabs remaining")
                return {
                    "success": True,
                    "message": f"Lesson cleared, {len(active_lessons)} tabs remaining"
                }

        except Exception as e:
            logger.error(f"Error clearing current lesson: {e}")
            return {
                "success": False,
                "message": f"Failed to clear current lesson: {str(e)}"
            }
