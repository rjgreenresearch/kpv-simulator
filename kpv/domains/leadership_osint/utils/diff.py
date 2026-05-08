from typing import Dict, Any, List
from .logger import get_logger


def compute_diff(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a structured diff between two KPV datasets.
    Tracks:
      - added
      - removed
      - modified
    """

    logger = get_logger("KPV.Diff")

    diff = {
        "persons": _diff_list(old.get("persons", []), new.get("persons", []), "id", logger),
        "organizations": _diff_list(old.get("organizations", []), new.get("organizations", []), "id", logger),
        "edges": _diff_list(old.get("edges", []), new.get("edges", []), "id", logger),
    }

    logger.info("Diff computation complete")
    return diff


def _diff_list(
    old_list: List[Dict[str, Any]],
    new_list: List[Dict[str, Any]],
    key: str,
    logger
) -> Dict[str, List[Dict[str, Any]]]:

    old_map = {item[key]: item for item in old_list if key in item}
    new_map = {item[key]: item for item in new_list if key in item}

    added = []
    removed = []
    modified = []

    # Detect added + modified
    for new_id, new_item in new_map.items():
        if new_id not in old_map:
            added.append(new_item)
            logger.info(f"Added: {new_id}")
        else:
            old_item = old_map[new_id]
            if new_item != old_item:
                modified.append({"old": old_item, "new": new_item})
                logger.info(f"Modified: {new_id}")

    # Detect removed
    for old_id, old_item in old_map.items():
        if old_id not in new_map:
            removed.append(old_item)
            logger.info(f"Removed: {old_id}")

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
    }
