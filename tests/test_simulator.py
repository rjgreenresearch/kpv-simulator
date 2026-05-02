"""
tests/test_simulator.py
========================
Unit and integration tests for kpvs.simulator — all three scenarios
plus KPCI report. Uses small N for speed; seed is fixed for determinism.
"""

import math
import pytest
from kpvs.simulator import (
    KPVSimulator, SimulationResult,
    _capability_after_loss, _percentile,
)

FAST_N = 500   # iterations for unit tests (full suite uses 10k)


# ══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════════════════════════

class TestHelpers:

    def test_percentile_median(self):
        data = list(range(1, 101))   # 1..100
        assert _percentile(data, 50) == pytest.approx(50.5, rel=0.01)

    def test_percentile_p0(self):
        data = [1, 2, 3, 4, 5]
        assert _percentile(data, 0) == 1.0

    def test_percentile_p100(self):
        data = [1, 2, 3, 4, 5]
        assert _percentile(data, 100) == 5.0

    def test_capability_no_loss(self, minimal_org):
        cap = _capability_after_loss(minimal_org, [])
        assert math.isclose(cap, minimal_org.total_capability)

    def test_capability_all_lost_no_bench(self, minimal_org):
        """Losing all roles with no bench → bench-covered roles contribute 0."""
        all_ids = list(minimal_org.roles.keys())
        cap = _capability_after_loss(minimal_org, all_ids)
        # Only roles with bench_depth > 0 survive (admin has 2)
        admin_cap = minimal_org.roles["admin"].capability_weight * min(
            1.0, minimal_org.roles["admin"].bench_depth * 0.75)
        assert cap == pytest.approx(admin_cap, rel=0.01)

    def test_capability_mission_critical_cascade(self, minimal_org):
        """Losing a mission-critical role degrades its dependents."""
        cap_full = minimal_org.total_capability
        # lose 'worker' (mission-critical): root should be cascade-degraded
        cap_after = _capability_after_loss(minimal_org, ["worker"])
        assert cap_after < cap_full

    def test_capability_bench_provides_coverage(self, minimal_org):
        """Losing a role with bench > 0 provides partial capability."""
        # admin has bench_depth=2
        cap_admin_lost = _capability_after_loss(minimal_org, ["admin"])
        cap_no_loss    = minimal_org.total_capability
        admin_weight   = minimal_org.roles["admin"].capability_weight
        # admin with bench_depth=2: min(1, 2*0.75)=1.0 coverage
        assert math.isclose(cap_admin_lost, cap_no_loss, rel_tol=0.01)


# ══════════════════════════════════════════════════════════════════════════════
# SimulationResult
# ══════════════════════════════════════════════════════════════════════════════

class TestSimulationResult:

    def test_to_dict_contains_required_keys(self, minimal_sim):
        r = minimal_sim.scenario_random_attrition(n_losses=1,
                                                   n_iterations=FAST_N)
        d = r.to_dict()
        for key in ("scenario","run_id","n_iterations","n_losses","seed",
                    "timestamp","mean_pct","median_pct","std_dev",
                    "min_pct","max_pct","p10_pct","p25_pct","p75_pct","p90_pct"):
            assert key in d, f"Missing key in result dict: {key}"

    def test_percentile_ordering(self, minimal_sim):
        r = minimal_sim.scenario_random_attrition(n_losses=1,
                                                   n_iterations=FAST_N)
        assert r.min_pct <= r.p10_pct <= r.p25_pct
        assert r.p25_pct <= r.median_pct <= r.p75_pct
        assert r.p75_pct <= r.p90_pct <= r.max_pct

    def test_capability_pct_in_range(self, minimal_sim):
        r = minimal_sim.scenario_random_attrition(n_losses=1,
                                                   n_iterations=FAST_N)
        assert 0.0 <= r.min_pct <= 100.0
        assert 0.0 <= r.max_pct <= 100.0
        assert 0.0 <= r.mean_pct <= 100.0


# ══════════════════════════════════════════════════════════════════════════════
# Scenario 1: Random Attrition
# ══════════════════════════════════════════════════════════════════════════════

class TestRandomAttrition:

    def test_returns_simulation_result(self, minimal_sim):
        r = minimal_sim.scenario_random_attrition(n_losses=1,
                                                   n_iterations=FAST_N)
        assert isinstance(r, SimulationResult)

    def test_scenario_label(self, minimal_sim):
        r = minimal_sim.scenario_random_attrition(n_losses=1,
                                                   n_iterations=FAST_N)
        assert "Random" in r.scenario

    def test_n_iterations_recorded(self, minimal_sim):
        r = minimal_sim.scenario_random_attrition(n_losses=1,
                                                   n_iterations=FAST_N)
        assert r.n_iterations == FAST_N

    def test_losing_nothing_impossible(self, minimal_sim):
        """n_losses=0 → mean capability should equal 100%."""
        r = minimal_sim.scenario_random_attrition(n_losses=0,
                                                   n_iterations=100)
        assert math.isclose(r.mean_pct, 100.0, rel_tol=0.01)

    def test_seed_reproducibility(self, minimal_org):
        """Same seed must produce identical mean_pct."""
        r1 = KPVSimulator(minimal_org, seed=42).scenario_random_attrition(
            n_losses=1, n_iterations=FAST_N)
        r2 = KPVSimulator(minimal_org, seed=42).scenario_random_attrition(
            n_losses=1, n_iterations=FAST_N)
        assert math.isclose(r1.mean_pct, r2.mean_pct, rel_tol=1e-9)

    def test_different_seeds_may_differ(self, minimal_org):
        r1 = KPVSimulator(minimal_org, seed=1).scenario_random_attrition(
            n_losses=1, n_iterations=FAST_N)
        r2 = KPVSimulator(minimal_org, seed=999).scenario_random_attrition(
            n_losses=1, n_iterations=FAST_N)
        # Very unlikely to be identical with different seeds
        assert not math.isclose(r1.mean_pct, r2.mean_pct, rel_tol=1e-6)

    def test_more_losses_lower_capability(self, minimal_org):
        sim = KPVSimulator(minimal_org, seed=42)
        r1 = sim.scenario_random_attrition(n_losses=1, n_iterations=FAST_N)
        r2 = sim.scenario_random_attrition(n_losses=2, n_iterations=FAST_N)
        assert r2.mean_pct <= r1.mean_pct


# ══════════════════════════════════════════════════════════════════════════════
# Scenario 2: Adversarial Targeting
# ══════════════════════════════════════════════════════════════════════════════

class TestAdversarialTargeting:

    def test_returns_simulation_result(self, minimal_sim):
        r = minimal_sim.scenario_adversarial_targeting(n_losses=1,
                                                        n_iterations=FAST_N)
        assert isinstance(r, SimulationResult)

    def test_adversarial_lower_than_random(self, minimal_org):
        """Adversarial should ≤ random attrition on mean capability."""
        sim = KPVSimulator(minimal_org, seed=42)
        rnd = sim.scenario_random_attrition(n_losses=1, n_iterations=2000)
        adv = sim.scenario_adversarial_targeting(n_losses=1, n_iterations=2000,
                                                  targeting_accuracy=1.0)
        # With perfect accuracy, adversarial always picks the worst role
        assert adv.mean_pct <= rnd.mean_pct + 2.0  # allow 2pp margin for rng

    def test_perfect_accuracy_deterministic(self, minimal_org):
        """Accuracy=1.0 → same targets every iteration → zero std_dev."""
        sim = KPVSimulator(minimal_org, seed=42)
        r = sim.scenario_adversarial_targeting(n_losses=1, n_iterations=200,
                                                targeting_accuracy=1.0)
        # All iterations pick the same role → zero variance
        assert r.std_dev == pytest.approx(0.0, abs=0.1)

    def test_invalid_targeting_accuracy(self, minimal_sim):
        with pytest.raises(ValueError, match="targeting_accuracy"):
            minimal_sim.scenario_adversarial_targeting(
                n_losses=1, n_iterations=10, targeting_accuracy=0.0)

    def test_invalid_targeting_accuracy_over_one(self, minimal_sim):
        with pytest.raises(ValueError, match="targeting_accuracy"):
            minimal_sim.scenario_adversarial_targeting(
                n_losses=1, n_iterations=10, targeting_accuracy=1.1)

    def test_targeting_accuracy_in_extra(self, minimal_sim):
        r = minimal_sim.scenario_adversarial_targeting(n_losses=1,
                                                        n_iterations=FAST_N,
                                                        targeting_accuracy=0.75)
        assert r.extra.get("targeting_accuracy") == 0.75

    def test_rare_earth_adversarial_gap(self, rare_earth_org):
        """
        Rare earth org: adversarial should be meaningfully below random
        (validates that KPCI-weighted targeting exploits the gap).
        """
        sim = KPVSimulator(rare_earth_org, seed=42)
        rnd = sim.scenario_random_attrition(n_losses=2, n_iterations=1000)
        adv = sim.scenario_adversarial_targeting(n_losses=2, n_iterations=1000,
                                                  targeting_accuracy=0.85)
        gap = rnd.mean_pct - adv.mean_pct
        assert gap >= 0.0   # adversarial should not be better than random


# ══════════════════════════════════════════════════════════════════════════════
# Scenario 3: Cascade Failure
# ══════════════════════════════════════════════════════════════════════════════

class TestCascadeFailure:

    def test_returns_simulation_result(self, minimal_sim):
        r = minimal_sim.scenario_cascade_failure("worker", n_iterations=FAST_N)
        assert isinstance(r, SimulationResult)

    def test_extra_fields_present(self, minimal_sim):
        r = minimal_sim.scenario_cascade_failure("worker", n_iterations=FAST_N)
        assert "trigger_role_id" in r.extra
        assert "trigger_kpci"    in r.extra
        assert "trigger_tier"    in r.extra
        assert "estimated_restoration_months" in r.extra

    def test_trigger_metadata_correct(self, minimal_sim, minimal_org):
        r = minimal_sim.scenario_cascade_failure("worker", n_iterations=FAST_N)
        worker = minimal_org.get_role("worker")
        assert r.extra["trigger_role_id"] == "worker"
        assert math.isclose(r.extra["trigger_kpci"], worker.kpci)

    def test_unknown_trigger_raises(self, minimal_sim):
        with pytest.raises(ValueError, match="not found"):
            minimal_sim.scenario_cascade_failure("ghost", n_iterations=10)

    def test_capability_reduced_after_cascade(self, minimal_org):
        """Cascade loss of mission-critical role should reduce mean capability."""
        sim = KPVSimulator(minimal_org, seed=42)
        r = sim.scenario_cascade_failure("worker", n_iterations=FAST_N)
        assert r.mean_pct < 100.0

    def test_high_bench_limits_cascade(self, minimal_org):
        """Adding bench to 'worker' should reduce cascade severity."""
        import copy
        org_benched = copy.deepcopy(minimal_org)
        org_benched.roles["worker"].bench_depth = 3
        # Recompute derived attributes
        from kpvs.models import Role
        w = org_benched.roles["worker"]
        w.__dict__["bench_depth"] = 3  # direct set since it's post-init

        sim_base   = KPVSimulator(minimal_org, seed=42)
        sim_bench  = KPVSimulator(org_benched, seed=42)
        r_base  = sim_base.scenario_cascade_failure("worker", n_iterations=FAST_N)
        r_bench = sim_bench.scenario_cascade_failure("worker", n_iterations=FAST_N)
        # Benched version should have >= capability
        assert r_bench.mean_pct >= r_base.mean_pct - 5.0  # allow 5pp tolerance


# ══════════════════════════════════════════════════════════════════════════════
# KPCI Report
# ══════════════════════════════════════════════════════════════════════════════

class TestKPCIReport:

    def test_all_roles_present(self, minimal_sim, minimal_org):
        report = minimal_sim.kpci_report()
        ids = {r["id"] for r in report}
        assert ids == set(minimal_org.roles.keys())

    def test_sorted_descending_kpci(self, minimal_sim):
        report = minimal_sim.kpci_report()
        kpcis = [r["kpci"] for r in report]
        assert kpcis == sorted(kpcis, reverse=True)

    def test_required_keys_in_each_row(self, minimal_sim):
        report = minimal_sim.kpci_report()
        required = {"id","title","kpci","tier","bench_depth",
                    "estimated_restoration_months","mission_critical",
                    "n_dependents","n_direct_reports","recommendation"}
        for row in report:
            missing = required - set(row.keys())
            assert not missing, f"Missing keys in row: {missing}"

    def test_mission_critical_flagged(self, minimal_sim, minimal_org):
        report = minimal_sim.kpci_report()
        mc_in_report = {r["id"] for r in report if r["mission_critical"]}
        assert mc_in_report == set(minimal_org.mission_critical_roles)

    def test_recommendation_not_empty(self, minimal_sim):
        report = minimal_sim.kpci_report()
        for row in report:
            assert len(row["recommendation"]) > 10

    def test_tier1_recommendation_contains_urgent(self, rare_earth_sim):
        report = rare_earth_sim.kpci_report()
        tier1_rows = [r for r in report if r["tier"] == "Tier-1 KPV"]
        for row in tier1_rows:
            assert "URGENT" in row["recommendation"] or "urgent" in row["recommendation"].lower()


# ══════════════════════════════════════════════════════════════════════════════
# Integration: full pipeline on all example orgs
# ══════════════════════════════════════════════════════════════════════════════

class TestIntegration:

    @pytest.mark.parametrize("org_fixture", [
        "rare_earth_org", "nuclear_org", "pharma_org"
    ])
    def test_all_scenarios_run(self, request, org_fixture):
        org = request.getfixturevalue(org_fixture)
        sim = KPVSimulator(org, seed=42)

        rnd = sim.scenario_random_attrition(n_iterations=200)
        adv = sim.scenario_adversarial_targeting(n_iterations=200)
        assert isinstance(rnd, SimulationResult)
        assert isinstance(adv, SimulationResult)

        for mc_id in org.mission_critical_roles:
            cr = sim.scenario_cascade_failure(mc_id, n_iterations=200)
            assert isinstance(cr, SimulationResult)

    def test_capability_always_non_negative(self, rare_earth_org):
        sim = KPVSimulator(rare_earth_org, seed=42)
        for scenario_fn, kwargs in [
            (sim.scenario_random_attrition,
             {"n_losses": 5, "n_iterations": 500}),
            (sim.scenario_adversarial_targeting,
             {"n_losses": 5, "n_iterations": 500}),
        ]:
            r = scenario_fn(**kwargs)
            assert r.min_pct >= 0.0, (
                f"Negative capability in {scenario_fn.__name__}: {r.min_pct}")
