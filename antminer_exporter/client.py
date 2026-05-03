import requests

from .logger import logger


def fetch_summary(ip, password):
    try:
        url = f"http://{ip}/api/v1/summary"

        r = requests.get(url, auth=("root", password), timeout=5)

        r.raise_for_status()
        return r.json()

    except Exception as e:
        logger.error(f"Error fetching data from {ip}: {e}")
        return None


def fetch_metrics(ip, password):
    try:
        url = f"http://{ip}/metrics"
        r = requests.get(url, auth=("root", password), timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Error fetching metrics from {ip}: {e}")
        return None


class MinerClient:
    """Client for ASIC miner API with unlock support."""

    def __init__(self, ip: str, password: str):
        self.ip = ip
        self.password = password
        self.token = None
        self.base_url = f"http://{ip}"

    def unlock(self) -> bool:
        """Unlock miner with password, returns True if successful."""
        try:
            url = f"{self.base_url}/api/v1/unlock"
            response = requests.post(
                url,
                json={"pw": self.password},
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                logger.debug(f"Unlocked {self.ip}, token: {self.token[:8] if self.token else 'None'}...")
                return True
            elif response.status_code == 403:
                logger.error(f"Wrong password for {self.ip}")
            else:
                logger.error(f"Unlock failed for {self.ip}: {response.status_code}")
        except Exception as e:
            logger.error(f"Unlock error for {self.ip}: {e}")
        return False

    def _get_headers(self) -> dict:
        """Return headers with token if available."""
        headers: dict[str, str] = {}
        if self.token:
            # Use token - need to check how miner expects it (cookie, header, etc.)
            # Based on typical patterns, might be sent as cookie or auth header
            pass
        return headers

    def fetch_summary(self):
        """Fetch from /api/v1/summary with auth."""
        try:
            url = f"{self.base_url}/api/v1/summary"
            response = requests.get(
                url,
                auth=("root", self.password),
                timeout=5,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching summary from {self.ip}: {e}")
            return None

    def fetch_metrics(self):
        """Fetch from /api/v1/metrics with auth."""
        try:
            url = f"{self.base_url}/api/v1/metrics"
            response = requests.get(
                url,
                auth=("root", self.password),
                timeout=5,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching metrics from {self.ip}: {e}")
            return None
