from unittest.mock import AsyncMock, patch

from main import app


def _setup_mocks():
    app.state.db_pool = AsyncMock()
    app.state.kafka_producer = AsyncMock()
    app.state.redis_client = AsyncMock()


def test_simple_predict_violation_true(client):
    mock_ad = {
        "id": 1, "seller_id": 1, "name": "Test",
        "description": "Short", "category": 5, "images_qty": 0,
        "is_verified_seller": False,
    }
    _setup_mocks()
    with (
        patch("routers.users.get_cached_prediction", new_callable=AsyncMock, return_value=None),
        patch("routers.users.get_advertisement", new_callable=AsyncMock, return_value=mock_ad),
        patch("routers.users.set_cached_prediction", new_callable=AsyncMock),
    ):
        response = client.post("/simple_predict?item_id=1")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["is_violation"], bool)
    assert isinstance(data["probability"], float)
    assert 0.0 <= data["probability"] <= 1.0


def test_simple_predict_violation_false(client):
    mock_ad = {
        "id": 2, "seller_id": 2, "name": "Good Item",
        "description": "This is a very long and detailed description of the product " * 20,
        "category": 3, "images_qty": 10, "is_verified_seller": True,
    }
    _setup_mocks()
    with (
        patch("routers.users.get_cached_prediction", new_callable=AsyncMock, return_value=None),
        patch("routers.users.get_advertisement", new_callable=AsyncMock, return_value=mock_ad),
        patch("routers.users.set_cached_prediction", new_callable=AsyncMock),
    ):
        response = client.post("/simple_predict?item_id=2")

    assert response.status_code == 200
    data = response.json()
    assert data["is_violation"] is False
    assert data["probability"] < 0.5


def test_simple_predict_cache_hit(client):
    cached = {"is_violation": True, "probability": 0.9}
    _setup_mocks()
    with patch("routers.users.get_cached_prediction", new_callable=AsyncMock, return_value=cached):
        response = client.post("/simple_predict?item_id=1")

    assert response.status_code == 200
    data = response.json()
    assert data["is_violation"] is True
    assert data["probability"] == 0.9


def test_simple_predict_not_found(client):
    _setup_mocks()
    with (
        patch("routers.users.get_cached_prediction", new_callable=AsyncMock, return_value=None),
        patch("routers.users.get_advertisement", new_callable=AsyncMock, return_value=None),
    ):
        response = client.post("/simple_predict?item_id=999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Advertisement not found"


def test_simple_predict_invalid_item_id(client):
    response = client.post("/simple_predict?item_id=-1")
    assert response.status_code == 422
