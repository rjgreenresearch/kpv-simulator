"""
kpvs/logging_config.py
======================
Centralised logging for KPVS.

Levels:  DEBUG (per-iteration) | INFO (run-level) | WARNING | ERROR | CRITICAL
File handler always captures DEBUG; console mirrors CLI --log-level flag.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path

CONSOLE_FMT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
FILE_FMT    = ("%(asctime)s [%(levelname)-8s] %(name)s "
               "(%(filename)s:%(lineno)d): %(message)s")
DATE_FMT    = "%Y-%m-%d %H:%M:%S"
VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def configure_logging(
    level: str = "INFO",
    log_file: str | None = None,
    log_dir:  str = "logs",
    quiet:    bool = False,
) -> logging.Logger:
    """
    Configure the root logger.

    Parameters
    ----------
    level    : console log level (default INFO).
    log_file : explicit path; None → auto-generate in log_dir;
               '' → suppress file logging.
    log_dir  : directory for auto-generated log files.
    quiet    : suppress console output entirely.
    """
    level = level.upper()
    if level not in VALID_LEVELS:
        raise ValueError(f"Invalid level '{level}'. Choose: {sorted(VALID_LEVELS)}")

    root = logging.getLogger()
    root.setLevel(getattr(logging, level))
    root.handlers.clear()

    if not quiet:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(getattr(logging, level))
        ch.setFormatter(logging.Formatter(CONSOLE_FMT, datefmt=DATE_FMT))
        root.addHandler(ch)

    if log_file != "":
        if log_file is None:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"kpvs_{ts}.log")

        fh = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(FILE_FMT, datefmt=DATE_FMT))
        root.addHandler(fh)
        logging.getLogger("kpvs").info("File logging → %s", log_file)

    return root


def get_run_logger(run_id: str) -> logging.Logger:
    """Return a child logger namespaced to a specific simulation run."""
    return logging.getLogger(f"kpvs.run.{run_id}")
