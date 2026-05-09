"""
kpvs/osint_graph.py — OSINT graph data structure for cascade scenarios
========================================================================

Lightweight per-country graph of persons + organizations + edges for
consumption by the cascade simulator. Designed to be agnostic about edge
types so the same module works whether your scrapers produce typed edges
(reports_to, co_faction, mentor) or untyped co-occurrence edges.

Design commitments
------------------
1. **No NetworkX requirement.** The dataclass works standalone. A
   `from_networkx()` adapter is provided for convenience, and graph
   metrics in role_mapper.py still use NetworkX when available.

2. **Per-country scope.** A graph instance represents one country's
   leadership network. Cross-country dynamics, if needed later, are
   handled by running multiple scenarios.

3. **Mixed node types.** Persons and organizations are first-class
   nodes. Edges can connect any pair (P-P, O-O, P-O, O-P). The cascade
   simulator handles all four cases.

4. **Optional edge types and weights.** Untyped, unweighted edges work.
   Typed/weighted edges enable finer cascade control. Cascade defaults
   gracefully when types/weights are absent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Edge dataclass
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class GraphEdge:
    """A directed edge in the OSINT graph.

    Attributes
    ----------
    source       : node ID (person_id or org_id)
    target       : node ID (person_id or org_id)
    source_type  : 'person' | 'org'
    target_type  : 'person' | 'org'
    weight       : ∈ [0, 1] — edge activation probability for cascade.
                   None = use default from cascade scenario invocation.
    edge_type    : optional analyst tag ('reports_to', 'co_faction',
                   'mentor', 'co_event', 'subordinate_of', etc.).
                   Untyped edges work fine.
    bidirectional: if True, cascade propagates in both directions
                   regardless of declared source→target. Most network
                   ties are functionally bidirectional (you cascade up
                   to your patron and down to your protégés both).
    source_ref   : provenance — where this edge was observed
    confidence   : ∈ [0, 1] — analyst confidence in the edge's existence
    notes        : free-text annotation
    """
    source: str
    target: str
    source_type: str  # 'person' | 'org'
    target_type: str  # 'person' | 'org'
    weight: Optional[float] = None
    edge_type: str = ""
    bidirectional: bool = True  # most leadership ties are functionally bidir
    source_ref: str = ""
    confidence: float = 1.0
    notes: str = ""

    def __post_init__(self) -> None:
        if self.source_type not in ("person", "org"):
            raise ValueError(
                f"source_type must be 'person' or 'org'; got {self.source_type!r}")
        if self.target_type not in ("person", "org"):
            raise ValueError(
                f"target_type must be 'person' or 'org'; got {self.target_type!r}")
        if self.weight is not None and not 0 <= self.weight <= 1:
            raise ValueError(
                f"GraphEdge weight must be in [0, 1] or None; got {self.weight}")
        if not 0 <= self.confidence <= 1:
            raise ValueError(
                f"GraphEdge confidence must be in [0, 1]; got {self.confidence}")
        if self.source == self.target:
            raise ValueError(
                f"Self-loops not allowed; got {self.source}")

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "source_type": self.source_type,
            "target_type": self.target_type,
            "weight": self.weight,
            "edge_type": self.edge_type,
            "bidirectional": self.bidirectional,
            "source_ref": self.source_ref,
            "confidence": self.confidence,
            "notes": self.notes,
        }


# ─────────────────────────────────────────────────────────────────────────
# OSINTGraph dataclass
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class OSINTGraph:
    """Per-country OSINT graph with persons, orgs, and edges.

    Attributes
    ----------
    country        : ISO-2 code ('CN', 'RU', 'IR', 'KP')
    person_ids     : set of all person nodes known in this graph
    org_ids        : set of all org nodes known in this graph
    edges          : list of GraphEdge objects
    person_to_orgs : dict[person_id, set[org_id]] — membership.
                     When an org fails, persons in this set fail too.
    role_to_org    : dict[role_id, org_id] — bridge from KPVS roles to
                     graph orgs. Required for org-failure → role-loss
                     cascade. Optional if you only use person-person
                     edges.

    The graph mutates rarely — analysts assemble it once per analysis run.
    """
    country: str
    person_ids: set = field(default_factory=set)
    org_ids: set = field(default_factory=set)
    edges: list = field(default_factory=list)
    person_to_orgs: dict = field(default_factory=dict)
    role_to_org: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.country or len(self.country) != 2:
            raise ValueError(
                f"OSINTGraph.country must be ISO-2; got {self.country!r}")
        # Ensure types are sets (allow construction from lists)
        self.person_ids = set(self.person_ids)
        self.org_ids = set(self.org_ids)

        # Build adjacency cache lazily on first lookup
        self._adj_cache = None

    # ── Node management ───────────────────────────────────────────────────
    def add_person(self, person_id: str,
                   orgs: Optional[list] = None) -> None:
        """Register a person node. Optionally attach org memberships."""
        self.person_ids.add(person_id)
        if orgs:
            self.person_to_orgs.setdefault(person_id, set()).update(orgs)
            self.org_ids.update(orgs)
        self._adj_cache = None

    def add_org(self, org_id: str) -> None:
        """Register an org node."""
        self.org_ids.add(org_id)
        self._adj_cache = None

    def add_edge(self, edge: GraphEdge) -> None:
        """Append an edge. Validates that endpoints exist (warns if not)."""
        if edge.source_type == "person" and edge.source not in self.person_ids:
            logger.warning(
                "Edge references unknown person source %r — adding to graph",
                edge.source)
            self.person_ids.add(edge.source)
        elif edge.source_type == "org" and edge.source not in self.org_ids:
            logger.warning(
                "Edge references unknown org source %r — adding to graph",
                edge.source)
            self.org_ids.add(edge.source)

        if edge.target_type == "person" and edge.target not in self.person_ids:
            logger.warning(
                "Edge references unknown person target %r — adding to graph",
                edge.target)
            self.person_ids.add(edge.target)
        elif edge.target_type == "org" and edge.target not in self.org_ids:
            logger.warning(
                "Edge references unknown org target %r — adding to graph",
                edge.target)
            self.org_ids.add(edge.target)

        self.edges.append(edge)
        self._adj_cache = None

    def link_role_to_org(self, role_id: str, org_id: str) -> None:
        """Attach a KPVS role_id to a graph org_id.

        Required for org-failure → role-cascade. Without this mapping,
        org failures still propagate through edges but don't directly
        knock out roles (roles will only fail via their occupant person
        being affected).
        """
        if org_id not in self.org_ids:
            self.org_ids.add(org_id)
        self.role_to_org[role_id] = org_id

    # ── Adjacency lookups ────────────────────────────────────────────────
    def _build_adjacency(self) -> dict:
        """Build {node_id: list[(neighbor_id, neighbor_type, weight, edge_type)]}.

        Treats bidirectional edges as appearing on both endpoints.
        """
        adj: dict = {}
        for e in self.edges:
            adj.setdefault(e.source, []).append(
                (e.target, e.target_type, e.weight, e.edge_type))
            if e.bidirectional:
                adj.setdefault(e.target, []).append(
                    (e.source, e.source_type, e.weight, e.edge_type))
        return adj

    def neighbors(self, node_id: str) -> list:
        """Return [(neighbor_id, neighbor_type, weight, edge_type), ...].

        Cached after first call until graph is mutated.
        """
        if self._adj_cache is None:
            self._adj_cache = self._build_adjacency()
        return self._adj_cache.get(node_id, [])

    def persons_in_org(self, org_id: str) -> set:
        """Return set of person_ids known to be members of an org."""
        return {pid for pid, orgs in self.person_to_orgs.items()
                if org_id in orgs}

    def roles_in_org(self, org_id: str) -> list:
        """Return list of role_ids attached to an org via link_role_to_org."""
        return [rid for rid, oid in self.role_to_org.items()
                if oid == org_id]

    # ── Diagnostics ──────────────────────────────────────────────────────
    def summary(self) -> dict:
        """Lightweight stats for reporting / logging."""
        return {
            "country": self.country,
            "n_persons": len(self.person_ids),
            "n_orgs": len(self.org_ids),
            "n_edges": len(self.edges),
            "n_typed_edges": sum(1 for e in self.edges if e.edge_type),
            "n_weighted_edges": sum(1 for e in self.edges
                                     if e.weight is not None),
            "n_role_to_org_mappings": len(self.role_to_org),
        }

    def to_dict(self) -> dict:
        return {
            "country": self.country,
            "person_ids": sorted(self.person_ids),
            "org_ids": sorted(self.org_ids),
            "edges": [e.to_dict() for e in self.edges],
            "person_to_orgs": {pid: sorted(orgs)
                                for pid, orgs in self.person_to_orgs.items()},
            "role_to_org": dict(self.role_to_org),
        }


# ─────────────────────────────────────────────────────────────────────────
# Constructor helpers
# ─────────────────────────────────────────────────────────────────────────
def from_networkx(G, country: str,
                  person_node_attr: str = "type",
                  weight_edge_attr: str = "weight",
                  type_edge_attr: str = "edge_type") -> OSINTGraph:
    """Adapter: build OSINTGraph from a NetworkX graph.

    Expects:
      - Each node has attribute `person_node_attr` valued 'person' or 'org'
      - Edges optionally carry `weight_edge_attr` and `type_edge_attr`

    Both directed and undirected NetworkX graphs are accepted.
    """
    try:
        import networkx as nx
    except ImportError:
        raise ImportError("networkx required for from_networkx adapter")

    g = OSINTGraph(country=country)
    for node_id, attrs in G.nodes(data=True):
        node_type = attrs.get(person_node_attr, "person")
        if node_type == "person":
            g.person_ids.add(node_id)
        elif node_type == "org":
            g.org_ids.add(node_id)
        else:
            logger.warning("Skipping node %r with unknown type %r",
                           node_id, node_type)

    is_directed = isinstance(G, nx.DiGraph)
    for u, v, attrs in G.edges(data=True):
        u_type = G.nodes[u].get(person_node_attr, "person")
        v_type = G.nodes[v].get(person_node_attr, "person")
        edge = GraphEdge(
            source=u, target=v,
            source_type=u_type, target_type=v_type,
            weight=attrs.get(weight_edge_attr),
            edge_type=attrs.get(type_edge_attr, ""),
            bidirectional=not is_directed,
        )
        g.edges.append(edge)

    return g


def empty_graph(country: str) -> OSINTGraph:
    """Convenience: return an empty graph for incremental assembly."""
    return OSINTGraph(country=country)


def auto_apex_edges(graph: OSINTGraph,
                    persons: dict,
                    role_assignments: list,
                    roles: dict,
                    apex_kpci_threshold: float = 10.0,
                    edge_type: str = "apex_loss") -> int:
    """Auto-generate Person→Org edges for apex figures.

    Membership alone (Person.factions / graph.person_to_orgs) does not
    trigger an org-cascade when a person fails — that's by design, so
    junior officers don't propagate institutional collapse. But for
    apex figures (high effective KPCI), the analyst typically WOULD
    want their loss to strain the institution.

    This helper auto-generates those P→O edges with type 'apex_loss'
    and bidirectional=False for any person whose effective KPCI on
    any role meets the threshold.

    Parameters
    ----------
    graph                : OSINTGraph to mutate (edges added in place)
    persons              : dict[person_id, Person]
    role_assignments     : list[RoleAssignment]
    roles                : dict[role_id, role_object] with .kpci attribute
    apex_kpci_threshold  : effective_kpci floor; default 10.0 (Tier-1)
    edge_type            : edge_type tag for new edges

    Returns
    -------
    int — number of edges added
    """
    from kpvs.effective_kpci import effective_kpci

    added = 0
    existing_p2o = {(e.source, e.target) for e in graph.edges
                    if e.source_type == "person" and e.target_type == "org"}

    for assignment in role_assignments:
        person = persons.get(assignment.person_id)
        role = roles.get(assignment.role_id)
        if person is None or role is None:
            continue

        eff = effective_kpci(role, person,
                              has_designated_successor=assignment.is_designated_successor)
        if eff < apex_kpci_threshold:
            continue

        # Add P→O edges to all of this person's known org memberships
        for org_id in graph.person_to_orgs.get(person.id, set()):
            if (person.id, org_id) in existing_p2o:
                continue
            graph.add_edge(GraphEdge(
                source=person.id, target=org_id,
                source_type="person", target_type="org",
                edge_type=edge_type,
                bidirectional=False,
                notes=f"auto-generated: effective_kpci={eff:.2f}",
            ))
            existing_p2o.add((person.id, org_id))
            added += 1

    return added
