from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_without_question_returns_validation_error():
    response = client.post("/chat", json={})

    assert response.status_code in [400, 422]