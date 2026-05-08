import os
from pathlib import Path
from typing import Any, Dict

from .logger import get_logger


class Config:
    """
    Centralized configuration loader for KPV.
    Supports:
      - environment variable overrides
      - default values
      - future expansion for API keys, rate limits, feature flags
    """

    DEFAULTS = {
        "DATA_ROOT": "./kpv_data",
        "LOG_LEVEL": "INFO",
        "ENABLE_SCRAPERS": "false",
        "ENABLE_EXPERIMENTAL": "false"
    }

    def __init__(self):
        self.logger = get_logger("KPV.Config", self.DEFAULTS["DATA_ROOT"])
        self.values = self._load()

    # ------------------------------------------------------------
    # Load configuration
    # ------------------------------------------------------------
    def _load(self) -> Dict[str, Any]:
        config = {}

        for key, default in self.DEFAULTS.items():
            value = os.environ.get(key, default)
            config[key] = value

        self.logger.info("Configuration loaded")
        return config

    # ------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    @property
    def data_root(self) -> str:
        return self.values["DATA_ROOT"]

    @property
    def log_level(self) -> str:
        return self.values["LOG_LEVEL"]

    @property
    def enable_scrapers(self) -> bool:
        return self.values["ENABLE_SCRAPERS"].lower() == "true"

    @property
    def enable_experimental(self) -> bool:
        return self.values["ENABLE_EXPERIMENTAL"].lower() == "true"
