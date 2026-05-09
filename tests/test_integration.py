"""
tests/test_integration.py — End-to-end smoke test for the full pipeline
==========================================================================

Verifies that all five PRs compose correctly:
  PR #1   — Person + Effective KPCI
  PR #1.5 — Aliases + name matching
  PR #2   — Person random/targeted attrition
  PR #3   — Graph cascade
  PR #4   — Faction purge
  PR #5   — Entity resolver

This is a single-test smoke check; behavioral correctness is covered by
the per-module test suites.
"""

import pytest
from dataclasses import dataclass, field

from kpvs import (
    # Data model
    Person, Alias, RoleAssignment,
    # Effective KPCI
    effective_kpci, continuity_loss,
    # Name matching
    find_person, match_score,
    # Simulators
    PersonAwareSimulator,
    FactionAwareSimulator, run_faction_vs_random,
    GraphAwareSimulator, cascade_vs_seed_only,
    # Graph
    OSINTGraph, GraphEdge, empty_graph, auto_apex_edges,
    # Entity resolver
    EntityResolver, MergeCandidate,
)


@dataclass
class StubRole:
    id: str
    title: str
    substitution_timeline: float
    documentation_ratio: float
    adversarial_observability: float
    capability_weight: float = 1.0
    institution: str = ""

    @property
    def kpci(self) -> float:
        return (self.substitution_timeline
                + self.documentation_ratio
                + self.adversarial_observability)


@dataclass
class StubOrg:
    name: str
    roles: list = field(default_factory=list)


def test_full_pipeline_smoke():
    """Single end-to-end run exercising every PR."""
    # ─── Build org (PR #1) ────────────────────────────────────────────────
    roles_dict = {
        "R1": StubRole("R1", "Apex", 4, 4, 4, 5.0, institution="CCP"),
        "R2": StubRole("R2", "Senior", 3, 3, 3, 3.0, institution="CMC"),
        "R3": StubRole("R3", "Mid", 2, 2, 2, 2.0, institution="State Council"),
        "R4": StubRole("R4", "Junior A", 1, 2, 1, 1.0,
                       institution="State Council"),
        "R5": StubRole("R5", "Junior B", 1, 1, 1, 0.5,
                       institution="State Council"),
    }
    org = StubOrg(name="Test Org", roles=list(roles_dict.values()))

    # ─── Build persons with aliases (PR #1.5) and factions (PR #4) ───────
    persons = {
        "P1": Person(
            id="P1", name="Apex Leader", country="CN",
            name_native="顶级",
            tacit_knowledge=4.0, network_integration=4.0,
            tenure_months=120, substitutes=0,
            factions=["regime-apex"],
            aliases=[Alias(text="顶级", script="hans", language="zh"),
                     Alias(text="Apex Leeder", confidence=0.7,
                           notes="OCR error variant")],
        ),
        "P2": Person(
            id="P2", name="Second Officer", country="CN",
            tacit_knowledge=3.0, network_integration=3.0,
            tenure_months=60, substitutes=2,
            factions=["regime-apex"],
        ),
        "P3": Person(
            id="P3", name="Third Officer", country="CN",
            tacit_knowledge=2.0, network_integration=2.0,
            tenure_months=24, substitutes=3,
        ),
        "P4": Person(
            id="P4", name="Fourth Officer", country="CN",
            tacit_knowledge=1.0, network_integration=1.0,
            tenure_months=12, substitutes=4,
        ),
        "P5": Person(
            id="P5", name="Fifth Officer", country="CN",
            tacit_knowledge=0.5, network_integration=0.5,
            tenure_months=6, substitutes=5,
        ),
    }
    assignments = [
        RoleAssignment("P1", "R1", capacity=0.6),
        RoleAssignment("P1", "R2", capacity=0.4),  # multi-hat
        RoleAssignment("P2", "R3"),
        RoleAssignment("P3", "R4"),
        RoleAssignment("P4", "R5"),
        # P5 unassigned — graph context only
    ]

    # ─── Effective KPCI (PR #1) ──────────────────────────────────────────
    apex_eff = effective_kpci(roles_dict["R1"], persons["P1"])
    assert apex_eff >= roles_dict["R1"].kpci  # floor invariant
    diag = continuity_loss(roles_dict["R1"], persons["P1"])
    assert "capability_loss" in diag
    assert "tacit_shock" in diag

    # ─── Fuzzy name matching (PR #1.5) ───────────────────────────────────
    assert match_score("Apex Leader", "Apex Leeder") > 0.85
    found = find_person("Apex Leader", persons, threshold=0.85)
    assert found is not None and found[0].id == "P1"

    # ─── PersonAwareSimulator scenarios (PR #2) ──────────────────────────
    sim_p = PersonAwareSimulator(org, persons, assignments, seed=42)
    rnd = sim_p.scenario_person_random_attrition(
        n_iterations=200, n_persons_per_iter=1)
    adv = sim_p.scenario_person_targeted_attrition(
        n_iterations=200, n_persons_per_iter=1, accuracy=1.0)
    # Smoke check: both scenarios ran and produced expected fields.
    # Behavioral correctness (targeted < random) is verified in
    # tests/test_person_simulator.py with appropriately-sized fixtures.
    assert 0 <= rnd.mean_pct <= 100
    assert 0 <= adv.mean_pct <= 100
    assert adv.target_frequency  # adversarial populates this; random doesn't

    # ─── Faction purge (PR #4) ───────────────────────────────────────────
    sim_f = FactionAwareSimulator(org, persons, assignments, seed=42)
    cmp = run_faction_vs_random(
        sim_f, faction_tag="regime-apex", n_iterations=500)
    assert cmp["faction"].faction_size == 2
    assert cmp["faction"].direct_roles_disabled == 3  # P1 multi-hat

    # ─── Build OSINT graph (PR #3) ───────────────────────────────────────
    graph = empty_graph("CN")
    graph.add_person("P1", orgs=["CCP"])
    graph.add_person("P2", orgs=["CMC"])
    graph.add_person("P3", orgs=["State Council"])
    graph.add_person("P4", orgs=["State Council"])
    graph.add_person("P5", orgs=["State Council"])
    graph.add_edge(GraphEdge(
        source="P1", target="P2",
        source_type="person", target_type="person",
        edge_type="patron", weight=0.7, bidirectional=False,
    ))
    graph.link_role_to_org("R1", "CCP")
    graph.link_role_to_org("R2", "CMC")

    # ─── auto_apex_edges helper ──────────────────────────────────────────
    n_added = auto_apex_edges(graph, persons, assignments, roles_dict,
                                apex_kpci_threshold=10.0)
    assert n_added > 0  # P1 holds R1 (KPCI 12, Tier-1)

    # ─── Graph cascade (PR #3) ───────────────────────────────────────────
    sim_g = GraphAwareSimulator(org, persons, assignments,
                                  graph=graph, seed=42)
    cascade_compare = cascade_vs_seed_only(
        sim_g, seed_persons=["P1"],
        default_edge_p=0.5,
        n_iterations=500,
    )
    assert cascade_compare["premium"]["cascade_premium_pp"] >= 0

    # ─── Entity resolver (PR #5) ─────────────────────────────────────────
    resolver = EntityResolver(persons, role_assignments=assignments,
                                roles=roles_dict, threshold=0.85)

    # Single resolution
    r = resolver.resolve("Apex Leader")
    assert r is not None and r.person.id == "P1"

    # Native script
    r2 = resolver.resolve("顶级")
    assert r2 is not None and r2.person.id == "P1"

    # Bulk merge candidate detection
    incoming = [
        Person(id="DUP-P1", name="Apex Leeder", country="CN"),  # OCR variant
        Person(id="UNRELATED", name="Random Stranger", country="CN"),
    ]
    candidates = resolver.find_merge_candidates(incoming)
    assert len(candidates) == 1
    assert candidates[0].canonical_id == "P1"
    assert candidates[0].incoming_id == "DUP-P1"

    # Apply graph deduplication
    graph.add_person("DUP-P1")
    graph.add_edge(GraphEdge(
        source="DUP-P1", target="P3",
        source_type="person", target_type="person",
        edge_type="co_event",
    ))
    persons["DUP-P1"] = incoming[0]

    new_graph = resolver.deduplicate_graph(graph, candidates)
    assert "DUP-P1" not in new_graph.person_ids
    # The edge from DUP-P1 → P3 should now be from P1 → P3
    rewritten = [e for e in new_graph.edges
                 if e.source == "P1" and e.target == "P3"]
    assert len(rewritten) >= 1

    # And P1 picked up an alias for the OCR variant
    p1 = resolver.population["P1"]
    alias_texts = [a.text for a in p1.aliases]
    assert any("Apex Leeder" in t for t in alias_texts)

    # All five PRs touched, output sane.
