"""
kpvs/optimizer.py — Bench Investment Optimizer
================================================
Greedy marginal-improvement allocation of bench depth investments
across organizational roles.

Conceptually analogous to the CAS simulator's optimal $1B portfolio:
  Which N succession investments produce the greatest improvement in
  expected capability retention under adversarial targeting?

Each unit of bench depth investment represents one identified successor
placed in an active development programme.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime

from .models import Organization
from .simulator import KPVSimulator, _capability_after_loss

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Output of the bench investment optimizer.

    Attributes
    ----------
    budget_units                : total bench investments allocated
    allocation                  : role_id → allocation detail dict
    baseline_mean_pct           : mean adversarial capability before optimization
    optimized_mean_pct          : mean adversarial capability after optimization
    improvement_pp              : percentage-point improvement
    run_id / timestamp          : provenance fields
    """
    budget_units:         int
    allocation:           dict
    baseline_mean_pct:    float
    optimized_mean_pct:   float
    improvement_pp:       float
    run_id:               str
    timestamp:            str

    def to_dict(self) -> dict:
        return {
            "run_id":              self.run_id,
            "timestamp":           self.timestamp,
            "budget_units":        self.budget_units,
            "baseline_mean_pct":   round(self.baseline_mean_pct,   2),
            "optimized_mean_pct":  round(self.optimized_mean_pct,  2),
            "improvement_pp":      round(self.improvement_pp,       2),
            "allocation":          self.allocation,
        }


class BenchOptimizer:
    """
    Greedy marginal-improvement optimizer for bench depth allocation.

    Algorithm
    ---------
    1. Compute baseline adversarial capability (current bench).
    2. For each budget unit:
       a. For each un-maxed role, temporarily add one bench unit.
       b. Re-run adversarial scenario (reduced iterations for speed).
       c. Score improvement weighted by role KPCI
          (avoid wasting bench on already-resilient roles).
       d. Commit the unit to the highest-scoring role.
    3. Return final allocation and pre/post capability metrics.

    Parameters
    ----------
    org              : Organization to optimise.
    seed             : RNG seed (for reproducibility).
    eval_iterations  : Monte Carlo iterations for each candidate evaluation.
                       Lower = faster; higher = more accurate.
                       Recommended: n_iterations // 20 (min 200).
    max_bench_per_role : Cap on bench depth per role (default 5).
    """

    def __init__(
        self,
        org: Organization,
        seed: int = 20260501,
        eval_iterations: int = 500,
        max_bench_per_role: int = 5,
    ) -> None:
        self.org               = org
        self.seed              = seed
        self.eval_iterations   = max(200, eval_iterations)
        self.max_bench         = max_bench_per_role
        self._rng              = random.Random(seed)
        logger.debug(
            "BenchOptimizer: org='%s', eval_iterations=%d, max_bench=%d",
            org.name, self.eval_iterations, self.max_bench,
        )

    def _adversarial_mean(self, n_losses: int) -> float:
        """Fast adversarial mean capability (reduced iterations)."""
        sorted_ids = [
            r.id for r in sorted(
                self.org.roles.values(), key=lambda r: r.kpci, reverse=True)
        ]
        total = 0.0
        cap   = self.org.total_capability
        rng   = random.Random(self._rng.randint(0, 2**31))

        for _ in range(self.eval_iterations):
            remaining = sorted_ids.copy()
            lost: list[str] = []
            for _ in range(min(n_losses, len(remaining))):
                target = remaining[0] if rng.random() < 0.85 else rng.choice(remaining)
                lost.append(target)
                remaining.remove(target)
            total += _capability_after_loss(self.org, lost) / cap * 100

        return total / self.eval_iterations

    def optimise(
        self,
        budget_units: int,
        run_id: str | None = None,
    ) -> OptimizationResult:
        """
        Allocate `budget_units` bench investments for maximum resilience.

        Returns
        -------
        OptimizationResult with role-level allocation and before/after metrics.
        """
        run_id   = run_id or datetime.now().strftime("opt_%Y%m%d_%H%M%S")
        n_losses = max(1, len(self.org.roles) // 5)

        logger.info(
            "[%s] BenchOptimizer.optimise: budget=%d units, n_losses=%d",
            run_id, budget_units, n_losses,
        )

        baseline_pct = self._adversarial_mean(n_losses)
        allocation: dict[str, int] = {}   # role_id → units added
        running_pct = baseline_pct

        for unit_idx in range(budget_units):
            best_role_id = None
            best_score   = -1.0

            for role_id, role in self.org.roles.items():
                # Skip roles already at max bench
                if role.bench_depth >= self.max_bench:
                    continue

                # Temporarily increment bench
                self.org.roles[role_id].bench_depth += 1

                candidate_pct = self._adversarial_mean(n_losses)
                improvement   = candidate_pct - running_pct

                # Weight by KPCI so high-vulnerability roles are preferred
                kpci_weight   = role.kpci / 12.0 + 0.05
                score         = improvement * kpci_weight

                # Restore bench
                self.org.roles[role_id].bench_depth -= 1

                if score > best_score:
                    best_score   = score
                    best_role_id = role_id

            if best_role_id is None:
                logger.warning(
                    "[%s] All roles at max bench; stopping at unit %d.",
                    run_id, unit_idx + 1,
                )
                break

            self.org.roles[best_role_id].bench_depth += 1
            allocation[best_role_id] = allocation.get(best_role_id, 0) + 1
            running_pct += best_score * 0.80   # conservative update
            logger.debug(
                "[%s] Unit %d → '%s' (KPCI=%.1f, score=%.3f)",
                run_id, unit_idx + 1,
                self.org.roles[best_role_id].title,
                self.org.roles[best_role_id].kpci,
                best_score,
            )

        # Final capability with optimized bench
        optimized_pct = self._adversarial_mean(n_losses)

        # Build rich allocation summary
        alloc_summary = {}
        for role_id, units_added in sorted(
            allocation.items(),
            key=lambda x: self.org.roles[x[0]].kpci, reverse=True,
        ):
            role = self.org.roles[role_id]
            alloc_summary[role_id] = {
                "title":         role.title,
                "kpci":          role.kpci,
                "tier":          role.tier,
                "units_added":   units_added,
                "total_bench":   role.bench_depth,
                "new_restoration_months": role.estimated_restoration_months,
            }

        result = OptimizationResult(
            budget_units       = budget_units,
            allocation         = alloc_summary,
            baseline_mean_pct  = baseline_pct,
            optimized_mean_pct = optimized_pct,
            improvement_pp     = optimized_pct - baseline_pct,
            run_id             = run_id,
            timestamp          = datetime.now().isoformat(timespec="seconds"),
        )

        logger.info(
            "[%s] Optimisation complete: %.1f%% → %.1f%% (+%.1f pp)",
            run_id, result.baseline_mean_pct,
            result.optimized_mean_pct, result.improvement_pp,
        )
        return result
