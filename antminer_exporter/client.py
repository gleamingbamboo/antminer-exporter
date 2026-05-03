import requests

from .logger import logger


class MinerClient:
    """Client for ASIC miner API with unlock support."""

    def __init__(self, ip: str, password: str):
        self.ip = ip
        self.password = password
        self.token = None
        self.base_url = f"http://{ip}"

    def _url(self, endpoint: str) -> str:
        """Build full URL for a given API endpoint."""
        return f"{self.base_url}{endpoint}"

    def unlock(self) -> bool:
        """Unlock miner with password, returns True if successful."""
        try:
            url = self._url("/api/v1/unlock")
            response = requests.post(
                url,
                json={"pw": self.password},
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                token_str = self.token[:8] if self.token else "None"
                logger.debug(f"Unlocked {self.ip}, token: {token_str}...")
                return True
            elif response.status_code == 403:
                logger.error(f"Wrong password for {self.ip}")
            else:
                logger.error(f"Unlock failed for {self.ip}: {response.status_code}")
        except Exception as e:
            logger.error(f"Unlock error for {self.ip}: {e}")
        return False

    def _get_headers(self) -> dict[str, str]:
        """Return headers with token if available."""
        headers: dict[str, str] = {}
        if self.token:
            # Token might be used as cookie or auth header - check per miner model
            pass
        return headers

    def fetch_summary(self):
        """Fetch from /api/v1/summary with auth."""
        try:
            url = self._url("/api/v1/summary")
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
            url = self._url("/api/v1/metrics")
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
