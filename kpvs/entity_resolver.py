"""
kpvs/entity_resolver.py — Cross-source person identity resolution
===================================================================

Final layer of the person-centric pipeline. Consolidates duplicate Person
nodes that arise when scrapers in different languages produce different
surface strings for the same individual.

Core problem
------------
Without entity resolution, a real OSINT pipeline produces:

    Xi Jinping        (English wire copy)        → Person id 'P-001'
    习近平             (Xinhua Chinese)            → Person id 'P-417'
    Си Цзиньпин       (TASS Russian source)      → Person id 'P-892'
    Hsi Chin-p'ing    (older English archive)    → Person id 'P-1024'

Each is a separate node in the OSINTGraph. Centrality, k-core, faction
membership — everything network-derived — is fragmented across these
duplicates and produces garbage scores.

Resolver responsibilities
-------------------------
1. Fuzzy match queries to canonical persons (built on PR #1.5 utilities)
2. Disambiguate ambiguous matches using role context ("Foreign Minister
   Wang" → Wang Yi, not Wang Huning)
3. Use graph-neighbor overlap as additional evidence when fuzzy match
   is borderline
4. Bulk find merge candidates across an incoming person list
5. Apply approved merges to the OSINTGraph: rewrite edges, preserve
   surface strings as aliases on the canonical person
6. Calibrate threshold against ground-truth pairs so the analyst can
   tune precision vs recall on their actual data

Out of scope (intentional)
--------------------------
- Active learning loops
- ML-based matching (transformer embeddings, BERT-NER, etc.)
- External knowledge-base lookups (Wikipedia, Wikidata)
- Cross-graph merging across multiple OSINTGraph instances
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from kpvs.persons import Person, Alias, RoleAssignment
from kpvs.name_matching import match_score, normalize

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class ResolveResult:
    """Output of a single-query resolution.

    Attributes
    ----------
    person          : the canonical Person matched
    score           : final confidence ∈ [0, 1] after all boosts
    name_score      : raw fuzzy name match score before boosts
    matched_via     : the alias text or primary name that matched
    role_context_match : True if role hint aligned with this person's role
    graph_evidence  : True if graph neighbors supported this match
    rejected        : list[(person_id, score)] of also-considered candidates
                      whose final score was lower
    """
    person: Person
    score: float
    name_score: float
    matched_via: str
    role_context_match: bool = False
    graph_evidence: bool = False
    rejected: list = field(default_factory=list)


@dataclass
class MergeCandidate:
    """Proposed merge of an incoming Person into a canonical Person.

    Attributes
    ----------
    incoming_id     : the duplicate person's ID (to be merged away)
    incoming_name   : surface string for analyst review
    canonical_id    : the canonical Person to merge into
    canonical_name  : canonical's display name
    score           : final confidence after all boosts
    evidence        : dict explaining what supported the match
                      {'name_score': 0.92, 'role_context': True, ...}
    """
    incoming_id: str
    incoming_name: str
    canonical_id: str
    canonical_name: str
    score: float
    evidence: dict = field(default_factory=dict)


@dataclass
class CalibrationReport:
    """Result of calibrating threshold against ground-truth pairs."""
    n_pairs: int
    threshold_table: list  # list of dicts with thresh/precision/recall/f1
    best_f1_threshold: float
    best_f1: float


# ─────────────────────────────────────────────────────────────────────────
# EntityResolver
# ─────────────────────────────────────────────────────────────────────────
class EntityResolver:
    """Identity resolution against a canonical person population.

    Parameters
    ----------
    population        : dict[person_id, Person] of canonical persons
    role_assignments  : list[RoleAssignment] (optional, enables role-context
                        disambiguation)
    roles             : dict[role_id, role_object] where role_object has
                        .title and .institution attributes (optional)
    graph             : OSINTGraph (optional, enables graph-evidence boost)
    threshold         : base score threshold for a match (default 0.85)
    role_context_boost: how much the score is increased when role context
                        aligns with the candidate's role (default 0.10)
    graph_evidence_boost : additive boost when graph neighbors overlap
                        (default 0.05)
    """

    def __init__(self,
                 population: dict,
                 role_assignments: Optional[list] = None,
                 roles: Optional[dict] = None,
                 graph=None,
                 threshold: float = 0.85,
                 role_context_boost: float = 0.10,
                 graph_evidence_boost: float = 0.05):
        if not 0 < threshold <= 1:
            raise ValueError(
                f"threshold must be in (0, 1]; got {threshold}")

        self.population = population
        self.role_assignments = role_assignments or []
        self.roles = roles or {}
        self.graph = graph
        self.threshold = threshold
        self.role_context_boost = role_context_boost
        self.graph_evidence_boost = graph_evidence_boost

        # Precompute person → roles index for fast role-context lookup
        self._person_roles_idx: dict = {}
        for a in self.role_assignments:
            self._person_roles_idx.setdefault(
                a.person_id, []).append(a.role_id)

    # ── Single-query resolution ─────────────────────────────────────────
    def resolve(self,
                query: str,
                role_hint: Optional[str] = None,
                role_id: Optional[str] = None,
                institution: Optional[str] = None) -> Optional[ResolveResult]:
        """Resolve a query string to a canonical Person.

        Returns None if no candidate exceeds threshold.

        Parameters
        ----------
        query        : the lookup string (any script, any romanization)
        role_hint    : free-text role description ("foreign minister",
                       "premier", "general secretary"). Fuzzy-matched
                       against candidates' role titles.
        role_id      : exact role ID ("CN-PB-FOREIGN"). Highest-precision
                       hint — direct lookup of who's in this role.
        institution  : institution name ("CCP Central Foreign Affairs
                       Commission"). Fuzzy-matched against role
                       institution field.
        """
        if not query:
            return None

        # Score every candidate by name
        scored = []
        for pid, person in self.population.items():
            name_score = 0.0
            matched_text = None
            for text in person.all_names():
                s = match_score(query, text)
                if s > name_score:
                    name_score = s
                    matched_text = text
            scored.append((pid, person, name_score, matched_text))

        # Sort by name score descending
        scored.sort(key=lambda x: -x[2])

        # Apply role-context boost where applicable
        boosted = []
        for pid, person, name_score, matched_text in scored:
            ctx_match = self._role_context_matches(
                pid, role_hint, role_id, institution)
            graph_match = self._graph_evidence_supports(
                query, pid)

            final = name_score
            if ctx_match:
                final = min(1.0, final + self.role_context_boost)
            if graph_match:
                final = min(1.0, final + self.graph_evidence_boost)
            boosted.append({
                "pid": pid,
                "person": person,
                "name_score": name_score,
                "final_score": final,
                "matched_via": matched_text,
                "role_context": ctx_match,
                "graph_evidence": graph_match,
            })

        # Re-sort by final score
        boosted.sort(key=lambda x: -x["final_score"])

        if not boosted or boosted[0]["final_score"] < self.threshold:
            return None

        winner = boosted[0]
        rejected = [(b["pid"], b["final_score"])
                    for b in boosted[1:6]
                    if b["final_score"] >= self.threshold * 0.7]

        return ResolveResult(
            person=winner["person"],
            score=winner["final_score"],
            name_score=winner["name_score"],
            matched_via=winner["matched_via"] or query,
            role_context_match=winner["role_context"],
            graph_evidence=winner["graph_evidence"],
            rejected=rejected,
        )

    # ── Role-context matching ────────────────────────────────────────────
    def _role_context_matches(self, person_id: str,
                              role_hint: Optional[str],
                              role_id: Optional[str],
                              institution: Optional[str]) -> bool:
        """Decide whether the role hints align with the person's roles."""
        if not (role_hint or role_id or institution):
            return False

        person_role_ids = self._person_roles_idx.get(person_id, [])
        if not person_role_ids:
            return False

        # Direct role_id match — highest precision
        if role_id and role_id in person_role_ids:
            return True

        # Fuzzy match against role title or institution
        for rid in person_role_ids:
            role = self.roles.get(rid)
            if role is None:
                continue
            title = getattr(role, "title", "")
            inst = getattr(role, "institution", "")

            if role_hint:
                if title and self._tokens_contained(role_hint, title):
                    return True
                if inst and self._tokens_contained(role_hint, inst):
                    return True
            if institution:
                if inst and self._tokens_contained(institution, inst):
                    return True
                if title and self._tokens_contained(institution, title):
                    return True

        return False

    @staticmethod
    def _tokens_contained(hint: str, text: str) -> bool:
        """True if all non-trivial tokens of hint appear in text.

        Right semantic for role-context matching: the hint is typically
        a short description ('foreign affairs', 'general secretary')
        that should appear within the longer role title or institution.
        """
        STOPWORDS = {"of", "the", "a", "an", "and", "for", "to", "in",
                     "on", "at", "by", "with"}
        hint_tokens = {t for t in normalize(hint).split()
                       if t and t not in STOPWORDS}
        text_tokens = {t for t in normalize(text).split() if t}
        if not hint_tokens:
            return False
        return hint_tokens.issubset(text_tokens)

    # ── Graph-evidence support ───────────────────────────────────────────
    def _graph_evidence_supports(self, query: str, person_id: str) -> bool:
        """Heuristic: if the query string itself appears as a node in the
        graph and shares neighbors with the candidate, that's evidence
        the two refer to the same individual.

        Conservative: only fires when query exists as a graph node AND
        neighbor overlap is non-trivial (≥ 1 shared neighbor).
        """
        if self.graph is None:
            return False

        # Check if the normalized query matches a graph node ID
        # (graphs typically use the same person_id format as Population,
        # but the analyst may also use surface strings as node IDs)
        norm_q = normalize(query)
        for node_id in self.graph.person_ids:
            if normalize(node_id) == norm_q:
                # Compare neighbors
                q_neighbors = {n[0] for n in self.graph.neighbors(node_id)}
                p_neighbors = {n[0] for n in self.graph.neighbors(person_id)}
                if q_neighbors and p_neighbors and (q_neighbors & p_neighbors):
                    return True
                break

        return False

    # ── Bulk merge-candidate generation ──────────────────────────────────
    def find_merge_candidates(self,
                               query_persons: list,
                               threshold: Optional[float] = None,
                               include_role_context: bool = True
                               ) -> list:
        """For each incoming person, find the best canonical match.

        Returns a list of MergeCandidate objects sorted by score descending.
        Items where best score < threshold are excluded.

        Parameters
        ----------
        query_persons        : list[Person] of incoming persons (potential dupes)
        threshold            : override for self.threshold
        include_role_context : when True, use the incoming person's
                                assignments to derive role hints
        """
        thresh = threshold if threshold is not None else self.threshold
        candidates = []

        for inc in query_persons:
            if inc.id in self.population:
                # Same id, skip — analyst should explicitly indicate duplicate
                continue

            # Try resolving the incoming person's primary name
            best = None
            for query_text in inc.all_names():
                role_hint = None
                if include_role_context:
                    inc_roles = [a.role_id for a in self.role_assignments
                                  if a.person_id == inc.id]
                    if inc_roles:
                        first_role = self.roles.get(inc_roles[0])
                        if first_role:
                            role_hint = getattr(first_role, "title", None)

                result = self.resolve(query_text, role_hint=role_hint)
                if result is None:
                    continue
                if best is None or result.score > best.score:
                    best = result
                    best_query = query_text

            if best is None or best.score < thresh:
                continue

            evidence = {
                "name_score": best.name_score,
                "role_context": best.role_context_match,
                "graph_evidence": best.graph_evidence,
                "matched_query": best_query,
                "matched_via_alias": best.matched_via,
            }
            candidates.append(MergeCandidate(
                incoming_id=inc.id,
                incoming_name=inc.name,
                canonical_id=best.person.id,
                canonical_name=best.person.name,
                score=best.score,
                evidence=evidence,
            ))

        candidates.sort(key=lambda c: -c.score)
        return candidates

    # ── Apply merges ─────────────────────────────────────────────────────
    def merge(self,
              canonical_id: str,
              duplicate_id: str,
              duplicate_person: Optional[Person] = None,
              merge_source: str = "entity-resolver") -> Person:
        """Merge a duplicate Person into a canonical Person.

        Updates the canonical Person in self.population:
        - Adds the duplicate's name and aliases as new Aliases on canonical
        - Preserves provenance via Alias.source

        Parameters
        ----------
        canonical_id      : ID of canonical (kept) person
        duplicate_id      : ID of duplicate (merged-away) person
        duplicate_person  : optional Person object for the duplicate. If
                            not provided, looked up in self.population.
        merge_source      : provenance string for the new aliases

        Returns the updated canonical Person.
        """
        canonical = self.population.get(canonical_id)
        if canonical is None:
            raise KeyError(f"Canonical person {canonical_id!r} not in population")

        if duplicate_person is None:
            duplicate_person = self.population.get(duplicate_id)
            if duplicate_person is None:
                raise KeyError(
                    f"Duplicate person {duplicate_id!r} not in population")

        # Add duplicate's primary name as alias if not already present
        existing_alias_texts = {a.text for a in canonical.aliases}
        existing_alias_texts.add(canonical.name)
        if canonical.name_native:
            existing_alias_texts.add(canonical.name_native)

        if duplicate_person.name and duplicate_person.name not in existing_alias_texts:
            canonical.aliases.append(Alias(
                text=duplicate_person.name,
                source=merge_source,
                notes=f"merged from {duplicate_id}",
            ))
            existing_alias_texts.add(duplicate_person.name)

        if duplicate_person.name_native and duplicate_person.name_native not in existing_alias_texts:
            canonical.aliases.append(Alias(
                text=duplicate_person.name_native,
                source=merge_source,
                notes=f"native-script from {duplicate_id}",
            ))
            existing_alias_texts.add(duplicate_person.name_native)

        # Carry over duplicate's existing aliases
        for a in duplicate_person.aliases:
            if a.text not in existing_alias_texts:
                canonical.aliases.append(a)
                existing_alias_texts.add(a.text)

        # Remove duplicate from population
        if duplicate_id in self.population:
            del self.population[duplicate_id]

        return canonical

    # ── Bulk graph deduplication ─────────────────────────────────────────
    def deduplicate_graph(self,
                          graph,
                          merges: list,
                          merge_source: str = "entity-resolver"):
        """Apply a list of (canonical_id, duplicate_id) merges to a graph.

        Returns a new OSINTGraph object with:
        - Duplicate person nodes removed
        - Edges rewritten so duplicate references point to canonical
        - Duplicate edges (same source/target after rewrite) deduplicated,
          keeping the highest weight
        - person_to_orgs and role_to_org rewritten
        - Self-loops created by rewriting are removed

        The original graph is NOT mutated. Returns a new graph.

        Parameters
        ----------
        graph         : OSINTGraph to deduplicate
        merges        : list of (canonical_id, duplicate_id) tuples
                        OR list of MergeCandidate objects
        merge_source  : provenance for new aliases on canonical persons
        """
        from kpvs.osint_graph import OSINTGraph, GraphEdge

        # Normalize merges to a {duplicate_id: canonical_id} dict
        rewrite_map = {}
        for m in merges:
            if isinstance(m, MergeCandidate):
                rewrite_map[m.incoming_id] = m.canonical_id
            elif isinstance(m, (tuple, list)) and len(m) == 2:
                canonical_id, duplicate_id = m
                rewrite_map[duplicate_id] = canonical_id
            else:
                raise TypeError(
                    "merges entries must be MergeCandidate or (canonical, duplicate) tuple")

        def rewrite(node_id):
            return rewrite_map.get(node_id, node_id)

        # Build new graph
        new_g = OSINTGraph(country=graph.country)
        new_g.person_ids = {rewrite(p) for p in graph.person_ids
                             if p not in rewrite_map}
        # Preserve canonical IDs that may have been duplicates of others
        new_g.person_ids.update(rewrite_map.values())
        new_g.org_ids = set(graph.org_ids)

        # Rewrite edges, deduplicating by (source, target, edge_type)
        seen_edges: dict = {}
        for e in graph.edges:
            new_src = rewrite(e.source) if e.source_type == "person" else e.source
            new_tgt = rewrite(e.target) if e.target_type == "person" else e.target

            if new_src == new_tgt:
                # Self-loop created by merge — skip
                continue

            key = (new_src, new_tgt, e.edge_type)
            if key in seen_edges:
                # Keep higher-weight version (None treated as low)
                existing = seen_edges[key]
                ew = e.weight if e.weight is not None else 0.0
                xw = existing.weight if existing.weight is not None else 0.0
                if ew > xw:
                    seen_edges[key] = GraphEdge(
                        source=new_src, target=new_tgt,
                        source_type=e.source_type, target_type=e.target_type,
                        weight=e.weight, edge_type=e.edge_type,
                        bidirectional=e.bidirectional,
                        source_ref=e.source_ref,
                        confidence=e.confidence,
                        notes=e.notes,
                    )
            else:
                seen_edges[key] = GraphEdge(
                    source=new_src, target=new_tgt,
                    source_type=e.source_type, target_type=e.target_type,
                    weight=e.weight, edge_type=e.edge_type,
                    bidirectional=e.bidirectional,
                    source_ref=e.source_ref,
                    confidence=e.confidence,
                    notes=e.notes,
                )

        new_g.edges = list(seen_edges.values())

        # Rewrite person_to_orgs
        for pid, orgs in graph.person_to_orgs.items():
            new_pid = rewrite(pid)
            new_g.person_to_orgs.setdefault(new_pid, set()).update(orgs)

        # Role_to_org carries over unchanged
        new_g.role_to_org = dict(graph.role_to_org)

        # Apply merges to population aliases
        for dup_id, canon_id in rewrite_map.items():
            try:
                self.merge(canon_id, dup_id, merge_source=merge_source)
            except KeyError:
                # Duplicate not in resolver's population — skip alias merge
                pass

        return new_g

    # ── Calibration against ground truth ─────────────────────────────────
    def calibrate(self,
                  ground_truth: list,
                  thresholds: Optional[list] = None) -> CalibrationReport:
        """Compute precision/recall/F1 across thresholds against a
        ground-truth set.

        Parameters
        ----------
        ground_truth : list of (query_string, expected_canonical_id) tuples.
                       expected_canonical_id can be None to indicate
                       "this query should NOT match anyone."
        thresholds   : list of thresholds to evaluate. Default: 0.5 to 0.99
                       in 0.05 steps.

        Returns
        -------
        CalibrationReport with per-threshold metrics.
        """
        if thresholds is None:
            thresholds = [round(0.50 + 0.05 * i, 2) for i in range(11)]

        table = []
        for t in thresholds:
            # Save and override threshold for this evaluation
            saved = self.threshold
            self.threshold = t

            tp = fp = fn = tn = 0
            for query, expected_id in ground_truth:
                result = self.resolve(query)
                got_id = result.person.id if result is not None else None
                if expected_id is None:
                    if got_id is None:
                        tn += 1
                    else:
                        fp += 1
                else:
                    if got_id == expected_id:
                        tp += 1
                    elif got_id is None:
                        fn += 1
                    else:
                        fp += 1  # wrong match

            self.threshold = saved

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall / (precision + recall)
                  if (precision + recall) > 0 else 0.0)

            table.append({
                "threshold": t,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            })

        best = max(table, key=lambda r: r["f1"])
        return CalibrationReport(
            n_pairs=len(ground_truth),
            threshold_table=table,
            best_f1_threshold=best["threshold"],
            best_f1=best["f1"],
        )
