from unittest.mock import MagicMock

import pytest
import requests


@pytest.fixture
def mock_logger(mocker):
    return mocker.patch("antminer_exporter.client.logger")


@pytest.fixture
def mock_requests_get(mocker):
    return mocker.patch("antminer_exporter.client.requests.get")


def test_fetch_summary_success(mock_logger, mock_requests_get):
    from antminer_exporter.client import fetch_summary

    # Mock successful response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"miner": {"instant_hashrate": 100}}
    mock_requests_get.return_value = mock_response

    result = fetch_summary("192.168.1.1", "admin")

    assert result == {"miner": {"instant_hashrate": 100}}
    mock_logger.error.assert_not_called()
    # Verify auth was used
    mock_requests_get.assert_called_once_with(
        "http://192.168.1.1/api/v1/summary",
        auth=("root", "admin"),
        timeout=5,
    )


def test_fetch_summary_http_error(mock_logger, mock_requests_get):
    from antminer_exporter.client import fetch_summary

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    mock_requests_get.return_value = mock_response

    result = fetch_summary("192.168.1.1", "admin")

    assert result is None
    mock_logger.error.assert_called_once()
    assert "Error fetching data from 192.168.1.1" in mock_logger.error.call_args[0][0]


def test_fetch_summary_timeout(mock_logger, mock_requests_get):
    from antminer_exporter.client import fetch_summary

    mock_requests_get.side_effect = requests.exceptions.Timeout()

    result = fetch_summary("192.168.1.1", "admin")

    assert result is None
    mock_logger.error.assert_called_once()


def test_fetch_summary_invalid_json(mock_logger, mock_requests_get):
    from antminer_exporter.client import fetch_summary

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests_get.return_value = mock_response

    result = fetch_summary("192.168.1.1", "admin")

    assert result is None
    mock_logger.error.assert_called_once()


def test_fetch_metrics_success(mock_logger, mock_requests_get):
    from antminer_exporter.client import fetch_metrics

    # Mock successful response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "metrics": [{"data": {"hashrate": 0.1, "chip_max_temp": 1073741824}}],
        "timezone": "GMT+1",
    }
    mock_requests_get.return_value = mock_response

    result = fetch_metrics("192.168.1.1", "admin")

    assert result["timezone"] == "GMT+1"
    assert "metrics" in result
    mock_logger.error.assert_not_called()
    # Verify correct URL
    mock_requests_get.assert_called_once_with(
        "http://192.168.1.1/metrics",
        auth=("root", "admin"),
        timeout=5,
    )


def test_fetch_metrics_error(mock_logger, mock_requests_get):
    from antminer_exporter.client import fetch_metrics

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    mock_requests_get.return_value = mock_response

    result = fetch_metrics("192.168.1.1", "admin")

    assert result is None
    mock_logger.error.assert_called_once()
    assert "Error fetching metrics from 192.168.1.1" in mock_logger.error.call_args[0][0]


def test_fetch_metrics_timeout(mock_logger, mock_requests_get):
    from antminer_exporter.client import fetch_metrics

    mock_requests_get.side_effect = requests.exceptions.Timeout()

    result = fetch_metrics("192.168.1.1", "admin")

    assert result is None
    mock_logger.error.assert_called_once()
