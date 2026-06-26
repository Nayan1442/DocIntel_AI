import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app


from services.auth_middleware import get_current_user


@pytest.fixture
def client():
    """Fixture to provide a test client with lifespan context manager."""
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "507f1f77bcf86cd799439011",
        "email": "test@example.com",
        "name": "Test User"
    }
    with patch("services.embedding_service.initialize"):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    app.dependency_overrides.clear()


def test_health_check(client):
    """Verify that the health check endpoint returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint(client):
    """Verify that the root endpoint returns app metadata."""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()
    assert "status" in response.json()


def test_get_documents_empty(client):
    """Verify that listing documents returns a valid list response."""
    response = client.get("/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_ask_question(client):
    """Verify that the RAG ask-question endpoint returns an answer and sources."""
    response = client.post("/ask-question", json={
        "question": "What is the total amount?",
        "document_id": None
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data


def test_search_endpoint(client):
    """Verify that the semantic search endpoint returns a list of results."""
    response = client.post("/search", json={
        "query": "invoice summary",
        "top_k": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "query" in data


def test_summarize_endpoint(client, mock_db):
    """Verify that the summarization endpoint fetches and returns a summary."""
    # Set up mock document returning in MongoDB
    mock_db.documents.find_one.return_value = {
        "_id": "507f1f77bcf86cd799439011",
        "filename": "test.pdf",
        "original_name": "test.pdf",
        "text_content": "This is a test document with long text contents."
    }

    response = client.post("/summarize", json={
        "document_id": "507f1f77bcf86cd799439011",
        "num_points": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["document_id"] == "507f1f77bcf86cd799439011"


def test_extract_data_endpoint(client, mock_db):
    """Verify that structured data extraction works on the endpoint."""
    mock_db.documents.find_one.return_value = {
        "_id": "507f1f77bcf86cd799439011",
        "filename": "test.pdf",
        "original_name": "test.pdf",
        "classification": "invoice",
        "text_content": "This is an invoice text content."
    }

    response = client.post("/extract-data", json={
        "document_id": "507f1f77bcf86cd799439011"
    })
    assert response.status_code == 200
    data = response.json()
    assert "extracted_data" in data
    assert data["document_id"] == "507f1f77bcf86cd799439011"


def test_generate_report_endpoint(client, mock_db):
    """Verify that the AI insights report endpoint gathers and returns structured details."""
    mock_db.documents.find_one.return_value = {
        "_id": "507f1f77bcf86cd799439011",
        "original_name": "test.pdf",
        "classification": "invoice",
        "text_content": "Test text"
    }

    response = client.get("/report/507f1f77bcf86cd799439011")
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "507f1f77bcf86cd799439011"
    assert "insights" in data
    assert "summary" in data
    assert "extracted_data" in data


def test_get_document_not_found(client, mock_db):
    """Verify that fetching a non-existent document returns 404."""
    mock_db.documents.find_one.return_value = None
    response = client.get("/documents/507f1f77bcf86cd799439011")
    assert response.status_code == 404
