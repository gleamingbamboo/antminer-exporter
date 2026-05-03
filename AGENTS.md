# AGENTS.md

## Package Management
Uses `uv` (not pip). Key commands:
- `uv sync` to install dependencies
- `uv add <package>` to add new dependencies
- `uv run <script>` to execute scripts with project dependencies

## Key Commands
- Run the Prometheus exporter: `uv run app.py` (serves metrics on `:9100`)
- Generate Grafana dashboard: `cd scripts; uv run generate_dashboard.py` (outputs `scripts/dashboard.json`)

## Architecture
- Entry point: `app.py` (polls configured miners on a loop)
- Miner config: `config.py` (IPs, passwords, poll interval)
- Miner API client: `client.py` calls `http://{ip}/api/v1/summary` with `root:{password}` HTTP basic auth
- Metrics: `metrics.py` defines Prometheus gauges (hashrate, temp, fan)

## Notable Dependencies
- `pyasic` is listed in `pyproject.toml` but not imported anywhere in the codebase

## Gaps
No tests, linting, typechecking, or CI configuration present
