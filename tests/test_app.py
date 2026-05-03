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


@pytest.fixture
def sample_metrics_data():
    return {
        "annotations": [{"data": {"chain_id": 1073741824, "type": "start"}, "time": 9007199254740991}],
        "metrics": [
            {
                "data": {
                    "chip_max_temp": 1073741824,  # 1.0 after scaling
                    "fan_duty": 1073741824,  # 1.0
                    "hashrate": 0.1,
                    "pcb_max_temp": 1073741824,  # 1.0
                    "power_consumption": 1073741824,  # 1.0
                },
                "time": 9007199254740991,
            }
        ],
        "timezone": "GMT+1",
    }


def test_process_valid_data(mocker, sample_miner_data):
    from antminer_exporter.app import process

    # Mock metrics
    mock_hashrate = MagicMock()
    mock_temp = MagicMock()
    mock_fan = MagicMock()

    mocker.patch("antminer_exporter.app.hashrate", mock_hashrate)
    mocker.patch("antminer_exporter.app.temp", mock_temp)
    mocker.patch("antminer_exporter.app.fan", mock_fan)

    # Mock logger
    mock_logger = mocker.patch("antminer_exporter.app.logger")

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
    from antminer_exporter.app import process

    mock_fan = MagicMock()
    mocker.patch("antminer_exporter.app.fan", mock_fan)
    mocker.patch("antminer_exporter.app.hashrate")
    mocker.patch("antminer_exporter.app.temp")
    mock_logger = mocker.patch("antminer_exporter.app.logger")

    ip = "192.168.1.1"
    data = {"miner": {"instant_hashrate": 50.0, "chip_temp": {"max": 60}, "cooling": {"fans": []}}}
    process(ip, data)

    # Fan should be set to 0
    mock_fan.labels.return_value.set.assert_called_once_with(0)
    mock_logger.debug.assert_called_once()


def test_process_parse_error(mocker):
    from antminer_exporter.app import process

    mock_logger = mocker.patch("antminer_exporter.app.logger")
    mocker.patch("antminer_exporter.app.hashrate")
    mocker.patch("antminer_exporter.app.temp")
    mocker.patch("antminer_exporter.app.fan")

    ip = "192.168.1.1"
    process(ip, None)  # Malformed data

    mock_logger.error.assert_called_once()
    assert f"Parse error for {ip}" in mock_logger.error.call_args[0][0]


def test_process_metrics_valid_data(mocker, sample_metrics_data):
    from antminer_exporter.app import process_metrics

    # Mock new metrics
    mock_chip_temp = MagicMock()
    mock_pcb_temp = MagicMock()
    mock_fan_duty = MagicMock()
    mock_power = MagicMock()
    mock_hashrate = MagicMock()

    mocker.patch("antminer_exporter.app.chip_temp", mock_chip_temp)
    mocker.patch("antminer_exporter.app.pcb_temp", mock_pcb_temp)
    mocker.patch("antminer_exporter.app.fan_duty", mock_fan_duty)
    mocker.patch("antminer_exporter.app.power", mock_power)
    mocker.patch("antminer_exporter.app.hashrate", mock_hashrate)

    mock_logger = mocker.patch("antminer_exporter.app.logger")

    ip = "192.168.1.1"
    process_metrics(ip, sample_metrics_data)

    # Check scaled values (1073741824 / 2^30 = 1.0)
    mock_chip_temp.labels.assert_called_once_with(ip=ip)
    mock_chip_temp.labels.return_value.set.assert_called_once_with(1.0)

    mock_pcb_temp.labels.assert_called_once_with(ip=ip)
    mock_pcb_temp.labels.return_value.set.assert_called_once_with(1.0)

    mock_fan_duty.labels.assert_called_once_with(ip=ip)
    mock_fan_duty.labels.return_value.set.assert_called_once_with(1.0)

    mock_power.labels.assert_called_once_with(ip=ip)
    mock_power.labels.return_value.set.assert_called_once_with(1.0)

    # Hashrate is already a float
    mock_hashrate.labels.assert_called_once_with(ip=ip)
    mock_hashrate.labels.return_value.set.assert_called_once_with(0.1)

    # Check logger.debug called
    mock_logger.debug.assert_called_once()


def test_process_metrics_no_data(mocker):
    from antminer_exporter.app import process_metrics

    mock_logger = mocker.patch("antminer_exporter.app.logger")

    ip = "192.168.1.1"
    process_metrics(ip, {"metrics": []})  # Empty metrics

    mock_logger.warning.assert_called_once()
    assert "No metrics data" in mock_logger.warning.call_args[0][0]


def test_scale_fixed_point():
    from antminer_exporter.app import scale_fixed_point

    assert scale_fixed_point(1073741824) == 1.0  # 2^30
    assert scale_fixed_point(0) == 0
    assert scale_fixed_point(None) == 0
    assert scale_fixed_point(2147483648) == 2.0  # 2 * 2^30
