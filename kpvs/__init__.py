"""
kpvs — Key Person Vulnerability Simulator
==========================================

Public API. The recommended import surface for downstream code:

    from kpvs import (
        # Data model
        Person, Alias, RoleAssignment,

        # Effective KPCI derivation
        effective_kpci, person_premium, continuity_loss,

        # Name matching utilities
        find_person, find_persons_above, match_score,

        # Person-centric simulator (PR #2)
        PersonAwareSimulator,

        # Faction purge (PR #4)
        FactionAwareSimulator, run_faction_vs_random,

        # Graph cascade (PR #3)
        OSINTGraph, GraphEdge, empty_graph, auto_apex_edges,
        GraphAwareSimulator, cascade_vs_seed_only,

        # Entity resolver (PR #5)
        EntityResolver, MergeCandidate, CalibrationReport,
    )

For working with the existing role-level simulator, import directly
from kpvs.models, kpvs.simulator, etc.
"""

from kpvs.persons import (
    Person,
    Alias,
    RoleAssignment,
    roles_held_by,
    persons_in_role,
    multi_hat_persons,
)

from kpvs.effective_kpci import (
    effective_kpci,
    effective_tier,
    person_premium,
    tenure_factor,
    continuity_loss,
)

from kpvs.name_matching import (
    normalize,
    match_score,
    find_person,
    find_persons_above,
    transliteration_variants,
)

from kpvs.person_simulator import (
    PersonAwareSimulator,
    PersonScenarioResult,
    person_adversarial_gap,
)

from kpvs.faction_purge import (
    FactionAwareSimulator,
    FactionPurgeResult,
    resolve_faction_members,
    faction_concentration_premium,
    run_faction_vs_random,
)

from kpvs.osint_graph import (
    OSINTGraph,
    GraphEdge,
    empty_graph,
    auto_apex_edges,
)

from kpvs.cascade_simulator import (
    GraphAwareSimulator,
    CascadeResult,
    cascade_vs_seed_only,
)

from kpvs.entity_resolver import (
    EntityResolver,
    ResolveResult,
    MergeCandidate,
    CalibrationReport,
)


__all__ = [
    # Data model
    "Person", "Alias", "RoleAssignment",
    "roles_held_by", "persons_in_role", "multi_hat_persons",

    # Effective KPCI
    "effective_kpci", "effective_tier", "person_premium",
    "tenure_factor", "continuity_loss",

    # Name matching
    "normalize", "match_score", "find_person",
    "find_persons_above", "transliteration_variants",

    # Simulators (in inheritance order)
    "PersonAwareSimulator", "PersonScenarioResult", "person_adversarial_gap",
    "FactionAwareSimulator", "FactionPurgeResult",
    "resolve_faction_members", "faction_concentration_premium",
    "run_faction_vs_random",
    "GraphAwareSimulator", "CascadeResult", "cascade_vs_seed_only",

    # Graph
    "OSINTGraph", "GraphEdge", "empty_graph", "auto_apex_edges",

    # Entity resolver
    "EntityResolver", "ResolveResult", "MergeCandidate", "CalibrationReport",
]


__version__ = "0.5.0"
