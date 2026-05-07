from typing import Dict, Any, List


def compute_diff(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute differences between old and new datasets.
    Returns a structured diff dictionary.
    """

    return {
        "persons": _diff_list(old.get("persons", []), new.get("persons", []), key="id"),
        "organizations": _diff_list(old.get("organizations", []), new.get("organizations", []), key="id"),
        "edges": _diff_list(old.get("edges", []), new.get("edges", []), key=lambda e: (e["source"], e["target"], e["type"])),
    }


def _diff_list(old_list: List[Any], new_list: List[Any], key):
    """
    Compute added, removed, and modified items in a list of dicts.
    """

    if isinstance(key, str):
        key_fn = lambda x: x[key]
    else:
        key_fn = key

    old_map = {key_fn(item): item for item in old_list}
    new_map = {key_fn(item): item for item in new_list}

    added = [new_map[k] for k in new_map.keys() - old_map.keys()]
    removed = [old_map[k] for k in old_map.keys() - new_map.keys()]

    modified = []
    for k in old_map.keys() & new_map.keys():
        if old_map[k] != new_map[k]:
            modified.append({"old": old_map[k], "new": new_map[k]})

    return {
        "added": added,
        "removed": removed,
        "modified": modified
    }
