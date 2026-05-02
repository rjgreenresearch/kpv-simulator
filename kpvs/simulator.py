"""
kpvs/simulator.py — Monte Carlo KPV Simulation Engine
=======================================================
Three canonical scenarios:
  1. random_attrition     — baseline natural-turnover model
  2. adversarial_targeting— high-KPCI roles targeted preferentially
  3. cascade_failure      — loss of one mission-critical role propagates

All scenarios return a SimulationResult dataclass with full
distributional statistics for publication-quality reporting.
"""

from __future__ import annotations

import logging
import random
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .models import Organization, Role

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Result dataclass
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SimulationResult:
    """Complete statistics for one simulation scenario.

    Capability values are expressed as percentage of total_capability.
    Distributions are computed over all N iterations.
    """
    scenario:            str
    run_id:              str
    n_iterations:        int
    n_losses:            int
    seed:                int
    timestamp:           str

    # Core capability distribution
    mean_pct:    float
    median_pct:  float
    std_dev:     float
    min_pct:     float
    max_pct:     float
    p10_pct:     float  # 10th percentile (pessimistic)
    p25_pct:     float
    p75_pct:     float
    p90_pct:     float  # 90th percentile (optimistic)

    # Optional scenario-specific metadata
    extra: dict = field(default_factory=dict)

    @property
    def adversarial_gap(self) -> Optional[float]:
        """Gap vs random baseline, if stored in extra."""
        return self.extra.get("adversarial_gap_pp")

    def to_dict(self) -> dict:
        return {
            "scenario":     self.scenario,
            "run_id":       self.run_id,
            "n_iterations": self.n_iterations,
            "n_losses":     self.n_losses,
            "seed":         self.seed,
            "timestamp":    self.timestamp,
            "mean_pct":     round(self.mean_pct,   2),
            "median_pct":   round(self.median_pct, 2),
            "std_dev":      round(self.std_dev,     2),
            "min_pct":      round(self.min_pct,     2),
            "max_pct":      round(self.max_pct,     2),
            "p10_pct":      round(self.p10_pct,     2),
            "p25_pct":      round(self.p25_pct,     2),
            "p75_pct":      round(self.p75_pct,     2),
            "p90_pct":      round(self.p90_pct,     2),
            **{f"extra_{k}": v for k, v in self.extra.items()},
        }


def _percentile(data: list[float], p: float) -> float:
    """Return the p-th percentile of a sorted or unsorted list."""
    data = sorted(data)
    idx  = (len(data) - 1) * p / 100
    lo   = int(idx)
    hi   = min(lo + 1, len(data) - 1)
    frac = idx - lo
    return data[lo] + frac * (data[hi] - data[lo])


def _build_result(
    scenario: str, run_id: str, n_iterations: int, n_losses: int,
    seed: int, distribution: list[float], extra: dict | None = None,
) -> SimulationResult:
    dist = distribution
    return SimulationResult(
        scenario     = scenario,
        run_id       = run_id,
        n_iterations = n_iterations,
        n_losses     = n_losses,
        seed         = seed,
        timestamp    = datetime.now().isoformat(timespec="seconds"),
        mean_pct     = statistics.mean(dist),
        median_pct   = statistics.median(dist),
        std_dev      = statistics.stdev(dist) if len(dist) > 1 else 0.0,
        min_pct      = min(dist),
        max_pct      = max(dist),
        p10_pct      = _percentile(dist, 10),
        p25_pct      = _percentile(dist, 25),
        p75_pct      = _percentile(dist, 75),
        p90_pct      = _percentile(dist, 90),
        extra        = extra or {},
    )


# ══════════════════════════════════════════════════════════════════════════════
# Capability calculation
# ══════════════════════════════════════════════════════════════════════════════

def _capability_after_loss(
    org: Organization, lost_ids: list[str]
) -> float:
    """
    Calculate residual capability after losing a set of roles.

    Rules
    -----
    - Lost role with bench: contributes capability_weight × min(1, bench × 0.75)
    - Lost role without bench: contributes 0
    - Dependent of a lost mission-critical role (not itself lost):
      contributes capability_weight × 0.50 (50% degradation)
    - All other roles: full capability_weight
    """
    lost_set = set(lost_ids)

    # Cascade: mission-critical losses degrade their dependents
    cascade_degraded: set[str] = set()
    for rid in lost_ids:
        if rid in org.mission_critical_roles:
            for dep in org.get_dependents(rid):
                if dep.id not in lost_set:
                    cascade_degraded.add(dep.id)

    residual = 0.0
    for rid, role in org.roles.items():
        if rid in lost_set:
            coverage = min(1.0, role.bench_depth * 0.75)
            residual += role.capability_weight * coverage
        elif rid in cascade_degraded:
            residual += role.capability_weight * 0.50
        else:
            residual += role.capability_weight

    return residual


# ══════════════════════════════════════════════════════════════════════════════
# KPV Simulator
# ══════════════════════════════════════════════════════════════════════════════

class KPVSimulator:
    """
    Monte Carlo simulator for organizational key person vulnerability.

    Parameters
    ----------
    org   : Organization — the network to analyse.
    seed  : int — RNG seed for full reproducibility.
    run_id: str — identifier embedded in all result objects.
    """

    def __init__(self, org: Organization, seed: int = 20260501,
                 run_id: str | None = None) -> None:
        self.org    = org
        self.seed   = seed
        self.rng    = random.Random(seed)
        self.run_id = run_id or datetime.now().strftime("run_%Y%m%d_%H%M%S")
        logger.info("KPVSimulator initialised: org='%s', seed=%d, run_id='%s'",
                    org.name, seed, self.run_id)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _pct(self, residual: float) -> float:
        return (residual / self.org.total_capability) * 100.0

    def _default_n_losses(self) -> int:
        """20% of roles, minimum 1."""
        return max(1, len(self.org.roles) // 5)

    # ── Scenario 1: Random Attrition ─────────────────────────────────────────

    def scenario_random_attrition(
        self,
        n_losses: int | None = None,
        n_iterations: int = 10_000,
    ) -> SimulationResult:
        """
        Baseline scenario: n_losses roles removed uniformly at random.

        Models natural turnover with no adversarial selection.
        This is the null-hypothesis distribution against which
        adversarial scenarios are compared.

        Parameters
        ----------
        n_losses     : roles removed per iteration (default: 20% of org).
        n_iterations : Monte Carlo iterations.
        """
        n_losses = self._default_n_losses() if n_losses is None else n_losses
        logger.info("[%s] random_attrition: n_losses=%d, N=%d",
                    self.run_id, n_losses, n_iterations)

        role_ids = list(self.org.roles.keys())
        dist: list[float] = []

        for i in range(n_iterations):
            lost = self.rng.sample(role_ids, min(n_losses, len(role_ids)))
            dist.append(self._pct(_capability_after_loss(self.org, lost)))
            if (i + 1) % 2500 == 0:
                logger.debug("[%s] random_attrition: %d/%d iterations",
                             self.run_id, i + 1, n_iterations)

        result = _build_result(
            "Random Attrition", self.run_id,
            n_iterations, n_losses, self.seed, dist,
        )
        logger.info("[%s] random_attrition complete: mean=%.1f%%",
                    self.run_id, result.mean_pct)
        return result

    # ── Scenario 2: Adversarial Targeting ────────────────────────────────────

    def scenario_adversarial_targeting(
        self,
        n_losses: int | None = None,
        n_iterations: int = 10_000,
        targeting_accuracy: float = 0.85,
    ) -> SimulationResult:
        """
        Adversarial scenario: high-KPCI roles targeted preferentially.

        The adversary correctly selects the highest remaining KPCI target
        with probability `targeting_accuracy`; otherwise selects at random.
        This models a sophisticated but imperfect adversarial intelligence
        assessment — consistent with documented Thousand Talents targeting
        patterns (see Paper 5, Section 3.1).

        Parameters
        ----------
        n_losses           : roles targeted per iteration.
        n_iterations       : Monte Carlo iterations.
        targeting_accuracy : P(adversary selects highest-KPCI role)
                             on each selection step. Default 0.85.
        """
        n_losses = self._default_n_losses() if n_losses is None else n_losses
        if not 0.0 < targeting_accuracy <= 1.0:
            raise ValueError("targeting_accuracy must be in (0, 1].")

        logger.info(
            "[%s] adversarial_targeting: n_losses=%d, N=%d, accuracy=%.0f%%",
            self.run_id, n_losses, n_iterations, targeting_accuracy * 100,
        )

        sorted_ids = [
            r.id for r in sorted(
                self.org.roles.values(), key=lambda r: r.kpci, reverse=True)
        ]
        dist: list[float] = []

        for i in range(n_iterations):
            remaining = sorted_ids.copy()
            lost: list[str] = []

            for _ in range(min(n_losses, len(remaining))):
                if self.rng.random() < targeting_accuracy:
                    target = remaining[0]   # highest KPCI
                else:
                    target = self.rng.choice(remaining)
                lost.append(target)
                remaining.remove(target)

            dist.append(self._pct(_capability_after_loss(self.org, lost)))
            if (i + 1) % 2500 == 0:
                logger.debug("[%s] adversarial_targeting: %d/%d",
                             self.run_id, i + 1, n_iterations)

        result = _build_result(
            f"Adversarial Targeting ({targeting_accuracy:.0%} accuracy)",
            self.run_id, n_iterations, n_losses, self.seed, dist,
            extra={"targeting_accuracy": targeting_accuracy},
        )
        logger.info("[%s] adversarial_targeting complete: mean=%.1f%%",
                    self.run_id, result.mean_pct)
        return result

    # ── Scenario 3: Cascade Failure ──────────────────────────────────────────

    def scenario_cascade_failure(
        self,
        trigger_role_id: str,
        n_iterations: int = 10_000,
    ) -> SimulationResult:
        """
        Cascade scenario: loss of one mission-critical role propagates.

        Each dependent role fails stochastically based on its
        Documentation Ratio component (undocumented roles are more
        vulnerable to upstream capability loss) and its bench depth
        (bench reduces cascade probability).

        Parameters
        ----------
        trigger_role_id : ID of the role whose loss is simulated.
        n_iterations    : Monte Carlo iterations.
        """
        trigger = self.org.get_role(trigger_role_id)
        if trigger is None:
            raise ValueError(
                f"Trigger role '{trigger_role_id}' not found in organisation.")

        logger.info("[%s] cascade_failure: trigger='%s' (KPCI=%.1f), N=%d",
                    self.run_id, trigger.title, trigger.kpci, n_iterations)

        dist: list[float] = []

        for i in range(n_iterations):
            lost    = [trigger_role_id]
            visited = {trigger_role_id}
            queue   = list(self.org.get_dependents(trigger_role_id))

            while queue:
                dep = queue.pop(0)
                if dep.id in visited:
                    continue
                visited.add(dep.id)

                # Failure probability: undocumented roles are more vulnerable
                p_fail = (dep.documentation_ratio / 4.0) * 0.70
                p_fail *= max(0.10, 1.0 - dep.bench_depth * 0.40)

                if self.rng.random() < p_fail:
                    lost.append(dep.id)
                    queue.extend([
                        d for d in self.org.get_dependents(dep.id)
                        if d.id not in visited
                    ])

            dist.append(self._pct(_capability_after_loss(self.org, lost)))
            if (i + 1) % 2500 == 0:
                logger.debug("[%s] cascade_failure: %d/%d",
                             self.run_id, i + 1, n_iterations)

        result = _build_result(
            f"Cascade Failure — trigger: {trigger.title}",
            self.run_id, n_iterations, 1, self.seed, dist,
            extra={
                "trigger_role_id": trigger_role_id,
                "trigger_kpci":    trigger.kpci,
                "trigger_tier":    trigger.tier,
                "estimated_restoration_months": trigger.estimated_restoration_months,
            },
        )
        logger.info("[%s] cascade_failure complete: mean=%.1f%%",
                    self.run_id, result.mean_pct)
        return result

    # ── KPCI full report ─────────────────────────────────────────────────────

    def kpci_report(self) -> list[dict]:
        """
        Generate KPCI analysis for all roles, sorted by vulnerability.
        Primary analytical output; no Monte Carlo required.
        """
        report = []
        for role in self.org.roles_by_kpci():
            dependents   = self.org.get_dependents(role.id)
            subordinates = self.org.get_subordinates(role.id)
            report.append({
                **role.to_dict(),
                "mission_critical":   role.id in self.org.mission_critical_roles,
                "n_dependents":       len(dependents),
                "n_direct_reports":   len(subordinates),
                "recommendation":     _recommendation(role),
            })
        return report


def _recommendation(role: Role) -> str:
    restore = role.estimated_restoration_months
    if role.tier == "Tier-1 KPV":
        return (
            f"URGENT — 0 bench depth creates a {restore:.0f}-month capability gap. "
            f"Identify ≥2 successors and initiate active development programme "
            f"immediately. Consider tacit knowledge documentation sprint."
        )
    if role.tier == "Tier-2 KPV":
        status = "adequate" if role.bench_depth >= 1 else "INSUFFICIENT"
        return (
            f"HIGH — current bench depth ({role.bench_depth}) is {status}. "
            f"Formalise succession plan with documented development milestones. "
            f"Estimated restoration: {restore:.0f} months without bench."
        )
    if role.tier == "Manageable":
        return (
            "MODERATE — standard succession planning adequate. "
            "Ensure role documentation is current and reviewed annually."
        )
    return (
        "LOW — institutional processes provide resilience. "
        "No special action required."
    )
