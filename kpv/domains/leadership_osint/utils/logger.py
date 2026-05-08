import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str, data_root: str = "./kpv_data") -> logging.Logger:
    """
    Returns a configured logger for the KPV system.
    Ensures:
      - consistent formatting
      - rotating file logs
      - console output
      - no duplicate handlers
    """

    logger = logging.getLogger(name)

    # If already configured, return it
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Ensure log directory exists
    log_dir = Path(data_root).resolve() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # File handler (rotating)
    # ------------------------------------------------------------
    file_handler = RotatingFileHandler(
        log_dir / "kpv.log",
        maxBytes=10_000_000,   # 10 MB
        backupCount=5,
        encoding="utf-8"
    )

    # ------------------------------------------------------------
    # Console handler
    # ------------------------------------------------------------
    console_handler = logging.StreamHandler()

    # ------------------------------------------------------------
    # Formatter
    # ------------------------------------------------------------
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
