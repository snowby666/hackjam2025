from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
database = None


async def init_database():
    """Initialize MongoDB connection"""
    global client, database
    try:
        # Validate MongoDB URL
        if not settings.mongodb_url or settings.mongodb_url.strip() == "":
            error_msg = "MONGODB_URL is not set in environment variables. Please set it in your .env file."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        client = AsyncIOMotorClient(settings.mongodb_url)
        database = client[settings.mongodb_db_name]
        # Test connection
        await client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
    except ValueError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        error_msg = f"Failed to connect to MongoDB: {str(e)}. Please check your MONGODB_URL in .env file."
        logger.error(error_msg)
        raise ValueError(error_msg) from e


async def get_database():
    """Get database instance"""
    if database is None:
        await init_database()
    return database


async def close_database():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")

