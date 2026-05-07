from typing import Dict, Any
from pathlib import Path

from .ingest_cn import ChinaIngestor
from ..utils.storage import StorageManager
from ..utils.diff import compute_diff
from ..analytics.scoring import score_graph


def update_country(country_code: str, data_root: str) -> Dict[str, Any]:
    """
    Orchestrates the full ingestion-update-scoring pipeline for a country.
    """

    storage = StorageManager(data_root)
    existing = storage.load_country_dataset(country_code)

    # ------------------------------------------------------------
    # Select ingestor
    # ------------------------------------------------------------
    if country_code.lower() == "cn":
        ingestor = ChinaIngestor()
    else:
        raise ValueError(f"No ingestor implemented for country: {country_code}")

    # ------------------------------------------------------------
    # Run ingestion pipeline
    # ------------------------------------------------------------
    raw = ingestor.fetch_raw()
    normalized = ingestor.normalize(raw)
    resolved = ingestor.resolve_identities(normalized, existing)
    updated = ingestor.update_dataset(resolved, existing)

    # ------------------------------------------------------------
    # Compute diff
    # ------------------------------------------------------------
    diff = compute_diff(existing, updated)

    # ------------------------------------------------------------
    # Save updated dataset
    # ------------------------------------------------------------
    storage.save_country_dataset(country_code, updated)

    # ------------------------------------------------------------
    # Write snapshot + diff
    # ------------------------------------------------------------
    snapshot_path = storage.write_snapshot(country_code, updated)
    diff_path = storage.write_diff(country_code, diff)

    # ------------------------------------------------------------
    # Apply scoring (optional for now)
    # ------------------------------------------------------------
    # score_graph(graph)  # integrate with your graph engine later

    return {
        "updated_dataset": updated,
        "diff": diff,
        "snapshot_path": str(snapshot_path),
        "diff_path": str(diff_path),
    }

