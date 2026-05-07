import difflib
from typing import Dict, Any, List, Optional


class IdentityResolver:
    """
    Resolve identities across OSINT sources using fuzzy matching,
    romanization variants, and contextual clues.
    """

    def __init__(self, threshold: float = 0.80):
        self.threshold = threshold

    def match_person(
        self,
        new_person: Dict[str, Any],
        existing_persons: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to match a new person record to an existing one.
        """

        candidates = []

        new_name = new_person.get("name_native") or new_person.get("name_latin")

        for person in existing_persons:
            existing_name = person.get("name_native") or person.get("name_latin")

            score = difflib.SequenceMatcher(None, new_name, existing_name).ratio()

            if score >= self.threshold:
                candidates.append((score, person))

        if not candidates:
            return None

        # return best match
        return max(candidates, key=lambda x: x[0])[1]

    def merge_person(self, old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge fields from new into old, preferring new when non-null.
        """
        merged = old.copy()
        for k, v in new.items():
            if v not in (None, "", [], {}):
                merged[k] = v
        return merged
