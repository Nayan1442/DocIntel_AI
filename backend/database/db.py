import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Connect to MongoDB."""
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    # Create indexes
    await db.documents.create_index("filename")
    await db.documents.create_index("classification")
    await db.documents.create_index("user_id")
    await db.chunks.create_index("document_id")
    await db.users.create_index("email", unique=True)
    logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")


async def disconnect_db():
    """Disconnect from MongoDB."""
    global client
    if client:
        client.close()
        logger.info("Disconnected from MongoDB")


def get_db():
    """Return the database instance."""
    return db
