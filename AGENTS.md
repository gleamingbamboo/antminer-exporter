# AGENTS.md

## Quick Start

**Commands (from repo root):**
```bash
uv sync                          # Install deps (uses uv, not pip)
uv run tox                        # Run all tests + lint + typecheck
uv run antminer-exporter          # Start Prometheus exporter (:9100)
cd scripts && uv run uploader.py   # Run VictoriaMetrics uploader
```

**CRITICAL**: Always use `uv run` prefix - this project uses `uv` package manager.

---

## Architecture

**Package**: `antminer_exporter/` (not root-level files anymore)
- `app.py` - Prometheus HTTP server, `process()`, `process_metrics()`
- `client.py` - `MinerClient` class + backward-compatible standalone functions
- `metrics.py` - Prometheus Gauges (asic_hashrate, asic_temp, asic_chip_temp, etc.)
- `logger.py` - Loguru setup (auto-configures on import)
- `config.py.example` - Template (copy to `config.py`, NOT tracked by git)

**scripts/**
- `uploader.py` - Fetches from miners → pushes to VictoriaMetrics via `prometheus_client`
- `generate_dashboard.py` - Generates Grafana dashboard JSON

**tests/**
- `test_app.py` - Tests for `process()`, `process_metrics()`, `scale_fixed_point()`
- `test_client.py` - Tests for `MinerClient` class (unlock, fetch_metrics, fetch_summary)

---

## Key Configuration

**File**: `antminer_exporter/config.py` (copied from `config.py.example`)
```python
MINERS = [{"ip": "miner-ip", "password": "password"}, ...]
POLL_INTERVAL = 10  # seconds

# VictoriaMetrics
VICTORIA_METRICS_URL = "http://localhost:8428/api/v1/import/prometheus"
VICTORIA_METRICS_TOKEN = ""  # Optional bearer token

# Logging
LOG_ENABLED = True
LOG_LEVEL = "INFO"
LOGS_DIR = "./logs"
```

**GITIGNORE**: `config.py` is NOT tracked. Never commit it. Copy from `config.py.example`.

---

## Testing

**Framework**: `pytest` + `pytest-mock` + `pytest-cov`

**Run specific test:**
```bash
uv run pytest tests/test_client.py::test_unlock_success -v
uv run pytest tests/ -v
```

**Tox environments** (defined in `tox.ini`):
- `py312` - Runs pytest with coverage
- `ruff` - Lint + format check
- `mypy` - Type checking

**Order for CI**: `ruff → mypy → py312` (lint first, then typecheck, then tests)

**Current coverage**: ~70% (missing lines in `app.py` main loop)

---

## MinerClient Class (`antminer_exporter/client.py`)

**Use this pattern:**
```python
from antminer_exporter.client import MinerClient

client = MinerClient("192.168.1.1", "admin")
# Optional: client.unlock()  # POST /api/v1/unlock

# Try /api/v1/metrics first, fallback to /api/v1/summary
data = client.fetch_metrics()  # GET /api/v1/metrics
# or: data = client.fetch_summary()  # GET /api/v1/summary
```

**Backward compatible**: `fetch_summary(ip, password)` and `fetch_metrics(ip, password)` still work.

---

## Metrics & Endpoints

**Prometheus metrics** (defined in `antminer_exporter/metrics.py`):
- `asic_hashrate` (TH/s), `asic_temp` (°C) - from `/api/v1/summary`
- `asic_chip_temp`, `asic_pcb_temp` (°C) - from `/api/v1/metrics`
- `asic_fan_duty` (%), `asic_power_watts` (W) - from `/api/v1/metrics`

**Fixed-point scaling**: Values from `/api/v1/metrics` use 30 fractional bits:
```python
def scale_fixed_point(value, scale=2**30):
    return value / scale if value else 0
```

**VictoriaMetrics uploader** (`scripts/uploader.py`):
- Uses `prometheus_client` library (Gauges + `generate_latest(REGISTRY)`)
- Pushes to VictoriaMetrics at `VICTORIA_METRICS_URL`
- Runs in infinite loop with `POLL_INTERVAL` sleep

---

## CI/CD (`.github/workflows/ci.yml`)

**Jobs** (run on push/PR to `master`):
1. `test` (tox:py312) - runs pytest
2. `lint` (tox:ruff) - ruff check + format
3. `typecheck` (tox:mypy) - mypy type checking
4. `build-and-push` - Docker build + push to `gleamingbamboo/antminer-exporter` (only if 1-3 pass)

**Required secrets**:
- `DOCKERHUB_USERNAME`: `gleamingbamboo`
- `DOCKERHUB_TOKEN`: DockerHub access token

---

## Common Gotchas

1. **Quote characters**: The Write tool sometimes converts `"` to `"` (smart quotes). Always run `uv run ruff check --fix .` after editing.

2. **Import paths**: Use relative imports within package (`from .logger import logger`), absolute from outside (`from antminer_exporter.client import MinerClient`).

3. **Endpoint URLs**: Miner API uses `/api/v1/metrics` (NOT `/metrics`). The exporter exposes Prometheus metrics at `:9100/metrics`.

4. **Config file**: Never import `config.py` directly - it's in `.gitignore`. Copy from `config.py.example` and edit.

5. **Token auth**: Miner unlock returns `{"token": "..."}` on success. The token *might* be used in cookies/headers - investigate per miner model.

---

## Quick Reference

| Task | Command |
|------|---------|
| Install deps | `uv sync` |
| Run exporter | `uv run antminer-exporter` |
| Run uploader | `cd scripts && uv run uploader.py` |
| Lint | `uv run ruff check .` |
| Fix lint | `uv run ruff check --fix .` |
| Typecheck | `uv run mypy antminer_exporter/` |
| Test all | `uv run tox` |
| Test single | `uv run pytest tests/test_client.py -v` |
| Build Docker | `docker build -t antminer-exporter .` |
| Generate dashboard | `cd scripts && uv run generate_dashboard.py` |

---

**Last updated**: 2026-05-03 (after MinerClient refactor + VictoriaMetrics uploader update)
