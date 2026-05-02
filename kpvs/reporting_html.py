"""
kpvs/reporting_html.py
=======================
Self-contained HTML report generator for KPVS.

Produces a single portable .html file with:
  - Executive summary dashboard
  - Color-coded KPCI table (Tier-1=red, Tier-2=amber, Manageable=blue, Resilient=green)
  - Horizontal KPCI bar chart (Chart.js)
  - Monte Carlo distribution comparison chart (random vs adversarial)
  - Cascade failure analysis cards
  - Bench investment optimizer results
  - Priority recommendations
  - Org dependency tree
  - Intelligence gap warning banner for adversarial orgs

Also produces a multi-org comparative report for --org-set runs.

All charts use Chart.js loaded from cdnjs.cloudflare.com.
No server required — opens directly in any browser.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Color palette ─────────────────────────────────────────────────────────────
TIER_COLORS = {
    "Tier-1 KPV": "#dc2626",   # red-600
    "Tier-2 KPV": "#d97706",   # amber-600
    "Manageable": "#2563eb",   # blue-600
    "Resilient":  "#16a34a",   # green-600
}
TIER_BG = {
    "Tier-1 KPV": "#fef2f2",
    "Tier-2 KPV": "#fffbeb",
    "Manageable": "#eff6ff",
    "Resilient":  "#f0fdf4",
}
TIER_BADGE = {
    "Tier-1 KPV": "T1",
    "Tier-2 KPV": "T2",
    "Manageable": "MG",
    "Resilient":  "RS",
}

VERSION = "1.0.0"


# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  font-size: 13px;
  background: #f8fafc;
  color: #1e293b;
  line-height: 1.5;
}
.page { max-width: 1200px; margin: 0 auto; padding: 24px 16px 60px; }

/* Header */
.report-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
  color: white; padding: 28px 32px; border-radius: 12px; margin-bottom: 24px;
}
.report-header h1 { font-size: 20px; font-weight: 700; margin-bottom: 6px; }
.report-header .subtitle { color: #94a3b8; font-size: 12px; }
.report-header .meta { display: flex; gap: 20px; margin-top: 14px; flex-wrap: wrap; }
.report-header .meta-item { font-size: 11px; color: #cbd5e1; }
.report-header .meta-item strong { color: white; }

/* Adversarial banner */
.adv-banner {
  background: #7c2d12; color: #fed7aa; padding: 12px 20px;
  border-radius: 8px; margin-bottom: 20px; font-size: 12px;
  border-left: 4px solid #f97316;
}
.adv-banner strong { color: #ffedd5; }

/* Cards */
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin-bottom: 24px; }
.card {
  background: white; border-radius: 10px; padding: 18px 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,.08); border: 1px solid #e2e8f0;
}
.card .label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
.card .value { font-size: 26px; font-weight: 700; line-height: 1; }
.card .sub { font-size: 11px; color: #94a3b8; margin-top: 4px; }
.card.danger .value { color: #dc2626; }
.card.warn   .value { color: #d97706; }
.card.good   .value { color: #16a34a; }
.card.info   .value { color: #2563eb; }

/* Section headers */
.section { margin-bottom: 28px; }
.section h2 {
  font-size: 14px; font-weight: 700; color: #1a1a2e;
  padding-bottom: 8px; border-bottom: 2px solid #1a1a2e;
  margin-bottom: 16px; text-transform: uppercase; letter-spacing: .06em;
}

/* KPCI Table */
.kpci-table { width: 100%; border-collapse: collapse; background: white;
  border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.08);
  font-size: 12px; }
.kpci-table th {
  background: #1a1a2e; color: #94a3b8; font-weight: 600; font-size: 10px;
  text-transform: uppercase; letter-spacing: .06em; padding: 10px 12px; text-align: left;
}
.kpci-table th.right { text-align: right; }
.kpci-table td { padding: 9px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.kpci-table tr:last-child td { border-bottom: none; }
.kpci-table tr:hover td { background: #f8fafc; }

/* Tier badge */
.badge {
  display: inline-block; padding: 2px 7px; border-radius: 4px;
  font-size: 10px; font-weight: 700; letter-spacing: .04em;
}
.mc-star { color: #d97706; font-weight: 700; margin-left: 4px; }
.kpci-bar-cell { width: 120px; }
.kpci-bar-bg { background: #f1f5f9; border-radius: 3px; height: 8px; overflow: hidden; }
.kpci-bar { height: 8px; border-radius: 3px; }

/* Chart containers */
.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
.chart-box {
  background: white; border-radius: 10px; padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,.08); border: 1px solid #e2e8f0;
}
.chart-box h3 { font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 14px;
  text-transform: uppercase; letter-spacing: .05em; }
.chart-full { grid-column: 1 / -1; }
canvas { max-width: 100%; }

/* Cascade cards */
.cascade-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
.cascade-card {
  background: white; border-radius: 10px; padding: 18px;
  border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
.cascade-card .trigger { font-weight: 700; font-size: 13px; margin-bottom: 10px; }
.cascade-card .stat-row { display: flex; justify-content: space-between;
  padding: 5px 0; border-bottom: 1px solid #f1f5f9; font-size: 12px; }
.cascade-card .stat-row:last-child { border-bottom: none; }
.cascade-card .stat-val { font-weight: 600; }
.stat-danger { color: #dc2626; }
.stat-warn   { color: #d97706; }
.stat-good   { color: #16a34a; }

/* Optimizer */
.optimizer-box {
  background: white; border-radius: 10px; padding: 20px;
  border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
.opt-header { display: flex; gap: 24px; margin-bottom: 18px; flex-wrap: wrap; }
.opt-stat { text-align: center; }
.opt-stat .val { font-size: 28px; font-weight: 700; }
.opt-stat .lbl { font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: .05em; }
.opt-arrow { font-size: 24px; color: #94a3b8; align-self: center; }
.opt-improvement { font-size: 28px; font-weight: 700; color: #16a34a; }
.alloc-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.alloc-table th { text-align: left; padding: 8px 10px; background: #f8fafc;
  font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: #64748b; }
.alloc-table td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; }
.alloc-table tr:last-child td { border-bottom: none; }

/* Recommendations */
.rec-list { display: flex; flex-direction: column; gap: 12px; }
.rec-item {
  background: white; border-radius: 10px; padding: 16px 18px;
  border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,.08);
  border-left: 4px solid #e2e8f0;
}
.rec-item.t1 { border-left-color: #dc2626; }
.rec-item.t2 { border-left-color: #d97706; }
.rec-title { font-weight: 700; font-size: 13px; margin-bottom: 4px; }
.rec-meta { font-size: 11px; color: #64748b; margin-bottom: 8px; }
.rec-text { font-size: 12px; color: #334155; }

/* Comparative table */
.comp-table { width: 100%; border-collapse: collapse; background: white;
  border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.comp-table th { background: #1a1a2e; color: #94a3b8; padding: 10px 14px;
  font-size: 10px; text-transform: uppercase; letter-spacing: .06em; text-align: left; }
.comp-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; font-size: 12px; }
.comp-table tr.adv-row td { background: #fff7ed; }
.gap-bar-wrap { display: flex; align-items: center; gap: 8px; }
.gap-bar-bg { flex: 1; background: #f1f5f9; border-radius: 3px; height: 8px; overflow: hidden; }
.gap-bar { height: 8px; border-radius: 3px; background: #2563eb; }
.gap-bar.warn { background: #d97706; }
.gap-bar.danger { background: #dc2626; }
.gap-num { font-size: 11px; font-weight: 600; width: 40px; text-align: right; }
.int-gap-note { font-size: 10px; color: #dc2626; font-style: italic; }

/* Footer */
.report-footer {
  text-align: center; font-size: 11px; color: #94a3b8; margin-top: 40px;
  padding-top: 20px; border-top: 1px solid #e2e8f0;
}

@media (max-width: 700px) {
  .chart-grid { grid-template-columns: 1fr; }
  .cards { grid-template-columns: repeat(2, 1fr); }
}
@media print {
  .page { max-width: 100%; padding: 16px; }
  .chart-box, .card, .kpci-table, .cascade-card { box-shadow: none; }
}
"""


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _badge(tier: str) -> str:
    color = TIER_COLORS.get(tier, "#64748b")
    bg    = TIER_BG.get(tier, "#f8fafc")
    label = TIER_BADGE.get(tier, "??")
    return (f'<span class="badge" '
            f'style="color:{color};background:{bg};'
            f'border:1px solid {color}20">{label}</span>')


def _kpci_bar(kpci: float, tier: str) -> str:
    pct = kpci / 12 * 100
    color = TIER_COLORS.get(tier, "#64748b")
    return (f'<div class="kpci-bar-bg">'
            f'<div class="kpci-bar" style="width:{pct:.1f}%;background:{color}"></div>'
            f'</div>')


def _pct_color(pct: float) -> str:
    if pct >= 90: return "stat-good"
    if pct >= 75: return "stat-warn"
    return "stat-danger"


def _card(label: str, value: str, sub: str = "",
          cls: str = "info") -> str:
    return (f'<div class="card {cls}">'
            f'<div class="label">{label}</div>'
            f'<div class="value">{value}</div>'
            f'{"<div class=sub>" + sub + "</div>" if sub else ""}'
            f'</div>')


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ══════════════════════════════════════════════════════════════════════════════
# Single-org HTML report
# ══════════════════════════════════════════════════════════════════════════════

def _build_single_report(data: dict) -> str:
    """Build a full HTML report from a KPVS summary JSON dict."""

    org      = data["organisation"]
    kpci     = data["kpci_report"]
    scenarios = data["scenarios"]
    cascades  = data.get("cascade", [])
    optimizer = data.get("optimizer")
    adversarial = data.get("adversarial_org", False)
    ao_note     = data.get("ao_note", "")

    tier_sum = org.get("tier_summary", {})
    t1 = tier_sum.get("Tier-1 KPV", 0)
    t2 = tier_sum.get("Tier-2 KPV", 0)

    # Scenario stats
    rnd = next((s for s in scenarios if "Random" in s["scenario"]), {})
    adv = next((s for s in scenarios if "Adversarial" in s["scenario"]), {})
    gap = round(rnd.get("mean_pct", 0) - adv.get("mean_pct", 0), 1)
    n_iter = rnd.get("n_iterations", 0)
    seed   = rnd.get("seed", "?")
    n_mc   = rnd.get("n_losses", 0)

    # ── Header ─────────────────────────────────────────────────────────────
    adv_banner = ""
    if adversarial:
        note = _esc(ao_note or
                    "AO scores are INVERTED — High AO = visible to allied OSINT. "
                    "Low AO = intelligence gap.")
        adv_banner = f"""
<div class="adv-banner">
  <strong>⚠ ADVERSARIAL ORGANIZATION — AO INVERSION ACTIVE</strong><br>
  {note}
</div>"""

    header = f"""
<div class="report-header">
  <h1>{_esc(org["name"])}</h1>
  <div class="subtitle">Key Person Vulnerability Assessment — KPVS v{VERSION}</div>
  <div class="meta">
    <div class="meta-item"><strong>Run ID</strong><br>{_esc(data["run_id"])}</div>
    <div class="meta-item"><strong>Seed</strong><br>{seed}</div>
    <div class="meta-item"><strong>Iterations</strong><br>{n_iter:,}</div>
    <div class="meta-item"><strong>Losses/iter</strong><br>{n_mc}</div>
    <div class="meta-item"><strong>Generated</strong><br>{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    <div class="meta-item"><strong>Total Roles</strong><br>{org["n_roles"]}</div>
  </div>
</div>"""

    # ── Summary cards ───────────────────────────────────────────────────────
    cards = f"""
<div class="cards">
  {_card("Tier-1 KPVs", str(t1), "Immediate action required", "danger" if t1 > 0 else "good")}
  {_card("Tier-2 KPVs", str(t2), "Elevated risk", "warn" if t2 > 0 else "good")}
  {_card("Adv. Gap", f"{gap:.1f} pp", "vs random attrition", "danger" if gap > 10 else "warn" if gap > 5 else "info")}
  {_card("Random Mean", f"{rnd.get('mean_pct',0):.1f}%", "Capability retention", "info")}
  {_card("Adversarial Mean", f"{adv.get('mean_pct',0):.1f}%", "Under targeted attack", _pct_color(adv.get("mean_pct", 100)).replace("stat-",""))}
  {_card("Zero-Bench T1", str(sum(1 for r in kpci if r["tier"]=="Tier-1 KPV" and r["bench_depth"]==0)), "Unprotected Tier-1 roles", "danger")}
</div>"""

    # ── KPCI Table ──────────────────────────────────────────────────────────
    rows = ""
    for r in kpci:
        mc = '<span class="mc-star" title="Mission-critical">★</span>' if r.get("mission_critical") else ""
        rows += f"""
<tr>
  <td>{_badge(r["tier"])}</td>
  <td><strong>{_esc(r["title"])}</strong>{mc}</td>
  <td style="text-align:right;font-weight:700;color:{TIER_COLORS.get(r['tier'],'#333')}">{r['kpci']:.1f}</td>
  <td style="text-align:right">{r['substitution_timeline']:.1f}</td>
  <td style="text-align:right">{r['documentation_ratio']:.1f}</td>
  <td style="text-align:right">{r['adversarial_observability']:.1f}</td>
  <td style="text-align:right">{r['bench_depth']}</td>
  <td style="text-align:right">{r['estimated_restoration_months']:.0f} mo</td>
  <td class="kpci-bar-cell">{_kpci_bar(r['kpci'], r['tier'])}</td>
</tr>"""

    kpci_table = f"""
<div class="section">
  <h2>KPCI Analysis — All Roles</h2>
  <table class="kpci-table">
    <thead>
      <tr>
        <th>Tier</th><th>Role</th>
        <th class="right">KPCI</th><th class="right">ST</th>
        <th class="right">DR</th><th class="right">AO</th>
        <th class="right">Bench</th><th class="right">Restore</th>
        <th>Score</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <p style="font-size:10px;color:#94a3b8;margin-top:8px">
    ★ Mission-critical &nbsp;|&nbsp;
    ST=Substitution Timeline &nbsp;DR=Documentation Ratio &nbsp;AO=Adversarial Observability &nbsp;|&nbsp;
    KPCI = ST + DR + AO (max 12)
  </p>
</div>"""

    # ── Chart data ──────────────────────────────────────────────────────────
    role_labels  = json.dumps([r["title"][:30] for r in kpci])
    kpci_vals    = json.dumps([r["kpci"] for r in kpci])
    kpci_colors  = json.dumps([TIER_COLORS.get(r["tier"], "#666") for r in kpci])
    tier_labels  = json.dumps(list(tier_sum.keys()))
    tier_vals    = json.dumps(list(tier_sum.values()))
    tier_cols    = json.dumps([TIER_COLORS[t] for t in tier_sum.keys()])

    # Distribution bars (5-percentile buckets)
    rnd_p = [rnd.get(f"p{p}_pct", 0) for p in [10, 25, 50, 75, 90]]
    adv_p = [adv.get(f"p{p}_pct", 0) for p in [10, 25, 50, 75, 90]]

    charts = f"""
<div class="chart-grid">
  <div class="chart-box">
    <h3>KPCI Scores by Role</h3>
    <canvas id="kpciChart" height="280"></canvas>
  </div>
  <div class="chart-box">
    <h3>Tier Distribution</h3>
    <canvas id="tierChart" height="280"></canvas>
  </div>
  <div class="chart-box chart-full">
    <h3>Capability Retention Distribution — Random Attrition vs Adversarial Targeting
      <span style="font-size:10px;color:#94a3b8;font-weight:400">
        (percentiles P10/P25/P50/P75/P90 · N={n_iter:,} · {n_mc} losses/iter)
      </span>
    </h3>
    <canvas id="distChart" height="120"></canvas>
  </div>
</div>"""

    chart_js = f"""
<script>
// KPCI bar chart
new Chart(document.getElementById('kpciChart'), {{
  type: 'bar',
  data: {{
    labels: {role_labels},
    datasets: [{{
      label: 'KPCI', data: {kpci_vals},
      backgroundColor: {kpci_colors}, borderRadius: 4,
    }}]
  }},
  options: {{
    indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ min: 0, max: 12, grid: {{ color: '#f1f5f9' }},
             ticks: {{ font: {{ size: 10 }} }} }},
      y: {{ ticks: {{ font: {{ size: 10 }}, color: '#334155' }} }}
    }}
  }}
}});

// Tier donut
new Chart(document.getElementById('tierChart'), {{
  type: 'doughnut',
  data: {{
    labels: {tier_labels},
    datasets: [{{ data: {tier_vals},
      backgroundColor: {tier_cols}, borderWidth: 2, borderColor: '#fff'
    }}]
  }},
  options: {{
    plugins: {{
      legend: {{ position: 'bottom',
        labels: {{ font: {{ size: 11 }}, padding: 12 }} }}
    }}
  }}
}});

// Distribution comparison
new Chart(document.getElementById('distChart'), {{
  type: 'bar',
  data: {{
    labels: ['P10', 'P25', 'Median', 'P75', 'P90'],
    datasets: [
      {{ label: 'Random Attrition',
         data: {json.dumps(rnd_p)},
         backgroundColor: '#3b82f680', borderColor: '#3b82f6',
         borderWidth: 1, borderRadius: 4 }},
      {{ label: 'Adversarial Targeting (85% accuracy)',
         data: {json.dumps(adv_p)},
         backgroundColor: '#dc262680', borderColor: '#dc2626',
         borderWidth: 1, borderRadius: 4 }},
    ]
  }},
  options: {{
    scales: {{
      y: {{ min: 0, max: 100, title: {{ display: true, text: 'Capability %',
             font: {{ size: 10 }} }},
             grid: {{ color: '#f1f5f9' }}, ticks: {{ font: {{ size: 10 }} }} }},
      x: {{ ticks: {{ font: {{ size: 10 }} }} }}
    }},
    plugins: {{
      legend: {{ labels: {{ font: {{ size: 11 }} }} }},
      tooltip: {{ callbacks: {{ label: function(c) {{
        return c.dataset.label + ': ' + c.parsed.y.toFixed(1) + '%';
      }} }} }}
    }}
  }}
}});
</script>"""

    # ── Cascade failure cards ───────────────────────────────────────────────
    cascade_html = ""
    if cascades:
        cards_html = ""
        for c in cascades:
            color = TIER_COLORS.get(c.get("extra_trigger_tier",""), "#666")
            restore = c.get("extra_estimated_restoration_months", "?")
            name = c["scenario"].replace("Cascade Failure — trigger: ", "")
            p10c  = _pct_color(c.get("p10_pct", 100))
            meanc = _pct_color(c.get("mean_pct", 100))
            cards_html += f"""
<div class="cascade-card">
  <div class="trigger" style="color:{color}">⚡ {_esc(name)}</div>
  <div class="stat-row">
    <span>KPCI</span>
    <span class="stat-val" style="color:{color}">
      {c.get('extra_trigger_kpci','?'):.1f} · {_esc(c.get('extra_trigger_tier',''))}
    </span>
  </div>
  <div class="stat-row">
    <span>Mean residual capability</span>
    <span class="stat-val {meanc}">{c.get('mean_pct',0):.1f}%</span>
  </div>
  <div class="stat-row">
    <span>Worst-case (P10)</span>
    <span class="stat-val {p10c}">{c.get('p10_pct',0):.1f}%</span>
  </div>
  <div class="stat-row">
    <span>Best-case (P90)</span>
    <span class="stat-val stat-good">{c.get('p90_pct',0):.1f}%</span>
  </div>
  <div class="stat-row">
    <span>Est. restoration</span>
    <span class="stat-val stat-danger">{restore} months</span>
  </div>
</div>"""
        cascade_html = f"""
<div class="section">
  <h2>Cascade Failure Analysis — Mission-Critical Roles</h2>
  <div class="cascade-grid">{cards_html}</div>
</div>"""

    # ── Optimizer ───────────────────────────────────────────────────────────
    opt_html = ""
    if optimizer:
        alloc_rows = ""
        for role_id, detail in optimizer.get("allocation", {}).items():
            color = TIER_COLORS.get(detail.get("tier",""), "#666")
            alloc_rows += f"""
<tr>
  <td><strong>{_esc(detail['title'])}</strong></td>
  <td style="color:{color};font-weight:700">{detail['kpci']:.1f}</td>
  <td>{_badge(detail['tier'])}</td>
  <td style="color:#16a34a;font-weight:700">+{detail['units_added']}</td>
  <td>{detail['total_bench']}</td>
  <td style="color:#16a34a">{detail.get('new_restoration_months','?'):.0f} mo</td>
</tr>"""

        imp = optimizer.get("improvement_pp", 0)
        base = optimizer.get("baseline_mean_pct", 0)
        opt_val = optimizer.get("optimized_mean_pct", 0)
        opt_html = f"""
<div class="section">
  <h2>Optimal Bench Investment — {optimizer.get('budget_units',0)}-Unit Allocation</h2>
  <div class="optimizer-box">
    <div class="opt-header">
      <div class="opt-stat">
        <div class="val {_pct_color(base).replace('stat-','')}" style="color:{TIER_COLORS['Tier-1 KPV'] if base<75 else '#d97706' if base<85 else '#16a34a'}">{base:.1f}%</div>
        <div class="lbl">Baseline (adversarial)</div>
      </div>
      <div class="opt-arrow">→</div>
      <div class="opt-stat">
        <div class="opt-improvement">{opt_val:.1f}%</div>
        <div class="lbl">After investment</div>
      </div>
      <div class="opt-stat" style="margin-left:16px">
        <div class="opt-improvement">+{imp:.1f} pp</div>
        <div class="lbl">Improvement</div>
      </div>
    </div>
    <table class="alloc-table">
      <thead>
        <tr><th>Role</th><th>KPCI</th><th>Tier</th>
            <th>Units Added</th><th>Total Bench</th><th>New Restore</th></tr>
      </thead>
      <tbody>{alloc_rows}</tbody>
    </table>
  </div>
</div>"""

    # ── Recommendations ─────────────────────────────────────────────────────
    urgent = [r for r in kpci if r["tier"] in ("Tier-1 KPV", "Tier-2 KPV")]
    rec_items = ""
    for r in urgent:
        cls  = "t1" if r["tier"] == "Tier-1 KPV" else "t2"
        mc   = " ★ MISSION-CRITICAL" if r.get("mission_critical") else ""
        deps = r.get("n_dependents", 0)
        rec_items += f"""
<div class="rec-item {cls}">
  <div class="rec-title">{_badge(r['tier'])} {_esc(r['title'])}<em style="color:#d97706">{mc}</em></div>
  <div class="rec-meta">
    KPCI {r['kpci']:.1f} &nbsp;|&nbsp;
    Bench: {r['bench_depth']} &nbsp;|&nbsp;
    Restoration: {r['estimated_restoration_months']:.0f} mo &nbsp;|&nbsp;
    {deps} dependent role(s)
  </div>
  <div class="rec-text">{_esc(r['recommendation'])}</div>
</div>"""

    rec_html = f"""
<div class="section">
  <h2>Priority Recommendations</h2>
  <div class="rec-list">{rec_items}</div>
</div>"""

    # ── Assemble ────────────────────────────────────────────────────────────
    title = _esc(org["name"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>KPVS Report — {title}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"
  crossorigin="anonymous"></script>
<style>{_CSS}</style>
</head>
<body>
<div class="page">
{header}
{adv_banner}
{cards}
{kpci_table}
{charts}
{cascade_html}
{opt_html}
{rec_html}
<div class="report-footer">
  KPVS v{VERSION} &nbsp;·&nbsp; MTS Research Programme Working Paper 5 &nbsp;·&nbsp;
  Robert J. Green &nbsp;·&nbsp; rjgreenresearch.org &nbsp;·&nbsp;
  github.com/rjgreenresearch/kpv-simulator<br>
  <em>All KPCI scores are analytical estimates. Calibrate with HR data and
  subject-matter expert review. No classified materials were used.</em>
</div>
</div>
{chart_js}
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# Multi-org comparative report
# ══════════════════════════════════════════════════════════════════════════════

def _build_comparative_report(summaries: list[dict],
                               set_name: str = "") -> str:
    """
    Build a comparative HTML report from multiple org summary dicts.
    Used for --org-set runs (Five Eyes, adversarial, all_intel).
    """

    rows = ""
    chart_orgs   = []
    chart_gaps   = []
    chart_colors = []
    chart_rnd    = []
    chart_adv    = []

    for data in summaries:
        org      = data["organisation"]
        scenarios = data["scenarios"]
        kpci_rep  = data["kpci_report"]
        adversarial = data.get("adversarial_org", False)

        rnd = next((s for s in scenarios if "Random" in s["scenario"]), {})
        adv = next((s for s in scenarios if "Adversarial" in s["scenario"]), {})
        gap = round(rnd.get("mean_pct", 0) - adv.get("mean_pct", 0), 1)

        ts   = org.get("tier_summary", {})
        t1   = ts.get("Tier-1 KPV", 0)
        t2   = ts.get("Tier-2 KPV", 0)
        mc   = len([r for r in kpci_rep if r.get("mission_critical")])
        zb   = sum(1 for r in kpci_rep
                   if r["tier"] == "Tier-1 KPV" and r["bench_depth"] == 0)

        # Gap bar
        bar_pct   = min(100, abs(gap) / 25 * 100)
        bar_class = "danger" if abs(gap) > 15 else "warn" if abs(gap) > 7 else ""
        adv_row   = "adv-row" if adversarial else ""
        int_gap   = ""
        if adversarial and abs(gap) < 2.0:
            int_gap = '<br><span class="int-gap-note">⚠ Near-zero gap = intelligence gap</span>'

        gap_cell = f"""
<div class="gap-bar-wrap">
  <div class="gap-bar-bg">
    <div class="gap-bar {bar_class}" style="width:{bar_pct:.0f}%"></div>
  </div>
  <span class="gap-num">{gap:+.1f}</span>
</div>{int_gap}"""

        rows += f"""
<tr class="{adv_row}">
  <td><strong>{_esc(org['name'][:55])}</strong>
      {"&nbsp;<em style='color:#d97706;font-size:10px'>[ADV]</em>" if adversarial else ""}
  </td>
  <td style="text-align:center">{org['n_roles']}</td>
  <td style="text-align:center;color:#dc2626;font-weight:700">{t1}</td>
  <td style="text-align:center;color:#d97706;font-weight:700">{t2}</td>
  <td style="text-align:center">{mc}</td>
  <td style="text-align:center;color:#dc2626;font-weight:700">{zb}</td>
  <td style="text-align:right">{rnd.get('mean_pct',0):.1f}%</td>
  <td style="text-align:right">{adv.get('mean_pct',0):.1f}%</td>
  <td>{gap_cell}</td>
</tr>"""

        chart_orgs.append(org["name"][:35])
        chart_gaps.append(abs(gap))
        chart_rnd.append(rnd.get("mean_pct", 0))
        chart_adv.append(adv.get("mean_pct", 0))
        chart_colors.append(TIER_COLORS["Tier-1 KPV"] if adversarial
                            else "#2563eb")

    title = f"Comparative KPV Assessment — {set_name}" if set_name else \
            "Comparative KPV Assessment"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>KPVS {_esc(title)}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"
  crossorigin="anonymous"></script>
<style>{_CSS}</style>
</head>
<body>
<div class="page">
<div class="report-header">
  <h1>{_esc(title)}</h1>
  <div class="subtitle">Key Person Vulnerability Simulator v{VERSION}
    — Multi-Organization Comparative Report</div>
  <div class="meta">
    <div class="meta-item"><strong>Organizations</strong><br>{len(summaries)}</div>
    <div class="meta-item"><strong>Generated</strong><br>{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    <div class="meta-item"><strong>Adversarial AO Note</strong><br>
      [ADV] rows: low gap = intelligence gap, not resilience</div>
  </div>
</div>

<div class="section">
  <h2>Comparative Summary</h2>
  <table class="comp-table">
    <thead>
      <tr>
        <th>Organization</th>
        <th style="text-align:center">Roles</th>
        <th style="text-align:center">T1</th>
        <th style="text-align:center">T2</th>
        <th style="text-align:center">MC</th>
        <th style="text-align:center">Zero-Bench T1</th>
        <th style="text-align:right">Rnd Mean%</th>
        <th style="text-align:right">Adv Mean%</th>
        <th>Adversarial Gap</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>

<div class="chart-grid">
  <div class="chart-box">
    <h3>Adversarial Targeting Gap by Organization</h3>
    <canvas id="gapChart" height="300"></canvas>
  </div>
  <div class="chart-box">
    <h3>Random vs Adversarial Mean Capability</h3>
    <canvas id="capChart" height="300"></canvas>
  </div>
</div>

<div class="report-footer">
  KPVS v{VERSION} &nbsp;·&nbsp; MTS Research Programme Working Paper 5 &nbsp;·&nbsp;
  Robert J. Green &nbsp;·&nbsp; rjgreenresearch.org<br>
  <em>[ADV] organizations: AO scores reflect allied OSINT visibility.
  Near-zero adversarial gap indicates intelligence gap, not resilience.
  Classified AO data would significantly alter adversarial org results.</em>
</div>
</div>

<script>
new Chart(document.getElementById('gapChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(chart_orgs)},
    datasets: [{{
      label: 'Adversarial Gap (pp)',
      data: {json.dumps(chart_gaps)},
      backgroundColor: {json.dumps(chart_colors)},
      borderRadius: 4,
    }}]
  }},
  options: {{
    indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ min: 0, title: {{ display: true,
             text: 'Adversarial Gap (percentage points)',
             font: {{ size: 10 }} }},
             grid: {{ color: '#f1f5f9' }}, ticks: {{ font: {{ size: 10 }} }} }},
      y: {{ ticks: {{ font: {{ size: 10 }} }} }}
    }}
  }}
}});

new Chart(document.getElementById('capChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(chart_orgs)},
    datasets: [
      {{ label: 'Random Attrition', data: {json.dumps(chart_rnd)},
         backgroundColor: '#3b82f680', borderRadius: 4 }},
      {{ label: 'Adversarial Targeting', data: {json.dumps(chart_adv)},
         backgroundColor: '#dc262680', borderRadius: 4 }},
    ]
  }},
  options: {{
    scales: {{
      y: {{ min: 0, max: 100,
             title: {{ display: true, text: 'Capability %', font: {{ size: 10 }} }},
             grid: {{ color: '#f1f5f9' }}, ticks: {{ font: {{ size: 10 }} }} }},
      x: {{ ticks: {{ font: {{ size: 10 }} }} }}
    }},
    plugins: {{ legend: {{ labels: {{ font: {{ size: 11 }} }} }} }}
  }}
}});
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# HTMLReporter class
# ══════════════════════════════════════════════════════════════════════════════

class HTMLReporter:
    """
    Generates HTML report files from KPVS summary JSON data.

    Usage
    -----
    Single org:
        reporter = HTMLReporter("reports/")
        reporter.write_report(summary_data)

    Multi-org (org-set):
        reporter.write_comparative(list_of_summary_dicts, set_name="five_eyes")
    """

    def __init__(self, html_dir: str = "reports") -> None:
        self.html_dir = html_dir
        os.makedirs(html_dir, exist_ok=True)
        logger.debug("HTMLReporter: output dir '%s'", html_dir)

    def _path(self, filename: str) -> str:
        return os.path.join(self.html_dir, filename)

    def write_report(self, data: dict,
                     filename: str | None = None) -> str:
        """
        Write a single-org HTML report.

        Parameters
        ----------
        data     : KPVS summary dict (from JSONReporter.write_summary or
                   loaded from a _summary.json file).
        filename : output filename; auto-generated from run_id if None.

        Returns
        -------
        str : path to the written HTML file.
        """
        if filename is None:
            filename = f"{data['run_id']}_report.html"

        html = _build_single_report(data)
        path = self._path(filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("HTML report written: %s", path)
        return path

    def write_comparative(self, summaries: list[dict],
                           set_name: str = "",
                           filename: str | None = None) -> str:
        """
        Write a multi-org comparative HTML report.

        Parameters
        ----------
        summaries : list of KPVS summary dicts.
        set_name  : label for the report (e.g. 'five_eyes').
        filename  : output filename; auto-generated if None.
        """
        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            slug = set_name.replace(" ", "_") or "comparative"
            filename = f"{slug}_{ts}_report.html"

        html = _build_comparative_report(summaries, set_name)
        path = self._path(filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Comparative HTML report written: %s", path)
        return path

    @staticmethod
    def from_json_file(json_path: str) -> dict:
        """Load a KPVS summary JSON file into a dict for report generation."""
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
