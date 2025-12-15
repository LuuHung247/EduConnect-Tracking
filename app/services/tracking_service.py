from datetime import datetime, timezone
from typing import Optional, Dict
from app.utils.mongodb import get_db
import logging

logger = logging.getLogger(__name__)


class TrackingService:
    """Service to track user's current lesson for chatbot context"""

    def __init__(self):
        self._client, self._db = get_db()
        self._tracking_collection = self._db["current_lesson_tracking"]

        # Create index for better performance
        self._create_indexes()

    def _create_indexes(self):
        """Create MongoDB indexes"""
        try:
            # Unique index on user_id
            self._tracking_collection.create_index("user_id", unique=True)
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    def set_current_lesson(
        self,
        user_id: str,
        lesson_id: str,
        serie_id: str,
        lesson_title: Optional[str] = None
    ) -> Dict:
        """
        Set user's current lesson (when user enters a lesson page)
        This helps chatbot know the context of what user is learning
        """
        try:
            now = datetime.now(timezone.utc)

            # Update or create tracking record
            tracking_data = {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "serie_id": serie_id,
                "lesson_title": lesson_title,
                "last_updated": now
            }

            # Use upsert to create or update
            self._tracking_collection.update_one(
                {"user_id": user_id},
                {"$set": tracking_data},
                upsert=True
            )

            logger.info(f"Set current lesson for user {user_id}: {lesson_id}")

            return {
                "success": True,
                "message": "Current lesson set successfully",
                "data": {
                    "user_id": user_id,
                    "lesson_id": lesson_id,
                    "serie_id": serie_id,
                    "lesson_title": lesson_title
                }
            }

        except Exception as e:
            logger.error(f"Error setting current lesson: {e}")
            return {
                "success": False,
                "message": f"Failed to set current lesson: {str(e)}"
            }

    def get_current_lesson(self, user_id: str) -> Optional[Dict]:
        """
        Get user's current lesson
        Returns None if user is not in any lesson (exploring, browsing series list, etc.)
        Chatbot will use this to know if it should answer questions about current lesson
        """
        try:
            tracking = self._tracking_collection.find_one({"user_id": user_id})

            if not tracking:
                logger.info(f"User {user_id} is not in any lesson")
                return None

            return {
                "user_id": tracking["user_id"],
                "lesson_id": tracking["lesson_id"],
                "serie_id": tracking["serie_id"],
                "lesson_title": tracking.get("lesson_title"),
                "last_updated": tracking["last_updated"]
            }

        except Exception as e:
            logger.error(f"Error getting current lesson: {e}")
            return None

    def clear_current_lesson(self, user_id: str) -> Dict:
        """
        Clear user's current lesson (when user exits lesson page)
        This tells chatbot that user is not in any specific lesson context
        """
        try:
            result = self._tracking_collection.delete_one({"user_id": user_id})

            if result.deleted_count > 0:
                logger.info(f"Cleared current lesson for user {user_id}")
                return {
                    "success": True,
                    "message": "Current lesson cleared successfully"
                }
            else:
                logger.info(f"No current lesson to clear for user {user_id}")
                return {
                    "success": True,
                    "message": "No current lesson was set"
                }

        except Exception as e:
            logger.error(f"Error clearing current lesson: {e}")
            return {
                "success": False,
                "message": f"Failed to clear current lesson: {str(e)}"
            }
