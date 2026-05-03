import requests

from logger import logger


def fetch_summary(ip, password):
    try:
        url = f"http://{ip}/api/v1/summary"

        r = requests.get(url, auth=("root", password), timeout=5)

        r.raise_for_status()
        return r.json()

    except Exception as e:
        logger.error(f"Error fetching data from {ip}: {e}")
        return None
