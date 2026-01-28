import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_predict_violation_true(client):
    response = client.post(
        "/predict",
        json={
            "seller_id": 1,
            "is_verified_seller": False,
            "item_id": 100,
            "name": "Test Item",
            "description": "Short",
            "category": 5,
            "images_qty": 0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_violation" in data
    assert "probability" in data
    assert isinstance(data["is_violation"], bool)
    assert isinstance(data["probability"], float)
    assert 0.0 <= data["probability"] <= 1.0


def test_predict_violation_false(client):
    response = client.post(
        "/predict",
        json={
            "seller_id": 2,
            "is_verified_seller": True,
            "item_id": 200,
            "name": "Test Item",
            "description": "This is a very long description " * 20,
            "category": 3,
            "images_qty": 10,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_violation"] is False
    assert data["probability"] < 0.5


def test_predict_validation_error_invalid_type(client):
    response = client.post(
        "/predict",
        json={
            "seller_id": "invalid",
            "is_verified_seller": True,
            "item_id": 500,
            "name": "Test Item",
            "description": "Test Description",
            "category": 4,
            "images_qty": 1,
        },
    )
    assert response.status_code == 422


def test_predict_validation_error_missing_field(client):
    response = client.post(
        "/predict",
        json={
            "seller_id": 4,
            "is_verified_seller": True,
            "item_id": 400,
            "category": 1,
            "images_qty": 2,
        },
    )
    assert response.status_code == 422


def test_predict_validation_error_negative_value(client):
    response = client.post(
        "/predict",
        json={
            "seller_id": -1,
            "is_verified_seller": False,
            "item_id": 600,
            "name": "Test Item",
            "description": "Test Description",
            "category": 2,
            "images_qty": 3,
        },
    )
    assert response.status_code == 422


def test_predict_model_unavailable(client):
    original_model = app.state.model
    app.state.model = None
    try:
        response = client.post(
            "/predict",
            json={
                "seller_id": 1,
                "is_verified_seller": True,
                "item_id": 100,
                "name": "Test",
                "description": "Test Description",
                "category": 1,
                "images_qty": 1,
            },
        )
        assert response.status_code == 503
        assert response.json()["detail"] == "Model not available"
    finally:
        app.state.model = original_model
