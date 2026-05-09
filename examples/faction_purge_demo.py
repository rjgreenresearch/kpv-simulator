"""
examples/faction_purge_demo.py — Wagner-Surovikin June 2023 case study
========================================================================

Synthetic recreation of the post-mutiny Russian regime response: the
moves against Wagner-affiliated military leadership in summer 2023.

Faction definition (synthetic):
  • Persons known to have coordinated with Prigozhin
  • Persons promoted via the "Surovikin line" (counter-Strelkov bloc)
  • Persons in MoD positions with operational ties to Wagner deployments

Scenario: Russian regime executes a coordinated purge of these persons.
We measure capability loss against an equivalent-N random attrition.

Note: All names, attributes, and faction memberships are SYNTHETIC for
demonstration. This is not an analytic product on actual Russian
leadership — it's a use-case demonstration of the simulator.
"""

from dataclasses import dataclass, field

from kpvs.persons import Person, RoleAssignment
from kpvs.faction_purge import (
    FactionAwareSimulator,
    run_faction_vs_random,
    faction_concentration_premium,
)


# Stub Role / Org — replace with kpvs.models in real repo
@dataclass
class StubRole:
    id: str
    title: str
    substitution_timeline: float
    documentation_ratio: float
    adversarial_observability: float
    capability_weight: float = 1.0

    @property
    def kpci(self) -> float:
        return (self.substitution_timeline
                + self.documentation_ratio
                + self.adversarial_observability)


@dataclass
class StubOrg:
    name: str
    roles: list = field(default_factory=list)


def build_ru_mod_org() -> StubOrg:
    """Synthetic Russian Ministry of Defense + General Staff org chart."""
    return StubOrg(
        name="RU MoD + General Staff (synthetic)",
        roles=[
            # Apex
            StubRole("RU-MOD-MIN", "Defense Minister", 4, 4, 4, 5.0),
            StubRole("RU-GS-CHIEF", "Chief of General Staff", 4, 4, 4, 5.0),
            # Strategic command
            StubRole("RU-AERO-CDR", "Aerospace Forces Commander",
                     3, 4, 3, 3.5),
            StubRole("RU-GROUND-CDR", "Ground Forces Commander",
                     3, 4, 3, 3.5),
            StubRole("RU-VKS-CDR", "VKS Commander", 3, 3, 3, 3.0),
            # Theater commands (Ukraine front)
            StubRole("RU-SMO-CDR", "Special Military Operation Commander",
                     3, 4, 4, 4.0),  # the rotating role Surovikin held
            StubRole("RU-SOUTH-CDR", "Southern Group Commander",
                     2, 3, 3, 2.5),
            StubRole("RU-CENTER-CDR", "Center Group Commander",
                     2, 3, 3, 2.5),
            StubRole("RU-WEST-CDR", "Western Group Commander",
                     2, 3, 3, 2.5),
            StubRole("RU-EAST-CDR", "Eastern Group Commander",
                     2, 3, 3, 2.5),
            # Support
            StubRole("RU-LOGISTICS", "Deputy MoD for Logistics",
                     2, 3, 2, 2.0),
            StubRole("RU-PROCUREMENT", "Deputy MoD for Procurement",
                     2, 3, 2, 2.0),
            # GRU and intelligence
            StubRole("RU-GRU-CHIEF", "GRU Chief", 3, 4, 3, 3.0),
            StubRole("RU-GRU-DEP", "GRU First Deputy", 2, 3, 2, 1.5),
            # Wagner-adjacent operational positions
            StubRole("RU-IRREGULAR", "Irregular Forces Liaison",
                     2, 3, 2, 1.5),
        ],
    )


def build_persons() -> dict:
    """Synthetic persons with faction tags.

    NB: The 'wagner-aligned' tag is the KEY column for this demo.
    Multi-faction memberships (e.g., 'wagner-aligned' + 'gru-veteran')
    are common — this is realistic.
    """
    return {
        # Apex — neutral / regime-aligned
        "P-RU-001": Person(
            id="P-RU-001", name="Defense Minister (alpha)",
            country="RU",
            tacit_knowledge=3.5, network_integration=4.0,
            tenure_months=180, substitutes=1,
            factions=["mod-careerist", "regime-apex"],
        ),
        "P-RU-002": Person(
            id="P-RU-002", name="GenStaff Chief (alpha)",
            country="RU",
            tacit_knowledge=4.0, network_integration=3.5,
            tenure_months=144, substitutes=1,
            factions=["genstaff-academy", "regime-apex"],
        ),
        # Aerospace — partial Wagner alignment via Syria deployments
        "P-RU-003": Person(
            id="P-RU-003", name="Aerospace Cdr (alpha)",
            country="RU",
            tacit_knowledge=3.5, network_integration=3.0,
            tenure_months=72, substitutes=2,
            factions=["wagner-aligned", "syria-veteran"],
        ),
        # Ground forces leadership
        "P-RU-004": Person(
            id="P-RU-004", name="Ground Cdr (alpha)",
            country="RU",
            tacit_knowledge=3.0, network_integration=2.5,
            tenure_months=60, substitutes=2,
            factions=["mod-careerist"],
        ),
        # SMO commander — the Surovikin-equivalent
        "P-RU-005": Person(
            id="P-RU-005", name="SMO Commander (alpha)",
            country="RU",
            tacit_knowledge=4.0, network_integration=3.5,
            tenure_months=18, substitutes=1,
            factions=["wagner-aligned", "syria-veteran",
                      "surovikin-line"],
        ),
        # Theater commanders — mixed alignment
        "P-RU-006": Person(
            id="P-RU-006", name="Southern Cdr (alpha)",
            country="RU",
            tacit_knowledge=3.0, network_integration=2.5,
            tenure_months=24, substitutes=2,
            factions=["wagner-aligned"],
        ),
        "P-RU-007": Person(
            id="P-RU-007", name="Center Cdr (alpha)",
            country="RU",
            tacit_knowledge=2.5, network_integration=2.0,
            tenure_months=36, substitutes=3,
            factions=["mod-careerist"],
        ),
        "P-RU-008": Person(
            id="P-RU-008", name="Western Cdr (alpha)",
            country="RU",
            tacit_knowledge=2.5, network_integration=2.5,
            tenure_months=18, substitutes=2,
            factions=["wagner-aligned", "surovikin-line"],
        ),
        "P-RU-009": Person(
            id="P-RU-009", name="Eastern Cdr (alpha)",
            country="RU",
            tacit_knowledge=2.0, network_integration=1.5,
            tenure_months=12, substitutes=3,
            factions=["mod-careerist"],
        ),
        # Logistics / procurement — outside Wagner network
        "P-RU-010": Person(
            id="P-RU-010", name="Logistics Dep (alpha)",
            country="RU",
            tacit_knowledge=3.0, network_integration=2.5,
            tenure_months=96, substitutes=2,
            factions=["mod-careerist"],
        ),
        "P-RU-011": Person(
            id="P-RU-011", name="Procurement Dep (alpha)",
            country="RU",
            tacit_knowledge=2.5, network_integration=2.0,
            tenure_months=72, substitutes=2,
            factions=["mod-careerist"],
        ),
        # GRU — partial Wagner liaison history
        "P-RU-012": Person(
            id="P-RU-012", name="GRU Chief (alpha)",
            country="RU",
            tacit_knowledge=3.5, network_integration=3.0,
            tenure_months=60, substitutes=1,
            factions=["gru-veteran"],
        ),
        "P-RU-013": Person(
            id="P-RU-013", name="GRU First Deputy (alpha)",
            country="RU",
            tacit_knowledge=3.0, network_integration=2.5,
            tenure_months=36, substitutes=2,
            factions=["gru-veteran", "wagner-aligned"],
        ),
        # Wagner liaison role — definitionally Wagner-aligned
        "P-RU-014": Person(
            id="P-RU-014", name="Irregular Forces Liaison (alpha)",
            country="RU",
            tacit_knowledge=4.0, network_integration=3.5,
            tenure_months=48, substitutes=0,
            factions=["wagner-aligned", "syria-veteran"],
        ),
    }


def build_assignments() -> list:
    return [
        RoleAssignment("P-RU-001", "RU-MOD-MIN"),
        RoleAssignment("P-RU-002", "RU-GS-CHIEF"),
        RoleAssignment("P-RU-003", "RU-AERO-CDR"),
        RoleAssignment("P-RU-004", "RU-GROUND-CDR"),
        # SMO commander is multi-hat: holds VKS too (Surovikin's prior role)
        RoleAssignment("P-RU-005", "RU-SMO-CDR", capacity=0.7),
        RoleAssignment("P-RU-005", "RU-VKS-CDR", capacity=0.3),
        RoleAssignment("P-RU-006", "RU-SOUTH-CDR"),
        RoleAssignment("P-RU-007", "RU-CENTER-CDR"),
        RoleAssignment("P-RU-008", "RU-WEST-CDR"),
        RoleAssignment("P-RU-009", "RU-EAST-CDR"),
        RoleAssignment("P-RU-010", "RU-LOGISTICS"),
        RoleAssignment("P-RU-011", "RU-PROCUREMENT"),
        RoleAssignment("P-RU-012", "RU-GRU-CHIEF"),
        RoleAssignment("P-RU-013", "RU-GRU-DEP"),
        RoleAssignment("P-RU-014", "RU-IRREGULAR"),
    ]


def banner(text: str) -> None:
    print("\n" + "═" * 76)
    print(f"  {text}")
    print("═" * 76)


def main() -> None:
    banner("WAGNER-SUROVIKIN FACTION PURGE — SYNTHETIC CASE STUDY")
    print("\n  Note: All names, attributes, and faction memberships are")
    print("  SYNTHETIC. This is a use-case demonstration, not an analytic")
    print("  product on actual Russian leadership.")

    org = build_ru_mod_org()
    persons = build_persons()
    assignments = build_assignments()
    sim = FactionAwareSimulator(org, persons, assignments, seed=20230624)

    # ── Show faction membership ──────────────────────────────────────────
    banner("FACTION ROSTER")
    print()
    for tag in ["wagner-aligned", "syria-veteran", "surovikin-line",
                "gru-veteran", "mod-careerist", "genstaff-academy"]:
        members = [p for p in persons.values() if tag in p.factions]
        if members:
            print(f"  [{tag:<20}]  {len(members)} members:")
            for m in members:
                print(f"       • {m.name}")

    # ── Scenario 1: Pure Wagner-aligned purge (deterministic) ────────────
    banner("SCENARIO 1: PURE 'wagner-aligned' PURGE (deterministic)")

    pure_compare = run_faction_vs_random(
        sim, faction_tag="wagner-aligned", n_iterations=5000)
    pure = pure_compare["faction"]
    rnd = pure_compare["random"]
    prem = pure_compare["premium"]

    print(f"\n  Faction size:                  {pure.faction_size} persons")
    print(f"  Direct roles disabled:         {pure.direct_roles_disabled}"
          f"  (multi-hat amplification: +{pure.multi_hat_amplification})")
    print(f"  Concentrated failures:         {pure.concentrated_failures}"
          f"  (roles where occupant has ≤1 substitute)")
    print(f"  Aggregate tacit shock:         {pure.direct_tacit_shock:.2f}")

    print()
    print(f"  Capability remaining:")
    print(f"    Coherent purge:              {pure.mean_pct:>5.1f}%")
    print(f"    Equivalent-N random:         {rnd.mean_pct:>5.1f}%  "
          f"(σ {rnd.std_pct:.1f})")
    print(f"    ──────────────────────────────────")
    print(f"    Concentration premium:       {prem['capability_premium_pp']:>+5.1f} pp")
    print(f"    Concentration factor:        ×"
          f"{1 + prem['concentration_factor']:.2f}")

    # ── Scenario 2: Wider purge with stochastic spillover ────────────────
    banner("SCENARIO 2: PURGE + 15% STOCHASTIC SPILLOVER")

    sto_result = sim.scenario_faction_purge(
        faction_tag="wagner-aligned",
        secondary_loss_p=0.15,
        n_iterations=3000,
        name="Wagner Purge (stochastic spillover)",
    )

    print(f"\n  Direct removal:                "
          f"{sto_result.faction_size} faction members")
    print(f"  Mean spillover (per iter):     "
          f"{sto_result.mean_secondary_loss:.2f} non-faction persons")
    print(f"  Mean additional tacit shock:   "
          f"{sto_result.secondary_tacit_shock:.2f}")
    print()
    print(f"  Capability remaining:")
    print(f"    Mean:                        "
          f"{sto_result.mean_pct:>5.1f}%  (σ {sto_result.std_pct:.1f})")
    print(f"    p05 (worst 5% case):         {sto_result.p05_pct:>5.1f}%")
    print(f"    Median:                      {sto_result.p50_pct:>5.1f}%")
    print(f"    p95 (best 5% case):          {sto_result.p95_pct:>5.1f}%")

    # ── Scenario 3: Faction comparison (Wagner vs MoD-careerist) ─────────
    banner("SCENARIO 3: WHICH FACTION IS THE BIGGER VULNERABILITY?")

    print("\n  Concentration premium by faction (vs equivalent-N random):")
    print("  Positive = MORE damaging than equivalent random loss")
    print("  Negative = LESS damaging (faction sits on lower-weight roles)\n")
    for tag in ["regime-apex", "wagner-aligned", "mod-careerist",
                "syria-veteran", "surovikin-line", "gru-veteran"]:
        try:
            cmp = run_faction_vs_random(sim, faction_tag=tag,
                                          n_iterations=2000)
            f = cmp["faction"]
            premium = cmp["premium"]["capability_premium_pp"]
            marker = " ←" if premium > 2 else ""
            print(f"  {tag:<20}  size={f.faction_size:>2}  "
                  f"roles={f.direct_roles_disabled:>2}  "
                  f"cap={f.mean_pct:>5.1f}%  "
                  f"premium=  {premium:>+5.1f} pp{marker}")
        except ValueError as e:
            print(f"  {tag:<20}  (no members)")

    # ── Interpretation ───────────────────────────────────────────────────
    banner("INTERPRETATION")
    print("""
  The concentration premium quantifies how much WORSE a coherent faction
  purge is than randomly losing the same number of persons. Sign matters:

    POSITIVE premium → faction is concentrated in HIGH-KPCI/high-weight
                       roles. Coherent purge worse than scattered loss.
                       Operational lesson: this faction is a critical
                       single-point-of-failure for the org.

    NEGATIVE premium → faction holds peripheral roles. Coherent purge
                       does LESS damage than random — random can stoch-
                       astically hit apex roles the faction doesn't hold.
                       Operational lesson: this faction is NOT regime-
                       critical; targeting it is operationally cosmetic.

  In the synthetic data above, regime-apex (Defense Minister + GenStaff
  Chief) produces large positive premium — those 2 persons concentrate
  10 of 43 capability units. wagner-aligned shows negative premium because
  it holds operational mid-level roles that a random draw would miss
  more often than the apex.

  This matches real-world dynamics: the Wagner-Surovikin June 2023
  events caused operational disruption in Russian theater commands but
  did not threaten regime continuity, because the regime-apex faction
  (Putin / Shoigu / Gerasimov) was untouched. A purge of regime-apex
  itself — Stalin against Yezhov, or a hypothetical action against
  Shoigu — would have produced a fundamentally different concentration
  premium.

  Operational use:
    • Risk register: rank factions by concentration premium SIGN AND
      magnitude. Positive = critical single-point-of-failure.
    • Resilience investment: roles inside positive-premium factions are
      where bench-depth investment yields highest dividend.
    • Crisis-game design: stochastic spillover (secondary_loss_p) bounds
      the post-purge instability range. Even peripheral-faction purges
      (negative direct premium) can become regime-critical when spillover
      probability is high enough that random apex loss becomes likely.
""")


if __name__ == "__main__":
    main()
