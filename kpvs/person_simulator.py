"""
kpvs/person_simulator.py — Person-centric Monte Carlo scenarios
================================================================

Adds two new scenarios to KPVS without modifying the existing simulator:

    scenario_person_random_attrition  — baseline: remove random PERSONS
    scenario_person_targeted_attrition — adversarial: rank by target value

The person-level adversarial gap is:

    gap = random_mean_pct - targeted_mean_pct

This is the additional capability degradation an adversary achieves by
identifying and targeting high-value persons (and inheriting all their
roles via multi-hat) versus random personnel turnover.

Why a person-level baseline matters
-----------------------------------
The role-level random_attrition baseline understates the multi-hat
dynamic — it only removes one role per draw. To compare apples-to-apples,
both the baseline and the adversarial scenario must operate at the person
level. A multi-hat person dropped randomly STILL costs all their roles;
the adversary's edge is in *targeting* such persons rather than getting
them by chance.

Target value (adversarial ranking metric)
-----------------------------------------
    target_value(person) = Σ_{r ∈ roles_held(person)} eff_kpci(r, person) * capacity(person, r)

This is the criticality footprint a single targeting operation removes.
Higher target value = more attractive target. An adversary at accuracy α
hits a top-K target_value person with probability α and a random person
with probability (1-α).
"""

from __future__ import annotations

import logging
import random
import statistics
from dataclasses import dataclass, field
from typing import Optional

from kpvs.persons import Person, RoleAssignment, multi_hat_persons, roles_held_by
from kpvs.effective_kpci import effective_kpci, continuity_loss

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Result dataclass — mirrors existing scenario result shape so reporting
# layer (kpvs/reporting.py, kpvs/reporting_html.py) can consume it.
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class PersonScenarioResult:
    """Output of a person-centric Monte Carlo scenario.

    Attributes mirror the existing role-based ScenarioResult where
    semantics overlap (mean_pct, std, percentiles, n_iterations) and
    add person-specific diagnostics.
    """
    name: str
    n_iterations: int
    n_persons_removed_per_iter: int

    # Capability-remaining distribution (% of total org capability)
    mean_pct: float
    std_pct: float
    p05_pct: float
    p25_pct: float
    p50_pct: float
    p75_pct: float
    p95_pct: float

    # Person-centric diagnostics
    mean_roles_disabled: float        # persons × multi-hat factor
    mean_tacit_shock: float           # Σ TK losses across removed
    mean_replacement_friction: float  # avg max friction (months)
    multi_hat_efficiency: float       # roles_disabled / persons_removed

    # For the adversarial scenario, list of most-frequently-targeted persons
    target_frequency: dict = field(default_factory=dict)

    def summary_line(self) -> str:
        """One-line summary matching existing scenario output style."""
        return (f"{self.name:<32} "
                f"mean={self.mean_pct:5.1f}% σ={self.std_pct:4.1f} "
                f"p05={self.p05_pct:5.1f}% p95={self.p95_pct:5.1f}% "
                f"roles/iter={self.mean_roles_disabled:.2f} "
                f"shock={self.mean_tacit_shock:.2f}")


# ─────────────────────────────────────────────────────────────────────────
# Simulator
# ─────────────────────────────────────────────────────────────────────────
class PersonAwareSimulator:
    """Runs person-centric Monte Carlo scenarios against an organization.

    Parameters
    ----------
    organization : kpvs.models.Organization
        The existing org with roles. Untouched.
    persons      : dict[str, Person]
        person_id → Person mapping.
    assignments  : list[RoleAssignment]
        Person ↔ Role linkages. A single person can appear multiple
        times for multi-hat coupling.
    seed         : int, optional
        RNG seed for reproducibility.

    The simulator does NOT mutate any inputs.
    """

    def __init__(self,
                 organization,
                 persons: dict,
                 assignments: list,
                 seed: Optional[int] = None):
        self.org = organization
        self.persons = persons
        self.assignments = assignments
        self._rng = random.Random(seed)

        # Pre-build lookups
        self._role_by_id = {r.id: r for r in organization.roles}
        self._roles_per_person = {}  # person_id → list[(role, assignment)]
        for a in assignments:
            role = self._role_by_id.get(a.role_id)
            if role is None:
                logger.warning("RoleAssignment references unknown role_id '%s'",
                               a.role_id)
                continue
            self._roles_per_person.setdefault(a.person_id, []).append((role, a))

        # Total org capability for percentage calculations
        self._total_capability = sum(r.capability_weight for r in organization.roles)
        if self._total_capability <= 0:
            raise ValueError("Organization total capability must be > 0")

        # Cache target values for adversarial ranking
        self._target_values = self._compute_target_values()

    # ── Core: target value for adversarial ranking ───────────────────────
    def _compute_target_values(self) -> dict:
        """Compute target_value(person) for all persons with assignments.

        target_value = Σ (effective_kpci(role, person) × capacity)
        """
        out: dict = {}
        for pid, role_assigns in self._roles_per_person.items():
            person = self.persons.get(pid)
            if person is None:
                continue
            tv = 0.0
            for role, assignment in role_assigns:
                eff = effective_kpci(
                    role, person,
                    has_designated_successor=assignment.is_designated_successor,
                )
                tv += eff * assignment.capacity
            out[pid] = tv
        return out

    def rank_persons(self) -> list:
        """Return [(person_id, target_value)] sorted descending."""
        return sorted(self._target_values.items(),
                      key=lambda kv: -kv[1])

    # ── Helper: compute capability loss for removing a set of persons ────
    def _compute_removal_impact(self, person_ids: list) -> dict:
        """For a set of removed persons, compute aggregate impact metrics."""
        roles_disabled = set()  # role IDs
        capability_lost = 0.0
        tacit_shock = 0.0
        max_friction = 0.0

        for pid in person_ids:
            person = self.persons.get(pid)
            role_assigns = self._roles_per_person.get(pid, [])
            for role, assignment in role_assigns:
                if role.id in roles_disabled:
                    continue  # already counted (rare: collective bodies)
                roles_disabled.add(role.id)
                # Capability proportional to assignment capacity
                capability_lost += role.capability_weight * assignment.capacity

                if person is not None:
                    diag = continuity_loss(
                        role, person,
                        has_designated_successor=assignment.is_designated_successor,
                    )
                    tacit_shock += diag["tacit_shock"]
                    max_friction = max(max_friction,
                                       diag["replacement_friction_months"])

        capability_remaining_pct = (
            100.0 * (self._total_capability - capability_lost)
            / self._total_capability
        )

        return {
            "capability_remaining_pct": max(0.0, capability_remaining_pct),
            "n_roles_disabled": len(roles_disabled),
            "tacit_shock": tacit_shock,
            "max_replacement_friction": max_friction,
        }

    # ── Scenario: random person attrition (baseline) ─────────────────────
    def scenario_person_random_attrition(self,
                                         n_iterations: int = 1000,
                                         n_persons_per_iter: int = 3
                                         ) -> PersonScenarioResult:
        """Baseline: remove n random persons per iteration.

        Provides the null-hypothesis distribution against which adversarial
        targeting is compared at the person level.
        """
        all_pids = list(self._roles_per_person.keys())
        if len(all_pids) < n_persons_per_iter:
            raise ValueError(
                f"Cannot remove {n_persons_per_iter} persons from a pool "
                f"of {len(all_pids)}.")

        cap_pcts = []
        roles_disabled = []
        shocks = []
        frictions = []

        for _ in range(n_iterations):
            picks = self._rng.sample(all_pids, n_persons_per_iter)
            impact = self._compute_removal_impact(picks)
            cap_pcts.append(impact["capability_remaining_pct"])
            roles_disabled.append(impact["n_roles_disabled"])
            shocks.append(impact["tacit_shock"])
            frictions.append(impact["max_replacement_friction"])

        return self._build_result(
            "Person Random Attrition",
            n_iterations, n_persons_per_iter,
            cap_pcts, roles_disabled, shocks, frictions,
            target_frequency={},
        )

    # ── Scenario: adversarial person targeting ───────────────────────────
    def scenario_person_targeted_attrition(self,
                                           n_iterations: int = 1000,
                                           n_persons_per_iter: int = 3,
                                           accuracy: float = 0.85
                                           ) -> PersonScenarioResult:
        """Adversarial: target highest target_value persons with given
        accuracy. Models Thousand-Talents-style identification.

        At accuracy α, the adversary picks correctly from the top-K
        target-value persons with probability α, and picks a random
        (non-top) person with probability (1 - α).
        """
        ranked = self.rank_persons()
        if not ranked:
            raise ValueError("No persons with assignments to target.")
        if len(ranked) < n_persons_per_iter:
            raise ValueError(
                f"Cannot target {n_persons_per_iter} persons from a pool "
                f"of {len(ranked)}.")

        ranked_ids = [pid for pid, _ in ranked]
        # Top-K pool from which accurate hits are drawn (slightly broader
        # than n_persons_per_iter to give the RNG some space)
        top_k = min(len(ranked_ids), max(n_persons_per_iter * 2, 5))
        top_pool = ranked_ids[:top_k]
        rest_pool = ranked_ids[top_k:] if top_k < len(ranked_ids) else ranked_ids

        cap_pcts = []
        roles_disabled = []
        shocks = []
        frictions = []
        target_freq: dict = {pid: 0 for pid in ranked_ids}

        for _ in range(n_iterations):
            picks = []
            available_top = list(top_pool)
            available_rest = list(rest_pool)
            for _slot in range(n_persons_per_iter):
                if self._rng.random() < accuracy and available_top:
                    pick = self._rng.choice(available_top)
                    available_top.remove(pick)
                    if pick in available_rest:
                        available_rest.remove(pick)
                elif available_rest:
                    pick = self._rng.choice(available_rest)
                    available_rest.remove(pick)
                    if pick in available_top:
                        available_top.remove(pick)
                else:
                    # Fallback: pool exhausted, pick from whatever's left
                    remaining = [p for p in ranked_ids if p not in picks]
                    if not remaining:
                        break
                    pick = self._rng.choice(remaining)
                picks.append(pick)
                target_freq[pick] = target_freq.get(pick, 0) + 1

            impact = self._compute_removal_impact(picks)
            cap_pcts.append(impact["capability_remaining_pct"])
            roles_disabled.append(impact["n_roles_disabled"])
            shocks.append(impact["tacit_shock"])
            frictions.append(impact["max_replacement_friction"])

        return self._build_result(
            f"Person Adversarial (acc={accuracy:.2f})",
            n_iterations, n_persons_per_iter,
            cap_pcts, roles_disabled, shocks, frictions,
            target_frequency=target_freq,
        )

    # ── Helper to build PersonScenarioResult from raw runs ───────────────
    @staticmethod
    def _build_result(name: str,
                      n_iter: int,
                      n_per_iter: int,
                      cap_pcts: list,
                      roles_disabled: list,
                      shocks: list,
                      frictions: list,
                      target_frequency: dict) -> PersonScenarioResult:
        def pct(seq, p):
            if not seq:
                return 0.0
            ordered = sorted(seq)
            idx = max(0, min(len(ordered) - 1,
                             int(round(p / 100 * (len(ordered) - 1)))))
            return ordered[idx]

        mean_caps = statistics.fmean(cap_pcts) if cap_pcts else 0.0
        std_caps = statistics.pstdev(cap_pcts) if len(cap_pcts) > 1 else 0.0
        mean_disabled = statistics.fmean(roles_disabled) if roles_disabled else 0.0
        mean_shock = statistics.fmean(shocks) if shocks else 0.0
        mean_friction = statistics.fmean(frictions) if frictions else 0.0
        mh_eff = (mean_disabled / n_per_iter) if n_per_iter > 0 else 1.0

        return PersonScenarioResult(
            name=name,
            n_iterations=n_iter,
            n_persons_removed_per_iter=n_per_iter,
            mean_pct=mean_caps,
            std_pct=std_caps,
            p05_pct=pct(cap_pcts, 5),
            p25_pct=pct(cap_pcts, 25),
            p50_pct=pct(cap_pcts, 50),
            p75_pct=pct(cap_pcts, 75),
            p95_pct=pct(cap_pcts, 95),
            mean_roles_disabled=mean_disabled,
            mean_tacit_shock=mean_shock,
            mean_replacement_friction=mean_friction,
            multi_hat_efficiency=mh_eff,
            target_frequency=target_frequency,
        )


# ── Convenience: compute the person-level adversarial gap ───────────────
def person_adversarial_gap(random_result: PersonScenarioResult,
                           targeted_result: PersonScenarioResult) -> dict:
    """Quantify the adversary's edge from intelligent targeting.

    Returns
    -------
    dict with:
        capability_gap_pp         : random.mean_pct - targeted.mean_pct
        tacit_shock_premium       : targeted.mean_tacit_shock - random.mean_tacit_shock
        roles_disabled_premium    : targeted.mean_roles_disabled - random.mean_roles_disabled
        friction_premium_months   : targeted.mean_replacement_friction
                                  - random.mean_replacement_friction
    """
    return {
        "capability_gap_pp": random_result.mean_pct - targeted_result.mean_pct,
        "tacit_shock_premium":
            targeted_result.mean_tacit_shock - random_result.mean_tacit_shock,
        "roles_disabled_premium":
            targeted_result.mean_roles_disabled - random_result.mean_roles_disabled,
        "friction_premium_months":
            targeted_result.mean_replacement_friction
            - random_result.mean_replacement_friction,
    }
