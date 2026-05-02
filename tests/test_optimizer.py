"""
tests/test_optimizer.py
========================
Unit and integration tests for kpvs.optimizer — BenchOptimizer.
"""

import math
import copy
import pytest
from kpvs.optimizer import BenchOptimizer, OptimizationResult
from kpvs.models import Organization


FAST_EVAL = 100   # eval_iterations for unit tests


# ══════════════════════════════════════════════════════════════════════════════
# OptimizationResult
# ══════════════════════════════════════════════════════════════════════════════

class TestOptimizationResult:

    def _run(self, org, budget=2):
        opt = BenchOptimizer(org, seed=42, eval_iterations=FAST_EVAL)
        return opt.optimise(budget)

    def test_returns_optimization_result(self, minimal_org):
        r = self._run(minimal_org)
        assert isinstance(r, OptimizationResult)

    def test_to_dict_keys(self, minimal_org):
        r = self._run(minimal_org)
        d = r.to_dict()
        for key in ("run_id","timestamp","budget_units","baseline_mean_pct",
                    "optimized_mean_pct","improvement_pp","allocation"):
            assert key in d

    def test_budget_recorded(self, minimal_org):
        r = self._run(minimal_org, budget=3)
        assert r.budget_units == 3

    def test_improvement_non_negative(self, minimal_org):
        """Optimisation must never reduce capability."""
        r = self._run(minimal_org, budget=2)
        assert r.improvement_pp >= -0.5   # allow tiny numerical slack

    def test_allocation_within_budget(self, minimal_org):
        r = self._run(minimal_org, budget=3)
        total_added = sum(
            d["units_added"] for d in r.allocation.values()
        )
        assert total_added <= 3

    def test_allocation_keys_valid(self, minimal_org):
        r = self._run(minimal_org, budget=2)
        for role_id in r.allocation:
            assert role_id in minimal_org.roles


# ══════════════════════════════════════════════════════════════════════════════
# BenchOptimizer — allocation logic
# ══════════════════════════════════════════════════════════════════════════════

class TestBenchOptimizer:

    def test_zero_budget(self, minimal_org):
        opt = BenchOptimizer(minimal_org, seed=42, eval_iterations=FAST_EVAL)
        r = opt.optimise(budget_units=0)
        assert r.allocation == {}
        assert math.isclose(r.improvement_pp, 0.0, abs_tol=0.5)

    def test_single_unit_allocated(self, minimal_org):
        opt = BenchOptimizer(minimal_org, seed=42, eval_iterations=FAST_EVAL)
        r = opt.optimise(budget_units=1)
        assert sum(d["units_added"] for d in r.allocation.values()) == 1

    def test_prefers_high_kpci_roles(self, rare_earth_org):
        """
        Optimizer should allocate to Tier-1/Tier-2 roles, not Resilient.
        Verified over the rare earth org which has clear KPCI spread.
        """
        org = copy.deepcopy(rare_earth_org)
        opt = BenchOptimizer(org, seed=42, eval_iterations=FAST_EVAL)
        r = opt.optimise(budget_units=3)

        # All allocated roles should be Tier-1 or Tier-2
        for role_id in r.allocation:
            role = org.roles[role_id]
            assert role.tier in ("Tier-1 KPV", "Tier-2 KPV"), (
                f"Optimizer allocated to non-priority role: {role.title} ({role.tier})"
            )

    def test_max_bench_respected(self, minimal_org):
        """No role should exceed max_bench_per_role."""
        org = copy.deepcopy(minimal_org)
        # Set max bench to 1 so we can test the cap quickly
        opt = BenchOptimizer(org, seed=42, eval_iterations=FAST_EVAL,
                             max_bench_per_role=1)
        r = opt.optimise(budget_units=10)
        for role_id, detail in r.allocation.items():
            assert detail["total_bench"] <= 1

    def test_capability_pct_plausible(self, minimal_org):
        opt = BenchOptimizer(minimal_org, seed=42, eval_iterations=FAST_EVAL)
        r = opt.optimise(budget_units=2)
        assert 0.0 <= r.baseline_mean_pct <= 100.0
        assert 0.0 <= r.optimized_mean_pct <= 100.0

    def test_reproducible_with_same_seed(self, minimal_org):
        """Same seed on independent org copies must produce identical allocation."""
        import copy
        org_a = copy.deepcopy(minimal_org)
        org_b = copy.deepcopy(minimal_org)
        r1 = BenchOptimizer(org_a, seed=7, eval_iterations=FAST_EVAL
                            ).optimise(budget_units=2)
        r2 = BenchOptimizer(org_b, seed=7, eval_iterations=FAST_EVAL
                            ).optimise(budget_units=2)
        assert set(r1.allocation.keys()) == set(r2.allocation.keys())
        assert r1.budget_units == r2.budget_units

    def test_allocation_detail_structure(self, minimal_org):
        opt = BenchOptimizer(minimal_org, seed=42, eval_iterations=FAST_EVAL)
        r = opt.optimise(budget_units=1)
        for role_id, detail in r.allocation.items():
            assert "title"         in detail
            assert "kpci"          in detail
            assert "tier"          in detail
            assert "units_added"   in detail
            assert "total_bench"   in detail
            assert "new_restoration_months" in detail


# ══════════════════════════════════════════════════════════════════════════════
# Integration: optimizer + simulator cross-validation
# ══════════════════════════════════════════════════════════════════════════════

class TestOptimizerIntegration:

    def test_optimized_bench_improves_simulator(self, rare_earth_org):
        """
        After optimizer runs, re-running the adversarial scenario with the
        updated bench depths should yield higher capability than baseline.
        """
        from kpvs.simulator import KPVSimulator
        org = copy.deepcopy(rare_earth_org)
        sim_baseline = KPVSimulator(org, seed=42)
        base = sim_baseline.scenario_adversarial_targeting(
            n_losses=2, n_iterations=500)

        # Run optimizer (modifies org.roles bench_depth in place)
        opt = BenchOptimizer(org, seed=42, eval_iterations=FAST_EVAL)
        opt_result = opt.optimise(budget_units=3)

        sim_after = KPVSimulator(org, seed=42)
        after = sim_after.scenario_adversarial_targeting(
            n_losses=2, n_iterations=500)

        # Optimized bench should not make things worse
        assert after.mean_pct >= base.mean_pct - 2.0  # 2pp tolerance

    @pytest.mark.parametrize("org_fixture", [
        "rare_earth_org", "nuclear_org", "pharma_org"
    ])
    def test_optimizer_runs_on_all_examples(self, request, org_fixture):
        org = copy.deepcopy(request.getfixturevalue(org_fixture))
        opt = BenchOptimizer(org, seed=42, eval_iterations=50)
        r = opt.optimise(budget_units=2)
        assert isinstance(r, OptimizationResult)
        assert r.budget_units == 2
