from typing import List, Dict, Any

from .ingest_base import BaseIngestor
from ..utils.identity import IdentityResolver
from ..utils.logger import get_logger


class ChinaIngestor(BaseIngestor):
    """
    China-specific OSINT ingestion module.
    Expand with:
      - CNKI scraping
      - Patent database queries
      - PLA Daily announcements
      - Xinhua leadership changes
      - Academic co-authorship networks
    """

    def __init__(self, data_root: str = "./kpv_data"):
        super().__init__("CN", data_root)
        self.identity = IdentityResolver()
        self.logger.info("Initialized ChinaIngestor")

    # ------------------------------------------------------------
    # STEP 1 — Fetch raw OSINT data
    # ------------------------------------------------------------
    def fetch_raw(self) -> List[Any]:
        self.logger.info("Fetching raw OSINT data for China")

        raw = [
            {
                "name_native": "王厚斌",
                "name_latin": "Wang Houbin",
                "sector": "military",
                "service_or_agency": "PLA Rocket Force",
                "current_position": "Commander",
                "thematic_keywords": ["missile forces", "nuclear posture"],
            }
        ]

        self.logger.info(f"Fetched {len(raw)} raw OSINT records")
        return raw

    # ------------------------------------------------------------
    # STEP 2 — Normalize raw OSINT into schema-compatible dicts
    # ------------------------------------------------------------
    def normalize(self, raw: List[Any]) -> List[Dict[str, Any]]:
        self.logger.info("Normalizing raw OSINT data")

        normalized = []

        for item in raw:
            person = {
                "id": None,
                "country_code": "CN",
                "name_native": item.get("name_native"),
                "name_latin": item.get("name_latin"),
                "aliases": [],
                "sector": item.get("sector"),
                "rank_or_grade": None,
                "service_or_agency": item.get("service_or_agency"),
                "current_position": item.get("current_position"),
                "current_org_id": None,
                "career_history": [],
                "academic_profiles": {},
                "thematic_keywords": item.get("thematic_keywords", []),
                "political_alignment_score": 0.0,
                "technical_expertise_score": 0.0,
                "doctrinal_influence_score": 0.0,
                "promotion_velocity_score": 0.0,
                "purge_or_arrest_risk_score": 0.0,
                "notes": None,
            }

            # Validate before adding
            if self.person_schema:
                self.validate_person(person)

            normalized.append({"type": "person", "data": person})

        self.logger.info(f"Normalized {len(normalized)} records")
        return normalized

    # ------------------------------------------------------------
    # STEP 3 — Identity resolution and merging
    # ------------------------------------------------------------
    def resolve_identities(
        self,
        normalized: List[Dict[str, Any]],
        existing: Dict[str, Any]
    ) -> Dict[str, Any]:

        self.logger.info("Resolving identities for China")

        persons = existing.get("persons", [])
        updated_persons = persons.copy()

        for item in normalized:
            if item["type"] != "person":
                continue

            new_person = item["data"]
            match = self.identity.match_person(new_person, persons)

            if match:
                self.logger.info(f"Matched existing person: {match.get('name_latin')}")
                merged = self.identity.merge_person(match, new_person)
                merged["id"] = match["id"]

                # Validate merged record
                if self.person_schema:
                    self.validate_person(merged)

                updated_persons = [
                    merged if p["id"] == match["id"] else p
                    for p in updated_persons
                ]

            else:
                new_id = f"cn_person_{len(updated_persons) + 1}"
                new_person["id"] = new_id

                # Validate new record
                if self.person_schema:
                    self.validate_person(new_person)

                updated_persons.append(new_person)
                self.logger.info(f"Created new person: {new_person.get('name_latin')} ({new_id})")

        return {
            "persons": updated_persons,
            "organizations": existing.get("organizations", []),
            "edges": existing.get("edges", []),
        }

    # ------------------------------------------------------------
    # STEP 4 — Final dataset update
    # ------------------------------------------------------------
    def update_dataset(
        self,
        resolved: Dict[str, Any],
        existing: Dict[str, Any]
    ) -> Dict[str, Any]:

        self.logger.info("Finalizing dataset update for China")
        return resolved
