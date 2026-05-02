"""
tests/test_reporting.py
========================
Tests for kpvs.reporting — JSON output integrity and console smoke tests.
"""

import json
import os
import tempfile
import pytest
from kpvs.simulator import KPVSimulator
from kpvs.optimizer import BenchOptimizer
from kpvs.reporting import ConsoleReporter, JSONReporter

FAST_N = 200


class TestJSONReporter:

    def test_kpci_report_file_created(self, minimal_org):
        sim = KPVSimulator(minimal_org, seed=42)
        report = sim.kpci_report()
        with tempfile.TemporaryDirectory() as d:
            jr = JSONReporter(d)
            path = jr.write_kpci_report(report, "test_run")
            assert os.path.exists(path)

    def test_kpci_report_valid_json(self, minimal_org):
        sim = KPVSimulator(minimal_org, seed=42)
        report = sim.kpci_report()
        with tempfile.TemporaryDirectory() as d:
            jr = JSONReporter(d)
            path = jr.write_kpci_report(report, "test_run")
            with open(path) as f:
                data = json.load(f)
            assert "roles" in data
            assert "run_id" in data

    def test_scenario_file_created(self, minimal_org):
        sim = KPVSimulator(minimal_org, seed=42)
        r = sim.scenario_random_attrition(n_losses=1, n_iterations=FAST_N)
        with tempfile.TemporaryDirectory() as d:
            jr = JSONReporter(d)
            path = jr.write_scenario(r)
            assert os.path.exists(path)

    def test_scenario_json_has_required_keys(self, minimal_org):
        sim = KPVSimulator(minimal_org, seed=42)
        r = sim.scenario_random_attrition(n_losses=1, n_iterations=FAST_N)
        with tempfile.TemporaryDirectory() as d:
            jr = JSONReporter(d)
            path = jr.write_scenario(r)
            with open(path) as f:
                data = json.load(f)
            for key in ("scenario","mean_pct","median_pct","p10_pct","p90_pct"):
                assert key in data

    def test_summary_json_created(self, minimal_org):
        sim = KPVSimulator(minimal_org, seed=42)
        rnd = sim.scenario_random_attrition(n_losses=1, n_iterations=FAST_N)
        adv = sim.scenario_adversarial_targeting(n_losses=1, n_iterations=FAST_N)
        report = sim.kpci_report()
        with tempfile.TemporaryDirectory() as d:
            jr = JSONReporter(d)
            path = jr.write_summary(
                minimal_org, report,
                [rnd, adv], [], None, sim.run_id,
            )
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert "organisation" in data
            assert "scenarios" in data
            assert data["organisation"]["n_roles"] == len(minimal_org.roles)

    def test_optimizer_json_created(self, minimal_org):
        import copy
        org = copy.deepcopy(minimal_org)
        opt = BenchOptimizer(org, seed=42, eval_iterations=50)
        result = opt.optimise(budget_units=1)
        with tempfile.TemporaryDirectory() as d:
            jr = JSONReporter(d)
            path = jr.write_optimizer(result)
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert "allocation" in data
            assert "improvement_pp" in data

    def test_run_dir_auto_created(self):
        with tempfile.TemporaryDirectory() as d:
            new_dir = os.path.join(d, "auto", "created")
            jr = JSONReporter(new_dir)
            assert os.path.isdir(new_dir)


class TestConsoleReporter:
    """Smoke tests — verify print methods don't raise."""

    def test_print_header_no_exception(self, minimal_org, capsys):
        sim = KPVSimulator(minimal_org, seed=42)
        cr = ConsoleReporter(minimal_org, sim)
        cr.print_header()
        captured = capsys.readouterr()
        assert "KPVS" in captured.out

    def test_print_kpci_table_no_exception(self, minimal_org, capsys):
        sim = KPVSimulator(minimal_org, seed=42)
        cr = ConsoleReporter(minimal_org, sim)
        cr.print_kpci_table()
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_print_scenario_table_no_exception(self, minimal_org, capsys):
        sim = KPVSimulator(minimal_org, seed=42)
        rnd = sim.scenario_random_attrition(n_losses=1, n_iterations=FAST_N)
        adv = sim.scenario_adversarial_targeting(n_losses=1, n_iterations=FAST_N)
        cr = ConsoleReporter(minimal_org, sim)
        cr.print_scenario_table([rnd, adv], n_losses=1)
        captured = capsys.readouterr()
        assert "Scenario" in captured.out

    def test_print_recommendations_no_exception(self, minimal_org, capsys):
        sim = KPVSimulator(minimal_org, seed=42)
        report = sim.kpci_report()
        cr = ConsoleReporter(minimal_org, sim)
        cr.print_recommendations(report)
        # No assertion on content — just must not raise

    def test_print_footer_no_exception(self, minimal_org, capsys):
        sim = KPVSimulator(minimal_org, seed=42)
        cr = ConsoleReporter(minimal_org, sim)
        cr.print_footer()
        captured = capsys.readouterr()
        assert "MTS" in captured.out or "KPVS" in captured.out
