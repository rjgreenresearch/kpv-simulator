from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple, Set

from kvp.orchestration.global_orchestrator import CountryRunResult
from kvp.domains.leadership_osint.utils.logger import get_logger


@dataclass
class GlobalGraph:
    """
    In-memory representation of the global leadership graph.

    Nodes:
      - persons:  node_type = "person",  id = person_id
      - orgs:     node_type = "org",     id = org_id

    Edges:
      - relationships, appointments, command links, etc.
    """

    persons: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    organizations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    edges: List[Dict[str, Any]] = field(default_factory=list)


class GlobalGraphAssembler:
    """
    Assembles a cross-country leadership graph from country run results.

    Responsibilities:
      - ingest per-country results (CN, RU, IR, KP)
      - assign deterministic global IDs to persons and orgs
      - merge nodes across countries when identity matches
      - preserve country provenance
      - emit a unified graph suitable for:
          * vulnerability analysis
          * kvp-simulator KPVI computation
          * reporting and visualization
    """

    def __init__(self, data_root: str = "./kpv_data"):
        self.data_root = data_root
        self.logger = get_logger("KPV.Graph.GlobalAssembler", data_root)

        # Global graph
        self.graph = GlobalGraph()

        # Simple identity maps (can later be replaced by a richer resolver)
        self._person_index: Dict[Tuple[str, str], str] = {}
        self._org_index: Dict[Tuple[str, str], str] = {}

        # Counters for deterministic ID generation
        self._person_counter: int = 0
        self._org_counter: int = 0

        self.logger.info("Initialized GlobalGraphAssembler")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def ingest_country_result(self, result: CountryRunResult) -> None:
        """
        Merge a single country's run result into the global graph.
        """
        if not result.success:
            self.logger.warning(
                f"Skipping country={result.country_code} due to failed run"
            )
            return

        cc = result.country_code

        # Persons
        for p in result.persons:
            global_id = self._resolve_person_id(cc, p)
            merged = self._merge_person(global_id, cc, p)
            self.graph.persons[global_id] = merged

        # Organizations
        for o in result.organizations:
            global_id = self._resolve_org_id(cc, o)
            merged = self._merge_org(global_id, cc, o)
            self.graph.organizations[global_id] = merged

        # Edges
        for e in result.edges:
            self.graph.edges.append(self._decorate_edge(cc, e))

        self.logger.info(
            f"Ingested country={cc}: "
            f"{len(result.persons)} persons, "
            f"{len(result.organizations)} orgs, "
            f"{len(result.edges)} edges"
        )

    def ingest_multiple(self, results: Dict[str, CountryRunResult]) -> None:
        for cc, res in results.items():
            self.ingest_country_result(res)

    def get_graph(self) -> GlobalGraph:
        return self.graph

    # ------------------------------------------------------------------
    # Identity resolution (simple, deterministic)
    # ------------------------------------------------------------------
    def _resolve_person_id(self, country_code: str, p: Dict[str, Any]) -> str:
        """
        Simple identity key:
          (country_code, normalized_name_native)
        This can later be replaced by a richer resolver.
        """
        name = (p.get("name_native") or "").strip()
        key = (country_code, name)

        if key in self._person_index:
            return self._person_index[key]

        self._person_counter += 1
        global_id = f"P-{self._person_counter:08d}"
        self._person_index[key] = global_id
        return global_id

    def _resolve_org_id(self, country_code: str, o: Dict[str, Any]) -> str:
        name = (o.get("name") or "").strip()
        key = (country_code, name)

        if key in self._org_index:
            return self._org_index[key]

        self._org_counter += 1
        global_id = f"O-{self._org_counter:08d}"
        self._org_index[key] = global_id
        return global_id

    # ------------------------------------------------------------------
    # Merge logic
    # ------------------------------------------------------------------
    def _merge_person(
        self,
        global_id: str,
        country_code: str,
        p: Dict[str, Any],
    ) -> Dict[str, Any]:
        existing = self.graph.persons.get(global_id, {})

        merged: Dict[str, Any] = dict(existing)
        merged.setdefault("id", global_id)
        merged.setdefault("countries", set())
        merged.setdefault("sources", [])
        merged.setdefault("aliases", set())
        merged.setdefault("thematic_keywords", set())

        merged["countries"].add(country_code)

        # Basic fields (prefer non-empty, latest wins)
        for field in [
            "name_native",
            "name_latin",
            "current_position",
            "service_or_agency",
            "rank_or_grade",
        ]:
            value = p.get(field)
            if value:
                merged[field] = value

        # Aliases
        for alias in p.get("aliases", []) or []:
            merged["aliases"].add(alias)

        # Thematic keywords
        for kw in p.get("thematic_keywords", []) or []:
            merged["thematic_keywords"].add(kw)

        # Source provenance
        merged["sources"].append(
            {
                "country": country_code,
                "raw": p,
            }
        )

        # Convert sets to lists for serialization
        merged["countries"] = sorted(list(merged["countries"]))
        merged["aliases"] = sorted(list(merged["aliases"]))
        merged["thematic_keywords"] = sorted(list(merged["thematic_keywords"]))

        return merged

    def _merge_org(
        self,
        global_id: str,
        country_code: str,
        o: Dict[str, Any],
    ) -> Dict[str, Any]:
        existing = self.graph.organizations.get(global_id, {})

        merged: Dict[str, Any] = dict(existing)
        merged.setdefault("id", global_id)
        merged.setdefault("countries", set())
        merged.setdefault("sources", [])

        merged["countries"].add(country_code)

        for field in ["name", "type", "parent_org"]:
            value = o.get(field)
            if value:
                merged[field] = value

        merged["sources"].append(
            {
                "country": country_code,
                "raw": o,
            }
        )

        merged["countries"] = sorted(list(merged["countries"]))

        return merged

    # ------------------------------------------------------------------
    # Edge decoration
    # ------------------------------------------------------------------
    def _decorate_edge(self, country_code: str, e: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attach country provenance and ensure minimal schema.
        """
        edge = dict(e)
        edge.setdefault("country", country_code)
        edge.setdefault("weight", e.get("weight", 1.0))
        return edge

    # ------------------------------------------------------------------
    # Export for simulator / KPVI / reporting
    # ------------------------------------------------------------------
    def to_simulator_payload(self) -> Dict[str, Any]:
        """
        Export the global graph in a normalized form suitable for:
          - kvp-simulator (KPVI computation)
          - vulnerability modeling
        """
        return {
            "persons": list(self.graph.persons.values()),
            "organizations": list(self.graph.organizations.values()),
            "edges": self.graph.edges,
        }
