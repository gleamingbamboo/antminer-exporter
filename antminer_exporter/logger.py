from pathlib import Path

from loguru import logger

from .config import LOG_ENABLED, LOG_LEVEL, LOGS_DIR

if LOG_ENABLED:
    log_dir = Path(LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / "antminer-exporter.log",
        level=LOG_LEVEL,
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )
else:
    logger.disable("antminer_exporter")
