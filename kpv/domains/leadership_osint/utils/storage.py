from pathlib import Path
import json
from typing import Dict, Any

from .logger import get_logger


class StorageManager:
    """
    Handles all read/write operations for KPV datasets, snapshots, and diffs.
    Ensures:
      - consistent directory structure
      - atomic writes
      - logging
    """

    def __init__(self, data_root: str = "./kpv_data"):
        self.data_root = Path(data_root).resolve()
        self.logger = get_logger("KPV.Storage", data_root)

        # Ensure base directories exist
        (self.data_root / "countries").mkdir(parents=True, exist_ok=True)
        (self.data_root / "snapshots").mkdir(parents=True, exist_ok=True)
        (self.data_root / "diffs").mkdir(parents=True, exist_ok=True)

        self.logger.info(f"StorageManager initialized at {self.data_root}")

    # ------------------------------------------------------------
    # Load country dataset
    # ------------------------------------------------------------
    def load_country_dataset(self, country_code: str) -> Dict[str, Any]:
        country_dir = self.data_root / "countries" / country_code.lower()
        country_dir.mkdir(parents=True, exist_ok=True)

        persons_path = country_dir / "persons.json"
        orgs_path = country_dir / "organizations.json"
        edges_path = country_dir / "edges.json"

        dataset = {
            "persons": self._load_json_list(persons_path),
            "organizations": self._load_json_list(orgs_path),
            "edges": self._load_json_list(edges_path),
        }

        self.logger.info(f"Loaded dataset for {country_code.upper()}")
        return dataset

    def _load_json_list(self, path: Path):
        if not path.exists():
            return []
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load {path}: {e}")
            return []

    # ------------------------------------------------------------
    # Save updated dataset
    # ------------------------------------------------------------
    def save_country_dataset(self, country_code: str, dataset: Dict[str, Any]):
        country_dir = self.data_root / "countries" / country_code.lower()
        country_dir.mkdir(parents=True, exist_ok=True)

        self._write_json(country_dir / "persons.json", dataset.get("persons", []))
        self._write_json(country_dir / "organizations.json", dataset.get("organizations", []))
        self._write_json(country_dir / "edges.json", dataset.get("edges", []))

        self.logger.info(f"Saved dataset for {country_code.upper()}")

    def _write_json(self, path: Path, data: Any):
        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to write {path}: {e}")
            raise

    # ------------------------------------------------------------
    # Write snapshot
    # ------------------------------------------------------------
    def write_snapshot(self, country_code: str, dataset: Dict[str, Any]) -> Path:
        snapshot_dir = self.data_root / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{self._timestamp()}-{country_code.lower()}.json"
        path = snapshot_dir / filename

        self._write_json(path, dataset)
        self.logger.info(f"Snapshot saved: {path}")

        return path

    # ------------------------------------------------------------
    # Write diff
    # ------------------------------------------------------------
    def write_diff(self, country_code: str, diff: Dict[str, Any]) -> Path:
        diff_dir = self.data_root / "diffs"
        diff_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{self._timestamp()}-{country_code.lower()}.diff.json"
        path = diff_dir / filename

        self._write_json(path, diff)
        self.logger.info(f"Diff saved: {path}")

        return path

    # ------------------------------------------------------------
    # Timestamp helper
    # ------------------------------------------------------------
    def _timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().strftime("%Y%m%d-%H%M%S")
