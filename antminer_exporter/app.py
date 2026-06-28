import time

from prometheus_client import start_http_server

from antminer_exporter.client import MinerClient
from antminer_exporter.logger import logger
from antminer_exporter.metrics import chip_temp, fan, fan_duty, hashrate, pcb_temp, power, temp
from antminer_exporter.utils import load_yaml


def scale_fixed_point(value, scale=2**30):
    """Convert fixed-point value (30 fractional bits) to float."""
    # return value / scale if value else 0
    return value


def process(ip, data):
    try:
        miner = data.get("miner", {})

        # --- Hashrate ---
        hr = miner.get("instant_hashrate", 0)  # TH/s

        # --- Temps ---
        temp_max = miner.get("chip_temp", {}).get("max", 0)

        # --- Fan (average RPM) ---
        fans = miner.get("cooling", {}).get("fans", [])
        if fans:
            avg_fan = sum(f["rpm"] for f in fans) / len(fans)
        else:
            avg_fan = 0

        # --- Metrics ---
        hashrate.labels(ip=ip).set(hr)
        temp.labels(ip=ip).set(temp_max)
        fan.labels(ip=ip).set(avg_fan)

        logger.debug(f"Updated metrics for {ip}: hashrate={hr}, temp={temp_max}, fan={avg_fan}")

    except Exception as e:
        logger.error(f"Parse error for {ip}: {e}")


def process_metrics(ip, data):
    try:
        metrics_array = data.get("metrics", [])
        if not metrics_array:
            logger.warning(f"No metrics data for {ip}")
            return

        # Get the latest metrics entry
        latest = metrics_array[-1]
        d = latest.get("data", {})

        # Scale fixed-point values (30 fractional bits)
        chip = scale_fixed_point(d.get("chip_max_temp", 0))
        pcb = scale_fixed_point(d.get("pcb_max_temp", 0))
        duty = scale_fixed_point(d.get("fan_duty", 0))
        power_w = scale_fixed_point(d.get("power_consumption", 0))
        hr = d.get("hashrate", 0)  # Already float

        # Update metrics
        chip_temp.labels(ip=ip).set(chip)
        pcb_temp.labels(ip=ip).set(pcb)
        fan_duty.labels(ip=ip).set(duty)
        power.labels(ip=ip).set(power_w)
        hashrate.labels(ip=ip).set(hr)

        logger.debug(
            f"Metrics for {ip}: chip={chip:.2f}°C, pcb={pcb:.2f}°C, "
            f"duty={duty:.1f}%, power={power_w:.1f}W, hashrate={hr} TH/s"
        )

    except Exception as e:
        logger.error(f"Metrics parse error for {ip}: {e}")


def main():
    start_http_server(9222)
    logger.info("Exporter started on :9222")

    while True:
        MINERS = load_yaml('../miners.yml')
        for ip, password in MINERS.items():
            # ip = miner["ip"]
            # password = miner["password"]

            logger.debug(f"Fetching data from {ip}")
            # Use MinerClient
            client = MinerClient(ip, password)
            # Optionally unlock
            # client.unlock()

            # Try new /api/v1/metrics endpoint first, fallback to /api/v1/summary
            data = client.fetch_metrics()
            if data:
                process_metrics(ip, data)
            else:
                data = client.fetch_summary()
                if data:
                    process(ip, data)
                else:
                    logger.warning(f"No data received from {ip}")

        time.sleep(10)


if __name__ == "__main__":
    main()
