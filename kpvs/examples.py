"""
kpvs/examples.py — Built-in demonstration organizations
=========================================================
Three example organizations cover the primary MTS sectors:
  1. build_rare_earth_org()      — domestic REE processing programme
  2. build_nuclear_programme_org()— stockpile stewardship design team
  3. build_pharma_org()          — pharmaceutical KSM synthesis facility
"""

from __future__ import annotations
from .models import Role, Organization


def _make_role(**kw) -> Role:
    return Role(**kw)


# ── 1. Rare Earth Processing Programme ───────────────────────────────────────

def build_rare_earth_org() -> Organization:
    """
    U.S. domestic rare earth processing programme (MP Materials scale).
    Models KPCI vulnerabilities documented in MTS Paper 4 / CICP Section 3.1.
    """
    roles = [
        _make_role(id="chief_sep_chemist", title="Chief Separation Process Chemist",
                   substitution_timeline=4.0, documentation_ratio=3.5,
                   adversarial_observability=3.5, reports_to="vp_technical",
                   critical_dependencies=["process_ops","qa_lead","scale_up"],
                   capability_weight=4.0, bench_depth=0,
                   notes="Irreplaceable HRE separation tacit knowledge; Thousand Talents target profile."),
        _make_role(id="heavy_ree_specialist", title="Heavy REE Extraction Specialist (Dy/Tb)",
                   substitution_timeline=4.0, documentation_ratio=3.0,
                   adversarial_observability=3.0, reports_to="chief_sep_chemist",
                   critical_dependencies=[],
                   capability_weight=3.5, bench_depth=0,
                   notes="Dysprosium/terbium separation; essential for THAAD/PAC-3 magnets."),
        _make_role(id="dod_program_exec", title="DoD DPA Title III Programme Executive",
                   substitution_timeline=3.5, documentation_ratio=2.5,
                   adversarial_observability=4.0, reports_to="ceo",
                   critical_dependencies=[],
                   capability_weight=3.0, bench_depth=0,
                   notes="Personal relationship capital with DoD PM office; high public visibility."),
        _make_role(id="vp_technical", title="VP Technical Operations",
                   substitution_timeline=3.0, documentation_ratio=2.0,
                   adversarial_observability=3.5, reports_to="ceo",
                   critical_dependencies=["chief_sep_chemist","process_ops"],
                   capability_weight=2.5, bench_depth=1),
        _make_role(id="allied_liaison", title="Lynas/Australia Supply Chain Liaison",
                   substitution_timeline=3.0, documentation_ratio=3.0,
                   adversarial_observability=2.0, reports_to="ceo",
                   critical_dependencies=[],
                   capability_weight=2.5, bench_depth=0,
                   notes="20-year relationship with Lynas Kalgoorlie management; not documented."),
        _make_role(id="scale_up", title="Commercial Scale-Up Engineer",
                   substitution_timeline=2.5, documentation_ratio=2.5,
                   adversarial_observability=2.5, reports_to="vp_technical",
                   critical_dependencies=["process_ops"],
                   capability_weight=2.0, bench_depth=0),
        _make_role(id="regulatory_lead", title="EPA/NRC Regulatory Compliance Lead",
                   substitution_timeline=2.5, documentation_ratio=1.5,
                   adversarial_observability=2.0, reports_to="vp_technical",
                   critical_dependencies=[],
                   capability_weight=2.0, bench_depth=0),
        _make_role(id="ceo", title="Chief Executive Officer",
                   substitution_timeline=2.5, documentation_ratio=1.5,
                   adversarial_observability=3.0, reports_to=None,
                   critical_dependencies=["dod_program_exec","allied_liaison"],
                   capability_weight=2.0, bench_depth=0),
        _make_role(id="process_ops", title="Process Operations Manager",
                   substitution_timeline=2.0, documentation_ratio=1.5,
                   adversarial_observability=1.5, reports_to="vp_technical",
                   critical_dependencies=[], capability_weight=1.5, bench_depth=1),
        _make_role(id="qa_lead", title="Quality Assurance Lead",
                   substitution_timeline=1.5, documentation_ratio=1.0,
                   adversarial_observability=1.0, reports_to="vp_technical",
                   critical_dependencies=[], capability_weight=1.0, bench_depth=1),
        _make_role(id="lab_tech_sr", title="Senior Laboratory Technician",
                   substitution_timeline=1.0, documentation_ratio=0.5,
                   adversarial_observability=0.5, reports_to="chief_sep_chemist",
                   critical_dependencies=[], capability_weight=0.75, bench_depth=2),
        _make_role(id="lab_tech", title="Laboratory Technician",
                   substitution_timeline=0.5, documentation_ratio=0.5,
                   adversarial_observability=0.5, reports_to="chief_sep_chemist",
                   critical_dependencies=[], capability_weight=0.5, bench_depth=3),
        _make_role(id="finance_mgr", title="Finance & Contracts Manager",
                   substitution_timeline=1.0, documentation_ratio=0.5,
                   adversarial_observability=1.0, reports_to="ceo",
                   critical_dependencies=[], capability_weight=0.75, bench_depth=1),
    ]
    roles_dict = {r.id: r for r in roles}
    return Organization(
        name="U.S. Domestic Rare Earth Processing Programme",
        roles=roles_dict,
        mission_critical_roles=["chief_sep_chemist", "heavy_ree_specialist",
                                 "dod_program_exec"],
        description=(
            "Models KPCI vulnerabilities in a Mountain Pass-scale REE "
            "separation and magnet manufacturing programme. Demonstrates "
            "Tier-1 KPV architecture documented in MTS Paper 4 / CICP §3.1."
        ),
    )


# ── 2. Nuclear Stockpile Stewardship Design Team ─────────────────────────────

def build_nuclear_programme_org() -> Organization:
    """
    Notional nuclear weapons design certification team (JASON-analogue).
    Models the stockpile stewardship KPV documented in MTS Paper 5, §4.1.
    """
    roles = [
        _make_role(id="senior_designer", title="Senior Warhead Design Physicist",
                   substitution_timeline=4.0, documentation_ratio=4.0,
                   adversarial_observability=3.0, reports_to="chief_scientist",
                   critical_dependencies=["design_lead","cert_process"],
                   capability_weight=5.0, bench_depth=0,
                   notes="30yr tacit knowledge in specific warhead family LEP. KPCI=11. JASON concern."),
        _make_role(id="chief_scientist", title="Chief Weapons Scientist",
                   substitution_timeline=4.0, documentation_ratio=3.0,
                   adversarial_observability=3.5, reports_to="lab_dir",
                   critical_dependencies=["senior_designer","simulation_lead"],
                   capability_weight=4.0, bench_depth=0),
        _make_role(id="simulation_lead", title="Hydrodynamic Simulation Lead",
                   substitution_timeline=3.5, documentation_ratio=3.5,
                   adversarial_observability=2.5, reports_to="chief_scientist",
                   critical_dependencies=["cert_process"],
                   capability_weight=3.5, bench_depth=0,
                   notes="Proprietary code validation methodology; partially tacit."),
        _make_role(id="cert_process", title="LEP Certification Process Lead",
                   substitution_timeline=3.0, documentation_ratio=2.5,
                   adversarial_observability=2.0, reports_to="chief_scientist",
                   critical_dependencies=[], capability_weight=3.0, bench_depth=1),
        _make_role(id="design_lead", title="Design Physics Group Lead",
                   substitution_timeline=3.0, documentation_ratio=2.0,
                   adversarial_observability=2.5, reports_to="chief_scientist",
                   critical_dependencies=["senior_designer"],
                   capability_weight=2.5, bench_depth=0),
        _make_role(id="lab_dir", title="Laboratory Director",
                   substitution_timeline=2.5, documentation_ratio=1.5,
                   adversarial_observability=4.0, reports_to=None,
                   critical_dependencies=["chief_scientist"],
                   capability_weight=2.0, bench_depth=1),
        _make_role(id="fy_budget_mgr", title="NNSA Programme Budget Manager",
                   substitution_timeline=2.0, documentation_ratio=1.5,
                   adversarial_observability=3.0, reports_to="lab_dir",
                   critical_dependencies=[], capability_weight=1.5, bench_depth=1),
        _make_role(id="junior_physicist", title="Junior Weapons Physicist",
                   substitution_timeline=2.0, documentation_ratio=1.0,
                   adversarial_observability=1.0, reports_to="design_lead",
                   critical_dependencies=[], capability_weight=1.0, bench_depth=2),
        _make_role(id="admin_support", title="Cleared Administrative Support",
                   substitution_timeline=0.5, documentation_ratio=0.5,
                   adversarial_observability=1.0, reports_to="lab_dir",
                   critical_dependencies=[], capability_weight=0.5, bench_depth=2),
    ]
    roles_dict = {r.id: r for r in roles}
    return Organization(
        name="Nuclear Stockpile Stewardship Design Team (Notional)",
        roles=roles_dict,
        mission_critical_roles=["senior_designer", "chief_scientist",
                                 "simulation_lead"],
        description=(
            "Notional model of a weapons design certification team. "
            "Illustrates extreme Tier-1 KPV in the nuclear domain. "
            "Informed by JASON (2009) JSR-09-334 unclassified analysis."
        ),
    )


# ── 3. Pharmaceutical KSM Synthesis Facility ─────────────────────────────────

def build_pharma_org() -> Organization:
    """
    Domestic pharmaceutical Key Starting Material synthesis facility.
    Models KPV in the pharmaceutical processing domain (MTS Paper 5, §4.4).
    """
    roles = [
        _make_role(id="chief_process_chemist", title="Chief Process Chemist (Antibiotic KSMs)",
                   substitution_timeline=3.5, documentation_ratio=3.5,
                   adversarial_observability=3.0, reports_to="vp_rd",
                   critical_dependencies=["synthesis_ops","qc_lead"],
                   capability_weight=4.0, bench_depth=0,
                   notes="Continuous flow synthesis expertise; 15yr vancomycin KSM programme."),
        _make_role(id="flow_chem_specialist", title="Continuous Flow Chemistry Specialist",
                   substitution_timeline=3.5, documentation_ratio=3.0,
                   adversarial_observability=2.5, reports_to="chief_process_chemist",
                   critical_dependencies=["synthesis_ops"],
                   capability_weight=3.0, bench_depth=0,
                   notes="Reactor design tacit knowledge; BARDA/Continuus programme liaison."),
        _make_role(id="fda_liaison", title="FDA CDER Regulatory Liaison",
                   substitution_timeline=3.0, documentation_ratio=2.0,
                   adversarial_observability=3.0, reports_to="ceo",
                   critical_dependencies=[],
                   capability_weight=3.0, bench_depth=0,
                   notes="10yr personal relationship with CDER review division."),
        _make_role(id="vp_rd", title="VP Research & Development",
                   substitution_timeline=3.0, documentation_ratio=2.0,
                   adversarial_observability=3.5, reports_to="ceo",
                   critical_dependencies=["chief_process_chemist"],
                   capability_weight=2.5, bench_depth=1),
        _make_role(id="ceo", title="Chief Executive Officer",
                   substitution_timeline=2.5, documentation_ratio=1.5,
                   adversarial_observability=3.5, reports_to=None,
                   critical_dependencies=["fda_liaison","vp_rd"],
                   capability_weight=2.0, bench_depth=0),
        _make_role(id="synthesis_ops", title="Synthesis Operations Manager",
                   substitution_timeline=2.0, documentation_ratio=1.5,
                   adversarial_observability=1.5, reports_to="vp_rd",
                   critical_dependencies=[], capability_weight=1.5, bench_depth=1),
        _make_role(id="qc_lead", title="Quality Control Lead",
                   substitution_timeline=1.5, documentation_ratio=1.0,
                   adversarial_observability=1.0, reports_to="vp_rd",
                   critical_dependencies=[], capability_weight=1.0, bench_depth=1),
        _make_role(id="supply_chain_mgr", title="API Supply Chain Manager",
                   substitution_timeline=2.0, documentation_ratio=1.0,
                   adversarial_observability=2.0, reports_to="ceo",
                   critical_dependencies=[], capability_weight=1.5, bench_depth=0),
        _make_role(id="lab_associate", title="Senior Laboratory Associate",
                   substitution_timeline=1.0, documentation_ratio=0.5,
                   adversarial_observability=0.5, reports_to="chief_process_chemist",
                   critical_dependencies=[], capability_weight=0.75, bench_depth=2),
    ]
    roles_dict = {r.id: r for r in roles}
    return Organization(
        name="Domestic Pharmaceutical KSM Synthesis Facility",
        roles=roles_dict,
        mission_critical_roles=["chief_process_chemist", "flow_chem_specialist",
                                 "fda_liaison"],
        description=(
            "CICP-aligned KSM synthesis facility model. "
            "Demonstrates pharmaceutical sector KPV (MTS Paper 5, §4.4 / "
            "CICP §3.3). Informed by BARDA/Continuus programme data."
        ),
    )
