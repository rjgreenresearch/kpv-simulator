"""
examples/prc_person_centric_demo.py — End-to-end person-centric demo
=====================================================================

Demonstrates the new person-centric layer using the PRC taxonomy with
synthetic-but-plausible occupant attributes. Shows:

  1. Loading the PRC taxonomy
  2. Attaching synthetic Person objects to roles
  3. Computing Effective KPCI vs Structural KPCI
  4. Multi-hat detection (Xi Jinping → 3 roles)
  5. Continuity-loss diagnostics for a decapitation scenario

Run:
    python examples/prc_person_centric_demo.py
"""

from kpvs.persons import (
    Person, RoleAssignment, multi_hat_persons, roles_held_by,
)
from kpvs.effective_kpci import (
    effective_kpci, effective_tier, continuity_loss, person_premium,
)
from kpvs.intelligence.role_mapper import PRC_TAXONOMY


def banner(text: str) -> None:
    print("\n" + "═" * 76)
    print(f"  {text}")
    print("═" * 76)


def main() -> None:
    banner("PRC PERSON-CENTRIC KPVS DEMO")

    # ── Step 1: build synthetic Person occupants ─────────────────────────
    # In production these come from the OSINT graph via role_mapper.map_country()
    persons = {
        "XI": Person(
            id="P-CN-XI-JINPING",
            name="Xi Jinping",
            name_native="习近平",
            country="CN",
            birth_year=1953,
            tacit_knowledge=4.0,        # 12+ yr at apex, multi-decade CCP
            network_integration=4.0,    # max centrality across CCP graph
            tenure_months=156,          # ~13 yr as Gen Sec
            substitutes=0,              # no equivalent successor
            sources=["OSINT-CN-2026-001"],
            last_updated="2026-04-15",
        ),
        "LI": Person(
            id="P-CN-LI-QIANG",
            name="Li Qiang",
            name_native="李强",
            country="CN",
            tacit_knowledge=2.5,        # newer to national role, deep Shanghai bench
            network_integration=3.0,    # PSC member, Xi-faction
            tenure_months=36,           # since Mar 2023
            substitutes=2,              # other Vice Premiers as candidates
        ),
        "ZHAO": Person(
            id="P-CN-ZHAO-LEJI",
            name="Zhao Leji",
            name_native="赵乐际",
            country="CN",
            tacit_knowledge=3.0,
            network_integration=2.5,
            tenure_months=36,
            substitutes=3,
        ),
        "WANG_HN": Person(
            id="P-CN-WANG-HUNING",
            name="Wang Huning",
            name_native="王沪宁",
            country="CN",
            tacit_knowledge=3.5,        # "philosopher-king" of CCP ideology
            network_integration=3.0,
            tenure_months=96,           # decades as ideologue
            substitutes=1,              # very few comparable theorists
        ),
        "CAI": Person(
            id="P-CN-CAI-QI",
            name="Cai Qi",
            name_native="蔡奇",
            country="CN",
            tacit_knowledge=2.5,
            network_integration=3.5,    # secretariat = nervous-system role
            tenure_months=36,
            substitutes=2,
        ),
        "DING": Person(
            id="P-CN-DING-XUEXIANG",
            name="Ding Xuexiang",
            name_native="丁薛祥",
            country="CN",
            tacit_knowledge=2.5,
            network_integration=2.5,
            tenure_months=36,
            substitutes=2,
        ),
        "LI_XI": Person(
            id="P-CN-LI-XI",
            name="Li Xi",
            name_native="李希",
            country="CN",
            tacit_knowledge=2.0,
            network_integration=2.5,
            tenure_months=36,
            substitutes=3,
        ),
        "ZHANG_YS": Person(
            id="P-CN-ZHANG-YOUXIA",
            name="Zhang Youxia",
            name_native="张又侠",
            country="CN",
            tacit_knowledge=3.5,        # PLA combat experience, deep mil network
            network_integration=3.0,
            tenure_months=36,
            substitutes=1,
        ),
        "HE_WD": Person(
            id="P-CN-HE-WEIDONG",
            name="He Weidong",
            name_native="何卫东",
            country="CN",
            tacit_knowledge=3.0,
            network_integration=2.5,
            tenure_months=36,
            substitutes=2,
        ),
    }

    # ── Step 2: assignments — note Xi's MULTI-HAT (3 roles) ──────────────
    assignments = [
        # PSC seats
        RoleAssignment("P-CN-XI-JINPING", "CN-PSC-01-GENSEC"),
        RoleAssignment("P-CN-LI-QIANG", "CN-PSC-02-PREMIER"),
        RoleAssignment("P-CN-ZHAO-LEJI", "CN-PSC-03-NPC"),
        RoleAssignment("P-CN-WANG-HUNING", "CN-PSC-04-CPPCC"),
        RoleAssignment("P-CN-CAI-QI", "CN-PSC-05-SECRETARIAT"),
        RoleAssignment("P-CN-LI-XI", "CN-PSC-06-CDIC"),
        RoleAssignment("P-CN-DING-XUEXIANG", "CN-PSC-07-VICEPREMIER"),
        # CMC — Xi as Chairman = MULTI-HAT
        RoleAssignment("P-CN-XI-JINPING", "CN-CMC-CHAIR", capacity=0.4),
        RoleAssignment("P-CN-ZHANG-YOUXIA", "CN-CMC-VC1"),
        RoleAssignment("P-CN-HE-WEIDONG", "CN-CMC-VC2"),
    ]

    # Update Xi's GENSEC capacity to reflect split focus
    assignments[0].capacity = 0.6  # Gen Sec gets the lion's share

    # ── Step 3: compute Effective KPCI for every assignment ──────────────
    banner("STRUCTURAL vs EFFECTIVE KPCI BY ROLE")
    print(f"\n{'Role':<35} {'Occupant':<18} {'Struct':>6} {'Eff':>6} {'Δ':>6}  Tier")
    print("─" * 76)

    spec_lookup = {s.role_id: s for s in PRC_TAXONOMY}

    for a in assignments:
        spec = spec_lookup.get(a.role_id)
        if not spec:
            continue
        person = next((p for p in persons.values() if p.id == a.person_id), None)
        if not person:
            continue

        # Build a minimal Role-like object for effective_kpci()
        class _R:
            kpci = spec.ST + spec.DR + spec.AO
            substitution_timeline = spec.ST
            capability_weight = spec.capability_weight

        struct_kpci = _R.kpci
        eff = effective_kpci(_R(), person)
        delta = eff - struct_kpci
        tier = effective_tier(eff)

        print(f"{spec.title[:34]:<35} {person.name[:17]:<18} "
              f"{struct_kpci:>6.1f} {eff:>6.1f} {delta:>+6.2f}  {tier}")

    # ── Step 4: multi-hat detection ──────────────────────────────────────
    banner("MULTI-HAT PERSONS (decapitation cascade vectors)")
    multi = multi_hat_persons(assignments)
    for pid, role_ids in multi.items():
        person = next((p for p in persons.values() if p.id == pid), None)
        name = person.name if person else pid
        print(f"\n  {name} ({pid}) holds {len(role_ids)} roles:")
        for rid in role_ids:
            spec = spec_lookup.get(rid)
            title = spec.title if spec else rid
            print(f"    • {title}")

    # ── Step 5: decapitation scenario diagnostic ─────────────────────────
    banner("DECAPITATION DIAGNOSTIC: REMOVAL OF XI JINPING")
    xi = persons["XI"]
    xi_roles = roles_held_by(xi.id, assignments)

    total_cap_loss = 0.0
    total_tacit_shock = 0.0
    max_friction = 0.0

    print(f"\n  Removing one person disables {len(xi_roles)} roles simultaneously:\n")

    for rid in xi_roles:
        spec = spec_lookup.get(rid)
        if not spec:
            continue

        class _R:
            kpci = spec.ST + spec.DR + spec.AO
            substitution_timeline = spec.ST
            capability_weight = spec.capability_weight

        loss = continuity_loss(_R(), xi)
        total_cap_loss += loss["capability_loss"]
        total_tacit_shock += loss["tacit_shock"]
        max_friction = max(max_friction, loss["replacement_friction_months"])

        print(f"    {spec.title}")
        print(f"      Capability loss:        {loss['capability_loss']:>7.2f}")
        print(f"      Replacement friction:   {loss['replacement_friction_months']:>5.1f} months")
        print(f"      Tacit shock:            {loss['tacit_shock']:>7.2f}")
        print(f"      Effective KPCI:         {loss['effective_kpci']:>7.2f} "
              f"(structural floor: {loss['floor_kpci']:.1f})")
        print()

    print("─" * 76)
    print(f"  AGGREGATE DECAPITATION IMPACT:")
    print(f"    Total capability loss:      {total_cap_loss:>7.2f}")
    print(f"    Aggregate tacit shock:      {total_tacit_shock:>7.2f}")
    print(f"    Bounding replacement time:  {max_friction:>5.1f} months")
    print()
    print("  Interpretation: a single targeting event removes the apex of party,")
    print("  state, and military command lines simultaneously. The 'replacement")
    print("  friction' is the upper-bound of any one role's restoration; the")
    print("  CASCADE effect (not modelled here) is that the surviving Politburo")
    print("  must select a successor across all three power lines while the")
    print("  factional balance that legitimated Xi's multi-hat is gone.")


if __name__ == "__main__":
    main()
