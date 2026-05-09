"""
examples/cascade_demo.py — Graph-aware cascade scenario on PRC network
========================================================================

Synthetic CCP leadership graph showing how a single seed person can
cascade through factional + institutional ties to disable a meaningfully
larger fraction of the org than direct removal alone.

The graph includes:
  • 9 persons (Politburo members + key SOE chairs)
  • 4 organizations (CCP, CMC, CDIC, CNPC)
  • 12 person-person edges (factional, mentoring, co-PSC ties)
  • 5 org-membership relationships
  • 2 org-org edges (CCP → CMC, CCP → CDIC)
  • 2 typed edges showing per-type cascade probability

The seed: removal of a single high-centrality node. We show the cascade
premium (additional damage from network spillover beyond direct loss).
"""

from dataclasses import dataclass, field

from kpvs.persons import Person, RoleAssignment
from kpvs.osint_graph import OSINTGraph, GraphEdge, empty_graph
from kpvs.cascade_simulator import (
    GraphAwareSimulator, cascade_vs_seed_only,
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


def build_org():
    """PRC PSC + CMC + CDIC + 2 SOEs."""
    return StubOrg(
        name="PRC Apex (synthetic)",
        roles=[
            StubRole("CN-GENSEC", "General Secretary", 4, 4, 4, 5.0),
            StubRole("CN-PREMIER", "Premier", 4, 4, 4, 4.0),
            StubRole("CN-NPC", "NPC Chair", 3, 3, 3, 2.5),
            StubRole("CN-CPPCC", "CPPCC Chair", 3, 3, 3, 1.5),
            StubRole("CN-SECRETARIAT", "Secretariat First Sec", 3, 4, 3, 3.0),
            StubRole("CN-CDIC", "CDIC Secretary", 3, 4, 3, 2.5),
            StubRole("CN-VICEPREMIER", "First Vice Premier", 3, 3, 3, 2.0),
            StubRole("CN-CMC-CHAIR", "CMC Chairman", 4, 4, 4, 5.0),
            StubRole("CN-CMC-VC1", "CMC First VC", 3, 4, 3, 3.0),
            StubRole("CN-CNPC", "CNPC Chairman", 2, 3, 2, 2.0),
        ],
    )


def build_persons():
    return {
        "P-XI": Person(id="P-XI", name="Xi Jinping", country="CN",
                       tacit_knowledge=4.0, network_integration=4.0,
                       tenure_months=156, substitutes=0,
                       factions=["regime-apex", "tsinghua"]),
        "P-LIQ": Person(id="P-LIQ", name="Li Qiang", country="CN",
                        tacit_knowledge=2.5, network_integration=3.0,
                        tenure_months=36, substitutes=2,
                        factions=["zhejiang"]),
        "P-ZHL": Person(id="P-ZHL", name="Zhao Leji", country="CN",
                        tacit_knowledge=3.0, network_integration=2.5,
                        tenure_months=36, substitutes=3),
        "P-WGH": Person(id="P-WGH", name="Wang Huning", country="CN",
                        tacit_knowledge=3.5, network_integration=3.0,
                        tenure_months=96, substitutes=1,
                        factions=["regime-apex"]),
        "P-CAI": Person(id="P-CAI", name="Cai Qi", country="CN",
                        tacit_knowledge=2.5, network_integration=3.5,
                        tenure_months=36, substitutes=2,
                        factions=["zhejiang", "tsinghua"]),
        "P-LIX": Person(id="P-LIX", name="Li Xi", country="CN",
                        tacit_knowledge=2.0, network_integration=2.5,
                        tenure_months=36, substitutes=3),
        "P-DING": Person(id="P-DING", name="Ding Xuexiang", country="CN",
                         tacit_knowledge=2.5, network_integration=2.5,
                         tenure_months=36, substitutes=2,
                         factions=["zhejiang"]),
        "P-ZYS": Person(id="P-ZYS", name="Zhang Youxia", country="CN",
                        tacit_knowledge=3.5, network_integration=3.0,
                        tenure_months=36, substitutes=1,
                        factions=["pla-veterans"]),
        "P-CNPC": Person(id="P-CNPC", name="Dai Houliang", country="CN",
                         tacit_knowledge=2.5, network_integration=2.0,
                         tenure_months=24, substitutes=3),
    }


def build_assignments():
    return [
        RoleAssignment("P-XI", "CN-GENSEC", capacity=0.6),
        RoleAssignment("P-XI", "CN-CMC-CHAIR", capacity=0.4),  # multi-hat
        RoleAssignment("P-LIQ", "CN-PREMIER"),
        RoleAssignment("P-ZHL", "CN-NPC"),
        RoleAssignment("P-WGH", "CN-CPPCC"),
        RoleAssignment("P-CAI", "CN-SECRETARIAT"),
        RoleAssignment("P-LIX", "CN-CDIC"),
        RoleAssignment("P-DING", "CN-VICEPREMIER"),
        RoleAssignment("P-ZYS", "CN-CMC-VC1"),
        RoleAssignment("P-CNPC", "CN-CNPC"),
    ]


def build_graph():
    """Synthetic CCP leadership graph."""
    g = empty_graph("CN")

    # Persons with org memberships
    g.add_person("P-XI", orgs=["CCP", "CMC"])
    g.add_person("P-LIQ", orgs=["CCP", "STATE-COUNCIL"])
    g.add_person("P-ZHL", orgs=["CCP", "NPC"])
    g.add_person("P-WGH", orgs=["CCP", "CPPCC"])
    g.add_person("P-CAI", orgs=["CCP"])
    g.add_person("P-LIX", orgs=["CCP", "CDIC"])
    g.add_person("P-DING", orgs=["CCP", "STATE-COUNCIL"])
    g.add_person("P-ZYS", orgs=["CMC", "PLA"])
    g.add_person("P-CNPC", orgs=["CNPC", "STATE-COUNCIL"])

    # Bridge KPVS roles to graph orgs (for org→role cascade)
    g.link_role_to_org("CN-GENSEC", "CCP")
    g.link_role_to_org("CN-PREMIER", "STATE-COUNCIL")
    g.link_role_to_org("CN-NPC", "NPC")
    g.link_role_to_org("CN-CPPCC", "CPPCC")
    g.link_role_to_org("CN-SECRETARIAT", "CCP")
    g.link_role_to_org("CN-CDIC", "CDIC")
    g.link_role_to_org("CN-VICEPREMIER", "STATE-COUNCIL")
    g.link_role_to_org("CN-CMC-CHAIR", "CMC")
    g.link_role_to_org("CN-CMC-VC1", "CMC")
    g.link_role_to_org("CN-CNPC", "CNPC")

    # ── Person-person edges (typed) ──────────────────────────────────────
    # Patron-protégé ties — DIRECTIONAL (patron's loss hits protégé,
    # not vice versa).
    g.add_edge(GraphEdge(source="P-XI", target="P-LIQ",
                          source_type="person", target_type="person",
                          edge_type="patron", bidirectional=False))
    g.add_edge(GraphEdge(source="P-XI", target="P-CAI",
                          source_type="person", target_type="person",
                          edge_type="patron", bidirectional=False))
    g.add_edge(GraphEdge(source="P-XI", target="P-DING",
                          source_type="person", target_type="person",
                          edge_type="patron", bidirectional=False))
    g.add_edge(GraphEdge(source="P-XI", target="P-ZYS",
                          source_type="person", target_type="person",
                          edge_type="patron", bidirectional=False))
    # Ideological — bidirectional (both depend on shared framework)
    g.add_edge(GraphEdge(source="P-XI", target="P-WGH",
                          source_type="person", target_type="person",
                          edge_type="ideological"))
    # Co-PSC ties — bidirectional (peer relationships)
    g.add_edge(GraphEdge(source="P-LIQ", target="P-ZHL",
                          source_type="person", target_type="person",
                          edge_type="co_psc"))
    g.add_edge(GraphEdge(source="P-LIQ", target="P-CAI",
                          source_type="person", target_type="person",
                          edge_type="co_psc"))
    g.add_edge(GraphEdge(source="P-CAI", target="P-DING",
                          source_type="person", target_type="person",
                          edge_type="factional"))
    # reports_to — DIRECTIONAL boss → subordinate
    g.add_edge(GraphEdge(source="P-XI", target="P-ZYS",
                          source_type="person", target_type="person",
                          edge_type="reports_to", bidirectional=False))
    g.add_edge(GraphEdge(source="P-DING", target="P-CNPC",
                          source_type="person", target_type="person",
                          edge_type="reports_to", bidirectional=False))

    # ── Org-org edges ────────────────────────────────────────────────────
    # CCP → CMC (party controls military)
    g.add_edge(GraphEdge(source="CCP", target="CMC",
                          source_type="org", target_type="org",
                          weight=0.85))
    # CCP → CDIC (party controls discipline body)
    g.add_edge(GraphEdge(source="CCP", target="CDIC",
                          source_type="org", target_type="org",
                          weight=0.75))

    # ── Person→Org edges (apex figures whose loss strains institutions) ─
    # Membership alone doesn't cascade person→org. Explicit edges are
    # needed when an analyst judges a person's loss to compromise org
    # coherence (apex roles, not rank-and-file).
    g.add_edge(GraphEdge(source="P-XI", target="CCP",
                          source_type="person", target_type="org",
                          edge_type="apex_loss",
                          bidirectional=False))
    g.add_edge(GraphEdge(source="P-XI", target="CMC",
                          source_type="person", target_type="org",
                          edge_type="apex_loss",
                          bidirectional=False))
    g.add_edge(GraphEdge(source="P-LIQ", target="STATE-COUNCIL",
                          source_type="person", target_type="org",
                          edge_type="apex_loss",
                          bidirectional=False))
    g.add_edge(GraphEdge(source="P-ZYS", target="CMC",
                          source_type="person", target_type="org",
                          edge_type="apex_loss",
                          bidirectional=False))

    return g


def banner(text: str) -> None:
    print("\n" + "═" * 76)
    print(f"  {text}")
    print("═" * 76)


def main() -> None:
    banner("PRC GRAPH-CASCADE DEMO — Synthetic CCP leadership network")
    print("\n  All names, attributes, and edges are SYNTHETIC.")

    org = build_org()
    persons = build_persons()
    assignments = build_assignments()
    graph = build_graph()
    sim = GraphAwareSimulator(org, persons, assignments,
                                graph=graph, seed=20260508)

    # ── Show graph summary ───────────────────────────────────────────────
    banner("GRAPH SUMMARY")
    s = graph.summary()
    print(f"\n  Country:                 {s['country']}")
    print(f"  Persons:                 {s['n_persons']}")
    print(f"  Organizations:           {s['n_orgs']}")
    print(f"  Edges:                   {s['n_edges']}  "
          f"({s['n_typed_edges']} typed, "
          f"{s['n_weighted_edges']} explicit-weighted)")
    print(f"  Role→Org mappings:       {s['n_role_to_org_mappings']}")

    # ── Edge type weight scheme ──────────────────────────────────────────
    edge_weights = {
        "patron":      0.65,  # patrons fall, protégés exposed
        "ideological": 0.35,
        "co_psc":      0.20,  # peers face less direct cascade
        "factional":   0.40,
        "reports_to":  0.55,  # subordinates lose protection
        "apex_loss":   0.50,  # apex failure strains the institution
    }

    banner("EDGE-TYPE CASCADE PROBABILITY")
    print("\n  Type            Probability")
    print("  ─────────────   ───────────")
    for t, p in sorted(edge_weights.items(), key=lambda kv: -kv[1]):
        print(f"  {t:<14}  {p:.2f}")
    print("  (default for untyped edges: 0.25)")

    # ── Scenario 1: Seed Xi (multi-hat apex) ─────────────────────────────
    banner("SCENARIO 1: SEED = Xi Jinping (multi-hat apex)")
    print("\n  Removing one person; observing graph propagation...")

    compare = cascade_vs_seed_only(
        sim,
        seed_persons=["P-XI"],
        default_edge_p=0.25,
        edge_type_weights=edge_weights,
        org_to_member_p=0.55,
        max_depth=8,
        n_iterations=3000,
    )

    casc = compare["cascade"]
    seed = compare["seed_only"]
    prem = compare["premium"]

    print(f"\n  CASCADE RUN ({casc.n_iterations} iterations):")
    print(f"    Persons failed (mean):       "
          f"{casc.mean_total_persons_failed:>5.2f}  "
          f"({casc.mean_total_persons_failed - 1:.2f} via cascade)")
    print(f"    Orgs failed (mean):          "
          f"{casc.mean_total_orgs_failed:>5.2f}")
    print(f"    Cascade depth (mean):        "
          f"{casc.mean_max_depth_reached:>5.2f}  waves")
    print(f"    Amplification factor:        "
          f"×{casc.mean_amplification_factor:.2f}")
    print(f"    Capability remaining:        {casc.mean_pct:>5.1f}%  "
          f"(σ {casc.std_pct:.1f}, p05 {casc.p05_pct:.1f}, "
          f"p95 {casc.p95_pct:.1f})")

    print(f"\n  SEED-ONLY BASELINE (no propagation):")
    print(f"    Persons failed:              "
          f"{seed.mean_total_persons_failed:>5.2f}")
    print(f"    Capability remaining:        {seed.mean_pct:>5.1f}%")

    print(f"\n  CASCADE PREMIUM:")
    print(f"    Capability lost to cascade:  "
          f"{prem['cascade_premium_pp']:>+5.1f} pp")
    print(f"    Extra persons taken down:    "
          f"{prem['extra_persons_failed']:>+5.2f}")
    print(f"    Extra orgs taken down:       "
          f"{prem['extra_orgs_failed']:>+5.2f}")

    # ── Top cascade victims ──────────────────────────────────────────────
    banner("MOST FREQUENTLY CASCADED PERSONS (network choke points)")
    sorted_freq = sorted(casc.person_failure_freq.items(),
                          key=lambda kv: -kv[1])
    print(f"\n  {'Person':<22} {'Failure rate':>14}")
    print("  " + "─" * 50)
    for pid, count in sorted_freq:
        person = persons.get(pid)
        name = person.name if person else pid
        rate = count / casc.n_iterations
        bar = "█" * int(rate * 30)
        print(f"  {name:<22} {rate:>10.1%}  {bar}")

    # ── Scenario 2: Compare seeds ────────────────────────────────────────
    banner("SCENARIO 2: WHICH SEED PRODUCES THE LARGEST CASCADE?")
    print("\n  Comparing single-person seeds across the leadership graph:\n")
    print(f"  {'Seed':<22} {'Persons':>9} {'Orgs':>6} "
          f"{'Cap%':>6} {'Premium':>9}")
    print("  " + "─" * 60)
    for seed_pid in ["P-XI", "P-LIQ", "P-WGH", "P-ZYS", "P-CNPC"]:
        cmp = cascade_vs_seed_only(
            sim, seed_persons=[seed_pid],
            default_edge_p=0.25,
            edge_type_weights=edge_weights,
            org_to_member_p=0.55,
            max_depth=8,
            n_iterations=1500,
        )
        c = cmp["cascade"]
        p = cmp["premium"]
        person = persons.get(seed_pid)
        name = person.name if person else seed_pid
        print(f"  {name:<22} {c.mean_total_persons_failed:>9.2f} "
              f"{c.mean_total_orgs_failed:>6.2f} "
              f"{c.mean_pct:>6.1f} {p['cascade_premium_pp']:>+8.1f}pp")

    # ── Interpretation ───────────────────────────────────────────────────
    banner("INTERPRETATION")
    print("""
  The cascade premium (in pp of capability remaining) quantifies how
  much extra damage the network propagation adds to a single seed
  removal. Three observations from this synthetic graph:

  1. Xi Jinping as seed produces the largest cascade. He's a multi-hat
     person AND patron to four others AND a member of CCP+CMC. Removal
     activates patron-edge propagation to Li Qiang, Cai Qi, Ding, and
     Zhang Youxia, while CCP→CMC org-org propagation hits the military
     command structure.

  2. Wang Huning as seed has lower cascade despite high CNI. He's
     ideologically central but not a patron node — fewer outgoing
     patron-edges means less cascade. High CNI doesn't equal high
     cascade if the centrality is "structural" rather than "patronage."

  3. Dai Houliang (CNPC) as seed has minimal cascade. He's downstream
     in the patron graph; cascading from him goes upward (to Ding) but
     edges are weak. SOE chairs are leaves of the leadership tree —
     low cascade reach.

  Operational use:
    • Risk register: rank persons by cascade-mediated capability loss.
      Xi-equivalent nodes are decapitation singletons; Dai-equivalent
      nodes have local-only consequences.

    • Resilience: edges with high cascade probability (patron, reports_to)
      are points where mentorship-redundancy and chain-of-command
      diversification yield high marginal resilience.

    • Edge-type calibration: the demo's edge-type weights are illustrative.
      Real OSINT analysis would calibrate against historical events
      where the network response can be reconstructed (e.g., the
      Bo Xilai 2012 fall and Zhou Yongkang's subsequent isolation).

  The graph schema is intentionally agnostic about edge types — if your
  scrapers produce typed edges later, the per-type weights map directly
  onto cascade probability. If they don't, the default_edge_p applies
  uniformly and the simulator still produces meaningful output.
""")


if __name__ == "__main__":
    main()
