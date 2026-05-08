from pathlib import Path
from typing import Dict, Any
import json

from .ingest_cn import ChinaIngestor
from .ingest_ru import RussiaIngestor
from .ingest_ir import IranIngestor
from .ingest_kp import NorthKoreaIngestor

from ..utils.storage import StorageManager
from ..utils.diff import compute_diff
from ..utils.logger import get_logger


def load_schema(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def update_country(country_code: str, data_root: str = "./kpv_data") -> Dict[str, Any]:
    """
    Orchestrates the full ingestion-update-validation pipeline for a country.
    """

    country_code = country_code.lower()
    logger = get_logger(f"KPV.Update.{country_code.upper()}", data_root)
    logger.info(f"Starting KPV ingestion pipeline for {country_code.upper()}")

    # ------------------------------------------------------------
    # Load schemas
    # ------------------------------------------------------------
    schema_dir = Path(__file__).resolve().parents[1] / "schemas"

    person_schema = load_schema(schema_dir / "person.schema.json")
    org_schema = load_schema(schema_dir / "organization.schema.json")
    edge_schema = load_schema(schema_dir / "edge.schema.json")

    logger.info("Loaded JSON schemas")

    # ------------------------------------------------------------
    # Select ingestor
    # ------------------------------------------------------------
    if country_code == "cn":
        ingestor = ChinaIngestor(data_root)
    elif country_code == "ru":
        ingestor = RussiaIngestor(data_root)
    elif country_code == "ir":
        ingestor = IranIngestor(data_root)
    elif country_code == "kp":
        ingestor = NorthKoreaIngestor(data_root)
    else:
        raise ValueError(f"No ingestor implemented for country: {country_code}")

    # Inject schemas into the ingestor
    ingestor.person_schema = person_schema
    ingestor.org_schema = org_schema
    ingestor.edge_schema = edge_schema

    logger.info("Schemas injected into ingestor")

    # ------------------------------------------------------------
    # Load existing dataset
    # ------------------------------------------------------------
    storage = StorageManager(data_root)
    existing = storage.load_country_dataset(country_code)
    logger.info("Loaded existing dataset")

    # ------------------------------------------------------------
    # Run ingestion pipeline
    # ------------------------------------------------------------
    raw = ingestor.fetch_raw()
    normalized = ingestor.normalize(raw)
    resolved = ingestor.resolve_identities(normalized, existing)
    updated = ingestor.update_dataset(resolved, existing)

    logger.info("Ingestion pipeline completed")

    # ------------------------------------------------------------
    # Compute diff
    # ------------------------------------------------------------
    diff = compute_diff(existing, updated)
    logger.info("Computed dataset diff")

    # ------------------------------------------------------------
    # Save updated dataset
    # ------------------------------------------------------------
    storage.save_country_dataset(country_code, updated)
    logger.info("Saved updated dataset")

    # ------------------------------------------------------------
    # Write snapshot + diff
    # ------------------------------------------------------------
    snapshot_path = storage.write_snapshot(country_code, updated)
    diff_path = storage.write_diff(country_code, diff)

    logger.info(f"Snapshot written: {snapshot_path}")
    logger.info(f"Diff written: {diff_path}")

    return {
        "updated_dataset": updated,
        "diff": diff,
        "snapshot_path": str(snapshot_path),
        "diff_path": str(diff_path),
    }
