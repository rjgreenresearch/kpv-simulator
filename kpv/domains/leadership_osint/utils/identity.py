from typing import Dict, Any, Optional
from .logger import get_logger


class IdentityResolver:
    """
    Handles identity matching and merging for KPV ingestion.
    Matching strategy:
      - Exact match on name_latin
      - Fallback: exact match on name_native
      - Future: fuzzy matching, alias matching, org/role matching
    """

    def __init__(self):
        self.logger = get_logger("KPV.Identity")

    # ------------------------------------------------------------
    # Person matching
    # ------------------------------------------------------------
    def match_person(
        self,
        new_person: Dict[str, Any],
        existing_persons: list
    ) -> Optional[Dict[str, Any]]:

        name_latin = new_person.get("name_latin")
        name_native = new_person.get("name_native")

        # Exact match on Latin name
        for person in existing_persons:
            if person.get("name_latin") == name_latin:
                self.logger.info(f"Identity match (latin): {name_latin}")
                return person

        # Exact match on native name
        for person in existing_persons:
            if person.get("name_native") == name_native:
                self.logger.info(f"Identity match (native): {name_native}")
                return person

        self.logger.info(f"No identity match for: {name_latin or name_native}")
        return None

    # ------------------------------------------------------------
    # Merge logic
    # ------------------------------------------------------------
    def merge_person(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any]
    ) -> Dict[str, Any]:

        merged = existing.copy()

        for key, value in new.items():
            if value is None:
                continue

            # Merge lists (e.g., aliases, keywords)
            if isinstance(value, list):
                old_list = merged.get(key, [])
                merged[key] = list({*old_list, *value})
                continue

            # Overwrite scalar fields
            merged[key] = value

        self.logger.info(f"Merged person record: {merged.get('id')}")
        return merged
