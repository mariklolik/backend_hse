import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from workers.moderation_worker import process_message


@pytest.fixture
def mock_pool():
    pool = AsyncMock()
    return pool


@pytest.fixture
def mock_model():
    model = MagicMock()
    return model


@pytest.fixture
def mock_producer():
    return AsyncMock()


@pytest.mark.asyncio
async def test_process_message_success(mock_pool, mock_model, mock_producer):
    mock_pool.fetch.return_value = [{"id": 42}]

    mock_ad = {
        "is_verified_seller": False, "images_qty": 0,
        "description": "Short", "category": 5,
    }

    import numpy as np
    mock_model.predict_proba.return_value = np.array([[0.3, 0.7]])

    message = {"item_id": 1, "timestamp": "2026-01-01T00:00:00Z"}

    with (
        patch("workers.moderation_worker.get_advertisement", new_callable=AsyncMock, return_value=mock_ad),
        patch("workers.moderation_worker.update_moderation_result", new_callable=AsyncMock) as mock_update,
    ):
        await process_message(message, mock_pool, mock_model, mock_producer)

    mock_update.assert_called_once()
    call_args = mock_update.call_args
    assert call_args[0][2] == "completed"
    assert call_args[1]["is_violation"] is True
    assert call_args[1]["probability"] == pytest.approx(0.7)


@pytest.mark.asyncio
async def test_process_message_ad_not_found(mock_pool, mock_model, mock_producer):
    mock_pool.fetch.return_value = [{"id": 42}]

    message = {"item_id": 999, "timestamp": "2026-01-01T00:00:00Z"}

    with (
        patch("workers.moderation_worker.get_advertisement", new_callable=AsyncMock, return_value=None),
        patch("workers.moderation_worker.update_moderation_result", new_callable=AsyncMock) as mock_update,
        patch("workers.moderation_worker.send_to_dlq", new_callable=AsyncMock) as mock_dlq,
    ):
        await process_message(message, mock_pool, mock_model, mock_producer)

    mock_update.assert_called_once()
    assert mock_update.call_args[0][2] == "failed"
    mock_dlq.assert_called_once()


@pytest.mark.asyncio
async def test_process_message_no_pending_task(mock_pool, mock_model, mock_producer):
    mock_pool.fetch.return_value = []

    message = {"item_id": 1, "timestamp": "2026-01-01T00:00:00Z"}

    await process_message(message, mock_pool, mock_model, mock_producer)
