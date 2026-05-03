FROM python:3.12-slim

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files first (leverage Docker layer caching)
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv sync

# Copy all project files
COPY . .

# Create default config from example
RUN cp config.py.example antminer_exporter/config.py

# Create logs directory
RUN mkdir -p /app/logs

# Expose Prometheus metrics port
EXPOSE 9100

# Start the exporter
CMD ["uv", "run", "python", "-m", "antminer_exporter.app"]
