import time

import requests
from loguru import logger

from antminer_exporter.app import scale_fixed_point
from antminer_exporter.client import fetch_metrics, fetch_summary
from antminer_exporter.config import (
    MINERS,
    POLL_INTERVAL,
    VICTORIA_METRICS_TOKEN,
    VICTORIA_METRICS_URL,
)


def metrics_to_prometheus(ip, metrics_data):
    """Convert ASIC /metrics JSON to Prometheus exposition format."""
    lines = []
    metrics_array = metrics_data.get("metrics", [])
    if not metrics_array:
        return ""

    latest = metrics_array[-1]
    d = latest.get("data", {})

    # Scale fixed-point values (30 fractional bits)
    chip_temp = scale_fixed_point(d.get("chip_max_temp", 0))
    pcb_temp = scale_fixed_point(d.get("pcb_max_temp", 0))
    fan_duty = scale_fixed_point(d.get("fan_duty", 0))
    power_w = scale_fixed_point(d.get("power_consumption", 0))
    hr = d.get("hashrate", 0)

    # Prometheus format
    lines.append("# HELP asic_chip_temp Chip max temperature (°C)")
    lines.append("# TYPE asic_chip_temp gauge")
    lines.append(f'asic_chip_temp{{ip="{ip}"}} {chip_temp}')

    lines.append("# HELP asic_pcb_temp PCB max temperature (°C)")
    lines.append("# TYPE asic_pcb_temp gauge")
    lines.append(f'asic_pcb_temp{{ip="{ip}"}} {pcb_temp}')

    lines.append("# HELP asic_fan_duty Fan duty percentage")
    lines.append("# TYPE asic_fan_duty gauge")
    lines.append(f'asic_fan_duty{{ip="{ip}"}} {fan_duty}')

    lines.append("# HELP asic_power_watts Power consumption (W)")
    lines.append("# TYPE asic_power_watts gauge")
    lines.append(f'asic_power_watts{{ip="{ip}"}} {power_w}')

    lines.append("# HELP asic_hashrate Instant hashrate (TH/s)")
    lines.append("# TYPE asic_hashrate gauge")
    lines.append(f'asic_hashrate{{ip="{ip}"}} {hr}')

    return "\n".join(lines)


def process_miner(ip, password):
    """Fetch metrics from a single miner and return Prometheus format string."""
    # Try /metrics endpoint first
    data = fetch_metrics(ip, password)
    if data:
        return metrics_to_prometheus(ip, data)

    # Fallback to /api/v1/summary
    data = fetch_summary(ip, password)
    if data:
        lines = []
        miner = data.get("miner", {})
        hr = miner.get("instant_hashrate", 0)
        temp_max = miner.get("chip_temp", {}).get("max", 0)
        fans = miner.get("cooling", {}).get("fans", [])
        avg_fan = sum(f["rpm"] for f in fans) / len(fans) if fans else 0

        lines.append("# HELP asic_hashrate Instant hashrate (TH/s)")
        lines.append("# TYPE asic_hashrate gauge")
        lines.append(f'asic_hashrate{{ip="{ip}"}} {hr}')

        lines.append("# HELP asic_temp Maximum chip temperature (°C)")
        lines.append("# TYPE asic_temp gauge")
        lines.append(f'asic_temp{{ip="{ip}"}} {temp_max}')

        lines.append("# HELP asic_fan Average fan RPM")
        lines.append("# TYPE asic_fan gauge")
        lines.append(f'asic_fan{{ip="{ip}"}} {avg_fan}')

        return "\n".join(lines)

    return ""


def push_to_victoriametrics(metrics_text):
    """Push Prometheus format metrics to VictoriaMetrics."""
    try:
        headers = {"Content-Type": "text/plain"}
        params = {}
        if VICTORIA_METRICS_TOKEN:
            params["token"] = VICTORIA_METRICS_TOKEN

        response = requests.post(
            VICTORIA_METRICS_URL,
            data=metrics_text,
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        logger.debug(f"Pushed {len(metrics_text)} bytes to VictoriaMetrics")

    except Exception as e:
        logger.error(f"Failed to push to VictoriaMetrics: {e}")


def main():
    logger.info(f"VictoriaMetrics uploader started, pushing to: {VICTORIA_METRICS_URL}")
    logger.info(f"Polling interval: {POLL_INTERVAL}s")

    while True:
        all_metrics = []
        for miner in MINERS:
            ip = miner["ip"]
            password = miner["password"]

            logger.debug(f"Fetching metrics from {ip}")
            metrics_text = process_miner(ip, password)
            if metrics_text:
                all_metrics.append(metrics_text)
            else:
                logger.warning(f"No data from {ip}")

        if all_metrics:
            combined = "\n\n".join(all_metrics)
            push_to_victoriametrics(combined)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
