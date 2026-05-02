#!/usr/bin/env python3
"""
main.py — KPVS Command-Line Interface
======================================
Key Person Vulnerability Simulator v1.0.0
MTS Research Programme · Working Paper 5 · Robert J. Green (2026)

Usage examples
--------------
  # Built-in examples
  python main.py --demo
  python main.py --example rare_earth --iterations 10000 --seed 20260501 --budget 3

  # Custom org JSON
  python main.py --org examples/rare_earth_org.json

  # Intelligence org sets  (--org-set fix included)
  python main.py --intel-org cn --iterations 10000
  python main.py --org-set five_eyes --iterations 10000 --budget 3
  python main.py --org-set adversarial --iterations 10000 --skip-optimizer
  python main.py --list-orgs

  # Output
  python main.py --demo --json-dir runs/ --html-dir reports/
  python main.py --demo --quiet --json-dir runs/ --html-dir reports/

  # Logging
  python main.py --demo --log-level DEBUG --log-file logs/debug.log
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime

# ── ensure project root on path ───────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kpvs import Organization, KPVSimulator, BenchOptimizer
from kpvs.examples import (
    build_rare_earth_org,
    build_nuclear_programme_org,
    build_pharma_org,
)
from kpvs.logging_config import configure_logging
from kpvs.reporting import ConsoleReporter, JSONReporter
from kpvs.reporting_html import HTMLReporter

logger = logging.getLogger("kpvs.cli")

EXAMPLE_BUILDERS = {
    "rare_earth": build_rare_earth_org,
    "nuclear":    build_nuclear_programme_org,
    "pharma":     build_pharma_org,
}


# ══════════════════════════════════════════════════════════════════════════════
# CLI argument parser
# ══════════════════════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="kpvs",
        description="Key Person Vulnerability Simulator (KPVS) v1.0.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python main.py --demo
  python main.py --example rare_earth --iterations 10000 --seed 20260501 --budget 3
  python main.py --org examples/rare_earth_org.json
  python main.py --org-set five_eyes --iterations 10000 --budget 3
  python main.py --org-set adversarial --iterations 10000 --skip-optimizer
  python main.py --intel-org cn --iterations 10000
  python main.py --list-orgs
  python main.py --demo --json-dir runs/ --html-dir reports/
        """,
    )

    # ── Organisation source ───────────────────────────────────────────────────
    src = p.add_mutually_exclusive_group()
    src.add_argument(
        "--demo",
        action="store_true",
        help="Run all three built-in example organisations sequentially.",
    )
    src.add_argument(
        "--example",
        choices=list(EXAMPLE_BUILDERS.keys()),
        metavar=f"{{{','.join(EXAMPLE_BUILDERS)}}}",
        help="Run a single named built-in example.",
    )
    src.add_argument(
        "--org",
        metavar="FILE",
        help="Path to a custom organisation JSON file.",
    )
    src.add_argument(
        "--intel-org",
        metavar="KEY",
        help=(
            "Load a named intelligence org: "
            "us_nsa | uk | ca | au | nz | cn | ru | ir | kp"
        ),
    )
    src.add_argument(
        "--org-set",
        metavar="SET",
        help=(
            "Run a predefined org set: "
            "five_eyes | adversarial | all_intel | us_and_china"
        ),
    )
    src.add_argument(
        "--list-orgs",
        action="store_true",
        help="List all available intelligence org keys and exit.",
    )

    # ── Simulation parameters ─────────────────────────────────────────────────
    p.add_argument(
        "--iterations", "-N",
        type=int,
        default=10_000,
        metavar="N",
        help="Monte Carlo iterations (default: 10,000).",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=20260501,
        help="RNG seed for reproducibility (default: 20260501).",
    )
    p.add_argument(
        "--n-losses",
        type=int,
        default=None,
        metavar="K",
        help="Roles lost per iteration (default: 20%% of org size).",
    )
    p.add_argument(
        "--targeting-accuracy",
        type=float,
        default=0.85,
        metavar="P",
        help="Adversarial KPCI targeting accuracy in (0,1] (default: 0.85).",
    )
    p.add_argument(
        "--budget",
        type=int,
        default=3,
        metavar="B",
        help="Bench investment units for optimizer (default: 3).",
    )
    p.add_argument(
        "--skip-cascade",
        action="store_true",
        help="Skip cascade failure scenario (faster run).",
    )
    p.add_argument(
        "--skip-optimizer",
        action="store_true",
        help="Skip bench investment optimizer (faster run).",
    )

    # ── Output ────────────────────────────────────────────────────────────────
    p.add_argument(
        "--json-dir",
        metavar="DIR",
        default=None,
        help="Directory for JSON output artefacts.",
    )
    p.add_argument(
        "--html-dir",
        metavar="DIR",
        default=None,
        help="Directory for HTML report output. "
             "Creates one .html per org plus a comparative report for --org-set.",
    )
    p.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress console output (JSON/HTML output unaffected).",
    )

    # ── Logging ───────────────────────────────────────────────────────────────
    p.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Console log level (default: INFO).",
    )
    p.add_argument(
        "--log-file",
        metavar="FILE",
        default=None,
        help="Log file path. Auto-generated in logs/ if omitted.",
    )
    p.add_argument(
        "--no-log-file",
        action="store_true",
        help="Disable file logging entirely.",
    )

    return p


# ══════════════════════════════════════════════════════════════════════════════
# Core run function — one organisation
# ══════════════════════════════════════════════════════════════════════════════

def run_simulation(
    org: Organization,
    args: argparse.Namespace,
    json_reporter: JSONReporter | None,
    html_reporter: HTMLReporter | None,
    adversarial: bool = False,
) -> dict | None:
    """
    Execute the full simulation suite for one organization.

    Returns the summary dict so --org-set can aggregate for
    the comparative HTML report.
    """
    sim     = KPVSimulator(org, seed=args.seed)
    console = ConsoleReporter(org, sim)

    if not args.quiet:
        if adversarial:
            print("\n  ⚠  ADVERSARIAL ORG — AO scores are INVERTED")
            print("     High AO = clearly visible to allied OSINT")
            print("     Low AO  = intelligence gap requiring attention\n")
        console.print_header()
        console.print_kpci_table()

    # ── KPCI report ───────────────────────────────────────────────────────────
    kpci_report = sim.kpci_report()
    if json_reporter:
        json_reporter.write_kpci_report(kpci_report, sim.run_id)

    # ── Scenario: random attrition ────────────────────────────────────────────
    n_losses = args.n_losses if args.n_losses is not None else max(1, len(org.roles) // 5)

    logger.info("Running random attrition scenario …")
    rnd = sim.scenario_random_attrition(n_losses, args.iterations)

    # ── Scenario: adversarial targeting ───────────────────────────────────────
    logger.info("Running adversarial targeting scenario …")
    adv = sim.scenario_adversarial_targeting(
        n_losses, args.iterations, args.targeting_accuracy
    )
    adv.extra["adversarial_gap_pp"] = rnd.mean_pct - adv.mean_pct

    scenario_results = [rnd, adv]

    if not args.quiet:
        console.print_scenario_table(scenario_results, n_losses)

    if json_reporter:
        for s in scenario_results:
            json_reporter.write_scenario(s)

    # ── Scenario: cascade failure ─────────────────────────────────────────────
    cascade_results = []
    if not args.skip_cascade and org.mission_critical_roles:
        logger.info("Running cascade failure scenarios …")
        for mc_id in org.mission_critical_roles:
            cr = sim.scenario_cascade_failure(mc_id, args.iterations)
            cascade_results.append(cr)
            if json_reporter:
                json_reporter.write_scenario(cr)
        if not args.quiet:
            console.print_cascade_results(cascade_results)

    # ── Optimizer ─────────────────────────────────────────────────────────────
    opt_result = None
    if not args.skip_optimizer:
        logger.info("Running bench investment optimizer (budget=%d) …", args.budget)
        optimizer = BenchOptimizer(
            org,
            seed=args.seed,
            eval_iterations=max(200, args.iterations // 20),
        )
        opt_result = optimizer.optimise(args.budget, run_id=sim.run_id)
        if not args.quiet:
            console.print_optimizer_result(opt_result)
        if json_reporter:
            json_reporter.write_optimizer(opt_result)

    # ── Recommendations ───────────────────────────────────────────────────────
    if not args.quiet:
        console.print_recommendations(kpci_report)
        console.print_footer()

    # ── Summary JSON ──────────────────────────────────────────────────────────
    summary_data = None
    if json_reporter:
        path = json_reporter.write_summary(
            org, kpci_report, scenario_results,
            cascade_results, opt_result, sim.run_id,
        )
        if not args.quiet:
            print(f"  JSON summary → {path}")

        # Load it back so we have the full dict for HTML generation
        with open(path, encoding="utf-8") as f:
            summary_data = json.load(f)
        # Attach adversarial flag for HTML reporter
        summary_data["adversarial_org"] = adversarial

    elif html_reporter:
        # Build summary dict in-memory if no JSON reporter
        from kpvs.reporting import JSONReporter as _JR
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_jr = _JR(tmpdir)
            p = tmp_jr.write_summary(
                org, kpci_report, scenario_results,
                cascade_results, opt_result, sim.run_id,
            )
            with open(p, encoding="utf-8") as f:
                summary_data = json.load(f)
        summary_data["adversarial_org"] = adversarial

    # ── HTML report ───────────────────────────────────────────────────────────
    if html_reporter and summary_data:
        html_path = html_reporter.write_report(summary_data)
        if not args.quiet:
            print(f"  HTML report  → {html_path}")

    return summary_data


# ══════════════════════════════════════════════════════════════════════════════
# Intelligence org mode
# ══════════════════════════════════════════════════════════════════════════════

def run_intel_mode(
    args: argparse.Namespace,
    json_reporter: JSONReporter | None,
    html_reporter: HTMLReporter | None,
) -> None:
    """Execute intelligence org or org-set analysis."""
    from kpvs.intelligence.org_loader import (
        load_org, load_org_set, available_orgs, available_org_sets
    )

    if args.list_orgs:
        print("\nAvailable intelligence org keys:")
        for key, info in available_orgs().items():
            status = "✓" if info["exists"] else "✗ MISSING"
            print(f"  {status}  {key:<15} {info['path']}")
        print("\nAvailable org sets:")
        for name, keys in available_org_sets().items():
            print(f"  {name:<15} {', '.join(keys)}")
        return

    # Collect orgs and adversarial flags
    org_pairs: list[tuple[Organization, bool]] = []

    if args.intel_org:
        org = load_org(args.intel_org)
        is_adv = getattr(org, "_adversarial", False)
        org_pairs = [(org, is_adv)]

    elif args.org_set:
        orgs = load_org_set(args.org_set)
        org_pairs = [(o, getattr(o, "_adversarial", False)) for o in orgs]

    summaries: list[dict] = []
    for org, is_adv in org_pairs:
        # Give each org its own JSON sub-dir to avoid filename collisions
        org_jr = None
        if json_reporter:
            slug = org.name[:20].lower().replace(" ", "_").replace("/", "")
            org_jr = JSONReporter(os.path.join(json_reporter.run_dir, slug))

        logger.info("=== Intelligence Analysis: %s ===", org.name)
        summary = run_simulation(org, args, org_jr, html_reporter, is_adv)
        if summary:
            summaries.append(summary)
        logger.info("=== Completed: %s ===", org.name)

    # Comparative HTML for org-set runs
    if html_reporter and len(summaries) > 1:
        set_name = args.org_set or "comparative"
        path = html_reporter.write_comparative(summaries, set_name)
        if not args.quiet:
            print(f"\n  Comparative HTML → {path}")


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    # ── Logging setup ─────────────────────────────────────────────────────────
    log_file = "" if args.no_log_file else args.log_file
    configure_logging(
        level    = args.log_level,
        log_file = log_file,
        quiet    = args.quiet,
    )
    logger.info("KPVS v1.0.0 starting (seed=%d, N=%d)",
                args.seed, args.iterations)

    # ── Reporters — timestamped subdirectories keep output paths clean ────────
    # e.g. --json-dir runs/  →  runs/run_20260502_075452/
    #      --org-set five_eyes  →  runs/five_eyes_20260502_075452/
    _ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    _label = (
        args.org_set    if getattr(args, "org_set",    None) else
        args.intel_org  if getattr(args, "intel_org",  None) else
        args.example    if getattr(args, "example",    None) else
        "run"
    )
    _run_folder = f"{_label}_{_ts}"

    json_reporter: JSONReporter | None = None
    if args.json_dir:
        from pathlib import Path as _P
        _jd = _P(args.json_dir) / _run_folder
        _jd.mkdir(parents=True, exist_ok=True)
        json_reporter = JSONReporter(str(_jd))

    html_reporter: HTMLReporter | None = None
    if args.html_dir:
        from pathlib import Path as _P
        _hd = _P(args.html_dir) / _run_folder
        _hd.mkdir(parents=True, exist_ok=True)
        html_reporter = HTMLReporter(str(_hd))

    # ── Intelligence org mode  (must check before demo/example/org) ───────────
    if args.list_orgs or args.intel_org or args.org_set:
        run_intel_mode(args, json_reporter, html_reporter)
        return

    # ── Resolve built-in / custom organisations ───────────────────────────────
    if args.demo:
        orgs = [b() for b in EXAMPLE_BUILDERS.values()]
    elif args.example:
        orgs = [EXAMPLE_BUILDERS[args.example]()]
    elif args.org:
        try:
            with open(args.org, encoding="utf-8") as f:
                data = json.load(f)
            orgs = [Organization.from_dict(data)]
        except FileNotFoundError:
            parser.error(f"Organisation file not found: {args.org}")
        except (json.JSONDecodeError, KeyError) as exc:
            parser.error(f"Invalid organisation JSON: {exc}")
    else:
        # Default: rare earth demo
        logger.info("No source specified — running rare_earth demo.")
        orgs = [build_rare_earth_org()]

    # ── Run each org ──────────────────────────────────────────────────────────
    summaries: list[dict] = []
    for org in orgs:
        logger.info("=== Starting: %s ===", org.name)
        summary = run_simulation(org, args, json_reporter, html_reporter)
        if summary:
            summaries.append(summary)
        logger.info("=== Completed: %s ===", org.name)

    # ── Comparative HTML for --demo (3 orgs) ──────────────────────────────────
    if html_reporter and len(summaries) > 1:
        path = html_reporter.write_comparative(summaries, "demo")
        if not args.quiet:
            print(f"\n  Comparative HTML → {path}")


if __name__ == "__main__":
    main()
