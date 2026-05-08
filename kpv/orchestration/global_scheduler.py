from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from kvp.orchestration.global_orchestrator import GlobalOrchestrator
from kvp.domains.leadership_osint.utils.logger import get_logger


@dataclass
class ScheduledRunRecord:
    run_id: str
    started_at: datetime
    finished_at: datetime
    countries: List[str]
    success: bool
    errors: Dict[str, str] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GlobalScheduler:
    """
    Global scheduler for multi-country OSINT ingestion.

    Responsibilities:
      - run orchestrator jobs on a defined cadence
      - support sequential or parallel execution
      - handle retries with exponential backoff
      - maintain run history
      - produce normalized scheduler-level metadata for:
          * kvp-simulator (KPVI trendlines)
          * reporting dashboards
          * reliability scoring
    """

    def __init__(
        self,
        data_root: str = "./kpv_data",
        max_workers: int = 4,
        retry_attempts: int = 3,
        retry_backoff_seconds: int = 5,
    ):
        self.data_root = data_root
        self.logger = get_logger("KPV.Scheduler.Global", data_root)

        self.orchestrator = GlobalOrchestrator(data_root=data_root)
        self.max_workers = max_workers
        self.retry_attempts = retry_attempts
        self.retry_backoff_seconds = retry_backoff_seconds

        self.run_history: List[ScheduledRunRecord] = []

        self.logger.info(
            f"Initialized GlobalScheduler with max_workers={max_workers}, "
            f"retry_attempts={retry_attempts}"
        )

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------
    def run_once(
        self,
        countries: Optional[List[str]] = None,
        parallel: bool = True,
    ) -> ScheduledRunRecord:
        """
        Execute one full scheduler cycle.
        """
        countries = countries or self.orchestrator.list_countries()
        run_id = f"sched-{int(time.time())}"

        self.logger.info(
            f"Starting scheduled run {run_id} for countries={countries}"
        )

        started_at = datetime.utcnow()
        results: Dict[str, Any] = {}
        errors: Dict[str, str] = {}

        if parallel:
            results, errors = self._run_parallel(countries)
        else:
            results, errors = self._run_sequential(countries)

        finished_at = datetime.utcnow()

        record = ScheduledRunRecord(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            countries=countries,
            success=(len(errors) == 0),
            errors=errors,
            results=results,
            metadata={
                "duration_seconds": (finished_at - started_at).total_seconds(),
                "parallel": parallel,
            },
        )

        self.run_history.append(record)

        self.logger.info(
            f"Completed scheduled run {run_id} in "
            f"{record.metadata['duration_seconds']}s"
        )

        return record

    # ------------------------------------------------------------------
    # Sequential execution
    # ------------------------------------------------------------------
    def _run_sequential(self, countries: List[str]):
        results = {}
        errors = {}

        for cc in countries:
            attempt = 0
            while attempt < self.retry_attempts:
                try:
                    results[cc] = self.orchestrator.run_country(cc)
                    if results[cc].success:
                        break
                    else:
                        raise RuntimeError(results[cc].error)
                except Exception as e:
                    attempt += 1
                    errors[cc] = str(e)
                    self.logger.error(
                        f"Sequential run failed for {cc} (attempt {attempt}): {e}"
                    )
                    if attempt < self.retry_attempts:
                        time.sleep(self.retry_backoff_seconds * attempt)

        return results, errors

    # ------------------------------------------------------------------
    # Parallel execution
    # ------------------------------------------------------------------
    def _run_parallel(self, countries: List[str]):
        results = {}
        errors = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._run_with_retries, cc): cc
                for cc in countries
            }

            for future in as_completed(futures):
                cc = futures[future]
                try:
                    results[cc] = future.result()
                    if not results[cc].success:
                        errors[cc] = results[cc].error
                except Exception as e:
                    errors[cc] = str(e)
                    self.logger.error(
                        f"Parallel run crashed for {cc}: {traceback.format_exc()}"
                    )

        return results, errors

    # ------------------------------------------------------------------
    # Retry wrapper
    # ------------------------------------------------------------------
    def _run_with_retries(self, country_code: str):
        attempt = 0
        while attempt < self.retry_attempts:
            try:
                result = self.orchestrator.run_country(country_code)
                if result.success:
                    return result
                else:
                    raise RuntimeError(result.error)
            except Exception as e:
                attempt += 1
                self.logger.error(
                    f"Retry {attempt}/{self.retry_attempts} failed for {country_code}: {e}"
                )
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_backoff_seconds * attempt)

        # Final failure
        return self.orchestrator.run_country(country_code)

    # ------------------------------------------------------------------
    # Export for kvp-simulator
    # ------------------------------------------------------------------
    def to_simulator_payload(self, record: ScheduledRunRecord) -> Dict[str, Any]:
        """
        Convert a scheduler run record into a simulator-ready payload.
        """
        return {
            "run_id": record.run_id,
            "generated_at": record.finished_at.isoformat() + "Z",
            "duration_seconds": record.metadata["duration_seconds"],
            "countries": {
                cc: {
                    "success": res.success,
                    "error": res.error,
                    "persons": res.persons,
                    "organizations": res.organizations,
                    "edges": res.edges,
                    "events": res.events,
                    "metadata": res.metadata,
                }
                for cc, res in record.results.items()
            },
        }
