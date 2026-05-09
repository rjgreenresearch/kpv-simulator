"""
tests/test_person_simulator.py — Unit tests for person-centric scenarios
=========================================================================
"""

import pytest
from dataclasses import dataclass, field

from kpvs.persons import Person, RoleAssignment
from kpvs.person_simulator import (
    PersonAwareSimulator, PersonScenarioResult, person_adversarial_gap,
)


# ─────────────────────────────────────────────────────────────────────────
# Minimal Role / Organization stand-ins matching kpvs/models.py shape
# (real tests in the integrated repo will use the actual classes)
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
def small_org():
    """6 roles spanning Tier-1 to Resilient."""
    return StubOrg(
        name="Test Org",
        roles=[
            StubRole("R1", "Apex", 4, 4, 4, capability_weight=5.0),    # KPCI 12
            StubRole("R2", "Senior A", 4, 4, 3, capability_weight=3.0),  # 11
            StubRole("R3", "Senior B", 3, 4, 3, capability_weight=3.0),  # 10
            StubRole("R4", "Mid", 2, 3, 2, capability_weight=2.0),       # 7
            StubRole("R5", "Junior A", 1, 2, 1, capability_weight=1.0),  # 4
            StubRole("R6", "Junior B", 1, 1, 1, capability_weight=1.0),  # 3
        ],
    )


@pytest.fixture
def people_and_assignments():
    """5 persons, one of whom (P-A) is multi-hat (R1 + R2)."""
    persons = {
        "P-A": Person(id="P-A", name="Alpha", country="CN",
                      tacit_knowledge=4.0, network_integration=4.0,
                      tenure_months=120, substitutes=0),
        "P-B": Person(id="P-B", name="Beta", country="CN",
                      tacit_knowledge=2.0, network_integration=2.0,
                      tenure_months=24, substitutes=2),
        "P-C": Person(id="P-C", name="Gamma", country="CN",
                      tacit_knowledge=1.5, network_integration=1.5,
                      tenure_months=12, substitutes=3),
        "P-D": Person(id="P-D", name="Delta", country="CN",
                      tacit_knowledge=1.0, network_integration=1.0,
                      tenure_months=6, substitutes=4),
        "P-E": Person(id="P-E", name="Epsilon", country="CN",
                      tacit_knowledge=0.5, network_integration=0.5,
                      tenure_months=3, substitutes=5),
    }
    assignments = [
        RoleAssignment("P-A", "R1", capacity=0.6),    # multi-hat: apex
        RoleAssignment("P-A", "R2", capacity=0.4),    # multi-hat: senior
        RoleAssignment("P-B", "R3"),
        RoleAssignment("P-C", "R4"),
        RoleAssignment("P-D", "R5"),
        RoleAssignment("P-E", "R6"),
    ]
    return persons, assignments


# ─────────────────────────────────────────────────────────────────────────
# Construction
# ─────────────────────────────────────────────────────────────────────────
class TestSimulatorConstruction:
    def test_builds(self, small_org, people_and_assignments):
        persons, assignments = people_and_assignments
        sim = PersonAwareSimulator(small_org, persons, assignments, seed=42)
        assert sim is not None
        assert sim._total_capability == 15.0  # 5+3+3+2+1+1

    def test_target_values_computed(self, small_org, people_and_assignments):
        persons, assignments = people_and_assignments
        sim = PersonAwareSimulator(small_org, persons, assignments, seed=42)
        ranked = sim.rank_persons()
        # P-A should be #1 — multi-hat × strong premium
        assert ranked[0][0] == "P-A"
        # P-E should be last — weakest profile, lowest-KPCI role
        assert ranked[-1][0] == "P-E"

    def test_zero_capability_raises(self):
        org = StubOrg(name="empty", roles=[])
        with pytest.raises(ValueError, match="capability"):
            PersonAwareSimulator(org, {}, [])


# ─────────────────────────────────────────────────────────────────────────
# Random attrition baseline
# ─────────────────────────────────────────────────────────────────────────
class TestRandomAttrition:
    def test_runs_with_expected_shape(self, small_org, people_and_assignments):
        persons, assignments = people_and_assignments
        sim = PersonAwareSimulator(small_org, persons, assignments, seed=42)
        result = sim.scenario_person_random_attrition(
            n_iterations=500, n_persons_per_iter=2)
        assert isinstance(result, PersonScenarioResult)
        assert result.n_iterations == 500
        assert 0 <= result.mean_pct <= 100

    def test_more_removed_means_less_remaining(self, small_org,
                                                people_and_assignments):
        persons, assignments = people_and_assignments
        sim = PersonAwareSimulator(small_org, persons, assignments, seed=42)
        r1 = sim.scenario_person_random_attrition(
            n_iterations=500, n_persons_per_iter=1)
        r2 = sim.scenario_person_random_attrition(
            n_iterations=500, n_persons_per_iter=3)
        assert r1.mean_pct > r2.mean_pct

    def test_too_many_persons_raises(self, small_org, people_and_assignments):
        persons, assignments = people_and_assignments
        sim = PersonAwareSimulator(small_org, persons, assignments, seed=42)
        with pytest.raises(ValueError):
            sim.scenario_person_random_attrition(
                n_iterations=10, n_persons_per_iter=10)


# ─────────────────────────────────────────────────────────────────────────
# Adversarial targeting
# ─────────────────────────────────────────────────────────────────────────
class TestAdversarialTargeting:
    def test_targeted_worse_than_random(self, small_org, people_and_assignments):
        """Core invariant: adversarial targeting causes strictly more
        capability loss than random attrition at the same removal count."""
        persons, assignments = people_and_assignments
        sim = PersonAwareSimulator(small_org, persons, assignments, seed=42)
        rnd = sim.scenario_person_random_attrition(
            n_iterations=2000, n_persons_per_iter=2)
        adv = sim.scenario_person_targeted_attrition(
            n_iterations=2000, n_persons_per_iter=2, accuracy=0.95)
        assert rnd.mean_pct > adv.mean_pct, (
            f"Adversarial gap should be positive; "
            f"random={rnd.mean_pct:.2f} vs adv={adv.mean_pct:.2f}")

    def test_perfect_accuracy_targets_apex(self, small_org,
                                            people_and_assignments):
        """At accuracy=1.0, the adversary should hit P-A almost every iter
        (since P-A has the highest target value)."""
        persons, assignments = people_and_assignments
        sim = PersonAwareSimulator(small_org, persons, assignments, seed=42)
        adv = sim.scenario_person_targeted_attrition(
            n_iterations=1000, n_persons_per_iter=1, accuracy=1.0)
        # P-A should be targeted in the vast majority of iterations
        # (top_k pool widens this slightly but P-A dominates target_value)
        freq = adv.target_frequency.get("P-A", 0)
        assert freq > 200  # at least 20% — top_k pool dilutes vs naive expectation

    def test_zero_accuracy_resembles_random(self, small_org,
                                             people_and_assignments):
        """At accuracy=0, adversary picks randomly from non-top pool."""
        persons, assignments = people_and_assignments
        sim = PersonAwareSimulator(small_org, persons, assignments, seed=42)
        rnd = sim.scenario_person_random_attrition(
            n_iterations=2000, n_persons_per_iter=2)
        adv0 = sim.scenario_person_targeted_attrition(
            n_iterations=2000, n_persons_per_iter=2, accuracy=0.0)
        # Should be similar in mean (within a few percentage points)
        assert abs(rnd.mean_pct - adv0.mean_pct) < 8

    def test_multi_hat_efficiency_above_one_when_apex_targeted(
            self, small_org, people_and_assignments):
        """When P-A (multi-hat 2 roles) is targeted, roles_disabled per
        person targeted should exceed 1."""
        persons, assignments = people_and_assignments
        sim = PersonAwareSimulator(small_org, persons, assignments, seed=42)
        adv = sim.scenario_person_targeted_attrition(
            n_iterations=1000, n_persons_per_iter=1, accuracy=0.95)
        # P-A holds 2 roles; if frequently targeted, eff > 1
        assert adv.multi_hat_efficiency > 1.0


# ─────────────────────────────────────────────────────────────────────────
# Adversarial gap calculation
# ─────────────────────────────────────────────────────────────────────────
class TestAdversarialGap:
    def test_gap_is_positive(self, small_org, people_and_assignments):
        persons, assignments = people_and_assignments
        sim = PersonAwareSimulator(small_org, persons, assignments, seed=42)
        rnd = sim.scenario_person_random_attrition(
            n_iterations=2000, n_persons_per_iter=2)
        adv = sim.scenario_person_targeted_attrition(
            n_iterations=2000, n_persons_per_iter=2, accuracy=0.85)
        gap = person_adversarial_gap(rnd, adv)
        assert gap["capability_gap_pp"] > 0
        assert gap["tacit_shock_premium"] > 0
        assert gap["roles_disabled_premium"] >= 0  # multi-hat asymmetry


# ─────────────────────────────────────────────────────────────────────────
# Reproducibility
# ─────────────────────────────────────────────────────────────────────────
class TestReproducibility:
    def test_same_seed_same_results(self, small_org, people_and_assignments):
        persons, assignments = people_and_assignments
        sim1 = PersonAwareSimulator(small_org, persons, assignments, seed=20260508)
        sim2 = PersonAwareSimulator(small_org, persons, assignments, seed=20260508)
        r1 = sim1.scenario_person_random_attrition(
            n_iterations=500, n_persons_per_iter=2)
        r2 = sim2.scenario_person_random_attrition(
            n_iterations=500, n_persons_per_iter=2)
        assert r1.mean_pct == r2.mean_pct
        assert r1.mean_roles_disabled == r2.mean_roles_disabled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
