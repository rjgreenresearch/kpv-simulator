from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

from kvp.domains.leadership_osint.pipeline.china_pipeline_builder import ChinaPipelineBuilder
from kvp.domains.leadership_osint.pipeline.russia_pipeline_builder import RussiaPipelineBuilder
from kvp.domains.leadership_osint.pipeline.iran_pipeline_builder import IranPipelineBuilder
from kvp.domains.leadership_osint.pipeline.north_korea_pipeline_builder import NorthKoreaPipelineBuilder

from kvp.domains.leadership_osint.utils.logger import get_logger


@dataclass
class CountryRunResult:
    country_code: str
    started_at: datetime
    finished_at: datetime
    success: bool
    error: Optional[str] = None
    persons: List[Dict[str, Any]] = field(default_factory=list)
    organizations: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GlobalOrchestrator:
    """
    Global orchestrator for leadership OSINT pipelines.

    Responsibilities:
      - maintain a registry of country pipeline builders
      - run one or more country pipelines on demand
      - emit normalized run artifacts for:
          * kvp-simulator (KPVI statistics, scenario inputs)
          * reporting and dashboards
      - provide a single, deterministic interface:
          run_country(), run_all(), run_subset()
    """

    def __init__(self, data_root: str = "./kpv_data"):
        self.data_root = data_root
        self.logger = get_logger("KPV.Orchestrator.Global", data_root)

        # Country registry: extendable without changing orchestrator logic
        self._registry = {
            "CN": ChinaPipelineBuilder,
            "RU": RussiaPipelineBuilder,
            "IR": IranPipelineBuilder,
            "KP": NorthKoreaPipelineBuilder,
        }

        self.logger.info(
            f"Initialized GlobalOrchestrator with countries={list(self._registry.keys())}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_countries(self) -> List[str]:
        return sorted(self._registry.keys())

    def run_country(self, country_code: str) -> CountryRunResult:
        """
        Run a single country pipeline and return a normalized result
        suitable for kvp-simulator and reporting.
        """
        country_code = country_code.upper()
        if country_code not in self._registry:
            raise ValueError(f"Unknown country code: {country_code}")

        builder_cls = self._registry[country_code]
        builder = builder_cls(data_root=self.data_root)

        self.logger.info(f"Starting pipeline run for country={country_code}")
        started_at = datetime.utcnow()

        try:
            pipeline = builder.build_pipeline()
            output = pipeline.run()

            finished_at = datetime.utcnow()
            self.logger.info(
                f"Completed pipeline run for country={country_code} "
                f"in {(finished_at - started_at).total_seconds()}s"
            )

            return CountryRunResult(
                country_code=country_code,
                started_at=started_at,
                finished_at=finished_at,
                success=True,
                persons=output.get("persons", []),
                organizations=output.get("organizations", []),
                edges=output.get("edges", []),
                events=output.get("events", []),
                metadata={
                    "run_id": output.get("run_id"),
                    "source_count": output.get("source_count"),
                    "llm_used": output.get("llm_used"),
                },
            )

        except Exception as e:
            finished_at = datetime.utcnow()
            self.logger.error(
                f"Pipeline run failed for country={country_code}: {e}",
                exc_info=True,
            )
            return CountryRunResult(
                country_code=country_code,
                started_at=started_at,
                finished_at=finished_at,
                success=False,
                error=str(e),
            )

    def run_all(self) -> Dict[str, CountryRunResult]:
        """
        Run all registered country pipelines sequentially.
        (Scheduling/parallelism will be handled by the scheduler layer.)
        """
        results: Dict[str, CountryRunResult] = {}
        for cc in self.list_countries():
            results[cc] = self.run_country(cc)
        return results

    def run_subset(self, country_codes: List[str]) -> Dict[str, CountryRunResult]:
        """
        Run a subset of country pipelines.
        """
        results: Dict[str, CountryRunResult] = {}
        for cc in country_codes:
            results[cc.upper()] = self.run_country(cc)
        return results

    # ------------------------------------------------------------------
    # Export for kvp-simulator / KPVI
    # ------------------------------------------------------------------
    def to_simulator_payload(
        self,
        results: Dict[str, CountryRunResult],
    ) -> Dict[str, Any]:
        """
        Convert run results into a normalized payload for kvp-simulator.

        This is the bridge into KPVI statistics and scenario modeling.
        """
        payload: Dict[str, Any] = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "countries": {},
        }

        for cc, res in results.items():
            payload["countries"][cc] = {
                "success": res.success,
                "error": res.error,
                "persons": res.persons,
                "organizations": res.organizations,
                "edges": res.edges,
                "events": res.events,
                "metadata": {
                    "started_at": res.started_at.isoformat() + "Z",
                    "finished_at": res.finished_at.isoformat() + "Z",
                    **res.metadata,
                },
            }

        return payload
