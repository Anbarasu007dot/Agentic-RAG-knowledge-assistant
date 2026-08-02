from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_response():
    with patch("app.main.insert_user_message") as mock_insert_user_message, \
         patch("app.main.ask_agent") as mock_ask_agent, \
         patch("app.main.insert_assistant_message") as mock_insert_assistant_message:

        mock_insert_user_message.return_value = None
        mock_ask_agent.return_value = "this is a mock Summary"
        mock_insert_assistant_message.return_value = None

        response = client.post(
            "/chat",
            json={
                "question": "What is AI?",
                "thread_id": "test-thread-1"
            }
        )

        assert response.status_code == 200
        assert "mock" in response.text.lower()