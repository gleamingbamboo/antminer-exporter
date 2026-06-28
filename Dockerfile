# Stage 1: Builder - Install dependencies
FROM python:3.12-slim as builder

WORKDIR /app

# Copy pyproject files first to leverage Docker caching
COPY pyproject.toml uv.lock ./

# Use uv to install dependencies for the build stage
RUN pip install --no-cache-dir uv && \
    uv sync --system # Assuming uv sync handles all necessary installs and virtual env setup

# Stage 2: Runner - Set up the final lightweight image
FROM python:3.12-slim as runner

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy source code (this includes antminer_exporter/, scripts/, tests/)
COPY . /app

# Expose the default Prometheus port
EXPOSE 9222

# Define the entrypoint script to handle startup logic
# This runs the exporter via uv run
CMD ["uv", "run", "antminer-exporter"]