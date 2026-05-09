"""
tests/test_cascade.py — Unit tests for OSINT graph + cascade simulator
========================================================================
"""

import pytest
from dataclasses import dataclass, field

from kpvs.persons import Person, RoleAssignment
from kpvs.osint_graph import OSINTGraph, GraphEdge, empty_graph
from kpvs.cascade_simulator import (
    GraphAwareSimulator, CascadeResult, cascade_vs_seed_only,
)


# ─────────────────────────────────────────────────────────────────────────
# Stubs
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class StubRole:
    id: str
    title: str
    substitution_timeline: float
    documentation_ratio: float
    adversarial_observability: float
    capability_weight: float = 1.0

    @property
    def kpci(self) -> float:
        return (self.substitution_timeline
                + self.documentation_ratio
                + self.adversarial_observability)


@dataclass
class StubOrg:
    name: str
    roles: list = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────
# OSINTGraph tests
# ─────────────────────────────────────────────────────────────────────────
class TestOSINTGraphConstruction:
    def test_empty_graph(self):
        g = empty_graph("CN")
        assert g.country == "CN"
        assert len(g.person_ids) == 0
        assert len(g.edges) == 0

    def test_invalid_country_raises(self):
        with pytest.raises(ValueError):
            OSINTGraph(country="CHN")  # too long

    def test_add_person_with_orgs(self):
        g = empty_graph("CN")
        g.add_person("P1", orgs=["CCP", "MoD"])
        assert "P1" in g.person_ids
        assert "CCP" in g.org_ids
        assert "MoD" in g.org_ids
        assert g.person_to_orgs["P1"] == {"CCP", "MoD"}

    def test_persons_in_org(self):
        g = empty_graph("CN")
        g.add_person("P1", orgs=["CCP"])
        g.add_person("P2", orgs=["CCP", "PLA"])
        g.add_person("P3", orgs=["PLA"])
        assert g.persons_in_org("CCP") == {"P1", "P2"}
        assert g.persons_in_org("PLA") == {"P2", "P3"}

    def test_role_to_org_mapping(self):
        g = empty_graph("CN")
        g.add_org("CCP")
        g.link_role_to_org("CN-PSC-01", "CCP")
        g.link_role_to_org("CN-PSC-02", "CCP")
        g.link_role_to_org("CN-CMC-CHAIR", "CMC")
        assert sorted(g.roles_in_org("CCP")) == ["CN-PSC-01", "CN-PSC-02"]
        assert g.roles_in_org("CMC") == ["CN-CMC-CHAIR"]


class TestGraphEdge:
    def test_valid_edge(self):
        e = GraphEdge(source="P1", target="P2",
                      source_type="person", target_type="person",
                      weight=0.5, edge_type="reports_to")
        assert e.source == "P1"

    def test_self_loop_raises(self):
        with pytest.raises(ValueError, match="Self-loops"):
            GraphEdge(source="P1", target="P1",
                      source_type="person", target_type="person")

    def test_invalid_weight(self):
        with pytest.raises(ValueError, match="weight"):
            GraphEdge(source="P1", target="P2",
                      source_type="person", target_type="person",
                      weight=1.5)

    def test_invalid_node_type(self):
        with pytest.raises(ValueError, match="source_type"):
            GraphEdge(source="P1", target="P2",
                      source_type="alien", target_type="person")


class TestNeighbors:
    def test_neighbors_undirected_default(self):
        g = empty_graph("CN")
        g.add_person("P1")
        g.add_person("P2")
        g.add_edge(GraphEdge(source="P1", target="P2",
                              source_type="person", target_type="person",
                              weight=0.5))
        # bidirectional default
        assert any(n[0] == "P2" for n in g.neighbors("P1"))
        assert any(n[0] == "P1" for n in g.neighbors("P2"))

    def test_neighbors_directed(self):
        g = empty_graph("CN")
        g.add_person("P1")
        g.add_person("P2")
        g.add_edge(GraphEdge(source="P1", target="P2",
                              source_type="person", target_type="person",
                              bidirectional=False))
        assert any(n[0] == "P2" for n in g.neighbors("P1"))
        assert not any(n[0] == "P1" for n in g.neighbors("P2"))

    def test_neighbors_caches_until_mutation(self):
        g = empty_graph("CN")
        g.add_person("P1")
        g.add_person("P2")
        g.add_edge(GraphEdge(source="P1", target="P2",
                              source_type="person", target_type="person"))
        n1 = g.neighbors("P1")
        n2 = g.neighbors("P1")  # cached
        assert n1 == n2
        # mutation invalidates
        g.add_person("P3")
        n3 = g.neighbors("P1")
        # should still work
        assert any(x[0] == "P2" for x in n3)


# ─────────────────────────────────────────────────────────────────────────
# Fixtures for cascade tests
# ─────────────────────────────────────────────────────────────────────────
@pytest.fixture
def small_org():
    return StubOrg(
        name="Test",
        roles=[
            StubRole("R1", "Apex", 4, 4, 4, 5.0),
            StubRole("R2", "Senior", 3, 4, 3, 3.0),
            StubRole("R3", "Mid", 2, 3, 2, 2.0),
            StubRole("R4", "Junior", 1, 2, 1, 1.0),
        ],
    )


@pytest.fixture
def small_persons():
    return {
        "P1": Person(id="P1", name="Alpha", country="CN",
                     tacit_knowledge=4.0, network_integration=4.0,
                     tenure_months=120, substitutes=0),
        "P2": Person(id="P2", name="Beta", country="CN",
                     tacit_knowledge=3.0, network_integration=3.0,
                     tenure_months=60, substitutes=2),
        "P3": Person(id="P3", name="Gamma", country="CN",
                     tacit_knowledge=2.0, network_integration=2.0,
                     tenure_months=24, substitutes=2),
        "P4": Person(id="P4", name="Delta", country="CN",
                     tacit_knowledge=1.5, network_integration=1.5,
                     tenure_months=12, substitutes=3),
    }


@pytest.fixture
def small_assignments():
    return [
        RoleAssignment("P1", "R1"),
        RoleAssignment("P2", "R2"),
        RoleAssignment("P3", "R3"),
        RoleAssignment("P4", "R4"),
    ]


@pytest.fixture
def chain_graph():
    """P1 → P2 → P3 → P4 (chain). High edge weights for predictable cascades."""
    g = empty_graph("CN")
    for pid in ["P1", "P2", "P3", "P4"]:
        g.add_person(pid)
    for src, tgt in [("P1", "P2"), ("P2", "P3"), ("P3", "P4")]:
        g.add_edge(GraphEdge(source=src, target=tgt,
                              source_type="person", target_type="person",
                              weight=0.95, bidirectional=False))
    return g


@pytest.fixture
def unweighted_chain():
    """Same chain but with no explicit weights — default_edge_p applies."""
    g = empty_graph("CN")
    for pid in ["P1", "P2", "P3", "P4"]:
        g.add_person(pid)
    for src, tgt in [("P1", "P2"), ("P2", "P3"), ("P3", "P4")]:
        g.add_edge(GraphEdge(source=src, target=tgt,
                              source_type="person", target_type="person",
                              bidirectional=False))
    return g


@pytest.fixture
def org_graph():
    """P1 ∈ ORG-A; P2, P3 ∈ ORG-B; P4 ∈ ORG-C; ORG-A → ORG-B edge."""
    g = empty_graph("CN")
    g.add_person("P1", orgs=["ORG-A"])
    g.add_person("P2", orgs=["ORG-B"])
    g.add_person("P3", orgs=["ORG-B"])
    g.add_person("P4", orgs=["ORG-C"])
    g.add_edge(GraphEdge(source="ORG-A", target="ORG-B",
                          source_type="org", target_type="org",
                          weight=0.9))
    g.link_role_to_org("R1", "ORG-A")
    g.link_role_to_org("R2", "ORG-B")
    g.link_role_to_org("R3", "ORG-B")
    g.link_role_to_org("R4", "ORG-C")
    return g


# ─────────────────────────────────────────────────────────────────────────
# Cascade simulator basic tests
# ─────────────────────────────────────────────────────────────────────────
class TestGraphAwareSimulatorBasic:
    def test_constructs_with_graph(self, small_org, small_persons,
                                     small_assignments, chain_graph):
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=chain_graph, seed=42)
        assert sim.graph is chain_graph

    def test_constructs_without_graph(self, small_org, small_persons,
                                        small_assignments):
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments, seed=42)
        assert sim.graph is None

    def test_cascade_without_graph_raises(self, small_org, small_persons,
                                            small_assignments):
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments, seed=42)
        with pytest.raises(ValueError, match="without a graph"):
            sim.scenario_graph_cascade(seed_persons=["P1"])

    def test_no_seed_raises(self, small_org, small_persons,
                              small_assignments, chain_graph):
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=chain_graph, seed=42)
        with pytest.raises(ValueError, match="at least one seed"):
            sim.scenario_graph_cascade()


# ─────────────────────────────────────────────────────────────────────────
# Person-person cascade
# ─────────────────────────────────────────────────────────────────────────
class TestPersonCascade:
    def test_chain_propagation_high_p(self, small_org, small_persons,
                                        small_assignments, chain_graph):
        """At p=0.95, a P1 seed should cascade to most/all of P2, P3, P4."""
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=chain_graph, seed=42)
        result = sim.scenario_graph_cascade(
            seed_persons=["P1"],
            default_edge_p=0.95,
            n_iterations=500,
        )
        # Mean failed persons should be close to 4 (full chain)
        assert result.mean_total_persons_failed > 3.0

    def test_low_p_minimal_propagation(self, small_org, small_persons,
                                         small_assignments, unweighted_chain):
        """At p=0.0 with no explicit edge weights, only the seed fails."""
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=unweighted_chain, seed=42)
        result = sim.scenario_graph_cascade(
            seed_persons=["P1"],
            default_edge_p=0.0,
            n_iterations=200,
        )
        assert result.mean_total_persons_failed == 1.0
        assert result.mean_amplification_factor == 1.0

    def test_max_depth_caps_propagation(self, small_org, small_persons,
                                          small_assignments, unweighted_chain):
        """At max_depth=1, only one wave of propagation."""
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=unweighted_chain, seed=42)
        result = sim.scenario_graph_cascade(
            seed_persons=["P1"],
            default_edge_p=1.0,  # always activate
            max_depth=1,
            n_iterations=50,
        )
        # P1 (seed) + at most one wave (P2) = 2 failures max
        assert result.mean_total_persons_failed == 2.0


# ─────────────────────────────────────────────────────────────────────────
# Org cascade
# ─────────────────────────────────────────────────────────────────────────
class TestOrgCascade:
    def test_seed_org_cascades_to_members(self, small_org, small_persons,
                                            small_assignments, org_graph):
        """Seeding ORG-B should immediately fail P2 and P3 (members)."""
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=org_graph, seed=42)
        result = sim.scenario_graph_cascade(
            seed_orgs=["ORG-B"],
            default_edge_p=0.0,  # no edge propagation
            org_to_member_p=1.0,  # all members fail
            max_depth=0,
            n_iterations=20,
        )
        # Must include both P2 and P3 as failed (membership cascade)
        assert result.mean_total_persons_failed >= 2.0
        assert "P2" in result.person_failure_freq
        assert "P3" in result.person_failure_freq

    def test_org_to_org_propagation(self, small_org, small_persons,
                                      small_assignments, org_graph):
        """Failing ORG-A should cascade through O→O edge to ORG-B,
        which then cascades to its members P2, P3."""
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=org_graph, seed=42)
        result = sim.scenario_graph_cascade(
            seed_orgs=["ORG-A"],
            default_edge_p=1.0,
            org_to_member_p=1.0,
            n_iterations=200,
        )
        # ORG-A seed (always); ORG-B from edge weight 0.9 (~90% iterations);
        # so mean orgs failed ≈ 1.9, mean persons failed ≈ 2.8 (P1 + ~1.8 P2/P3)
        assert result.mean_total_orgs_failed > 1.7
        assert result.mean_total_persons_failed > 2.5


# ─────────────────────────────────────────────────────────────────────────
# Cascade premium
# ─────────────────────────────────────────────────────────────────────────
class TestCascadePremium:
    def test_cascade_worse_than_seed_only(self, small_org, small_persons,
                                            small_assignments, chain_graph):
        """Cascade should result in more capability lost than seed-only."""
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=chain_graph, seed=42)
        compare = cascade_vs_seed_only(
            sim, seed_persons=["P1"],
            default_edge_p=0.7,
            n_iterations=500,
        )
        assert compare["premium"]["cascade_premium_pp"] > 0
        assert compare["cascade"].mean_pct < compare["seed_only"].mean_pct

    def test_premium_zero_at_p_zero(self, small_org, small_persons,
                                     small_assignments, unweighted_chain):
        """At default_edge_p=0 on an unweighted graph, cascade collapses
        to seed-only (no edge weights override the default)."""
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=unweighted_chain, seed=42)
        compare = cascade_vs_seed_only(
            sim, seed_persons=["P1"],
            default_edge_p=0.0,
            org_to_member_p=0.0,
            n_iterations=200,
        )
        # No propagation → cascade ≈ seed_only
        assert abs(compare["premium"]["cascade_premium_pp"]) < 0.5


# ─────────────────────────────────────────────────────────────────────────
# Edge type weights
# ─────────────────────────────────────────────────────────────────────────
class TestEdgeTypeWeights:
    def test_per_type_weights_apply(self, small_org, small_persons,
                                      small_assignments):
        """An edge tagged 'reports_to' should use the reports_to weight,
        not the default."""
        g = empty_graph("CN")
        for pid in ["P1", "P2", "P3", "P4"]:
            g.add_person(pid)
        g.add_edge(GraphEdge(source="P1", target="P2",
                              source_type="person", target_type="person",
                              edge_type="reports_to",
                              bidirectional=False))
        g.add_edge(GraphEdge(source="P1", target="P3",
                              source_type="person", target_type="person",
                              edge_type="co_event",
                              bidirectional=False))

        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=g, seed=42)
        result = sim.scenario_graph_cascade(
            seed_persons=["P1"],
            default_edge_p=0.5,
            edge_type_weights={"reports_to": 1.0, "co_event": 0.0},
            n_iterations=200,
        )
        # P2 (reports_to, p=1.0) always fails; P3 (co_event, p=0.0) never
        assert result.person_failure_freq.get("P2", 0) == 200
        assert result.person_failure_freq.get("P3", 0) == 0


# ─────────────────────────────────────────────────────────────────────────
# Reproducibility
# ─────────────────────────────────────────────────────────────────────────
class TestReproducibility:
    def test_same_seed_same_cascade(self, small_org, small_persons,
                                      small_assignments, chain_graph):
        sim1 = GraphAwareSimulator(small_org, small_persons,
                                     small_assignments,
                                     graph=chain_graph, seed=20260508)
        sim2 = GraphAwareSimulator(small_org, small_persons,
                                     small_assignments,
                                     graph=chain_graph, seed=20260508)
        r1 = sim1.scenario_graph_cascade(
            seed_persons=["P1"], default_edge_p=0.5, n_iterations=300)
        r2 = sim2.scenario_graph_cascade(
            seed_persons=["P1"], default_edge_p=0.5, n_iterations=300)
        assert r1.mean_pct == r2.mean_pct
        assert r1.mean_total_persons_failed == r2.mean_total_persons_failed


# ─────────────────────────────────────────────────────────────────────────
# Inheritance: prior scenarios still work
# ─────────────────────────────────────────────────────────────────────────
class TestInheritance:
    def test_random_attrition_still_works(self, small_org, small_persons,
                                            small_assignments, chain_graph):
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=chain_graph, seed=42)
        result = sim.scenario_person_random_attrition(
            n_iterations=200, n_persons_per_iter=2)
        assert result.n_iterations == 200

    def test_faction_purge_still_works(self, small_org, small_persons,
                                         small_assignments, chain_graph):
        # Add faction tags to enable purge
        small_persons["P1"].factions = ["test-faction"]
        small_persons["P2"].factions = ["test-faction"]
        sim = GraphAwareSimulator(small_org, small_persons,
                                    small_assignments,
                                    graph=chain_graph, seed=42)
        result = sim.scenario_faction_purge(faction_tag="test-faction")
        assert result.faction_size == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
