"""
kpvs/cascade_simulator.py — Graph-aware cascade scenarios for KPVS
====================================================================

Adds graph-aware cascade propagation to the simulator inheritance chain:

    KPVSimulator (existing)
      → PersonAwareSimulator
        → FactionAwareSimulator
          → GraphAwareSimulator   ← NEW

GraphAwareSimulator inherits all prior scenarios and adds
`scenario_graph_cascade`, which propagates failures through an
OSINTGraph using the Independent Cascade Model (ICM).

Independent Cascade Model
-------------------------
Standard influence-propagation model in network science. When node u
fails at step t, each not-yet-failed neighbor v becomes a candidate
to fail at step t+1, with probability:

    p(u → v) = edge_weight(u, v) if defined,
               else edge_type_weight(type(u, v)) if defined,
               else default_p.

Each propagation attempt is an independent Bernoulli trial. The cascade
runs until equilibrium (no new activations) or until max_depth.

Person/Org duality
------------------
When a graph org fails, all persons attached to that org via
`person_to_orgs` are added to the failed-persons set. Org-to-org edges
also propagate — losing a parent agency cascades to subsidiary agencies.

Capability accounting
---------------------
Capability loss is computed only over persons in the simulator's roster
(those with assignments). Persons known in the graph but without
assignments propagate cascade pressure but contribute no capability loss.
This lets analysts include broader graph context (junior officers,
liaison personnel) without inflating the capability denominator.
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from typing import Optional

from kpvs.faction_purge import FactionAwareSimulator
from kpvs.osint_graph import OSINTGraph

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class CascadeResult:
    """Output of a graph-cascade scenario.

    Attributes
    ----------
    name              : descriptive label
    n_iterations      : Monte Carlo samples
    seed_persons      : input — person_ids initially failed
    seed_orgs         : input — org_ids initially failed
    default_edge_p    : default activation probability used
    max_depth         : depth cap

    Capability-remaining distribution:
    mean_pct, std_pct, p05_pct, p50_pct, p95_pct

    Cascade-specific diagnostics:
    mean_total_persons_failed   : seed + cascaded
    mean_total_orgs_failed
    mean_max_depth_reached      : how far the cascade actually propagated
    mean_amplification_factor   : total_failed / |seed_persons + seed_orgs|

    Most-frequent victims (network choke points):
    person_failure_freq         : dict[person_id, int] counts across iters
    org_failure_freq            : dict[org_id, int]

    Comparison-to-baseline (filled by run_cascade_vs_seed_only):
    seed_only_pct               : mean_pct if cascade were disabled
    cascade_premium_pp          : seed_only_pct - mean_pct
    """
    name: str
    n_iterations: int
    seed_persons: list
    seed_orgs: list
    default_edge_p: float
    max_depth: int

    mean_pct: float
    std_pct: float
    p05_pct: float
    p50_pct: float
    p95_pct: float

    mean_total_persons_failed: float
    mean_total_orgs_failed: float
    mean_max_depth_reached: float
    mean_amplification_factor: float

    person_failure_freq: dict = field(default_factory=dict)
    org_failure_freq: dict = field(default_factory=dict)

    seed_only_pct: float = 0.0
    cascade_premium_pp: float = 0.0

    def summary_line(self) -> str:
        return (f"{self.name:<32} "
                f"seed={len(self.seed_persons)+len(self.seed_orgs):>2} "
                f"failed={self.mean_total_persons_failed:.1f}p+"
                f"{self.mean_total_orgs_failed:.1f}o "
                f"amp×{self.mean_amplification_factor:.2f} "
                f"depth={self.mean_max_depth_reached:.1f} "
                f"cap={self.mean_pct:.1f}%")


# ─────────────────────────────────────────────────────────────────────────
# Single cascade run (deterministic given RNG state)
# ─────────────────────────────────────────────────────────────────────────
def _resolve_edge_p(edge_weight, edge_type: str,
                    edge_type_weights: dict,
                    default_p: float) -> float:
    """Edge probability resolution order:
       1. Explicit edge.weight
       2. Per-edge-type weight from edge_type_weights
       3. default_p
    """
    if edge_weight is not None:
        return edge_weight
    if edge_type and edge_type in edge_type_weights:
        return edge_type_weights[edge_type]
    return default_p


def _run_single_cascade(graph: OSINTGraph,
                        seed_persons: list,
                        seed_orgs: list,
                        default_p: float,
                        max_depth: int,
                        edge_type_weights: dict,
                        org_to_member_p: float,
                        rng) -> dict:
    """Execute one Monte Carlo cascade.

    Returns
    -------
    dict with:
      failed_persons      : set of person_ids
      failed_orgs         : set of org_ids
      max_depth_reached   : actual depth cascade ran
      activation_history  : list[(depth, node_id, node_type)]
    """
    failed_persons: set = set(seed_persons)
    failed_orgs: set = set(seed_orgs)

    # Org-membership cascade for seed orgs (immediate)
    for oid in seed_orgs:
        for pid in graph.persons_in_org(oid):
            failed_persons.add(pid)

    activation_history = (
        [(0, n, "person") for n in seed_persons]
        + [(0, n, "org") for n in seed_orgs]
    )

    current_persons = set(seed_persons)
    current_orgs = set(seed_orgs)
    max_depth_reached = 0

    for depth in range(1, max_depth + 1):
        new_persons: set = set()
        new_orgs: set = set()

        # ── Propagate from active persons ────────────────────────────────
        for pid in current_persons:
            for neighbor_id, neighbor_type, weight, etype in graph.neighbors(pid):
                if neighbor_type == "person":
                    if neighbor_id in failed_persons or neighbor_id in new_persons:
                        continue
                    p = _resolve_edge_p(weight, etype,
                                         edge_type_weights, default_p)
                    if rng.random() < p:
                        new_persons.add(neighbor_id)
                else:  # org
                    if neighbor_id in failed_orgs or neighbor_id in new_orgs:
                        continue
                    p = _resolve_edge_p(weight, etype,
                                         edge_type_weights, default_p)
                    if rng.random() < p:
                        new_orgs.add(neighbor_id)

        # ── Propagate from active orgs ───────────────────────────────────
        for oid in current_orgs:
            # Org failure → all attached persons fail (high probability)
            for pid in graph.persons_in_org(oid):
                if pid in failed_persons or pid in new_persons:
                    continue
                if rng.random() < org_to_member_p:
                    new_persons.add(pid)

            # Org-to-org edges (already covered above via neighbors())
            for neighbor_id, neighbor_type, weight, etype in graph.neighbors(oid):
                if neighbor_type == "org":
                    if neighbor_id in failed_orgs or neighbor_id in new_orgs:
                        continue
                    p = _resolve_edge_p(weight, etype,
                                         edge_type_weights, default_p)
                    if rng.random() < p:
                        new_orgs.add(neighbor_id)
                else:  # person
                    if neighbor_id in failed_persons or neighbor_id in new_persons:
                        continue
                    p = _resolve_edge_p(weight, etype,
                                         edge_type_weights, default_p)
                    if rng.random() < p:
                        new_persons.add(neighbor_id)

        # When a new org activates this wave, its members cascade too
        for oid in new_orgs:
            for pid in graph.persons_in_org(oid):
                if pid in failed_persons or pid in new_persons:
                    continue
                # Members of a freshly-failed org are at very high risk
                if rng.random() < org_to_member_p:
                    new_persons.add(pid)

        if not new_persons and not new_orgs:
            break  # equilibrium

        max_depth_reached = depth
        for nid in new_persons:
            activation_history.append((depth, nid, "person"))
        for nid in new_orgs:
            activation_history.append((depth, nid, "org"))

        failed_persons.update(new_persons)
        failed_orgs.update(new_orgs)
        current_persons = new_persons
        current_orgs = new_orgs

    return {
        "failed_persons": failed_persons,
        "failed_orgs": failed_orgs,
        "max_depth_reached": max_depth_reached,
        "activation_history": activation_history,
    }


# ─────────────────────────────────────────────────────────────────────────
# GraphAwareSimulator
# ─────────────────────────────────────────────────────────────────────────
class GraphAwareSimulator(FactionAwareSimulator):
    """Final layer in the simulator inheritance chain. Adds graph-aware
    cascade scenario.

    Parameters
    ----------
    organization, persons, assignments, seed
        — as in PersonAwareSimulator / FactionAwareSimulator
    graph : OSINTGraph, optional
        The OSINT graph for cascade propagation. If None, the cascade
        scenario raises; all other scenarios still work.
    """

    def __init__(self, organization, persons, assignments,
                 graph: Optional[OSINTGraph] = None,
                 seed: Optional[int] = None):
        super().__init__(organization, persons, assignments, seed=seed)
        self.graph = graph

    def scenario_graph_cascade(
        self,
        seed_persons: Optional[list] = None,
        seed_orgs: Optional[list] = None,
        default_edge_p: float = 0.25,
        edge_type_weights: Optional[dict] = None,
        org_to_member_p: float = 0.6,
        max_depth: int = 10,
        n_iterations: int = 1000,
        name: Optional[str] = None,
    ) -> CascadeResult:
        """Run a graph-cascade scenario.

        Parameters
        ----------
        seed_persons      : list[person_id] initially failed
        seed_orgs         : list[org_id] initially failed
        default_edge_p    : ∈ [0, 1] — fallback edge activation probability
                            when edge has no explicit weight or type-weight
        edge_type_weights : dict[edge_type, p] — per-type override.
                            E.g., {'reports_to': 0.6, 'co_event': 0.1}
        org_to_member_p   : ∈ [0, 1] — when an org fails, probability
                            that each of its members also fails. Default
                            0.6 reflects that membership ties are stronger
                            than ad-hoc edges.
        max_depth         : maximum cascade waves to simulate. Real cascades
                            often equilibrate by depth 4-6; 10 is safe cap.
        n_iterations      : Monte Carlo samples
        name              : optional label

        Returns
        -------
        CascadeResult
        """
        if self.graph is None:
            raise ValueError(
                "GraphAwareSimulator was constructed without a graph. "
                "Pass an OSINTGraph to the constructor to use this scenario.")

        if seed_persons is None:
            seed_persons = []
        if seed_orgs is None:
            seed_orgs = []
        if not seed_persons and not seed_orgs:
            raise ValueError("Must provide at least one seed (person or org).")

        if not 0 <= default_edge_p <= 1:
            raise ValueError(
                f"default_edge_p must be in [0, 1]; got {default_edge_p}")
        if not 0 <= org_to_member_p <= 1:
            raise ValueError(
                f"org_to_member_p must be in [0, 1]; got {org_to_member_p}")

        edge_type_weights = edge_type_weights or {}

        # Validate seeds exist in graph
        for pid in seed_persons:
            if pid not in self.graph.person_ids:
                logger.warning(
                    "seed person %r not in graph — adding for cascade", pid)
                self.graph.person_ids.add(pid)
        for oid in seed_orgs:
            if oid not in self.graph.org_ids:
                logger.warning(
                    "seed org %r not in graph — adding for cascade", oid)
                self.graph.org_ids.add(oid)

        # ── Monte Carlo loop ─────────────────────────────────────────────
        cap_pcts = []
        n_persons_failed = []
        n_orgs_failed = []
        depths = []
        person_freq: dict = {}
        org_freq: dict = {}

        for _ in range(n_iterations):
            run = _run_single_cascade(
                graph=self.graph,
                seed_persons=seed_persons,
                seed_orgs=seed_orgs,
                default_p=default_edge_p,
                max_depth=max_depth,
                edge_type_weights=edge_type_weights,
                org_to_member_p=org_to_member_p,
                rng=self._rng,
            )

            # Capability accounting: union of failed persons +
            # persons in roles attached to failed orgs (via role_to_org)
            removal_set = set(run["failed_persons"])
            for oid in run["failed_orgs"]:
                for rid in self.graph.roles_in_org(oid):
                    # All persons assigned to this role
                    for a in self.assignments:
                        if a.role_id == rid:
                            removal_set.add(a.person_id)

            # Filter to persons in our roster
            tracked_removed = [pid for pid in removal_set
                               if pid in self._roles_per_person]

            impact = self._compute_removal_impact(tracked_removed)
            cap_pcts.append(impact["capability_remaining_pct"])
            n_persons_failed.append(len(run["failed_persons"]))
            n_orgs_failed.append(len(run["failed_orgs"]))
            depths.append(run["max_depth_reached"])

            for pid in run["failed_persons"]:
                person_freq[pid] = person_freq.get(pid, 0) + 1
            for oid in run["failed_orgs"]:
                org_freq[oid] = org_freq.get(oid, 0) + 1

        # ── Build result ──────────────────────────────────────────────────
        def pct(seq, p):
            if not seq:
                return 0.0
            ordered = sorted(seq)
            idx = max(0, min(len(ordered) - 1,
                             int(round(p / 100 * (len(ordered) - 1)))))
            return ordered[idx]

        seed_total = len(seed_persons) + len(seed_orgs)
        mean_p_failed = statistics.fmean(n_persons_failed) if n_persons_failed else 0.0
        mean_o_failed = statistics.fmean(n_orgs_failed) if n_orgs_failed else 0.0
        amplification = ((mean_p_failed + mean_o_failed) / seed_total
                         if seed_total > 0 else 1.0)

        return CascadeResult(
            name=name or f"Graph Cascade (seed={seed_total}, p={default_edge_p:.2f})",
            n_iterations=n_iterations,
            seed_persons=list(seed_persons),
            seed_orgs=list(seed_orgs),
            default_edge_p=default_edge_p,
            max_depth=max_depth,
            mean_pct=statistics.fmean(cap_pcts) if cap_pcts else 0.0,
            std_pct=statistics.pstdev(cap_pcts) if len(cap_pcts) > 1 else 0.0,
            p05_pct=pct(cap_pcts, 5),
            p50_pct=pct(cap_pcts, 50),
            p95_pct=pct(cap_pcts, 95),
            mean_total_persons_failed=mean_p_failed,
            mean_total_orgs_failed=mean_o_failed,
            mean_max_depth_reached=statistics.fmean(depths) if depths else 0.0,
            mean_amplification_factor=amplification,
            person_failure_freq=person_freq,
            org_failure_freq=org_freq,
        )


# ─────────────────────────────────────────────────────────────────────────
# Comparison helper: cascade vs seed-only baseline
# ─────────────────────────────────────────────────────────────────────────
def cascade_vs_seed_only(sim: GraphAwareSimulator,
                          seed_persons: Optional[list] = None,
                          seed_orgs: Optional[list] = None,
                          default_edge_p: float = 0.25,
                          edge_type_weights: Optional[dict] = None,
                          org_to_member_p: float = 0.6,
                          max_depth: int = 10,
                          n_iterations: int = 1000) -> dict:
    """Run the cascade scenario AND a no-propagation baseline (seed only).

    The cascade premium = seed_only_capability − cascade_capability
    quantifies the additional damage from network spillover beyond the
    direct seed impact. This is the operationally meaningful number for
    asking "how much does the cascade actually matter?"

    Returns
    -------
    {'cascade': CascadeResult, 'seed_only': dict, 'premium': dict}
    """
    cascade = sim.scenario_graph_cascade(
        seed_persons=seed_persons,
        seed_orgs=seed_orgs,
        default_edge_p=default_edge_p,
        edge_type_weights=edge_type_weights,
        org_to_member_p=org_to_member_p,
        max_depth=max_depth,
        n_iterations=n_iterations,
    )

    # Seed-only baseline: same seed but no propagation (equivalent to
    # depth=0 or default_edge_p=0)
    seed_only = sim.scenario_graph_cascade(
        seed_persons=seed_persons,
        seed_orgs=seed_orgs,
        default_edge_p=0.0,            # no edge activation
        edge_type_weights={},
        org_to_member_p=org_to_member_p,  # org membership still cascades
        max_depth=0,                   # no propagation waves
        n_iterations=max(100, n_iterations // 10),  # baseline can be cheaper
        name="Seed-only baseline",
    )

    cascade.seed_only_pct = seed_only.mean_pct
    cascade.cascade_premium_pp = seed_only.mean_pct - cascade.mean_pct

    return {
        "cascade": cascade,
        "seed_only": seed_only,
        "premium": {
            "cascade_premium_pp": cascade.cascade_premium_pp,
            "amplification_factor": cascade.mean_amplification_factor,
            "extra_persons_failed":
                cascade.mean_total_persons_failed
                - seed_only.mean_total_persons_failed,
            "extra_orgs_failed":
                cascade.mean_total_orgs_failed
                - seed_only.mean_total_orgs_failed,
        },
    }
