from unittest.mock import MagicMock

import pytest
import requests


@pytest.fixture
def mock_logger(mocker):
    return mocker.patch("antminer_exporter.client.logger")


@pytest.fixture
def miner_client():
    from antminer_exporter.client import MinerClient
    return MinerClient("192.168.1.1", "admin")


def test_unlock_success(mock_logger, miner_client, mocker):
    mock_post = mocker.patch("antminer_exporter.client.requests.post")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"token": "abc123..."}
    mock_post.return_value = mock_response

    result = miner_client.unlock()

    assert result is True
    assert miner_client.token == "abc123..."
    mock_logger.debug.assert_called_once()


def test_unlock_wrong_password(mock_logger, miner_client, mocker):
    mock_post = mocker.patch("antminer_exporter.client.requests.post")
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_post.return_value = mock_response

    result = miner_client.unlock()

    assert result is False
    mock_logger.error.assert_called_once()
    assert "Wrong password" in mock_logger.error.call_args[0][0]


def test_unlock_error(mock_logger, miner_client, mocker):
    mock_post = mocker.patch("antminer_exporter.client.requests.post")
    mock_post.side_effect = Exception("Connection error")

    result = miner_client.unlock()

    assert result is False
    mock_logger.error.assert_called_once()


def test_fetch_summary_success(mock_logger, miner_client, mocker):
    mock_get = mocker.patch("antminer_exporter.client.requests.get")
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"miner": {"instant_hashrate": 100}}
    mock_get.return_value = mock_response

    result = miner_client.fetch_summary()

    assert result == {"miner": {"instant_hashrate": 100}}
    mock_logger.error.assert_not_called()
    mock_get.assert_called_once()
    # Verify auth was used
    call_args = mock_get.call_args
    assert call_args[1]["auth"] == ("root", "admin")
    assert "/api/v1/summary" in call_args[0][0]


def test_fetch_summary_error(mock_logger, miner_client, mocker):
    mock_get = mocker.patch("antminer_exporter.client.requests.get")
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    mock_get.return_value = mock_response

    result = miner_client.fetch_summary()

    assert result is None
    mock_logger.error.assert_called_once()


def test_fetch_metrics_success(mock_logger, miner_client, mocker):
    mock_get = mocker.patch("antminer_exporter.client.requests.get")
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "metrics": [{"data": {"hashrate": 0.1, "chip_max_temp": 1073741824}}],
        "timezone": "GMT+1",
    }
    mock_get.return_value = mock_response

    result = miner_client.fetch_metrics()

    assert result["timezone"] == "GMT+1"
    assert "metrics" in result
    mock_logger.error.assert_not_called()
    # Verify correct URL
    call_args = mock_get.call_args
    assert "/api/v1/metrics" in call_args[0][0]


def test_fetch_metrics_error(mock_logger, miner_client, mocker):
    mock_get = mocker.patch("antminer_exporter.client.requests.get")
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    mock_get.return_value = mock_response

    result = miner_client.fetch_metrics()

    assert result is None
    mock_logger.error.assert_called_once()
