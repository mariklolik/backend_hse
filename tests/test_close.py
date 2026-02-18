from unittest.mock import AsyncMock, patch

from main import app


def _setup_mocks():
    app.state.db_pool = AsyncMock()
    app.state.kafka_producer = AsyncMock()
    app.state.redis_client = AsyncMock()


def test_close_success(client):
    _setup_mocks()
    mock_ad = {
        "id": 1, "seller_id": 1, "name": "Test",
        "description": "Desc", "category": 1, "images_qty": 0,
        "is_verified_seller": False,
    }

    with (
        patch("routers.users.get_advertisement", new_callable=AsyncMock, return_value=mock_ad),
        patch("routers.users.delete_moderation_results_for_item", new_callable=AsyncMock) as mock_del_mod,
        patch("routers.users.close_advertisement", new_callable=AsyncMock, return_value=True) as mock_close,
        patch("routers.users.delete_cached_prediction", new_callable=AsyncMock) as mock_del_cache,
    ):
        response = client.post("/close?item_id=1")

    assert response.status_code == 200
    assert response.json()["message"] == "Advertisement closed"
    mock_del_mod.assert_called_once()
    mock_close.assert_called_once()
    mock_del_cache.assert_called_once()


def test_close_not_found(client):
    _setup_mocks()
    with patch("routers.users.get_advertisement", new_callable=AsyncMock, return_value=None):
        response = client.post("/close?item_id=999")

    assert response.status_code == 404


def test_close_invalid_item_id(client):
    response = client.post("/close?item_id=-1")
    assert response.status_code == 422
