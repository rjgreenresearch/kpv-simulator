"""
kpvs/intelligence/role_mapper.py — OSINT graph → KPVS role assignments
=======================================================================

Bridges the OSINT global graph (persons, orgs, edges) to KPVS by:

  1. Resolving curated role taxonomies (per country) to current occupants
  2. Computing person profiles (TK, CNI, substitutes) from graph metrics
  3. Emitting (Person, RoleAssignment, Role) bundles for the simulator

This module is a sketch — the heavy lifting is the curated taxonomy. Graph
metric computation uses NetworkX if available; falls back to degree-only
heuristics if not.

Entity resolution (separate concern)
------------------------------------
Before this layer is invoked, the OSINT graph must already have stable
person_ids that survive cross-source merging. Xi Jinping / 习近平 / Си
Цзиньпин must collapse to one node. That belongs in an entity-resolution
module (likely fuzzy-match + role-context disambiguation against the
curated taxonomies in this file). Out of scope here.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Optional NetworkX import — graceful fallback.
try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False
    logger.info("networkx not available — using degree-only heuristics for CNI.")


# ─────────────────────────────────────────────────────────────────────────
# Curated role taxonomies
# ─────────────────────────────────────────────────────────────────────────
# Each entry defines a structural role with its KPCI components (ST, DR, AO)
# established from doctrine, NOT from the current occupant. Occupants vary
# over time; the role's structural fragility does not.
#
# These are starting values — analyst should refine. The point is to anchor
# the role-level KPCI in MTS WP-5 doctrine before person-level overlays
# are applied.

@dataclass
class RoleSpec:
    """A taxonomic role definition (structural, occupant-independent)."""
    role_id: str
    title: str
    country: str
    institution: str
    ST: float            # Substitution Timeline ∈ [0,4]
    DR: float            # Documentation Ratio ∈ [0,4]
    AO: float            # Adversarial Observability ∈ [0,4]
    capability_weight: float = 1.0
    notes: str = ""
    # Hint to entity resolver: how to query the OSINT graph for occupant
    occupant_query: dict = field(default_factory=dict)


# ── PRC: Politburo Standing Committee + key party/state/military roles ──
PRC_TAXONOMY: list = [
    # Politburo Standing Committee (PSC) — apex of CCP power
    RoleSpec(
        role_id="CN-PSC-01-GENSEC",
        title="General Secretary, CCP",
        country="CN",
        institution="Chinese Communist Party",
        ST=4.0, DR=4.0, AO=4.0,  # KPCI = 12, Tier-1
        capability_weight=5.0,
        notes="Apex political authority. Multi-hat with State President + CMC Chair.",
        occupant_query={"institution": "CCP", "title_zh": "总书记"},
    ),
    RoleSpec(
        role_id="CN-PSC-02-PREMIER",
        title="Premier of the State Council",
        country="CN",
        institution="State Council",
        ST=3.5, DR=3.5, AO=4.0,  # KPCI = 11, Tier-1
        capability_weight=4.0,
        notes="Head of government. Manages state ministries.",
    ),
    RoleSpec(
        role_id="CN-PSC-03-NPC",
        title="Chairman, NPC Standing Committee",
        country="CN",
        institution="National People's Congress",
        ST=3.0, DR=3.0, AO=3.5,  # KPCI = 9.5, Tier-2
        capability_weight=2.5,
    ),
    RoleSpec(
        role_id="CN-PSC-04-CPPCC",
        title="Chairman, CPPCC",
        country="CN",
        institution="Chinese People's Political Consultative Conference",
        ST=2.5, DR=2.5, AO=3.0,  # KPCI = 8, Tier-2
        capability_weight=1.5,
    ),
    RoleSpec(
        role_id="CN-PSC-05-SECRETARIAT",
        title="First Secretary, CCP Secretariat",
        country="CN",
        institution="CCP Secretariat",
        ST=3.0, DR=3.5, AO=3.5,  # KPCI = 10, Tier-1
        capability_weight=3.0,
        notes="Day-to-day party administration.",
    ),
    RoleSpec(
        role_id="CN-PSC-06-CDIC",
        title="Secretary, Central Discipline Inspection Commission",
        country="CN",
        institution="CDIC",
        ST=3.0, DR=3.5, AO=3.5,  # KPCI = 10, Tier-1
        capability_weight=2.5,
        notes="Anti-corruption enforcement. Powerful internal lever.",
    ),
    RoleSpec(
        role_id="CN-PSC-07-VICEPREMIER",
        title="First Vice Premier",
        country="CN",
        institution="State Council",
        ST=3.0, DR=3.0, AO=3.0,  # KPCI = 9, Tier-2
        capability_weight=2.0,
    ),

    # Central Military Commission (CMC) — distinct power line
    RoleSpec(
        role_id="CN-CMC-CHAIR",
        title="Chairman, Central Military Commission",
        country="CN",
        institution="Central Military Commission",
        ST=4.0, DR=4.0, AO=4.0,  # KPCI = 12, Tier-1
        capability_weight=5.0,
        notes="Civilian control of military. Often held by General Secretary.",
    ),
    RoleSpec(
        role_id="CN-CMC-VC1",
        title="First Vice Chairman, CMC",
        country="CN",
        institution="Central Military Commission",
        ST=3.5, DR=4.0, AO=3.5,  # KPCI = 11, Tier-1
        capability_weight=3.5,
    ),
    RoleSpec(
        role_id="CN-CMC-VC2",
        title="Second Vice Chairman, CMC",
        country="CN",
        institution="Central Military Commission",
        ST=3.5, DR=4.0, AO=3.5,  # KPCI = 11, Tier-1
        capability_weight=3.5,
    ),

    # Key Politburo (non-PSC) full members — the next tier of decision-makers
    # 17 additional Politburo members; 3 high-leverage examples below.
    RoleSpec(
        role_id="CN-PB-FOREIGN",
        title="Director, CCP Central Foreign Affairs Commission Office",
        country="CN",
        institution="CCP Central Foreign Affairs Commission",
        ST=2.5, DR=3.5, AO=3.5,  # KPCI = 9.5, Tier-2
        capability_weight=2.5,
        notes="Architect of foreign policy execution.",
    ),
    RoleSpec(
        role_id="CN-PB-POLISEC",
        title="Secretary, Central Political and Legal Affairs Commission",
        country="CN",
        institution="Central Political and Legal Affairs Commission",
        ST=2.5, DR=3.5, AO=3.5,  # KPCI = 9.5, Tier-2
        capability_weight=2.5,
        notes="Oversees MPS, MSS, courts, procuratorate. Coercive apparatus.",
    ),
    RoleSpec(
        role_id="CN-PB-ORGDEPT",
        title="Director, CCP Central Organization Department",
        country="CN",
        institution="CCP Central Organization Department",
        ST=2.5, DR=4.0, AO=3.0,  # KPCI = 9.5, Tier-2
        capability_weight=2.5,
        notes="Personnel kingmaker for entire CCP nomenklatura.",
    ),

    # Key SOE / strategic-sector heads
    RoleSpec(
        role_id="CN-SOE-CNPC",
        title="Chairman, China National Petroleum Corporation",
        country="CN",
        institution="CNPC",
        ST=2.0, DR=3.0, AO=2.5,  # KPCI = 7.5, Tier-2
        capability_weight=2.0,
    ),
    RoleSpec(
        role_id="CN-SOE-SINOCHEM",
        title="Chairman, Sinochem Holdings",
        country="CN",
        institution="Sinochem (parent of Syngenta)",
        ST=2.0, DR=3.0, AO=2.5,  # KPCI = 7.5, Tier-2
        capability_weight=2.0,
        notes="Owns Syngenta — directly relevant to AFIDA/CFIUS research.",
    ),
]


# Stubs for additional countries — to be expanded.
RU_TAXONOMY: list = []  # FSB Director, GRU Chief, Security Council Secretary, ...
IR_TAXONOMY: list = []  # Supreme Leader, IRGC CG, Quds Force CG, ...
KP_TAXONOMY: list = []  # Chairman SAC, OGD Director, MSS Director, ...

ALL_TAXONOMIES = {
    "CN": PRC_TAXONOMY,
    "RU": RU_TAXONOMY,
    "IR": IR_TAXONOMY,
    "KP": KP_TAXONOMY,
}


# ─────────────────────────────────────────────────────────────────────────
# Graph-derived person profile computation
# ─────────────────────────────────────────────────────────────────────────
def compute_network_integration(graph, person_id: str) -> float:
    """Map graph centrality → CNI ∈ [0, 4].

    Uses k-core position + normalized betweenness if NetworkX is available;
    falls back to normalized degree if not.

    The mapping is deliberately conservative: a maximally-central node in
    a 1000-node graph gets CNI = 4.0; an isolate gets 0.0. Distribution
    is calibrated so a typical Politburo-level node lands around CNI 3.0–3.5.
    """
    if not HAS_NX:
        # Degree-only fallback
        if hasattr(graph, "degree"):
            d = graph.degree(person_id)
            n = max(getattr(graph, "number_of_nodes", lambda: 100)(), 2)
            return min(4.0, 4.0 * d / max(n - 1, 1) * 5)  # boost factor
        return 0.0

    if person_id not in graph:
        return 0.0

    # k-core: structural embeddedness
    try:
        core_numbers = nx.core_number(graph)
        max_core = max(core_numbers.values()) if core_numbers else 1
        k = core_numbers.get(person_id, 0)
        kcore_score = k / max(max_core, 1)
    except Exception:
        kcore_score = 0.0

    # Betweenness: brokerage role
    try:
        # On large graphs, sample for performance
        n = graph.number_of_nodes()
        k_sample = min(500, n)
        bc = nx.betweenness_centrality(graph, k=k_sample, normalized=True)
        bc_score = bc.get(person_id, 0.0)
        # Betweenness distributions are heavy-tailed; log-scale
        bc_score = math.log(1 + 100 * bc_score) / math.log(101)
    except Exception:
        bc_score = 0.0

    # Combine: average of normalized scores, then scale to [0, 4]
    combined = 0.5 * kcore_score + 0.5 * bc_score
    return min(4.0, 4.0 * combined)


def compute_tacit_knowledge(graph, person_id: str,
                            tenure_months: int,
                            n_concurrent_roles: int,
                            n_events: int = 0) -> float:
    """Heuristic TK ∈ [0, 4] from tenure × multi-hat × event frequency.

    TK = base(tenure) + multihat_bonus + event_bonus, capped at 4.
    """
    # Base from tenure: 0 at month 0, ~2.5 at 60 months, ~3.0 at 120 months
    base = 3.0 * (1.0 - math.exp(-tenure_months / 36.0))

    # Multi-hat bonus: each additional concurrent role adds 0.4, capped
    multihat = 0.4 * max(0, n_concurrent_roles - 1)

    # Event frequency bonus: appearing in many events suggests operational
    # depth. Log-scaled.
    event_bonus = 0.5 * math.log(1 + n_events) / math.log(10)

    return min(4.0, base + multihat + event_bonus)


def estimate_substitutes(graph, person_id: str,
                         role_spec: RoleSpec,
                         pool_filter=None) -> int:
    """Count plausible succession candidates.

    Default heuristic: persons in the same institution within 2 ranks of
    seniority. Analyst can supply a pool_filter callable for taxonomy-
    specific logic (e.g., for PSC succession, only Politburo full members).
    """
    if pool_filter is None:
        return 3  # neutral default — "some bench, no specific count"

    pool = [n for n in (graph.nodes() if HAS_NX and graph else [])
            if pool_filter(n, role_spec)]
    return max(0, len(pool))


# ─────────────────────────────────────────────────────────────────────────
# Pipeline: emit KPVS-ready bundles
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class MappedAssignment:
    """A complete bundle ready for KPVS consumption."""
    role_spec: RoleSpec
    person: object  # kpvs.persons.Person — circular import avoided
    assignment: object  # kpvs.persons.RoleAssignment
    effective_kpci: float
    provenance: dict


def map_country(country: str, graph=None,
                occupant_resolver=None) -> list:
    """Build MappedAssignment list for a country.

    Parameters
    ----------
    country : 'CN' | 'RU' | 'IR' | 'KP'
    graph   : OSINT global graph (NetworkX DiGraph or compatible).
              Optional — if None, returns role specs with placeholder
              persons so the simulator can still run on structural KPCI.
    occupant_resolver : callable(role_spec, graph) → person_id | None
              The entity-resolution layer. If None, falls back to
              role_spec.occupant_query directly against graph node attrs.
    """
    from kpvs.persons import Person, RoleAssignment
    from kpvs.effective_kpci import effective_kpci

    taxonomy = ALL_TAXONOMIES.get(country, [])
    if not taxonomy:
        logger.warning("No taxonomy defined for country '%s'.", country)
        return []

    out = []
    for spec in taxonomy:
        person_id = None
        if graph is not None and occupant_resolver is not None:
            person_id = occupant_resolver(spec, graph)

        if person_id is None:
            # Placeholder person — preserves role for structural-KPCI runs
            person = Person(
                id=f"UNKNOWN-{spec.role_id}",
                name="(occupant unknown)",
                country=country,
            )
            assignment = RoleAssignment(
                person_id=person.id,
                role_id=spec.role_id,
            )
            eff = effective_kpci_from_components(spec, person)
            out.append(MappedAssignment(
                role_spec=spec, person=person, assignment=assignment,
                effective_kpci=eff,
                provenance={"resolved": False},
            ))
            continue

        # Real person — pull attributes from graph
        attrs = graph.nodes[person_id] if HAS_NX else {}
        cni = compute_network_integration(graph, person_id)
        tenure = attrs.get("tenure_months", 0)
        concurrent = attrs.get("n_concurrent_roles", 1)
        events = attrs.get("n_events", 0)
        tk = compute_tacit_knowledge(graph, person_id, tenure, concurrent, events)
        subs = estimate_substitutes(graph, person_id, spec)

        person = Person(
            id=person_id,
            name=attrs.get("name", person_id),
            name_native=attrs.get("name_native", ""),
            country=country,
            tacit_knowledge=tk,
            network_integration=cni,
            tenure_months=tenure,
            substitutes=subs,
            sources=attrs.get("sources", []),
            last_updated=attrs.get("last_updated", ""),
        )
        assignment = RoleAssignment(
            person_id=person.id,
            role_id=spec.role_id,
        )
        eff = effective_kpci_from_components(spec, person)
        out.append(MappedAssignment(
            role_spec=spec, person=person, assignment=assignment,
            effective_kpci=eff,
            provenance={
                "resolved": True,
                "graph_attrs": dict(attrs),
            },
        ))

    return out


def effective_kpci_from_components(spec: RoleSpec, person) -> float:
    """Compute effective KPCI from RoleSpec + Person without instantiating
    a full Role object (used during mapping pipeline)."""
    structural = spec.ST + spec.DR + spec.AO

    import math
    ALPHA, BETA, GAMMA = 0.45, 0.45, 0.6
    tk_term = ALPHA * person.tacit_knowledge
    cni_term = BETA * person.network_integration
    sub_penalty = GAMMA * math.log(person.substitutes + 1)
    premium = tk_term + cni_term - sub_penalty

    return max(structural, structural + premium)
