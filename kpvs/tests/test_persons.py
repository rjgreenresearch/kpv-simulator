"""
tests/test_persons.py — Unit tests for the person-centric layer
================================================================
"""

import math
import pytest

# These imports assume the extension files are placed in the existing
# kpvs/ package alongside models.py, simulator.py, etc.
from kpvs.persons import (
    Person, RoleAssignment,
    roles_held_by, persons_in_role, multi_hat_persons,
)
from kpvs.effective_kpci import (
    effective_kpci, person_premium, tenure_factor,
    effective_tier, continuity_loss,
)


# Mock a minimal Role for testing without depending on kpvs.models
class MockRole:
    def __init__(self, kpci, st=2, capability_weight=1.0):
        self.kpci = kpci
        self.substitution_timeline = st
        self.capability_weight = capability_weight


# ── Person validation ────────────────────────────────────────────────────
class TestPersonValidation:
    def test_valid_person(self):
        p = Person(id="P-001", name="Test", country="CN",
                   tacit_knowledge=2.5, network_integration=3.0,
                   tenure_months=24, substitutes=2)
        assert p.id == "P-001"
        assert p.tacit_knowledge == 2.5

    def test_tk_out_of_range_raises(self):
        with pytest.raises(ValueError, match="tacit_knowledge"):
            Person(id="P", name="X", country="CN", tacit_knowledge=4.5)

    def test_cni_negative_raises(self):
        with pytest.raises(ValueError, match="network_integration"):
            Person(id="P", name="X", country="CN", network_integration=-0.1)

    def test_negative_tenure_raises(self):
        with pytest.raises(ValueError, match="tenure_months"):
            Person(id="P", name="X", country="CN", tenure_months=-1)

    def test_bad_country_code_raises(self):
        with pytest.raises(ValueError, match="country"):
            Person(id="P", name="X", country="CHN")

    def test_default_substitutes_is_one(self):
        """Default subs=1 prevents log(0) in premium calc."""
        p = Person(id="P", name="X", country="CN")
        assert p.substitutes == 1


# ── RoleAssignment validation ────────────────────────────────────────────
class TestRoleAssignment:
    def test_valid_assignment(self):
        a = RoleAssignment(person_id="P-001", role_id="CN-PSC-01-GENSEC")
        assert a.capacity == 1.0
        assert not a.is_designated_successor

    def test_capacity_zero_raises(self):
        with pytest.raises(ValueError, match="capacity"):
            RoleAssignment(person_id="P", role_id="R", capacity=0)

    def test_capacity_over_one_raises(self):
        with pytest.raises(ValueError, match="capacity"):
            RoleAssignment(person_id="P", role_id="R", capacity=1.1)


# ── Multi-hat detection ──────────────────────────────────────────────────
class TestMultiHat:
    def test_identifies_multi_hat(self):
        assignments = [
            RoleAssignment(person_id="XI", role_id="CN-PSC-01-GENSEC"),
            RoleAssignment(person_id="XI", role_id="CN-CMC-CHAIR"),
            RoleAssignment(person_id="XI", role_id="CN-STATE-PRES"),
            RoleAssignment(person_id="LI", role_id="CN-PSC-02-PREMIER"),
        ]
        result = multi_hat_persons(assignments)
        assert "XI" in result
        assert len(result["XI"]) == 3
        assert "LI" not in result  # only 1 role

    def test_roles_held_by(self):
        assignments = [
            RoleAssignment(person_id="XI", role_id="A"),
            RoleAssignment(person_id="XI", role_id="B"),
            RoleAssignment(person_id="LI", role_id="C"),
        ]
        assert sorted(roles_held_by("XI", assignments)) == ["A", "B"]
        assert roles_held_by("LI", assignments) == ["C"]


# ── Tenure factor sanity ─────────────────────────────────────────────────
class TestTenureFactor:
    def test_zero_tenure_is_half(self):
        assert tenure_factor(0) == 0.5

    def test_long_tenure_approaches_one(self):
        assert tenure_factor(120) > 0.99

    def test_monotonic(self):
        prev = 0
        for m in [0, 6, 12, 24, 60, 120]:
            curr = tenure_factor(m)
            assert curr >= prev
            prev = curr


# ── Effective KPCI ───────────────────────────────────────────────────────
class TestEffectiveKPCI:
    def test_no_person_returns_structural(self):
        role = MockRole(kpci=10.0)
        assert effective_kpci(role, person=None) == pytest.approx(10.0)

    def test_neutral_person_no_premium(self):
        """A person with TK=0, CNI=0, 1 substitute: premium ≈ -log(2)·γ ≈ -0.42.
        Floor invariant says effective ≥ structural, so we get structural."""
        role = MockRole(kpci=10.0)
        p = Person(id="P", name="N", country="CN",
                   tacit_knowledge=0, network_integration=0,
                   tenure_months=24, substitutes=1)
        assert effective_kpci(role, p) == pytest.approx(10.0, abs=0.01)

    def test_strong_person_adds_premium(self):
        """High TK + high CNI + 0 substitutes → premium > 0."""
        role = MockRole(kpci=8.0)
        p = Person(id="P", name="N", country="CN",
                   tacit_knowledge=4.0, network_integration=4.0,
                   tenure_months=120, substitutes=0)
        eff = effective_kpci(role, p)
        assert eff > 8.0
        assert eff > 11.0  # should push into Tier-1 territory

    def test_floor_invariant_holds(self):
        """Even a weak occupant cannot drop effective below structural."""
        role = MockRole(kpci=10.0)
        p = Person(id="P", name="N", country="CN",
                   tacit_knowledge=0, network_integration=0,
                   tenure_months=0, substitutes=20)
        assert effective_kpci(role, p) >= 10.0

    def test_designated_successor_reduces_st(self):
        """Successor flag reduces effective ST contribution."""
        role = MockRole(kpci=10.0, st=4.0)
        no_succ = effective_kpci(role, person=None,
                                  has_designated_successor=False)
        with_succ = effective_kpci(role, person=None,
                                    has_designated_successor=True)
        assert with_succ < no_succ

    def test_new_occupant_tk_discounted(self):
        """A brand-new occupant gets less premium than a long-tenured one
        at identical TK/CNI/substitutes."""
        role = MockRole(kpci=8.0)
        p_new = Person(id="A", name="N", country="CN",
                       tacit_knowledge=4.0, network_integration=2.0,
                       tenure_months=0, substitutes=2)
        p_old = Person(id="B", name="O", country="CN",
                       tacit_knowledge=4.0, network_integration=2.0,
                       tenure_months=120, substitutes=2)
        # CNI same, TK same on paper — but tenure factor discounts new TK
        assert effective_kpci(role, p_old) > effective_kpci(role, p_new)


# ── Tier classification ──────────────────────────────────────────────────
class TestEffectiveTier:
    def test_tier_thresholds(self):
        assert effective_tier(11.5) == "Tier-1 KPV"
        assert effective_tier(10.0) == "Tier-1 KPV"
        assert effective_tier(9.9) == "Tier-2 KPV"
        assert effective_tier(7.0) == "Tier-2 KPV"
        assert effective_tier(5.0) == "Manageable"
        assert effective_tier(3.5) == "Resilient"


# ── Continuity loss diagnostics ──────────────────────────────────────────
class TestContinuityLoss:
    def test_returns_all_keys(self):
        role = MockRole(kpci=10.0, st=3, capability_weight=2.0)
        p = Person(id="P", name="N", country="CN",
                   tacit_knowledge=3.0, network_integration=3.0,
                   tenure_months=48, substitutes=2)
        out = continuity_loss(role, p)
        assert set(out.keys()) >= {
            "capability_loss", "replacement_friction_months",
            "tacit_shock", "effective_kpci", "floor_kpci",
        }

    def test_irreplaceable_person_higher_friction(self):
        role = MockRole(kpci=10, st=3)
        p_irr = Person(id="A", name="N", country="CN",
                       tacit_knowledge=4, network_integration=4,
                       tenure_months=60, substitutes=0)
        p_subs = Person(id="B", name="N", country="CN",
                        tacit_knowledge=4, network_integration=4,
                        tenure_months=60, substitutes=10)
        f_irr = continuity_loss(role, p_irr)["replacement_friction_months"]
        f_subs = continuity_loss(role, p_subs)["replacement_friction_months"]
        assert f_irr > f_subs

    def test_long_tenure_higher_shock(self):
        role = MockRole(kpci=10, st=3)
        p_new = Person(id="A", name="N", country="CN",
                       tacit_knowledge=4, network_integration=2,
                       tenure_months=0)
        p_old = Person(id="B", name="N", country="CN",
                       tacit_knowledge=4, network_integration=2,
                       tenure_months=120)
        s_new = continuity_loss(role, p_new)["tacit_shock"]
        s_old = continuity_loss(role, p_old)["tacit_shock"]
        assert s_old > s_new


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
