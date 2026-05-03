import time

from prometheus_client import start_http_server

from client import fetch_summary
from config import MINERS, POLL_INTERVAL
from logger import logger
from metrics import fan, hashrate, temp


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


def main():
    start_http_server(9100)
    logger.info("Exporter started on :9100")

    while True:
        for miner in MINERS:
            ip = miner["ip"]
            password = miner["password"]

            logger.debug(f"Fetching data from {ip}")
            data = fetch_summary(ip, password)
            if data:
                process(ip, data)
            else:
                logger.warning(f"No data received from {ip}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
