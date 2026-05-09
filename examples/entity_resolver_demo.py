"""
examples/entity_resolver_demo.py — Bulk OSINT graph deduplication
====================================================================

Realistic scenario: an analyst runs scrapers against multiple sources
(Xinhua Chinese, TASS Russian, KCNA Korean, English wire copy) and ends
up with duplicate Person nodes for the same individual. The resolver
detects the duplicates, the analyst reviews proposed merges, and the
deduplicated graph is then fed to the cascade simulator.

This is the workflow PR #5 was built to support.
"""

from kpvs.persons import Person, Alias, RoleAssignment
from kpvs.osint_graph import OSINTGraph, GraphEdge, empty_graph
from kpvs.entity_resolver import EntityResolver, MergeCandidate


def banner(text: str) -> None:
    print("\n" + "═" * 76)
    print(f"  {text}")
    print("═" * 76)


def main() -> None:
    banner("OSINT GRAPH DEDUPLICATION — REALISTIC WORKFLOW")

    # ── Stage 1: Canonical population (curated by analyst) ──────────────
    canonical = {
        "P-CN-XI": Person(
            id="P-CN-XI", name="Xi Jinping", country="CN",
            name_native="习近平",
            tacit_knowledge=4.0, network_integration=4.0,
            tenure_months=156, substitutes=0,
            aliases=[Alias(text="Hsi Chin-p'ing", romanization="wade-giles")],
        ),
        "P-CN-WANG-Y": Person(
            id="P-CN-WANG-Y", name="Wang Yi", country="CN",
            name_native="王毅",
            tacit_knowledge=3.5, network_integration=3.0,
            tenure_months=72, substitutes=1,
        ),
        "P-CN-WANG-H": Person(
            id="P-CN-WANG-H", name="Wang Huning", country="CN",
            name_native="王沪宁",
            tacit_knowledge=3.5, network_integration=3.0,
            tenure_months=96, substitutes=1,
        ),
        "P-RU-PUTIN": Person(
            id="P-RU-PUTIN", name="Vladimir Putin", country="RU",
            name_native="Владимир Путин",
            tacit_knowledge=4.0, network_integration=4.0,
            tenure_months=288, substitutes=0,
        ),
    }

    # Stub roles for role-context disambiguation
    class StubRole:
        def __init__(self, id, title, institution):
            self.id, self.title, self.institution = id, title, institution

    roles = {
        "CN-PSC-01": StubRole("CN-PSC-01", "General Secretary, CCP",
                                "Chinese Communist Party"),
        "CN-PB-FOREIGN": StubRole("CN-PB-FOREIGN",
                                    "Director, CCP Central Foreign Affairs Commission Office",
                                    "CCP Central Foreign Affairs Commission"),
        "CN-PSC-04": StubRole("CN-PSC-04", "Chairman, CPPCC",
                                "Chinese People's Political Consultative Conference"),
        "RU-PRES": StubRole("RU-PRES", "President of Russia",
                              "Russian Federation"),
    }

    assignments = [
        RoleAssignment("P-CN-XI", "CN-PSC-01"),
        RoleAssignment("P-CN-WANG-Y", "CN-PB-FOREIGN"),
        RoleAssignment("P-CN-WANG-H", "CN-PSC-04"),
        RoleAssignment("P-RU-PUTIN", "RU-PRES"),
    ]

    print(f"\n  Canonical population: {len(canonical)} persons")
    for pid, p in canonical.items():
        print(f"    {pid:<18} {p.name:<22} ({p.name_native})")

    # ── Stage 2: Incoming persons from various scrapers ──────────────────
    banner("STAGE 2: INCOMING SCRAPED PERSONS (potential duplicates)")

    # Each "incoming" person represents a scraper output. In a real
    # pipeline these come from different language sources and each
    # gets a unique node ID before resolution.
    incoming = [
        Person(id="SCRAPE-RU-001", name="Си Цзиньпин", country="CN",
               aliases=[Alias(text="general secretary of the chinese communist party",
                              source="TASS-2024")]),
        Person(id="SCRAPE-EN-002", name="Hsi Chinping", country="CN",
               notes="Older English source using Wade-Giles"),
        Person(id="SCRAPE-FR-003", name="Wang Yi", country="CN",
               aliases=[Alias(text="ministre des affaires étrangères chinois",
                              source="Le Monde-2024", language="fr")]),
        Person(id="SCRAPE-EN-004", name="Putin", country="RU",
               notes="Common abbreviated form"),
        Person(id="SCRAPE-EN-005", name="Vladimir V. Putin", country="RU",
               aliases=[Alias(text="V.V. Putin")]),
        Person(id="SCRAPE-DE-006", name="Wladimir Putin", country="RU",
               notes="German transliteration"),
        Person(id="SCRAPE-EN-007", name="John Smith", country="US",
               notes="Unrelated person — should NOT match"),
        Person(id="SCRAPE-EN-008", name="Wang", country="CN",
               notes="Ambiguous: which Wang?",
               aliases=[Alias(text="王", script="hans")]),
    ]

    print(f"\n  Incoming persons: {len(incoming)}")
    for p in incoming:
        print(f"    {p.id:<18} {p.name:<25} ({p.notes or 'no notes'})")

    # ── Stage 3: Run resolver ────────────────────────────────────────────
    banner("STAGE 3: RESOLVER FINDS MERGE CANDIDATES")

    resolver = EntityResolver(
        canonical, role_assignments=assignments, roles=roles,
        threshold=0.85,
    )
    candidates = resolver.find_merge_candidates(incoming)

    print(f"\n  Found {len(candidates)} merge candidates above threshold:\n")
    print(f"  {'Incoming':<22} → {'Canonical':<18} {'Score':>6}  Evidence")
    print("  " + "─" * 72)
    for c in candidates:
        evidence_flags = []
        if c.evidence.get("role_context"):
            evidence_flags.append("role-ctx")
        if c.evidence.get("graph_evidence"):
            evidence_flags.append("graph")
        ev_str = ",".join(evidence_flags) or "name-only"
        print(f"  {c.incoming_name:<22} → "
              f"{c.canonical_name:<18} {c.score:>6.3f}  {ev_str}")

    # ── Stage 4: Identify rejected (no good match) ───────────────────────
    banner("STAGE 4: INCOMING WITH NO GOOD MATCH")
    matched_ids = {c.incoming_id for c in candidates}
    unmatched = [p for p in incoming if p.id not in matched_ids]
    print(f"\n  {len(unmatched)} unmatched incoming persons "
          f"(may be new individuals, or below threshold):\n")
    for p in unmatched:
        # Show the best score they got
        best = None
        for q in p.all_names():
            r = resolver.resolve(q, role_hint=None)  # no boost
            if r is None:
                # Below threshold — try at lower threshold for diagnostic
                resolver.threshold = 0.5
                r = resolver.resolve(q)
                resolver.threshold = 0.85
            if r is not None:
                if best is None or r.score > best.score:
                    best = r
        if best is None:
            print(f"    {p.id:<18} {p.name:<25} no match at any threshold")
        else:
            print(f"    {p.id:<18} {p.name:<25} best={best.score:.3f} "
                  f"to {best.person.name} (below threshold)")

    # ── Stage 5: Apply merges to a graph ─────────────────────────────────
    banner("STAGE 5: APPLY MERGES TO OSINT GRAPH")

    # Build a graph that includes both canonical AND duplicate person IDs
    g = empty_graph("CN")
    for pid in list(canonical.keys()) + [p.id for p in incoming]:
        if pid.startswith("P-RU"):
            country_org = "KREMLIN"
        elif pid.startswith("SCRAPE-EN-005") or pid.startswith("SCRAPE-EN-004") or pid.startswith("SCRAPE-DE-006"):
            country_org = "KREMLIN"
        else:
            country_org = "CCP"
        g.add_person(pid, orgs=[country_org])

    # Add edges between scraper-produced duplicates and other nodes
    g.add_edge(GraphEdge(source="SCRAPE-RU-001", target="P-CN-WANG-Y",
                          source_type="person", target_type="person",
                          edge_type="co_event"))
    g.add_edge(GraphEdge(source="SCRAPE-EN-002", target="P-CN-WANG-H",
                          source_type="person", target_type="person",
                          edge_type="co_psc"))
    g.add_edge(GraphEdge(source="SCRAPE-EN-004", target="P-CN-XI",
                          source_type="person", target_type="person",
                          edge_type="bilateral_meeting"))
    g.add_edge(GraphEdge(source="SCRAPE-EN-005", target="P-CN-XI",
                          source_type="person", target_type="person",
                          edge_type="bilateral_meeting"))

    # Add incoming persons to canonical so merge() can find them
    for p in incoming:
        if p.id not in canonical:
            canonical[p.id] = p

    print(f"\n  Pre-merge:")
    print(f"    Person nodes:  {len(g.person_ids)}")
    print(f"    Edges:         {len(g.edges)}")

    deduped = resolver.deduplicate_graph(g, candidates)

    print(f"\n  Post-merge (after {len(candidates)} merges applied):")
    print(f"    Person nodes:  {len(deduped.person_ids)}")
    print(f"    Edges:         {len(deduped.edges)}")
    print(f"    Persons removed:  "
          f"{len(g.person_ids) - len(deduped.person_ids)}")
    print(f"    Edges deduped/removed:  "
          f"{len(g.edges) - len(deduped.edges)}")

    # ── Stage 6: Show enriched canonical ─────────────────────────────────
    banner("STAGE 6: CANONICAL PERSONS NOW CARRY MERGED ALIASES")
    print()
    for pid in ["P-CN-XI", "P-RU-PUTIN", "P-CN-WANG-Y"]:
        p = resolver.population[pid]
        print(f"  {p.name} ({pid}):")
        print(f"    Native:   {p.name_native}")
        print(f"    Aliases ({len(p.aliases)}):")
        for a in p.aliases:
            src = f" [{a.source}]" if a.source else ""
            print(f"      • {a.text}{src}")
        print()

    # ── Stage 7: Calibrate threshold (on a fresh resolver) ───────────────
    banner("STAGE 7: CALIBRATION AGAINST GROUND TRUTH")
    print("\n  Calibration is run against the ORIGINAL canonical population")
    print("  (before dedup merges enriched aliases) — this shows how the")
    print("  resolver would have performed against fresh OSINT data.")

    # Fresh canonical without the post-merge aliases — restore from
    # original source. We reconstruct because the live resolver has
    # been mutated by Stage 5.
    fresh_canonical = {
        "P-CN-XI": Person(
            id="P-CN-XI", name="Xi Jinping", country="CN",
            name_native="习近平",
            tacit_knowledge=4.0, network_integration=4.0,
            tenure_months=156, substitutes=0,
            aliases=[Alias(text="Hsi Chin-p'ing", romanization="wade-giles")],
        ),
        "P-CN-WANG-Y": Person(
            id="P-CN-WANG-Y", name="Wang Yi", country="CN",
            name_native="王毅",
            tacit_knowledge=3.5, network_integration=3.0,
            tenure_months=72, substitutes=1,
        ),
        "P-CN-WANG-H": Person(
            id="P-CN-WANG-H", name="Wang Huning", country="CN",
            name_native="王沪宁",
            tacit_knowledge=3.5, network_integration=3.0,
            tenure_months=96, substitutes=1,
        ),
        "P-RU-PUTIN": Person(
            id="P-RU-PUTIN", name="Vladimir Putin", country="RU",
            name_native="Владимир Путин",
            tacit_knowledge=4.0, network_integration=4.0,
            tenure_months=288, substitutes=0,
        ),
    }
    fresh_resolver = EntityResolver(fresh_canonical, threshold=0.5)

    # Hypothetical ground-truth pairs — in production these come from
    # analyst review of historical merges
    ground_truth = [
        ("Xi Jinping", "P-CN-XI"),
        ("习近平", "P-CN-XI"),
        ("Hsi Chinping", "P-CN-XI"),  # Wade-Giles
        ("Си Цзиньпин", "P-CN-XI"),    # Russian source — only matchable via fuzzy
        ("Wang Yi", "P-CN-WANG-Y"),
        ("王毅", "P-CN-WANG-Y"),
        ("Wang Huning", "P-CN-WANG-H"),
        ("Vladimir Putin", "P-RU-PUTIN"),
        ("Putin", "P-RU-PUTIN"),
        ("V.V. Putin", "P-RU-PUTIN"),
        ("Wladimir Putin", "P-RU-PUTIN"),  # German variant — only fuzzy
        ("John Smith", None),       # should NOT match
        ("Random Stranger", None),  # should NOT match
    ]

    report = fresh_resolver.calibrate(ground_truth)
    print(f"\n  Tested {report.n_pairs} ground-truth pairs across thresholds:\n")
    print(f"  {'Thresh':>7} {'Precision':>10} {'Recall':>9} "
          f"{'F1':>7}   TP/FP/FN/TN")
    print("  " + "─" * 60)
    for row in report.threshold_table:
        print(f"  {row['threshold']:>7.2f} {row['precision']:>10.3f} "
              f"{row['recall']:>9.3f} {row['f1']:>7.3f}   "
              f"{row['tp']}/{row['fp']}/{row['fn']}/{row['tn']}")
    print(f"\n  Best F1 = {report.best_f1:.3f} at threshold "
          f"{report.best_f1_threshold}")

    banner("WORKFLOW SUMMARY")
    print("""
  This is the operational pattern for any production OSINT pipeline:

    1. Maintain a curated canonical population (analyst-managed)
    2. Run scrapers, accumulate raw incoming Persons
    3. resolver.find_merge_candidates(incoming, threshold=…)
    4. Analyst reviews candidates above threshold; rejects spurious ones
    5. resolver.deduplicate_graph(graph, approved_merges)
    6. Pass deduplicated graph to GraphAwareSimulator for cascade analysis

  Calibration (Stage 7) provides defensible threshold selection. F1
  optimization is a starting point; in adversarial intel settings,
  high-precision (low FP) is often more important than recall.
""")


if __name__ == "__main__":
    main()
