"""
tests/test_models.py
====================
Unit tests for kpvs.models — Role, Organization, validation, serialisation.
"""

import json
import math
import pytest
from kpvs.models import Role, Organization, TIER1, TIER2, MANAGEABLE


# ══════════════════════════════════════════════════════════════════════════════
# Role — construction and KPCI derivation
# ══════════════════════════════════════════════════════════════════════════════

class TestRoleConstruction:

    def test_kpci_sum(self):
        r = Role("r1", "Test Role",
                 substitution_timeline=2.0,
                 documentation_ratio=3.0,
                 adversarial_observability=1.5)
        assert math.isclose(r.kpci, 6.5)

    def test_kpci_boundary_zero(self):
        r = Role("r0", "Zero", 0.0, 0.0, 0.0)
        assert r.kpci == 0.0
        assert r.tier == "Resilient"

    def test_kpci_boundary_max(self):
        r = Role("rmax", "Max", 4.0, 4.0, 4.0)
        assert r.kpci == 12.0
        assert r.tier == "Tier-1 KPV"

    def test_tier_tier1(self):
        r = Role("t1", "T1", 4.0, 3.5, 3.0)
        assert r.tier == "Tier-1 KPV"
        assert r.kpci >= TIER1

    def test_tier_tier2(self):
        r = Role("t2", "T2", 2.5, 2.5, 2.5)
        assert r.tier == "Tier-2 KPV"
        assert TIER2 <= r.kpci < TIER1

    def test_tier_manageable(self):
        r = Role("mg", "MG", 1.5, 1.5, 1.5)
        assert r.tier == "Manageable"
        assert MANAGEABLE <= r.kpci < TIER2

    def test_tier_resilient(self):
        r = Role("rs", "RS", 0.5, 0.5, 0.5)
        assert r.tier == "Resilient"
        assert r.kpci < MANAGEABLE

    def test_defaults(self):
        r = Role("d", "Default", 1.0, 1.0, 1.0)
        assert r.reports_to is None
        assert r.critical_dependencies == []
        assert r.capability_weight == 1.0
        assert r.bench_depth == 0
        assert r.notes == ""


# ══════════════════════════════════════════════════════════════════════════════
# Role — validation
# ══════════════════════════════════════════════════════════════════════════════

class TestRoleValidation:

    @pytest.mark.parametrize("st", [-0.1, 4.1, 5.0, -1.0])
    def test_invalid_substitution_timeline(self, st):
        with pytest.raises(ValueError, match="substitution_timeline"):
            Role("r", "T", st, 1.0, 1.0)

    @pytest.mark.parametrize("dr", [-0.1, 4.01])
    def test_invalid_documentation_ratio(self, dr):
        with pytest.raises(ValueError, match="documentation_ratio"):
            Role("r", "T", 1.0, dr, 1.0)

    @pytest.mark.parametrize("ao", [-1.0, 4.5])
    def test_invalid_adversarial_observability(self, ao):
        with pytest.raises(ValueError, match="adversarial_observability"):
            Role("r", "T", 1.0, 1.0, ao)

    def test_invalid_capability_weight_zero(self):
        with pytest.raises(ValueError, match="capability_weight"):
            Role("r", "T", 1.0, 1.0, 1.0, capability_weight=0.0)

    def test_invalid_capability_weight_negative(self):
        with pytest.raises(ValueError, match="capability_weight"):
            Role("r", "T", 1.0, 1.0, 1.0, capability_weight=-1.0)

    def test_invalid_bench_depth_negative(self):
        with pytest.raises(ValueError, match="bench_depth"):
            Role("r", "T", 1.0, 1.0, 1.0, bench_depth=-1)

    def test_boundary_values_accepted(self):
        """Boundary values 0.0 and 4.0 must be valid."""
        r = Role("r", "T", 0.0, 4.0, 0.0)
        assert r.kpci == 4.0


# ══════════════════════════════════════════════════════════════════════════════
# Role — restoration months
# ══════════════════════════════════════════════════════════════════════════════

class TestRestorationMonths:

    def test_no_bench_st4(self):
        r = Role("r", "T", 4.0, 0.0, 0.0, bench_depth=0)
        assert r.estimated_restoration_months == 72.0

    def test_bench_reduces_time(self):
        r0 = Role("r0", "T", 3.0, 0.0, 0.0, bench_depth=0)
        r1 = Role("r1", "T", 3.0, 0.0, 0.0, bench_depth=1)
        assert r1.estimated_restoration_months < r0.estimated_restoration_months

    def test_large_bench_floored(self):
        """Bench depth 10 should not produce negative months."""
        r = Role("r", "T", 4.0, 0.0, 0.0, bench_depth=10)
        assert r.estimated_restoration_months > 0

    def test_st0_fast(self):
        r = Role("r", "T", 0.0, 0.0, 0.0)
        # ST=0 → base 2 months
        assert r.estimated_restoration_months == pytest.approx(2.0, rel=0.01)


# ══════════════════════════════════════════════════════════════════════════════
# Role — serialisation
# ══════════════════════════════════════════════════════════════════════════════

class TestRoleSerialization:

    def test_to_dict_keys(self):
        r = Role("r1", "Title", 2.0, 2.0, 2.0,
                 reports_to="boss", critical_dependencies=["dep1"],
                 capability_weight=1.5, bench_depth=1, notes="test")
        d = r.to_dict()
        for key in ("id", "title", "kpci", "tier",
                    "substitution_timeline", "documentation_ratio",
                    "adversarial_observability", "bench_depth",
                    "capability_weight", "estimated_restoration_months",
                    "reports_to", "critical_dependencies", "notes"):
            assert key in d, f"Missing key: {key}"

    def test_to_dict_values(self):
        r = Role("r1", "Title", 1.0, 2.0, 3.0)
        d = r.to_dict()
        assert d["kpci"] == 6.0
        assert d["tier"] == "Manageable"


# ══════════════════════════════════════════════════════════════════════════════
# Organization — construction and validation
# ══════════════════════════════════════════════════════════════════════════════

class TestOrganizationConstruction:

    def test_total_capability(self, minimal_org):
        expected = sum(r.capability_weight for r in minimal_org.roles.values())
        assert math.isclose(minimal_org.total_capability, expected)

    def test_tier_summary_keys(self, minimal_org):
        ts = minimal_org.tier_summary()
        assert set(ts.keys()) == {"Tier-1 KPV","Tier-2 KPV","Manageable","Resilient"}
        assert sum(ts.values()) == len(minimal_org.roles)

    def test_invalid_mission_critical(self):
        roles = {"r": Role("r","T",1,1,1)}
        with pytest.raises(ValueError, match="unknown role"):
            Organization("O", roles, mission_critical_roles=["nonexistent"])

    def test_invalid_dependency_reference(self):
        roles = {
            "r": Role("r","T",1,1,1, critical_dependencies=["ghost"])
        }
        with pytest.raises(ValueError, match="unknown role"):
            Organization("O", roles, mission_critical_roles=[])

    def test_invalid_reports_to(self):
        roles = {
            "r": Role("r","T",1,1,1, reports_to="ghost")
        }
        with pytest.raises(ValueError, match="unknown role"):
            Organization("O", roles, mission_critical_roles=[])

    def test_get_role_found(self, minimal_org):
        r = minimal_org.get_role("worker")
        assert r is not None
        assert r.title == "Key Technical Expert"

    def test_get_role_missing(self, minimal_org):
        assert minimal_org.get_role("ghost") is None

    def test_get_dependents(self, minimal_org):
        deps = minimal_org.get_dependents("worker")
        # root has worker in critical_dependencies
        assert any(d.id == "root" for d in deps)

    def test_get_subordinates(self, minimal_org):
        subs = minimal_org.get_subordinates("root")
        ids = {s.id for s in subs}
        assert "worker" in ids
        assert "admin" in ids

    def test_roles_by_kpci_descending(self, minimal_org):
        roles = minimal_org.roles_by_kpci(descending=True)
        kpcis = [r.kpci for r in roles]
        assert kpcis == sorted(kpcis, reverse=True)

    def test_roles_by_kpci_ascending(self, minimal_org):
        roles = minimal_org.roles_by_kpci(descending=False)
        kpcis = [r.kpci for r in roles]
        assert kpcis == sorted(kpcis)


# ══════════════════════════════════════════════════════════════════════════════
# Organization — from_dict round-trip
# ══════════════════════════════════════════════════════════════════════════════

class TestOrganizationSerialization:

    def test_to_dict_structure(self, minimal_org):
        d = minimal_org.to_dict()
        assert "name" in d
        assert "roles" in d
        assert "mission_critical_roles" in d
        assert isinstance(d["roles"], list)

    def test_from_dict_roundtrip(self, minimal_org):
        d = minimal_org.to_dict()
        rebuilt = Organization.from_dict(d)
        assert rebuilt.name == minimal_org.name
        assert set(rebuilt.roles.keys()) == set(minimal_org.roles.keys())
        assert rebuilt.mission_critical_roles == minimal_org.mission_critical_roles

    def test_from_dict_kpci_preserved(self, minimal_org):
        d = minimal_org.to_dict()
        rebuilt = Organization.from_dict(d)
        for rid, role in minimal_org.roles.items():
            assert math.isclose(rebuilt.roles[rid].kpci, role.kpci, rel_tol=1e-6)


# ══════════════════════════════════════════════════════════════════════════════
# Built-in examples smoke tests
# ══════════════════════════════════════════════════════════════════════════════

class TestBuiltinExamples:

    def test_rare_earth_org_loads(self, rare_earth_org):
        assert len(rare_earth_org.roles) >= 10
        assert len(rare_earth_org.mission_critical_roles) >= 2

    def test_rare_earth_has_tier1(self, rare_earth_org):
        tier1 = [r for r in rare_earth_org.roles.values()
                 if r.tier == "Tier-1 KPV"]
        assert len(tier1) >= 1

    def test_nuclear_org_loads(self, nuclear_org):
        assert len(nuclear_org.roles) >= 5

    def test_nuclear_has_extreme_kpci(self, nuclear_org):
        max_kpci = max(r.kpci for r in nuclear_org.roles.values())
        assert max_kpci >= 10.0

    def test_pharma_org_loads(self, pharma_org):
        assert len(pharma_org.roles) >= 5
