"""
kpvs/persons.py — Person-centric layer for KPVS
================================================
Extends the role-centric KPV framework (Green, MTS WP-5) with a person
layer derived from OSINT graph data on adversary leadership networks.

Architecture
------------
The existing Role model captures intrinsic structural fragility via
KPCI = ST + DR + AO. This module adds three new objects WITHOUT modifying
that model:

    Alias           — a structured name alternate with metadata (script,
                      romanization, source, confidence). Powers fuzzy
                      matching across multi-script OSINT sources.

    Person          — an individual occupying one or more roles, with
                      OSINT-derived attributes (tacit knowledge, network
                      centrality, tenure, substitutes) and a list of
                      aliases for cross-source resolution.

    RoleAssignment  — the link between a Person and a Role, with capacity
                      and provenance metadata.

Effective KPCI is then derived (in kpvs.effective_kpci) as a function
of (Role, Person, Assignment) — never stored, always recomputed.

Multi-hat coupling
------------------
A single Person can hold multiple RoleAssignments. When the simulator
removes a Person, ALL their assignments fail simultaneously.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── Person attribute bounds (mirror KPCI component scale) ────────────────
TK_MIN, TK_MAX = 0.0, 4.0   # Tacit Knowledge
CNI_MIN, CNI_MAX = 0.0, 4.0  # Critical Network Integration


def _validate_unit(name: str, value: float, lo: float, hi: float) -> float:
    value = float(value)
    if not lo <= value <= hi:
        raise ValueError(f"Person attribute '{name}' must be in [{lo},{hi}]; got {value}.")
    return value


# ─────────────────────────────────────────────────────────────────────────
# Alias dataclass
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class Alias:
    """A structured name alternate with provenance metadata.

    Used for fuzzy matching across multi-script OSINT sources where the
    same person appears under different transliterations, orderings, or
    honorific prefixes.

    Attributes
    ----------
    text         : the alias string itself (any script)
    script       : ISO 15924 code or shorthand
                   ('latn', 'hans', 'hant', 'cyrl', 'arab', 'hang')
    language     : ISO 639-1 code ('zh', 'ru', 'fa', 'ko', 'en', ...)
                   for the source language this alias was observed in
    romanization : transliteration scheme name when applicable
                   ('pinyin', 'wade-giles', 'bgn-pcgn', 'ala-lc',
                    'mccune-reischauer', 'revised', '')
    surname_first: True if cultural ordering puts surname first
                   (East Asian convention) — informs comparison order
    source       : provenance — where this alias was observed
                   ('OSINT-CN-2026-001', 'Xinhua-2024-03-15', etc.)
    confidence   : ∈ [0, 1] — confidence this alias actually refers to
                   the person. 1.0 for confirmed; lower for unverified
                   transliterations or partial matches.
    notes        : free-text analyst annotation
    """
    text: str
    script: str = "latn"
    language: str = ""
    romanization: str = ""
    surname_first: bool = False
    source: str = ""
    confidence: float = 1.0
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("Alias.text cannot be empty.")
        if not 0 <= self.confidence <= 1:
            raise ValueError(
                f"Alias.confidence must be in [0, 1]; got {self.confidence}.")

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "script": self.script,
            "language": self.language,
            "romanization": self.romanization,
            "surname_first": self.surname_first,
            "source": self.source,
            "confidence": self.confidence,
            "notes": self.notes,
        }


def _normalize_aliases(aliases: list) -> list:
    """Convert list[str | Alias | dict] → list[Alias].

    Backward compatibility: accept plain strings (legacy usage) and dicts
    (loaded from JSON) and promote them to Alias objects.
    """
    out = []
    for a in aliases:
        if isinstance(a, Alias):
            out.append(a)
        elif isinstance(a, str):
            out.append(Alias(text=a))
        elif isinstance(a, dict):
            out.append(Alias(**a))
        else:
            raise TypeError(
                f"Alias entry must be Alias, str, or dict; got {type(a).__name__}")
    return out


# ─────────────────────────────────────────────────────────────────────────
# Person dataclass
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class Person:
    """An individual leader in an adversary organization.

    Attributes
    ----------
    id              : stable identifier (e.g. 'P-CN-00001234')
    name            : display name (romanized English convention)
    country         : ISO-2 code (CN, RU, IR, KP)

    name_native     : original-script name (Chinese, Cyrillic, Persian, Korean)
    aliases         : list of Alias objects (auto-promoted from strings/dicts)
    birth_year      : optional, used for age-related succession friction

    OSINT-derived continuity attributes:
    tacit_knowledge      : TK ∈ [0, 4]
    network_integration  : CNI ∈ [0, 4]
    tenure_months        : raw months in current role-set
    substitutes          : count of plausible replacements

    Faction tags:
    factions        : list of faction tags this person is associated with
                      (e.g. ['zhejiang-faction', 'princeling']). Consumed
                      by Faction.member_tag resolution in faction-purge
                      scenarios. Multiple memberships allowed.

    Provenance:
    sources         : list of OSINT source URLs / IDs
    last_updated    : ISO-8601 date string of latest graph update
    notes           : free-text analyst annotation
    """

    id: str
    name: str
    country: str  # 'CN' | 'RU' | 'IR' | 'KP' | other ISO-2

    name_native: str = ""
    aliases: list = field(default_factory=list)
    birth_year: Optional[int] = None

    tacit_knowledge: float = 0.0
    network_integration: float = 0.0
    tenure_months: int = 0
    substitutes: int = 1

    factions: list = field(default_factory=list)

    sources: list = field(default_factory=list)
    last_updated: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        self.tacit_knowledge = _validate_unit(
            "tacit_knowledge", self.tacit_knowledge, TK_MIN, TK_MAX)
        self.network_integration = _validate_unit(
            "network_integration", self.network_integration, CNI_MIN, CNI_MAX)

        if self.tenure_months < 0:
            raise ValueError(
                f"Person '{self.id}': tenure_months must be ≥ 0; "
                f"got {self.tenure_months}.")

        if self.substitutes < 0:
            raise ValueError(
                f"Person '{self.id}': substitutes must be ≥ 0; "
                f"got {self.substitutes}.")

        if not self.country or len(self.country) != 2:
            raise ValueError(
                f"Person '{self.id}': country must be ISO-2 code; "
                f"got '{self.country}'.")

        # Promote string/dict aliases to Alias objects for consistency
        self.aliases = _normalize_aliases(self.aliases)

    # ── Derived properties ────────────────────────────────────────────────
    @property
    def person_premium(self) -> float:
        """Person-level premium added to a role's structural KPCI."""
        import math
        ALPHA, BETA, GAMMA = 0.45, 0.45, 0.6
        return (ALPHA * self.tacit_knowledge
                + BETA * self.network_integration
                - GAMMA * math.log(self.substitutes + 1))

    # ── Alias management ──────────────────────────────────────────────────
    def add_alias(self, text: str, **kwargs) -> Alias:
        """Add an alias to this person. Returns the created Alias."""
        alias = Alias(text=text, **kwargs)
        self.aliases.append(alias)
        return alias

    def all_names(self) -> list:
        """Return all known name forms: [primary, native?, *alias_texts]."""
        out = [self.name]
        if self.name_native:
            out.append(self.name_native)
        out.extend(a.text for a in self.aliases)
        return out

    def match(self, query: str, threshold: float = 0.85) -> Optional[tuple]:
        """Test whether a query string matches this person.

        Returns (score, matched_text) on success, None on failure.

        Uses the kpvs.name_matching utilities — diacritic stripping,
        transliteration variant generation, and fuzzy SequenceMatcher
        scoring across primary name, native-script name, and all aliases.
        """
        # Lazy import to avoid circular dependency
        from kpvs.name_matching import match_score

        best_score = 0.0
        best_text = None
        for text in self.all_names():
            score = match_score(query, text)
            if score > best_score:
                best_score = score
                best_text = text

        if best_score >= threshold:
            return (best_score, best_text)
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "name_native": self.name_native,
            "aliases": [a.to_dict() for a in self.aliases],
            "birth_year": self.birth_year,
            "tacit_knowledge": self.tacit_knowledge,
            "network_integration": self.network_integration,
            "tenure_months": self.tenure_months,
            "substitutes": self.substitutes,
            "factions": list(self.factions),
            "sources": list(self.sources),
            "last_updated": self.last_updated,
            "notes": self.notes,
        }


# ─────────────────────────────────────────────────────────────────────────
# RoleAssignment (unchanged from PR #1)
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class RoleAssignment:
    """Link between a Person and a Role.

    A single Person can hold multiple RoleAssignments (multi-hat). A single
    Role typically has exactly one active RoleAssignment, but the schema
    permits collective bodies (e.g., shared command) via multiple.
    """

    person_id: str
    role_id: str
    capacity: float = 1.0
    is_designated_successor: bool = False
    start_date: str = ""
    sources: list = field(default_factory=list)
    notes: str = ""

    def __post_init__(self) -> None:
        if not 0 < self.capacity <= 1:
            raise ValueError(
                f"RoleAssignment ({self.person_id} → {self.role_id}): "
                f"capacity must be in (0, 1]; got {self.capacity}.")

    def to_dict(self) -> dict:
        return {
            "person_id": self.person_id,
            "role_id": self.role_id,
            "capacity": self.capacity,
            "is_designated_successor": self.is_designated_successor,
            "start_date": self.start_date,
            "sources": list(self.sources),
            "notes": self.notes,
        }


# ── Helpers for working with person-role networks (unchanged) ───────────
def roles_held_by(person_id: str, assignments: list) -> list:
    """Return all role_ids assigned to a given person."""
    return [a.role_id for a in assignments if a.person_id == person_id]


def persons_in_role(role_id: str, assignments: list) -> list:
    """Return all person_ids assigned to a given role (usually 1)."""
    return [a.person_id for a in assignments if a.role_id == role_id]


def multi_hat_persons(assignments: list) -> dict:
    """Identify persons holding 2+ roles. Returns {person_id: [role_ids]}."""
    counts: dict = {}
    for a in assignments:
        counts.setdefault(a.person_id, []).append(a.role_id)
    return {pid: roles for pid, roles in counts.items() if len(roles) >= 2}
