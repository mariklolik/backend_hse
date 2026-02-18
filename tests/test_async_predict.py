from unittest.mock import AsyncMock, patch

from main import app


def _setup_mocks():
    app.state.db_pool = AsyncMock()
    app.state.kafka_producer = AsyncMock()


def test_async_predict_success(client):
    _setup_mocks()
    mock_ad = {
        "id": 1, "seller_id": 1, "name": "Test",
        "description": "Short", "category": 5, "images_qty": 0,
        "is_verified_seller": False,
    }
    mock_task = {"id": 42, "item_id": 1, "status": "pending"}

    with (
        patch("routers.users.get_advertisement", new_callable=AsyncMock, return_value=mock_ad),
        patch("routers.users.create_moderation_task", new_callable=AsyncMock, return_value=mock_task),
        patch("routers.users.send_moderation_request", new_callable=AsyncMock) as mock_send,
    ):
        response = client.post("/async_predict?item_id=1")

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == 42
    assert data["status"] == "pending"
    assert data["message"] == "Moderation request accepted"
    mock_send.assert_called_once()


def test_async_predict_not_found(client):
    _setup_mocks()
    with patch("routers.users.get_advertisement", new_callable=AsyncMock, return_value=None):
        response = client.post("/async_predict?item_id=999")

    assert response.status_code == 404


def test_async_predict_invalid_item_id(client):
    response = client.post("/async_predict?item_id=-1")
    assert response.status_code == 422


def test_moderation_result_pending(client):
    _setup_mocks()
    mock_result = {
        "id": 42, "item_id": 1, "status": "pending",
        "is_violation": None, "probability": None,
    }
    with patch("routers.users.get_moderation_result", new_callable=AsyncMock, return_value=mock_result):
        response = client.get("/moderation_result/42")

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == 42
    assert data["status"] == "pending"
    assert data["is_violation"] is None
    assert data["probability"] is None


def test_moderation_result_completed(client):
    _setup_mocks()
    mock_result = {
        "id": 42, "item_id": 1, "status": "completed",
        "is_violation": True, "probability": 0.87,
    }
    with patch("routers.users.get_moderation_result", new_callable=AsyncMock, return_value=mock_result):
        response = client.get("/moderation_result/42")

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == 42
    assert data["status"] == "completed"
    assert data["is_violation"] is True
    assert data["probability"] == 0.87


def test_moderation_result_not_found(client):
    _setup_mocks()
    with patch("routers.users.get_moderation_result", new_callable=AsyncMock, return_value=None):
        response = client.get("/moderation_result/999")

    assert response.status_code == 404
