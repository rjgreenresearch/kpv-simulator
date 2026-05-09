"""
tests/test_faction_purge.py — Unit tests for faction-purge scenario
=====================================================================
"""

import pytest
from dataclasses import dataclass, field

from kpvs.persons import Person, RoleAssignment
from kpvs.faction_purge import (
    FactionAwareSimulator, FactionPurgeResult,
    resolve_faction_members, faction_concentration_premium,
    run_faction_vs_random,
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
# Fixtures
# ─────────────────────────────────────────────────────────────────────────
@pytest.fixture
def factional_org():
    """8 roles across two synthetic factions + neutrals."""
    return StubOrg(
        name="Factional Test Org",
        roles=[
            StubRole("R1", "Apex", 4, 4, 4, capability_weight=5.0),       # 12
            StubRole("R2", "Senior A", 4, 3, 3, capability_weight=3.0),   # 10
            StubRole("R3", "Senior B", 3, 4, 3, capability_weight=3.0),   # 10
            StubRole("R4", "Senior C", 3, 3, 3, capability_weight=2.5),   # 9
            StubRole("R5", "Mid A", 2, 3, 2, capability_weight=2.0),      # 7
            StubRole("R6", "Mid B", 2, 3, 2, capability_weight=2.0),      # 7
            StubRole("R7", "Junior A", 1, 2, 1, capability_weight=1.0),   # 4
            StubRole("R8", "Junior B", 1, 2, 1, capability_weight=1.0),   # 4
        ],
    )


@pytest.fixture
def factional_persons():
    """5 persons in faction-A, 3 in faction-B, 1 neutral.

    P-A1 (apex of faction A) is multi-hat (R1 + R2).
    """
    return {
        "P-A1": Person(
            id="P-A1", name="A1 Leader", country="CN",
            tacit_knowledge=4.0, network_integration=4.0,
            tenure_months=120, substitutes=0,
            factions=["faction-a", "tsinghua-mafia"],
        ),
        "P-A2": Person(
            id="P-A2", name="A2", country="CN",
            tacit_knowledge=3.0, network_integration=3.0,
            tenure_months=60, substitutes=1,
            factions=["faction-a"],
        ),
        "P-A3": Person(
            id="P-A3", name="A3", country="CN",
            tacit_knowledge=2.5, network_integration=2.5,
            tenure_months=36, substitutes=2,
            factions=["faction-a"],
        ),
        "P-A4": Person(
            id="P-A4", name="A4", country="CN",
            tacit_knowledge=2.0, network_integration=2.0,
            tenure_months=24, substitutes=3,
            factions=["faction-a"],
        ),
        "P-A5": Person(
            id="P-A5", name="A5", country="CN",
            tacit_knowledge=1.5, network_integration=1.5,
            tenure_months=12, substitutes=3,
            factions=["faction-a", "youth-league"],
        ),
        "P-B1": Person(
            id="P-B1", name="B1 Leader", country="CN",
            tacit_knowledge=3.0, network_integration=3.0,
            tenure_months=72, substitutes=2,
            factions=["faction-b"],
        ),
        "P-B2": Person(
            id="P-B2", name="B2", country="CN",
            tacit_knowledge=2.0, network_integration=2.0,
            tenure_months=36, substitutes=3,
            factions=["faction-b"],
        ),
        "P-B3": Person(
            id="P-B3", name="B3", country="CN",
            tacit_knowledge=1.5, network_integration=1.5,
            tenure_months=24, substitutes=3,
            factions=["faction-b"],
        ),
        "P-N1": Person(
            id="P-N1", name="Neutral", country="CN",
            tacit_knowledge=2.0, network_integration=1.5,
            tenure_months=36, substitutes=4,
        ),
    }


@pytest.fixture
def factional_assignments():
    """A1 multi-hat at apex; faction-A holds 4 senior roles, faction-B holds
    middle, neutral holds junior."""
    return [
        RoleAssignment("P-A1", "R1", capacity=0.6),  # multi-hat
        RoleAssignment("P-A1", "R2", capacity=0.4),  # multi-hat
        RoleAssignment("P-A2", "R3"),
        RoleAssignment("P-A3", "R4"),
        RoleAssignment("P-A4", "R5"),
        RoleAssignment("P-A5", "R6"),
        RoleAssignment("P-B1", "R7"),
        RoleAssignment("P-B2", "R8"),
        # P-B3 unassigned — illustrates that membership doesn't require
        # current role assignment
        # P-N1 unassigned for same reason
    ]


# ─────────────────────────────────────────────────────────────────────────
# Faction resolution
# ─────────────────────────────────────────────────────────────────────────
class TestFactionResolution:
    def test_resolve_by_tag(self, factional_persons):
        members = resolve_faction_members(factional_persons,
                                          faction_tag="faction-a")
        assert len(members) == 5
        assert set(members) == {"P-A1", "P-A2", "P-A3", "P-A4", "P-A5"}

    def test_resolve_by_filter(self, factional_persons):
        # All Chinese persons (all of them in this fixture)
        members = resolve_faction_members(
            factional_persons,
            faction_filter=lambda p: p.country == "CN")
        assert len(members) == len(factional_persons)

    def test_filter_takes_precedence(self, factional_persons):
        members = resolve_faction_members(
            factional_persons,
            faction_tag="faction-a",
            faction_filter=lambda p: "faction-b" in p.factions)
        # filter wins
        assert len(members) == 3
        assert all(m.startswith("P-B") for m in members)

    def test_neither_raises(self, factional_persons):
        with pytest.raises(ValueError, match="faction"):
            resolve_faction_members(factional_persons)

    def test_multi_faction_membership(self, factional_persons):
        """P-A1 and P-A5 are also in tsinghua-mafia / youth-league."""
        m1 = resolve_faction_members(factional_persons,
                                      faction_tag="tsinghua-mafia")
        assert m1 == ["P-A1"]
        m2 = resolve_faction_members(factional_persons,
                                      faction_tag="youth-league")
        assert m2 == ["P-A5"]


# ─────────────────────────────────────────────────────────────────────────
# Deterministic faction purge
# ─────────────────────────────────────────────────────────────────────────
class TestDeterministicPurge:
    def test_runs_with_correct_membership(self, factional_org,
                                           factional_persons,
                                           factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        result = sim.scenario_faction_purge(faction_tag="faction-a")
        assert result.faction_size == 5
        assert result.deterministic
        assert result.n_iterations == 1

    def test_multi_hat_amplification_detected(self, factional_org,
                                               factional_persons,
                                               factional_assignments):
        """Faction A includes P-A1 (multi-hat with 2 roles). The faction
        has 5 members but should disable 6 roles — amplification of +1."""
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        result = sim.scenario_faction_purge(faction_tag="faction-a")
        # Faction A members: P-A1 (R1+R2), P-A2 (R3), P-A3 (R4),
        # P-A4 (R5), P-A5 (R6) = 6 roles disabled
        assert result.direct_roles_disabled == 6
        assert result.multi_hat_amplification == 1

    def test_concentrated_failures_counted(self, factional_org,
                                            factional_persons,
                                            factional_assignments):
        """Members with substitutes <= 1 contribute to concentrated
        failures. P-A1 (subs=0) and P-A2 (subs=1) qualify."""
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        result = sim.scenario_faction_purge(faction_tag="faction-a")
        # P-A1 with 2 roles + P-A2 with 1 role = 3 concentrated failures
        assert result.concentrated_failures == 3

    def test_capability_remaining_makes_sense(self, factional_org,
                                                factional_persons,
                                                factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        result = sim.scenario_faction_purge(faction_tag="faction-a")
        # Faction A removed: R1 (cap 5×0.6=3.0), R2 (3×0.4=1.2),
        # R3 (3.0), R4 (2.5), R5 (2.0), R6 (2.0)
        # Removed cap: 3.0 + 1.2 + 3.0 + 2.5 + 2.0 + 2.0 = 13.7
        # Total: 5+3+3+2.5+2+2+1+1 = 19.5
        # Remaining %: (19.5 - 13.7) / 19.5 * 100 ≈ 29.7%
        assert 28 < result.mean_pct < 32

    def test_empty_faction_raises(self, factional_org,
                                   factional_persons,
                                   factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        with pytest.raises(ValueError, match="No persons"):
            sim.scenario_faction_purge(faction_tag="nonexistent-faction")

    def test_callable_filter_works(self, factional_org,
                                    factional_persons,
                                    factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        result = sim.scenario_faction_purge(
            faction_filter=lambda p: p.tenure_months >= 60)
        # P-A1 (120), P-A2 (60), P-B1 (72) all qualify
        assert result.faction_size == 3


# ─────────────────────────────────────────────────────────────────────────
# Stochastic spillover
# ─────────────────────────────────────────────────────────────────────────
class TestStochasticSpillover:
    def test_secondary_loss_runs_iterations(self, factional_org,
                                              factional_persons,
                                              factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        result = sim.scenario_faction_purge(
            faction_tag="faction-a",
            secondary_loss_p=0.3,
            n_iterations=500)
        assert not result.deterministic
        assert result.n_iterations == 500

    def test_secondary_loss_increases_total_loss(self, factional_org,
                                                   factional_persons,
                                                   factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        det = sim.scenario_faction_purge(
            faction_tag="faction-a", secondary_loss_p=0)
        sto = sim.scenario_faction_purge(
            faction_tag="faction-a", secondary_loss_p=0.5,
            n_iterations=2000)
        # Stochastic version should on average have lower capability remaining
        assert sto.mean_pct < det.mean_pct

    def test_secondary_loss_zero_collapses_to_deterministic(
            self, factional_org, factional_persons, factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        result = sim.scenario_faction_purge(
            faction_tag="faction-a",
            secondary_loss_p=0,
            n_iterations=5000)  # ignored
        assert result.deterministic
        assert result.n_iterations == 1

    def test_secondary_loss_invalid_raises(self, factional_org,
                                             factional_persons,
                                             factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        with pytest.raises(ValueError, match="secondary_loss_p"):
            sim.scenario_faction_purge(faction_tag="faction-a",
                                        secondary_loss_p=1.5)


# ─────────────────────────────────────────────────────────────────────────
# Concentration premium
# ─────────────────────────────────────────────────────────────────────────
class TestConcentrationPremium:
    def test_premium_is_positive_for_well_chosen_faction(
            self, factional_org, factional_persons, factional_assignments):
        """Faction A holds the apex roles — purging them coherently
        should be MUCH worse than losing 5 random persons."""
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        compare = run_faction_vs_random(
            sim, faction_tag="faction-a", n_iterations=2000)

        assert compare["premium"]["capability_premium_pp"] > 0
        assert (compare["faction"].mean_pct
                < compare["random"].mean_pct)

    def test_premium_ordering(self, factional_org,
                                factional_persons,
                                factional_assignments):
        """An apex-concentrated faction (A) should have larger premium
        than a junior-concentrated faction (B)."""
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        cmp_a = run_faction_vs_random(
            sim, faction_tag="faction-a", n_iterations=2000)
        cmp_b = run_faction_vs_random(
            sim, faction_tag="faction-b", n_iterations=2000)

        # Faction A holds all apex roles → higher premium
        assert (cmp_a["premium"]["capability_premium_pp"]
                > cmp_b["premium"]["capability_premium_pp"])

    def test_compare_returns_three_keys(self, factional_org,
                                         factional_persons,
                                         factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        compare = run_faction_vs_random(
            sim, faction_tag="faction-a", n_iterations=1000)
        assert set(compare.keys()) == {"faction", "random", "premium"}


# ─────────────────────────────────────────────────────────────────────────
# Cross-org / multi-country
# ─────────────────────────────────────────────────────────────────────────
class TestCrossOrgFaction:
    def test_single_country_faction(self, factional_org,
                                      factional_persons,
                                      factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        result = sim.scenario_faction_purge(faction_tag="faction-a")
        assert result.countries_affected == ["CN"]
        assert not result.cross_org_amplifier

    def test_cross_country_faction(self, factional_org):
        """A 'shared bloc' faction with persons in multiple countries."""
        persons = {
            "P-CN-1": Person(id="P-CN-1", name="A", country="CN",
                              factions=["sco-bloc"]),
            "P-RU-1": Person(id="P-RU-1", name="B", country="RU",
                              factions=["sco-bloc"]),
        }
        # Need at least one assignment for the simulator to work
        assignments = [RoleAssignment("P-CN-1", "R1")]
        sim = FactionAwareSimulator(factional_org, persons, assignments,
                                     seed=42)
        result = sim.scenario_faction_purge(faction_tag="sco-bloc")
        assert sorted(result.countries_affected) == ["CN", "RU"]
        assert result.cross_org_amplifier


# ─────────────────────────────────────────────────────────────────────────
# Reproducibility
# ─────────────────────────────────────────────────────────────────────────
class TestReproducibility:
    def test_same_seed_same_stochastic_result(self, factional_org,
                                                factional_persons,
                                                factional_assignments):
        sim1 = FactionAwareSimulator(factional_org, factional_persons,
                                      factional_assignments, seed=20260508)
        sim2 = FactionAwareSimulator(factional_org, factional_persons,
                                      factional_assignments, seed=20260508)
        r1 = sim1.scenario_faction_purge(
            faction_tag="faction-a", secondary_loss_p=0.3,
            n_iterations=500)
        r2 = sim2.scenario_faction_purge(
            faction_tag="faction-a", secondary_loss_p=0.3,
            n_iterations=500)
        assert r1.mean_pct == r2.mean_pct
        assert r1.mean_secondary_loss == r2.mean_secondary_loss


# ─────────────────────────────────────────────────────────────────────────
# Inheritance: PersonAware methods still work
# ─────────────────────────────────────────────────────────────────────────
class TestInheritance:
    def test_random_attrition_still_works(self, factional_org,
                                           factional_persons,
                                           factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        result = sim.scenario_person_random_attrition(
            n_iterations=500, n_persons_per_iter=2)
        assert result.n_iterations == 500

    def test_targeted_attrition_still_works(self, factional_org,
                                              factional_persons,
                                              factional_assignments):
        sim = FactionAwareSimulator(factional_org, factional_persons,
                                     factional_assignments, seed=42)
        result = sim.scenario_person_targeted_attrition(
            n_iterations=500, n_persons_per_iter=2, accuracy=0.85)
        assert result.n_iterations == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
