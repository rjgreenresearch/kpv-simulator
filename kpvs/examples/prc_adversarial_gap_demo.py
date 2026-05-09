"""
examples/prc_adversarial_gap_demo.py — Person-centric Monte Carlo on PRC
=========================================================================

Demonstrates the new PersonAwareSimulator on the PRC PSC + CMC organization.
Compares random vs adversarial scenarios at the person level, computes
the adversarial gap, and reports the multi-hat efficiency premium.

Run:
    python examples/prc_adversarial_gap_demo.py
"""

from dataclasses import dataclass, field

from kpvs.persons import Person, RoleAssignment
from kpvs.person_simulator import (
    PersonAwareSimulator, person_adversarial_gap,
)
from kpvs.intelligence.role_mapper import PRC_TAXONOMY


# ─────────────────────────────────────────────────────────────────────────
# Stub Role / Org matching kpvs/models.py shape — when integrated into
# the real repo, replace these imports with `from kpvs.models import ...`
# ─────────────────────────────────────────────────────────────────────────
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


def build_prc_org() -> StubOrg:
    """Build a StubOrg from the PRC taxonomy."""
    roles = [
        StubRole(
            id=spec.role_id,
            title=spec.title,
            substitution_timeline=spec.ST,
            documentation_ratio=spec.DR,
            adversarial_observability=spec.AO,
            capability_weight=spec.capability_weight,
        )
        for spec in PRC_TAXONOMY
    ]
    return StubOrg(name="PRC PSC + CMC + Selected Politburo", roles=roles)


def build_persons_and_assignments():
    """Synthetic but plausible occupant profiles. Xi multi-hat (Gen Sec + CMC Chair).

    These are SYNTHETIC values for demonstration. Production use replaces
    this with role_mapper.map_country('CN', graph, resolver).
    """
    persons = {
        "P-CN-XI": Person(
            id="P-CN-XI", name="Xi Jinping", country="CN",
            tacit_knowledge=4.0, network_integration=4.0,
            tenure_months=156, substitutes=0,
        ),
        "P-CN-LI-Q": Person(
            id="P-CN-LI-Q", name="Li Qiang", country="CN",
            tacit_knowledge=2.5, network_integration=3.0,
            tenure_months=36, substitutes=2,
        ),
        "P-CN-ZHAO-L": Person(
            id="P-CN-ZHAO-L", name="Zhao Leji", country="CN",
            tacit_knowledge=3.0, network_integration=2.5,
            tenure_months=36, substitutes=3,
        ),
        "P-CN-WANG-H": Person(
            id="P-CN-WANG-H", name="Wang Huning", country="CN",
            tacit_knowledge=3.5, network_integration=3.0,
            tenure_months=96, substitutes=1,
        ),
        "P-CN-CAI-Q": Person(
            id="P-CN-CAI-Q", name="Cai Qi", country="CN",
            tacit_knowledge=2.5, network_integration=3.5,
            tenure_months=36, substitutes=2,
        ),
        "P-CN-DING-X": Person(
            id="P-CN-DING-X", name="Ding Xuexiang", country="CN",
            tacit_knowledge=2.5, network_integration=2.5,
            tenure_months=36, substitutes=2,
        ),
        "P-CN-LI-X": Person(
            id="P-CN-LI-X", name="Li Xi", country="CN",
            tacit_knowledge=2.0, network_integration=2.5,
            tenure_months=36, substitutes=3,
        ),
        "P-CN-ZHANG-YS": Person(
            id="P-CN-ZHANG-YS", name="Zhang Youxia", country="CN",
            tacit_knowledge=3.5, network_integration=3.0,
            tenure_months=36, substitutes=1,
        ),
        "P-CN-HE-WD": Person(
            id="P-CN-HE-WD", name="He Weidong", country="CN",
            tacit_knowledge=3.0, network_integration=2.5,
            tenure_months=36, substitutes=2,
        ),
        # 3 additional Politburo members assigned to non-PSC roles
        "P-CN-WANG-Y": Person(
            id="P-CN-WANG-Y", name="Wang Yi", country="CN",
            tacit_knowledge=3.5, network_integration=3.0,
            tenure_months=72, substitutes=1,
        ),
        "P-CN-CHEN-WQ": Person(
            id="P-CN-CHEN-WQ", name="Chen Wenqing", country="CN",
            tacit_knowledge=3.0, network_integration=3.0,
            tenure_months=48, substitutes=2,
        ),
        "P-CN-SHI-TF": Person(
            id="P-CN-SHI-TF", name="Shi Taifeng", country="CN",
            tacit_knowledge=2.5, network_integration=2.5,
            tenure_months=36, substitutes=3,
        ),
        "P-CN-CNPC": Person(
            id="P-CN-CNPC", name="Dai Houliang", country="CN",
            tacit_knowledge=2.5, network_integration=2.0,
            tenure_months=24, substitutes=3,
        ),
        "P-CN-SINOCHEM": Person(
            id="P-CN-SINOCHEM", name="Li Fanrong", country="CN",
            tacit_knowledge=2.0, network_integration=2.0,
            tenure_months=24, substitutes=3,
        ),
    }

    # Xi MULTI-HAT: General Secretary + CMC Chairman
    assignments = [
        RoleAssignment("P-CN-XI", "CN-PSC-01-GENSEC", capacity=0.6),
        RoleAssignment("P-CN-XI", "CN-CMC-CHAIR", capacity=0.4),
        RoleAssignment("P-CN-LI-Q", "CN-PSC-02-PREMIER"),
        RoleAssignment("P-CN-ZHAO-L", "CN-PSC-03-NPC"),
        RoleAssignment("P-CN-WANG-H", "CN-PSC-04-CPPCC"),
        RoleAssignment("P-CN-CAI-Q", "CN-PSC-05-SECRETARIAT"),
        RoleAssignment("P-CN-LI-X", "CN-PSC-06-CDIC"),
        RoleAssignment("P-CN-DING-X", "CN-PSC-07-VICEPREMIER"),
        RoleAssignment("P-CN-ZHANG-YS", "CN-CMC-VC1"),
        RoleAssignment("P-CN-HE-WD", "CN-CMC-VC2"),
        RoleAssignment("P-CN-WANG-Y", "CN-PB-FOREIGN"),
        RoleAssignment("P-CN-CHEN-WQ", "CN-PB-POLISEC"),
        RoleAssignment("P-CN-SHI-TF", "CN-PB-ORGDEPT"),
        RoleAssignment("P-CN-CNPC", "CN-SOE-CNPC"),
        RoleAssignment("P-CN-SINOCHEM", "CN-SOE-SINOCHEM"),
    ]
    return persons, assignments


def banner(text: str) -> None:
    print("\n" + "═" * 76)
    print(f"  {text}")
    print("═" * 76)


def main() -> None:
    banner("PRC PERSON-CENTRIC ADVERSARIAL GAP")

    org = build_prc_org()
    persons, assignments = build_persons_and_assignments()
    sim = PersonAwareSimulator(org, persons, assignments, seed=20260508)

    # ── Show top-5 persons by target value ───────────────────────────────
    banner("TARGET-VALUE RANKING (adversary's prioritisation)")
    print(f"\n  {'Rank':<5} {'Person':<22} {'Target Value':>14} {'Roles':>6}")
    print("  " + "─" * 60)
    for i, (pid, tv) in enumerate(sim.rank_persons()[:8], 1):
        person = persons[pid]
        n_roles = len(sim._roles_per_person.get(pid, []))
        marker = "  ← multi-hat" if n_roles > 1 else ""
        print(f"  {i:<5} {person.name:<22} {tv:>14.2f} {n_roles:>6}{marker}")

    # ── Run the two scenarios ────────────────────────────────────────────
    N_ITERATIONS = 5000
    N_PER_ITER = 3
    ACCURACY = 0.85

    banner(f"MONTE CARLO ({N_ITERATIONS} iter, {N_PER_ITER} persons/iter, "
           f"acc={ACCURACY})")

    rnd = sim.scenario_person_random_attrition(
        n_iterations=N_ITERATIONS, n_persons_per_iter=N_PER_ITER)
    adv = sim.scenario_person_targeted_attrition(
        n_iterations=N_ITERATIONS, n_persons_per_iter=N_PER_ITER,
        accuracy=ACCURACY)

    print("\n  " + rnd.summary_line())
    print("  " + adv.summary_line())

    # ── Adversarial gap ──────────────────────────────────────────────────
    gap = person_adversarial_gap(rnd, adv)

    banner("PERSON-LEVEL ADVERSARIAL GAP")
    print(f"\n  Capability gap (random − adversarial):  "
          f"{gap['capability_gap_pp']:>+5.2f} pp")
    print(f"    Random scenario:    {rnd.mean_pct:.2f}% capability remaining")
    print(f"    Adversarial:        {adv.mean_pct:.2f}% capability remaining")
    print()
    print(f"  Tacit-shock premium:                    "
          f"{gap['tacit_shock_premium']:>+5.2f}")
    print(f"  Roles-disabled premium:                 "
          f"{gap['roles_disabled_premium']:>+5.2f}")
    print(f"  Replacement-friction premium:           "
          f"{gap['friction_premium_months']:>+5.1f} months")
    print()
    print(f"  Multi-hat efficiency:")
    print(f"    Random:        {rnd.multi_hat_efficiency:.3f} "
          f"roles/person targeted")
    print(f"    Adversarial:   {adv.multi_hat_efficiency:.3f} "
          f"roles/person targeted")
    print()
    print(f"  → A {ACCURACY*100:.0f}%-accurate adversary degrades capability")
    print(f"    by an additional {gap['capability_gap_pp']:.1f} percentage points")
    print(f"    over random turnover, while inflicting "
          f"{gap['tacit_shock_premium']:+.1f} extra")
    print(f"    units of tacit-knowledge shock per operation.")

    # ── Most-frequently-targeted persons ─────────────────────────────────
    banner("ADVERSARY HIT FREQUENCY (top 6)")
    sorted_freq = sorted(adv.target_frequency.items(),
                         key=lambda kv: -kv[1])[:6]
    print(f"\n  {'Person':<22} {'Hits':>8} {'% of iter':>11}")
    print("  " + "─" * 50)
    for pid, hits in sorted_freq:
        person = persons.get(pid)
        name = person.name if person else pid
        pct = 100 * hits / N_ITERATIONS
        print(f"  {name:<22} {hits:>8} {pct:>10.1f}%")


if __name__ == "__main__":
    main()
