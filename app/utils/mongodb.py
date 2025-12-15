import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger(__name__)

_client = None
_db = None


def get_db():
    """Get MongoDB database connection"""
    global _client, _db

    if _db is not None:
        return _client, _db

    try:
        mongodb_uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
        db_name = os.environ.get('MONGODB_NAME', 'edu-connect')

        logger.info(f"Connecting to MongoDB: {db_name}")

        _client = MongoClient(mongodb_uri)
        _db = _client[db_name]

        # Test connection
        _client.admin.command('ping')
        logger.info("MongoDB connection established successfully")

        return _client, _db

    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise


def close_db():
    """Close MongoDB connection"""
    global _client, _db

    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")
