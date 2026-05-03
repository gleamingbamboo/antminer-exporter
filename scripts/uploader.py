import time

import requests
from loguru import logger
from prometheus_client import REGISTRY, Gauge, generate_latest

from antminer_exporter.app import scale_fixed_point
from antminer_exporter.config import (
    MINERS,
    POLL_INTERVAL,
    VICTORIA_METRICS_TOKEN,
    VICTORIA_METRICS_URL,
)

# Define Prometheus Gauges for VictoriaMetrics upload
# These will be auto-collected by generate_latest(REGISTRY)
asic_chip_temp = Gauge('asic_chip_temp', 'Chip max temperature (°C)', ['ip'])
asic_pcb_temp = Gauge('asic_pcb_temp', 'PCB max temperature (°C)', ['ip'])
asic_fan_duty = Gauge('asic_fan_duty', 'Fan duty percentage', ['ip'])
asic_power_watts = Gauge('asic_power_watts', 'Power consumption (W)', ['ip'])
asic_hashrate = Gauge('asic_hashrate', 'Instant hashrate (TH/s)', ['ip'])
# Keep backward compatible ones
asic_temp = Gauge('asic_temp', 'Temperature', ['ip'])
asic_fan = Gauge('asic_fan', 'Fan speed', ['ip'])


def process_miner_data(ip: str, data: dict, source: str = "metrics"):
    """Process miner data and set Prometheus gauge values."""
    try:
        if source == "metrics":
            # New /api/v1/metrics format
            metrics_array = data.get("metrics", [])
            if not metrics_array:
                return

            latest = metrics_array[-1]
            d = latest.get("data", {})
            
            # Scale fixed-point values (30 fractional bits)
            chip = scale_fixed_point(d.get("chip_max_temp", 0))
            pcb = scale_fixed_point(d.get("pcb_max_temp", 0))
            duty = scale_fixed_point(d.get("fan_duty", 0))
            power_w = scale_fixed_point(d.get("power_consumption", 0))
            hr = d.get("hashrate", 0)
            
            # Set gauge values
            asic_chip_temp.labels(ip=ip).set(chip)
            asic_pcb_temp.labels(ip=ip).set(pcb)
            asic_fan_duty.labels(ip=ip).set(duty)
            asic_power_watts.labels(ip=ip).set(power_w)
            asic_hashrate.labels(ip=ip).set(hr)
            
            logger.debug(f"Processed /metrics for {ip}: chip={chip:.2f}°C")
            
        else:
            # Old /api/v1/summary format
            miner = data.get("miner", {})
            hr = miner.get("instant_hashrate", 0)
            temp_max = miner.get("chip_temp", {}).get("max", 0)
            fans = miner.get("cooling", {}).get("fans", [])
            avg_fan = sum(f["rpm"] for f in fans) / len(fans) if fans else 0
            
            asic_hashrate.labels(ip=ip).set(hr)
            asic_temp.labels(ip=ip).set(temp_max)
            asic_fan.labels(ip=ip).set(avg_fan)
            
            logger.debug(f"Processed summary for {ip}: hashrate={hr}")
            
    except Exception as e:
        logger.error(f"Error processing data for {ip}: {e}")


def push_to_victoriametrics():
    """Push Prometheus-format metrics to VictoriaMetrics."""
    try:
        # Generate properly formatted Prometheus exposition text
        metrics_data = generate_latest(REGISTRY)
        
        headers = {"Content-Type": "text/plain"}
        params = {}
        if VICTORIA_METRICS_TOKEN:
            params["token"] = VICTORIA_METRICS_TOKEN

        response = requests.post(
            VICTORIA_METRICS_URL,
            data=metrics_data,
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        logger.debug(f"Pushed {len(metrics_data)} bytes to VictoriaMetrics")

    except Exception as e:
        logger.error(f"Failed to push to VictoriaMetrics: {e}")


def main():
    logger.info(f"VictoriaMetrics uploader started, pushing to: {VICTORIA_METRICS_URL}")
    logger.info(f"Poll interval: {POLL_INTERVAL}s")

    while True:
        for miner in MINERS:
            ip = miner["ip"]
            password = miner["password"]
            
            logger.debug(f"Fetching from {ip}")
            
            # Try new /api/v1/metrics first
            try:
                url = f"http://{ip}/api/v1/metrics"
                r = requests.get(url, auth=("root", password), timeout=5)
                r.raise_for_status()
                data = r.json()
                if data:
                    process_miner_data(ip, data, "metrics")
                    continue
            except Exception:
                pass  # Fall back to summary
            
            # Fallback to /api/v1/summary
            try:
                url = f"http://{ip}/api/v1/summary"
                r = requests.get(url, auth=("root", password), timeout=5)
                r.raise_for_status()
                data = r.json()
                if data:
                    process_miner_data(ip, data, "summary")
                else:
                    logger.warning(f"No data from {ip}")
            except Exception as e:
                logger.warning(f"No data from {ip}: {e}")
        
        # Push all collected metrics to VictoriaMetrics
        push_to_victoriametrics()
        
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
