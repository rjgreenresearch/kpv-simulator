"""
tests/test_entity_resolver.py — Tests for cross-source identity resolution
============================================================================
"""

import pytest
from dataclasses import dataclass, field

from kpvs.persons import Person, Alias, RoleAssignment
from kpvs.osint_graph import OSINTGraph, GraphEdge, empty_graph
from kpvs.entity_resolver import (
    EntityResolver, MergeCandidate, ResolveResult, CalibrationReport,
)


# ─────────────────────────────────────────────────────────────────────────
# Stubs
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class StubRole:
    id: str
    title: str
    institution: str = ""
    kpci: float = 0.0


@pytest.fixture
def population():
    """Three persons including two Wangs (the disambiguation use case)."""
    return {
        "P-XI": Person(
            id="P-XI", name="Xi Jinping", country="CN",
            name_native="习近平",
            tacit_knowledge=4.0, network_integration=4.0,
            tenure_months=156, substitutes=0,
            aliases=[
                Alias(text="Hsi Chin-p'ing", romanization="wade-giles"),
                Alias(text="Си Цзиньпин", script="cyrl", language="ru"),
            ],
        ),
        "P-WANG-Y": Person(
            id="P-WANG-Y", name="Wang Yi", country="CN",
            name_native="王毅",
            tacit_knowledge=3.5, network_integration=3.0,
            tenure_months=72, substitutes=1,
            aliases=[Alias(text="Wang I", romanization="wade-giles")],
        ),
        "P-WANG-H": Person(
            id="P-WANG-H", name="Wang Huning", country="CN",
            name_native="王沪宁",
            tacit_knowledge=3.5, network_integration=3.0,
            tenure_months=96, substitutes=1,
            aliases=[Alias(text="Wang Hu-ning", romanization="wade-giles")],
        ),
    }


@pytest.fixture
def roles():
    return {
        "CN-PSC-01-GENSEC": StubRole(
            id="CN-PSC-01-GENSEC",
            title="General Secretary, CCP",
            institution="Chinese Communist Party",
            kpci=12.0,
        ),
        "CN-PB-FOREIGN": StubRole(
            id="CN-PB-FOREIGN",
            title="Director, CCP Central Foreign Affairs Commission Office",
            institution="CCP Central Foreign Affairs Commission",
            kpci=9.5,
        ),
        "CN-PSC-04-CPPCC": StubRole(
            id="CN-PSC-04-CPPCC",
            title="Chairman, CPPCC",
            institution="Chinese People's Political Consultative Conference",
            kpci=8.0,
        ),
    }


@pytest.fixture
def assignments():
    return [
        RoleAssignment("P-XI", "CN-PSC-01-GENSEC"),
        RoleAssignment("P-WANG-Y", "CN-PB-FOREIGN"),
        RoleAssignment("P-WANG-H", "CN-PSC-04-CPPCC"),
    ]


# ─────────────────────────────────────────────────────────────────────────
# Single-query resolution
# ─────────────────────────────────────────────────────────────────────────
class TestResolve:
    def test_unambiguous_resolves(self, population):
        r = EntityResolver(population)
        result = r.resolve("Xi Jinping")
        assert result is not None
        assert result.person.id == "P-XI"
        assert result.score == 1.0

    def test_native_script_resolves(self, population):
        r = EntityResolver(population)
        result = r.resolve("习近平")
        assert result is not None
        assert result.person.id == "P-XI"

    def test_alias_resolves(self, population):
        r = EntityResolver(population)
        result = r.resolve("Hsi Chin-p'ing")
        assert result is not None
        assert result.person.id == "P-XI"

    def test_no_match_returns_none(self, population):
        r = EntityResolver(population)
        assert r.resolve("Unrelated Person") is None

    def test_below_threshold_returns_none(self, population):
        r = EntityResolver(population, threshold=0.99)
        # Wade-Giles match scores ~0.95–0.96, below 0.99
        assert r.resolve("Hsi Chinping") is None

    def test_empty_query_returns_none(self, population):
        r = EntityResolver(population)
        assert r.resolve("") is None


# ─────────────────────────────────────────────────────────────────────────
# Role-context disambiguation — the Wang problem
# ─────────────────────────────────────────────────────────────────────────
class TestRoleContextDisambiguation:
    def test_wang_without_context_picks_one(self, population):
        """Bare 'Wang' has high false-positive risk; should still
        return SOMETHING (top score) but it's ambiguous."""
        r = EntityResolver(population, threshold=0.5)
        result = r.resolve("Wang")
        # Either Wang Yi or Wang Huning — both are valid given just 'Wang'
        assert result is not None
        assert result.person.id in ("P-WANG-Y", "P-WANG-H")

    def test_role_hint_picks_correct_wang(self, population, roles, assignments):
        """'Foreign Minister Wang' should resolve to Wang Yi via role hint."""
        r = EntityResolver(population, role_assignments=assignments,
                            roles=roles, threshold=0.5)
        result = r.resolve("Wang Yi", role_hint="Foreign Affairs")
        assert result is not None
        assert result.person.id == "P-WANG-Y"
        assert result.role_context_match

    def test_role_id_direct_lookup(self, population, roles, assignments):
        """Direct role_id is the highest-precision hint."""
        r = EntityResolver(population, role_assignments=assignments,
                            roles=roles, threshold=0.5)
        result = r.resolve("Wang", role_id="CN-PB-FOREIGN")
        assert result is not None
        assert result.role_context_match
        # With role context boost, Wang Yi should win
        assert result.person.id == "P-WANG-Y"

    def test_institution_hint(self, population, roles, assignments):
        r = EntityResolver(population, role_assignments=assignments,
                            roles=roles, threshold=0.5)
        result = r.resolve(
            "Wang Yi",
            institution="Foreign Affairs Commission")
        assert result is not None
        assert result.person.id == "P-WANG-Y"

    def test_no_hint_no_context_match(self, population, roles, assignments):
        r = EntityResolver(population, role_assignments=assignments,
                            roles=roles)
        result = r.resolve("Xi Jinping")
        assert result is not None
        assert not result.role_context_match


# ─────────────────────────────────────────────────────────────────────────
# Bulk merge candidate generation
# ─────────────────────────────────────────────────────────────────────────
class TestFindMergeCandidates:
    def test_finds_obvious_duplicate(self, population):
        """An incoming Person with the Cyrillic alias of Xi should be
        proposed as a merge candidate to canonical Xi."""
        r = EntityResolver(population, threshold=0.85)
        incoming = [Person(
            id="INCOMING-001",
            name="Си Цзиньпин",  # Russian rendering of Xi Jinping
            country="CN",
        )]
        candidates = r.find_merge_candidates(incoming)
        assert len(candidates) >= 1
        assert candidates[0].canonical_id == "P-XI"
        assert candidates[0].incoming_id == "INCOMING-001"

    def test_rejects_unrelated(self, population):
        r = EntityResolver(population, threshold=0.85)
        incoming = [Person(
            id="INCOMING-X", name="Unrelated Person", country="CN",
        )]
        candidates = r.find_merge_candidates(incoming)
        assert len(candidates) == 0

    def test_skips_same_id(self, population):
        """Don't merge a person with their own existing canonical id."""
        r = EntityResolver(population, threshold=0.85)
        incoming = [Person(id="P-XI", name="Xi Jinping", country="CN")]
        candidates = r.find_merge_candidates(incoming)
        assert len(candidates) == 0


# ─────────────────────────────────────────────────────────────────────────
# Merge application
# ─────────────────────────────────────────────────────────────────────────
class TestMerge:
    def test_merge_adds_alias(self, population):
        r = EntityResolver(population)
        dup = Person(
            id="INC-1", name="Hsi Chin-p'ing variant", country="CN",
            name_native="习仲勋的儿子",  # silly placeholder, but tests native
        )
        canonical = r.merge("P-XI", "INC-1", duplicate_person=dup)
        alias_texts = [a.text for a in canonical.aliases]
        assert "Hsi Chin-p'ing variant" in alias_texts
        assert "习仲勋的儿子" in alias_texts

    def test_merge_does_not_duplicate_existing_alias(self, population):
        r = EntityResolver(population)
        # Xi already has 'Hsi Chin-p'ing' as alias
        dup = Person(id="INC-1", name="Hsi Chin-p'ing", country="CN")
        canonical = r.merge("P-XI", "INC-1", duplicate_person=dup)
        # Should NOT create a duplicate alias
        n_matching = sum(1 for a in canonical.aliases
                         if a.text == "Hsi Chin-p'ing")
        assert n_matching == 1

    def test_merge_preserves_provenance(self, population):
        r = EntityResolver(population)
        dup = Person(id="INC-1", name="A New Surface String", country="CN")
        canonical = r.merge("P-XI", "INC-1", duplicate_person=dup,
                             merge_source="test-suite")
        new_alias = next(a for a in canonical.aliases
                          if a.text == "A New Surface String")
        assert new_alias.source == "test-suite"
        assert "INC-1" in new_alias.notes

    def test_merge_unknown_canonical_raises(self, population):
        r = EntityResolver(population)
        dup = Person(id="X", name="X", country="CN")
        with pytest.raises(KeyError):
            r.merge("P-NONEXISTENT", "X", duplicate_person=dup)


# ─────────────────────────────────────────────────────────────────────────
# Bulk graph deduplication
# ─────────────────────────────────────────────────────────────────────────
class TestDeduplicateGraph:
    def test_dedupe_rewrites_edges(self, population):
        """Graph with two duplicate Xi nodes; merge should produce
        single canonical node with all edges preserved."""
        g = empty_graph("CN")
        g.add_person("P-XI", orgs=["CCP"])
        g.add_person("P-DUP-XI", orgs=["CCP"])  # duplicate
        g.add_person("P-WANG-Y")
        g.add_edge(GraphEdge(source="P-XI", target="P-WANG-Y",
                              source_type="person", target_type="person",
                              edge_type="patron"))
        g.add_edge(GraphEdge(source="P-DUP-XI", target="P-WANG-Y",
                              source_type="person", target_type="person",
                              edge_type="patron"))

        r = EntityResolver(population)
        # Add P-DUP-XI to population so merge() can find it
        population["P-DUP-XI"] = Person(
            id="P-DUP-XI", name="Xi Jinping (dup)", country="CN")

        merges = [("P-XI", "P-DUP-XI")]
        new_g = r.deduplicate_graph(g, merges)

        # P-DUP-XI should be gone
        assert "P-DUP-XI" not in new_g.person_ids
        assert "P-XI" in new_g.person_ids

        # Should be one canonical edge from P-XI → P-WANG-Y
        # (duplicate after rewrite was deduped)
        edges_xi_to_wang = [e for e in new_g.edges
                             if e.source == "P-XI" and e.target == "P-WANG-Y"]
        assert len(edges_xi_to_wang) == 1

    def test_dedupe_removes_self_loops(self, population):
        """If duplicate had an edge to canonical, that edge becomes a
        self-loop after rewrite. Should be discarded."""
        g = empty_graph("CN")
        g.add_person("P-XI")
        g.add_person("P-DUP-XI")
        g.add_edge(GraphEdge(source="P-DUP-XI", target="P-XI",
                              source_type="person", target_type="person"))

        r = EntityResolver(population)
        population["P-DUP-XI"] = Person(
            id="P-DUP-XI", name="Xi (dup)", country="CN")
        new_g = r.deduplicate_graph(g, [("P-XI", "P-DUP-XI")])

        # Self-loops not in the new graph
        for e in new_g.edges:
            assert e.source != e.target

    def test_dedupe_rewrites_person_to_orgs(self, population):
        g = empty_graph("CN")
        g.add_person("P-XI", orgs=["CCP"])
        g.add_person("P-DUP-XI", orgs=["CMC"])  # different org membership
        r = EntityResolver(population)
        population["P-DUP-XI"] = Person(
            id="P-DUP-XI", name="Xi (dup)", country="CN")
        new_g = r.deduplicate_graph(g, [("P-XI", "P-DUP-XI")])

        # Canonical now has both org memberships
        assert "CCP" in new_g.person_to_orgs.get("P-XI", set())
        assert "CMC" in new_g.person_to_orgs.get("P-XI", set())
        # Duplicate's entry gone
        assert "P-DUP-XI" not in new_g.person_to_orgs

    def test_dedupe_preserves_role_to_org(self, population):
        g = empty_graph("CN")
        g.add_person("P-XI")
        g.add_person("P-DUP-XI")
        g.link_role_to_org("CN-PSC-01", "CCP")
        r = EntityResolver(population)
        population["P-DUP-XI"] = Person(
            id="P-DUP-XI", name="Xi (dup)", country="CN")
        new_g = r.deduplicate_graph(g, [("P-XI", "P-DUP-XI")])
        assert new_g.role_to_org.get("CN-PSC-01") == "CCP"

    def test_dedupe_accepts_merge_candidate_objects(self, population):
        g = empty_graph("CN")
        g.add_person("P-XI")
        g.add_person("P-DUP-XI")
        r = EntityResolver(population)
        population["P-DUP-XI"] = Person(
            id="P-DUP-XI", name="Xi (dup)", country="CN")

        mc = MergeCandidate(
            incoming_id="P-DUP-XI",
            incoming_name="Xi (dup)",
            canonical_id="P-XI",
            canonical_name="Xi Jinping",
            score=0.95,
        )
        new_g = r.deduplicate_graph(g, [mc])
        assert "P-DUP-XI" not in new_g.person_ids


# ─────────────────────────────────────────────────────────────────────────
# Calibration
# ─────────────────────────────────────────────────────────────────────────
class TestCalibration:
    def test_calibration_perfect(self, population):
        r = EntityResolver(population)
        ground_truth = [
            ("Xi Jinping", "P-XI"),
            ("习近平", "P-XI"),
            ("Wang Yi", "P-WANG-Y"),
            ("Wang Huning", "P-WANG-H"),
            ("Unrelated stranger", None),
        ]
        report = r.calibrate(ground_truth, thresholds=[0.5, 0.7, 0.9])
        assert report.n_pairs == 5
        assert report.best_f1 >= 0.8

    def test_high_threshold_increases_precision_decreases_recall(
            self, population):
        r = EntityResolver(population)
        ground_truth = [
            # Good matches
            ("Xi Jinping", "P-XI"),
            ("Hsi Chinping", "P-XI"),  # Wade-Giles, ~0.96
            # Tricky cases
            ("Wang", "P-WANG-Y"),  # ambiguous; depends on threshold
        ]
        report = r.calibrate(ground_truth, thresholds=[0.5, 0.99])
        # At 0.5 threshold, recall is high; at 0.99, recall drops
        low = next(r for r in report.threshold_table if r["threshold"] == 0.5)
        high = next(r for r in report.threshold_table if r["threshold"] == 0.99)
        assert high["recall"] <= low["recall"]


# ─────────────────────────────────────────────────────────────────────────
# Resolver options validation
# ─────────────────────────────────────────────────────────────────────────
class TestResolverConstruction:
    def test_invalid_threshold_raises(self, population):
        with pytest.raises(ValueError, match="threshold"):
            EntityResolver(population, threshold=1.5)
        with pytest.raises(ValueError, match="threshold"):
            EntityResolver(population, threshold=0)

    def test_minimal_construction(self, population):
        """Resolver should work with just population (no roles/graph)."""
        r = EntityResolver(population)
        result = r.resolve("Xi Jinping")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
