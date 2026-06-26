import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


class MockCursor:
    """Async iterator mock for Motor cursor."""
    def __init__(self, items):
        self.items = items
        self.index = 0

    def sort(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


@pytest.fixture(autouse=True)
def mock_db():
    """Mock MongoDB database collections."""
    db_mock = MagicMock()

    # Mock collections
    db_mock.documents = MagicMock()
    db_mock.chunks = MagicMock()
    db_mock.conversations = MagicMock()

    # Setup default return values
    db_mock.documents.find_one = AsyncMock(return_value=None)
    db_mock.documents.insert_one = AsyncMock(return_value=MagicMock(inserted_id="507f1f77bcf86cd799439011"))
    db_mock.documents.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    db_mock.documents.count_documents = AsyncMock(return_value=5)
    db_mock.documents.find = MagicMock(return_value=MockCursor([]))
    db_mock.documents.aggregate = MagicMock(return_value=MockCursor([]))
    db_mock.documents.update_one = AsyncMock()

    db_mock.chunks.insert_many = AsyncMock()
    db_mock.chunks.delete_many = AsyncMock()
    db_mock.chunks.find_one = AsyncMock(return_value={"text": "Mocked chunk text from database"})
    db_mock.chunks.create_index = AsyncMock()

    db_mock.conversations.insert_one = AsyncMock(return_value=MagicMock(inserted_id="507f1f77bcf86cd799439022"))
    db_mock.conversations.update_one = AsyncMock()
    db_mock.conversations.find_one = AsyncMock(return_value=None)
    db_mock.conversations.find = MagicMock(return_value=MockCursor([]))
    db_mock.conversations.aggregate = MagicMock(return_value=MockCursor([]))
    db_mock.conversations.count_documents = AsyncMock(return_value=1)

    import database.db
    # Override the database module level variable directly
    orig_db = database.db.db
    database.db.db = db_mock

    yield db_mock

    database.db.db = orig_db


@pytest.fixture(autouse=True)
def mock_db_connection():
    """Mock database connection setup and teardown inside main to prevent overwriting mock_db."""
    with patch("main.connect_db", new_callable=AsyncMock), \
         patch("main.disconnect_db", new_callable=AsyncMock):
        yield


@pytest.fixture(autouse=True)
def mock_call_llm():
    """Mock LLM calls to return a default JSON response."""
    with patch("services.llm_client.call_llm", new_callable=AsyncMock) as mock:
        mock.return_value = '{"overall_sentiment": "positive", "confidence": 0.9, "tone": "formal", "key_emotions": ["confidence"], "section_analysis": [], "summary": "Mock summary", "keywords": ["test"], "entities": {}, "tags": ["test"]}'
        yield mock
