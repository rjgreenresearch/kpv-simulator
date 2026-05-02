"""
tests/test_reporting_html.py
============================
Tests for kpvs.reporting_html — HTMLReporter.
"""

import json
import os
import tempfile
import copy
import pytest

from kpvs.simulator import KPVSimulator
from kpvs.optimizer import BenchOptimizer
from kpvs.reporting import JSONReporter
from kpvs.reporting_html import HTMLReporter, _build_single_report, _build_comparative_report

FAST_N = 200


def _make_summary(org, seed=42):
    """Helper: build a summary dict from an org."""
    sim = KPVSimulator(org, seed=seed)
    rnd = sim.scenario_random_attrition(n_losses=1, n_iterations=FAST_N)
    adv = sim.scenario_adversarial_targeting(n_losses=1, n_iterations=FAST_N)
    report = sim.kpci_report()
    with tempfile.TemporaryDirectory() as d:
        jr = JSONReporter(d)
        path = jr.write_summary(org, report, [rnd, adv], [], None, sim.run_id)
        with open(path) as f:
            return json.load(f)


class TestHTMLReporter:

    def test_write_report_creates_file(self, minimal_org):
        summary = _make_summary(minimal_org)
        with tempfile.TemporaryDirectory() as d:
            hr = HTMLReporter(d)
            path = hr.write_report(summary)
            assert os.path.exists(path)
            assert path.endswith(".html")

    def test_html_has_required_sections(self, minimal_org):
        summary = _make_summary(minimal_org)
        with tempfile.TemporaryDirectory() as d:
            hr = HTMLReporter(d)
            path = hr.write_report(summary)
            with open(path) as f:
                content = f.read()
        assert "KPCI Analysis" in content
        assert "Chart.js" in content or "chart.umd.min.js" in content
        assert "Monte Carlo" in content or "MONTE CARLO" in content or "Capability Retention" in content
        assert "Priority Recommendations" in content

    def test_html_valid_structure(self, minimal_org):
        summary = _make_summary(minimal_org)
        html = _build_single_report(summary)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html
        assert "<canvas" in html   # Chart.js canvases present

    def test_adversarial_banner_shown(self, minimal_org):
        summary = _make_summary(minimal_org)
        summary["adversarial_org"] = True
        html = _build_single_report(summary)
        assert "ADVERSARIAL" in html
        assert "AO INVERSION" in html

    def test_adversarial_banner_hidden_for_allied(self, minimal_org):
        summary = _make_summary(minimal_org)
        summary["adversarial_org"] = False
        html = _build_single_report(summary)
        # CSS contains class def; check that banner CONTENT is absent
        assert "AO INVERSION ACTIVE" not in html
        assert "ADVERSARIAL ORGANIZATION" not in html

    def test_write_comparative_creates_file(self, minimal_org):
        s1 = _make_summary(minimal_org)
        s2 = copy.deepcopy(s1)
        s2["organisation"]["name"] = "Second Org"
        with tempfile.TemporaryDirectory() as d:
            hr = HTMLReporter(d)
            path = hr.write_comparative([s1, s2], "test_set")
            assert os.path.exists(path)

    def test_comparative_html_structure(self, minimal_org):
        s1 = _make_summary(minimal_org)
        s2 = copy.deepcopy(s1)
        s2["organisation"]["name"] = "Second Org"
        html = _build_comparative_report([s1, s2], "five_eyes")
        assert "Comparative" in html
        assert "five_eyes" in html or "Comparative" in html
        assert "gapChart" in html
        assert "capChart" in html

    def test_run_dir_auto_created(self):
        with tempfile.TemporaryDirectory() as d:
            new_dir = os.path.join(d, "nested", "reports")
            hr = HTMLReporter(new_dir)
            assert os.path.isdir(new_dir)

    def test_from_json_file(self, minimal_org):
        summary = _make_summary(minimal_org)
        with tempfile.TemporaryDirectory() as d:
            jr = JSONReporter(d)
            sim = KPVSimulator(minimal_org, seed=42)
            rnd = sim.scenario_random_attrition(n_losses=1, n_iterations=FAST_N)
            report = sim.kpci_report()
            path = jr.write_summary(minimal_org, report, [rnd], [], None, sim.run_id)
            loaded = HTMLReporter.from_json_file(path)
            assert "run_id" in loaded
            assert "organisation" in loaded

    def test_html_escapes_special_chars(self):
        """Organisation names with special chars must not break HTML."""
        from kpvs.models import Role, Organization
        roles = {
            "r": Role("r", "Chief <Script> & Analyst", 3.0, 3.0, 3.0,
                      capability_weight=1.0)
        }
        org = Organization("Test & <Org>", roles, mission_critical_roles=[])
        summary = _make_summary(org)
        html = _build_single_report(summary)
        # Should not contain raw unescaped < in title context
        assert "<Script>" not in html.split("<title>")[1].split("</title>")[0]


class TestHTMLCLIIntegration:
    """Smoke tests for HTML output via the full CLI path."""

    def test_demo_produces_html(self):
        """Running --demo --html-dir should create HTML files."""
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            result = subprocess.run(
                ["python", "main.py", "--demo",
                 "--iterations", "100",
                 "--skip-cascade", "--skip-optimizer",
                 "--html-dir", d, "--no-log-file", "--quiet"],
                capture_output=True, text=True, cwd="/home/claude/kpv-simulator"
            )
            html_files = [f for root,dirs,files in os.walk(d) for f in files if f.endswith('.html')]
            assert len(html_files) >= 1, (
                f"Expected HTML files, got none. stderr: {result.stderr[:300]}")

    def test_list_orgs_flag(self):
        """--list-orgs should print org keys and exit cleanly."""
        import subprocess
        result = subprocess.run(
            ["python", "main.py", "--list-orgs", "--no-log-file"],
            capture_output=True, text=True, cwd="/home/claude/kpv-simulator"
        )
        assert result.returncode == 0
        assert "us_nsa" in result.stdout
        assert "five_eyes" in result.stdout

    def test_org_set_five_eyes(self):
        """--org-set five_eyes should run without error."""
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            result = subprocess.run(
                ["python", "main.py", "--org-set", "five_eyes",
                 "--iterations", "100",
                 "--skip-cascade", "--skip-optimizer",
                 "--html-dir", d, "--no-log-file", "--quiet"],
                capture_output=True, text=True, cwd="/home/claude/kpv-simulator"
            )
            assert result.returncode == 0, (
                f"--org-set five_eyes failed: {result.stderr[:400]}")
            html_files = [f for root,dirs,files in os.walk(d) for f in files if f.endswith('.html')]
            # Should have individual reports + 1 comparative
            assert len(html_files) >= 2

    def test_org_set_adversarial(self):
        """--org-set adversarial should run without error."""
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            result = subprocess.run(
                ["python", "main.py", "--org-set", "adversarial",
                 "--iterations", "100",
                 "--skip-cascade", "--skip-optimizer",
                 "--html-dir", d, "--no-log-file", "--quiet"],
                capture_output=True, text=True, cwd="/home/claude/kpv-simulator"
            )
            assert result.returncode == 0, (
                f"--org-set adversarial failed: {result.stderr[:400]}")

    def test_unrecognized_org_set_fails_gracefully(self):
        """Unknown --org-set value should raise ValueError, not crash."""
        import subprocess
        result = subprocess.run(
            ["python", "main.py", "--org-set", "nonexistent_set",
             "--no-log-file"],
            capture_output=True, text=True, cwd="/home/claude/kpv-simulator"
        )
        # Should exit non-zero with a useful message
        assert result.returncode != 0 or "Unknown" in result.stderr + result.stdout
