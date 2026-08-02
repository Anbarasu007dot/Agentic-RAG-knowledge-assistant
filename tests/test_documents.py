from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client=TestClient(app)

def test_get_documents_returns_list():
    with patch("app.main.list_documents") as mock_list_documents:
        mock_list_documents.return_value = []

        response = client.get("/documents")

        assert response.status_code == 200
        assert response.json() == []