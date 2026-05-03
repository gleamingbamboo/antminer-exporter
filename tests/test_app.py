from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_miner_data():
    return {
        "miner": {
            "instant_hashrate": 100.5,
            "chip_temp": {"max": 75},
            "cooling": {"fans": [{"rpm": 3000}, {"rpm": 3200}, {"rpm": 3100}, {"rpm": 2900}]},
        }
    }


def test_process_valid_data(mocker, sample_miner_data):
    from app import process

    # Mock metrics
    mock_hashrate = MagicMock()
    mock_temp = MagicMock()
    mock_fan = MagicMock()

    mocker.patch("app.hashrate", mock_hashrate)
    mocker.patch("app.temp", mock_temp)
    mocker.patch("app.fan", mock_fan)

    # Mock logger
    mock_logger = mocker.patch("app.logger")

    ip = "192.168.1.1"
    process(ip, sample_miner_data)

    # Check hashrate metrics
    mock_hashrate.labels.assert_called_once_with(ip=ip)
    mock_hashrate.labels.return_value.set.assert_called_once_with(100.5)

    # Check temp metrics
    mock_temp.labels.assert_called_once_with(ip=ip)
    mock_temp.labels.return_value.set.assert_called_once_with(75)

    # Check fan metrics (average: (3000+3200+3100+2900)/4 = 3050)
    mock_fan.labels.assert_called_once_with(ip=ip)
    mock_fan.labels.return_value.set.assert_called_once_with(3050)

    # Check logger.debug called
    mock_logger.debug.assert_called_once()
    assert f"Updated metrics for {ip}" in mock_logger.debug.call_args[0][0]


def test_process_no_fans(mocker):
    from app import process

    mock_fan = MagicMock()
    mocker.patch("app.fan", mock_fan)
    mocker.patch("app.hashrate")
    mocker.patch("app.temp")
    mock_logger = mocker.patch("app.logger")

    ip = "192.168.1.1"
    data = {"miner": {"instant_hashrate": 50.0, "chip_temp": {"max": 60}, "cooling": {"fans": []}}}
    process(ip, data)

    # Fan should be set to 0
    mock_fan.labels.return_value.set.assert_called_once_with(0)
    mock_logger.debug.assert_called_once()


def test_process_parse_error(mocker):
    from app import process

    mock_logger = mocker.patch("app.logger")
    mocker.patch("app.hashrate")
    mocker.patch("app.temp")
    mocker.patch("app.fan")

    ip = "192.168.1.1"
    process(ip, None)  # Malformed data

    mock_logger.error.assert_called_once()
    assert f"Parse error for {ip}" in mock_logger.error.call_args[0][0]
