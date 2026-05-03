# antminer-exporter

Prometheus exporter for ASIC miners. Polls miner HTTP APIs at configured intervals and exposes hashrate, temperature, and fan speed metrics on port 9100. Includes a Grafana dashboard generator.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
uv sync
```

## Configuration

Copy the example config:

```bash
cp config.py.example config.py
```

Then edit `config.py` to add miner IPs, passwords, and adjust the poll interval:

```python
MINERS = [
    {"ip": "miner-ip", "password": "miner-password"},
]
POLL_INTERVAL = 10  # seconds
```

### Logging Configuration

Configure logging in `config.py`:

```python
LOG_ENABLED = True          # Enable/disable logging
LOG_LEVEL = "INFO"          # Log level: DEBUG, INFO, WARNING, ERROR
LOGS_DIR = "./logs"         # Directory for log files
```

Logs are written to `antminer-exporter.log` in the specified directory with rotation (10 MB) and retention (30 days).

Uses miner API endpoint `http://{ip}/api/v1/summary` with HTTP basic auth `root:{password}`.

## Run Exporter

```bash
uv run app.py
```

Metrics available at `http://localhost:9100/metrics`.

## Docker

### Prerequisites
- Docker and Docker Compose installed

### Build and Run with Docker Compose
```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Run with Docker (Manual)
```bash
# Build the image
docker build -t antminer-exporter .

# Run the container
docker run -d -p 9100:9100 --name antminer-exporter \
  -v ./config.py:/app/config.py \
  -v ./logs:/app/logs \
  antminer-exporter
```

### Custom Configuration
- Mount a custom `config.py` to `/app/config.py` to override miner settings, log level, etc.
- Logs are written to `./logs` on the host machine by default (via volume mount).

## Generate Grafana Dashboard

```bash
cd scripts
uv run generate_dashboard.py
```

Outputs `scripts/dashboard.json` ready to import into Grafana.

## Exposed Metrics

| Metric | Description | Labels |
|--------|-------------|--------|
| `asic_hashrate` | Instant hashrate (TH/s) | `ip` |
| `asic_temp` | Maximum chip temperature (°C) | `ip` |
| `asic_fan` | Average fan RPM | `ip` |
