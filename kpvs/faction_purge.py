"""
kpvs/faction_purge.py — Faction-purge Monte Carlo scenario
============================================================

Models the removal of a coherent leadership subgroup defined by shared
faction membership. Captures dynamics that role-by-role attrition cannot:
correlated loss across persons sharing patronage networks, ideological
schools, institutional cohorts, or family ties.

Historical reference cases this scenario captures
-------------------------------------------------
  • Wagner-Surovikin June 2023 — Russian regime moved against
    Wagner-affiliated officers after Prigozhin's mutiny
  • Xi anti-corruption purges 2012-2017 — sequential removal of the
    Bo Xilai, Zhou Yongkang, and Ling Jihua networks
  • Stalin's NKVD purges 1936-1938 — coherent waves against Trotskyists,
    Old Bolsheviks, then NKVD itself
  • Kim Jong Un's 2013-2017 consolidation — removal of the Jang
    Song-thaek network
  • Saudi 2017 Ritz-Carlton "anti-corruption" detentions — coherent
    targeting of rival princely networks

Scenario mechanics
------------------
A faction is defined either by a tag string (matching Person.factions)
or by a callable predicate (for complex multi-criteria membership). The
scenario:

  1. Removes ALL persons matching the faction definition (deterministic core)
  2. Optionally applies stochastic "secondary loss" — non-faction persons
     are independently lost with probability `secondary_loss_p`, modeling
     general political turmoil following a major purge
  3. Reports both the deterministic floor and the stochastic distribution

When `secondary_loss_p == 0`, the scenario is fully deterministic and
runs once. When > 0, n_iterations samples the spillover distribution.

The right comparison baseline is N-equivalent random attrition — given
a faction of K members, the comparator removes K random persons. The
gap quantifies the "concentration premium" of coordinated targeting
versus scattered turnover.
"""

from __future__ import annotations

import logging
import random
import statistics
from dataclasses import dataclass, field
from typing import Callable, Optional

from kpvs.persons import Person
from kpvs.person_simulator import PersonAwareSimulator, PersonScenarioResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class FactionPurgeResult:
    """Output of a faction-purge scenario.

    Attributes
    ----------
    name                : descriptive label for reporting
    faction_tag         : the tag used to resolve membership (or ""
                          if a callable filter was used)
    faction_size        : number of persons identified as members
    member_ids          : list of resolved person IDs

    deterministic       : True if secondary_loss_p == 0 (single iteration)
    n_iterations        : number of stochastic samples (1 if deterministic)
    secondary_loss_p    : probability of non-faction loss per iteration

    Capability-remaining distribution (% of total org capability):
    mean_pct, std_pct, p05_pct, p50_pct, p95_pct

    Faction-specific diagnostics:
    direct_roles_disabled       : roles failed from faction core (deterministic)
    multi_hat_amplification     : direct_roles - faction_size (extra leverage
                                  via multi-hat persons inside the faction)
    direct_tacit_shock          : aggregate TK lost from faction core
    concentrated_failures       : roles where occupant in faction AND
                                  substitutes <= 1 (no bench)
    countries_affected          : ISO-2 codes of countries with members
    cross_org_amplifier         : True if faction crosses org boundaries

    Stochastic spillover (zero if deterministic):
    mean_secondary_loss         : avg additional non-faction persons lost
    secondary_tacit_shock       : avg additional TK lost via spillover
    """

    name: str
    faction_tag: str
    faction_size: int
    member_ids: list

    deterministic: bool
    n_iterations: int
    secondary_loss_p: float

    mean_pct: float
    std_pct: float
    p05_pct: float
    p50_pct: float
    p95_pct: float

    direct_roles_disabled: int
    multi_hat_amplification: int
    direct_tacit_shock: float
    concentrated_failures: int
    countries_affected: list
    cross_org_amplifier: bool

    mean_secondary_loss: float = 0.0
    secondary_tacit_shock: float = 0.0

    def summary_line(self) -> str:
        det_str = "DET" if self.deterministic else f"STO×{self.n_iterations}"
        return (f"{self.name:<32} "
                f"members={self.faction_size:>2} "
                f"roles={self.direct_roles_disabled:>2} "
                f"(+{self.multi_hat_amplification} multi-hat) "
                f"cap={self.mean_pct:5.1f}% [{det_str}]")


# ─────────────────────────────────────────────────────────────────────────
# Faction membership resolution
# ─────────────────────────────────────────────────────────────────────────
def resolve_faction_members(persons,
                            faction_tag: Optional[str] = None,
                            faction_filter: Optional[Callable] = None) -> list:
    """Resolve faction membership to a list of person IDs.

    Parameters
    ----------
    persons         : dict[person_id, Person] OR iterable of Person
    faction_tag     : tag string matched against Person.factions
    faction_filter  : callable (person) -> bool. Takes precedence over
                      faction_tag if both are provided.

    Returns
    -------
    list[str] of person IDs matching the faction definition.
    """
    if faction_filter is None and faction_tag is None:
        raise ValueError(
            "Must provide either faction_tag or faction_filter.")

    pool = persons.values() if isinstance(persons, dict) else persons

    if faction_filter is not None:
        return [p.id for p in pool if faction_filter(p)]

    return [p.id for p in pool
            if faction_tag in (getattr(p, "factions", None) or [])]


# ─────────────────────────────────────────────────────────────────────────
# FactionAwareSimulator — extends PersonAwareSimulator with one new method
# ─────────────────────────────────────────────────────────────────────────
class FactionAwareSimulator(PersonAwareSimulator):
    """PersonAwareSimulator + faction-purge scenario.

    Drop-in replacement for PersonAwareSimulator. Inherits all existing
    scenarios; adds scenario_faction_purge.
    """

    def scenario_faction_purge(
        self,
        faction_tag: Optional[str] = None,
        faction_filter: Optional[Callable] = None,
        secondary_loss_p: float = 0.0,
        n_iterations: int = 1000,
        name: Optional[str] = None,
    ) -> FactionPurgeResult:
        """Run a faction-purge scenario.

        Parameters
        ----------
        faction_tag       : str — tag name in Person.factions to match
        faction_filter    : callable (person) -> bool — overrides tag
        secondary_loss_p  : float ∈ [0, 1] — probability of independent
                            non-faction loss per iteration. Models post-
                            purge political instability. 0 = deterministic.
        n_iterations      : Monte Carlo samples (forced to 1 if
                            secondary_loss_p == 0)
        name              : optional label for reporting

        Returns
        -------
        FactionPurgeResult
        """
        if not 0 <= secondary_loss_p <= 1:
            raise ValueError(
                f"secondary_loss_p must be in [0, 1]; got {secondary_loss_p}")

        # Resolve members
        member_ids = resolve_faction_members(
            self.persons, faction_tag=faction_tag,
            faction_filter=faction_filter)

        if not member_ids:
            raise ValueError(
                f"No persons match faction definition "
                f"(tag={faction_tag!r}, filter={faction_filter!r}).")

        # Determinism: if no secondary loss, one iteration suffices
        deterministic = (secondary_loss_p == 0)
        if deterministic:
            effective_n_iter = 1
        else:
            effective_n_iter = n_iterations

        # ── Deterministic core: compute direct purge impact ───────────────
        direct_impact = self._compute_removal_impact(member_ids)
        direct_roles_disabled = direct_impact["n_roles_disabled"]
        direct_tacit_shock = direct_impact["tacit_shock"]
        multi_hat_amp = direct_roles_disabled - len(member_ids)

        # Members across countries / orgs
        countries_in_faction = sorted({
            self.persons[pid].country for pid in member_ids
            if pid in self.persons
        })
        cross_org = len(countries_in_faction) > 1

        # Concentrated failures: faction-occupied roles with thin bench
        concentrated = 0
        for pid in member_ids:
            person = self.persons.get(pid)
            if person is None:
                continue
            if person.substitutes <= 1:
                # All this person's roles are concentrated failures
                concentrated += len(self._roles_per_person.get(pid, []))

        # ── Stochastic spillover: run n_iterations ───────────────────────
        cap_pcts = []
        secondary_counts = []
        secondary_shocks = []

        non_member_ids = [pid for pid in self._roles_per_person
                          if pid not in member_ids]

        for _ in range(effective_n_iter):
            removed = list(member_ids)
            secondary_count = 0

            if secondary_loss_p > 0:
                for pid in non_member_ids:
                    if self._rng.random() < secondary_loss_p:
                        removed.append(pid)
                        secondary_count += 1

            impact = self._compute_removal_impact(removed)
            cap_pcts.append(impact["capability_remaining_pct"])
            secondary_counts.append(secondary_count)
            secondary_shocks.append(
                impact["tacit_shock"] - direct_tacit_shock)

        # ── Build result ──────────────────────────────────────────────────
        def pct(seq, p):
            if not seq:
                return 0.0
            ordered = sorted(seq)
            idx = max(0, min(len(ordered) - 1,
                             int(round(p / 100 * (len(ordered) - 1)))))
            return ordered[idx]

        mean_caps = statistics.fmean(cap_pcts) if cap_pcts else 0.0
        std_caps = (statistics.pstdev(cap_pcts)
                    if len(cap_pcts) > 1 else 0.0)
        mean_sec = (statistics.fmean(secondary_counts)
                    if secondary_counts else 0.0)
        mean_sec_shock = (statistics.fmean(secondary_shocks)
                          if secondary_shocks else 0.0)

        label = name or (faction_tag or "<callable filter>")

        return FactionPurgeResult(
            name=f"Faction Purge: {label}",
            faction_tag=faction_tag or "",
            faction_size=len(member_ids),
            member_ids=member_ids,
            deterministic=deterministic,
            n_iterations=effective_n_iter,
            secondary_loss_p=secondary_loss_p,
            mean_pct=mean_caps,
            std_pct=std_caps,
            p05_pct=pct(cap_pcts, 5),
            p50_pct=pct(cap_pcts, 50),
            p95_pct=pct(cap_pcts, 95),
            direct_roles_disabled=direct_roles_disabled,
            multi_hat_amplification=multi_hat_amp,
            direct_tacit_shock=direct_tacit_shock,
            concentrated_failures=concentrated,
            countries_affected=countries_in_faction,
            cross_org_amplifier=cross_org,
            mean_secondary_loss=mean_sec,
            secondary_tacit_shock=mean_sec_shock,
        )


# ─────────────────────────────────────────────────────────────────────────
# Comparison helpers
# ─────────────────────────────────────────────────────────────────────────
def faction_concentration_premium(faction_result: FactionPurgeResult,
                                  random_result: PersonScenarioResult) -> dict:
    """Quantify how much worse a coordinated faction purge is than
    losing the same number of persons at random.

    The comparator must be a random-attrition run with
    n_persons_per_iter == faction_result.faction_size.

    Returns
    -------
    dict with:
        capability_premium_pp     : random.mean_pct - faction.mean_pct
        tacit_shock_premium       : faction.direct_tacit_shock
                                  - random.mean_tacit_shock
        roles_premium             : faction.direct_roles_disabled
                                  - random.mean_roles_disabled
        concentration_factor      : capability_premium / random.mean_pct
                                    (premium as fraction of random baseline)
    """
    if random_result.n_persons_removed_per_iter != faction_result.faction_size:
        logger.warning(
            "Comparing faction (size=%d) to random (n=%d) — N mismatch may "
            "produce misleading premium",
            faction_result.faction_size,
            random_result.n_persons_removed_per_iter,
        )

    cap_premium = random_result.mean_pct - faction_result.mean_pct
    return {
        "capability_premium_pp": cap_premium,
        "tacit_shock_premium": (faction_result.direct_tacit_shock
                                - random_result.mean_tacit_shock),
        "roles_premium": (faction_result.direct_roles_disabled
                          - random_result.mean_roles_disabled),
        "concentration_factor": (cap_premium / random_result.mean_pct
                                 if random_result.mean_pct > 0 else 0.0),
    }


def run_faction_vs_random(sim: FactionAwareSimulator,
                          faction_tag: Optional[str] = None,
                          faction_filter: Optional[Callable] = None,
                          n_iterations: int = 2000,
                          secondary_loss_p: float = 0.0) -> dict:
    """Convenience: run faction purge, run equivalent-N random, compute
    premium — all in one call.

    Returns
    -------
    {'faction': FactionPurgeResult, 'random': PersonScenarioResult,
     'premium': dict}
    """
    faction = sim.scenario_faction_purge(
        faction_tag=faction_tag,
        faction_filter=faction_filter,
        secondary_loss_p=secondary_loss_p,
        n_iterations=n_iterations,
    )

    rnd = sim.scenario_person_random_attrition(
        n_iterations=n_iterations,
        n_persons_per_iter=faction.faction_size,
    )

    premium = faction_concentration_premium(faction, rnd)

    return {
        "faction": faction,
        "random": rnd,
        "premium": premium,
    }
