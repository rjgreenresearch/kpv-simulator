import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List


class StorageManager:
    """
    Handles reading/writing leadership OSINT datasets, snapshots, and diffs.
    """

    def __init__(self, data_root: str):
        self.data_root = Path(data_root)
        self.countries_dir = self.data_root / "countries"
        self.snapshots_dir = self.data_root / "snapshots"
        self.diffs_dir = self.data_root / "diffs"

        self.countries_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.diffs_dir.mkdir(parents=True, exist_ok=True)

    def load_country_dataset(self, country_code: str) -> Dict[str, Any]:
        """
        Load persons, organizations, and edges for a given country.
        """
        cc = country_code.lower()
        country_path = self.countries_dir / cc

        persons = self._load_json(country_path / "persons.json")
        orgs = self._load_json(country_path / "organizations.json")
        edges = self._load_json(country_path / "edges.json")

        return {"persons": persons, "organizations": orgs, "edges": edges}

    def save_country_dataset(self, country_code: str, dataset: Dict[str, Any]) -> None:
        """
        Save updated persons, organizations, and edges.
        """
        cc = country_code.lower()
        country_path = self.countries_dir / cc
        country_path.mkdir(parents=True, exist_ok=True)

        self._write_json(country_path / "persons.json", dataset["persons"])
        self._write_json(country_path / "organizations.json", dataset["organizations"])
        self._write_json(country_path / "edges.json", dataset["edges"])

    def write_snapshot(self, country_code: str, dataset: Dict[str, Any]) -> Path:
        """
        Write a timestamped snapshot of the dataset.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        snapshot_path = self.snapshots_dir / f"{timestamp}-{country_code}.json"
        self._write_json(snapshot_path, dataset)
        return snapshot_path

    def write_diff(self, country_code: str, diff: Dict[str, Any]) -> Path:
        """
        Write a timestamped diff file.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        diff_path = self.diffs_dir / f"{timestamp}-{country_code}.diff.json"
        self._write_json(diff_path, diff)
        return diff_path

    def _load_json(self, path: Path) -> Any:
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
