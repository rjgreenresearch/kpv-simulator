"""
kpvs/persons.py — Person-centric layer for KPVS
================================================
Extends the role-centric KPV framework (Green, MTS WP-5) with a person
layer derived from OSINT graph data on adversary leadership networks.

Architecture
------------
The existing Role model captures intrinsic structural fragility via
KPCI = ST + DR + AO. This module adds two new objects WITHOUT modifying
that model:

    Person          — an individual occupying one or more roles, with
                      OSINT-derived attributes (tacit knowledge, network
                      centrality, tenure, substitutes).

    RoleAssignment  — the link between a Person and a Role, with capacity
                      and provenance metadata.

Effective KPCI is then derived (in kpvs.effective_kpci) as a function
of (Role, Person, Assignment) — never stored, always recomputed. This
preserves the published role-level methodology (peer review, MTS WP-5)
while enabling person-centric scenarios.

Multi-hat coupling
------------------
A single Person can hold multiple RoleAssignments. When the simulator
removes a Person, ALL their assignments fail simultaneously. This models
decapitation cascades that role-only simulators miss (Putin holding
President + Security Council Chair + de facto roles; Xi holding General
Secretary + State President + CMC Chair).
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


@dataclass
class Person:
    """An individual leader in an adversary organization.

    Attributes
    ----------
    id              : stable identifier (e.g. 'P-CN-00001234'). Required to
                      survive entity-resolution across language sources.
    name            : display name (romanized English convention)
    name_native     : original-script name (Chinese, Cyrillic, Persian, Korean)
    aliases         : alternate transliterations / known aliases
    country         : ISO-2 code (CN, RU, IR, KP)
    birth_year      : optional, used for age-related succession friction

    OSINT-derived continuity attributes:
    tacit_knowledge      : TK ∈ [0, 4]. Concentration of undocumented
                           operational knowledge. Derived from tenure ×
                           multi-hat exposure × event-frequency.
    network_integration  : CNI ∈ [0, 4]. Structural embeddedness. Derived
                           from k-core position, betweenness centrality,
                           and brokerage role across factions.
    tenure_months        : raw months in current role-set. Used for
                           learning-curve dynamics in simulator (a brand-
                           new occupant has different KPCI dynamics than
                           a 20-year incumbent even at identical CNI).
    substitutes          : count of plausible replacements in the
                           formal/informal succession pool. Used to
                           compute replacement friction.

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
    substitutes: int = 1  # default to 1 to avoid log(0); means "no info"

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

    # ── Derived properties ────────────────────────────────────────────────
    @property
    def person_premium(self) -> float:
        """Person-level premium added to a role's structural KPCI.

        premium = α·TK + β·CNI − γ·log(substitutes + 1)

        Default coefficients tuned so a maximally-embedded irreplaceable
        person adds roughly +3 to KPCI (saturating at the Tier-1 boundary
        for a borderline-Tier-2 role).

        See kpvs.effective_kpci for the full derivation.
        """
        import math
        ALPHA, BETA, GAMMA = 0.45, 0.45, 0.6
        return (ALPHA * self.tacit_knowledge
                + BETA * self.network_integration
                - GAMMA * math.log(self.substitutes + 1))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "name_native": self.name_native,
            "aliases": list(self.aliases),
            "birth_year": self.birth_year,
            "tacit_knowledge": self.tacit_knowledge,
            "network_integration": self.network_integration,
            "tenure_months": self.tenure_months,
            "substitutes": self.substitutes,
            "sources": list(self.sources),
            "last_updated": self.last_updated,
            "notes": self.notes,
        }


@dataclass
class RoleAssignment:
    """Link between a Person and a Role.

    A single Person can hold multiple RoleAssignments (multi-hat). A single
    Role typically has exactly one active RoleAssignment, but the schema
    permits collective bodies (e.g., shared command) via multiple.

    Attributes
    ----------
    person_id     : foreign key to Person.id
    role_id       : foreign key to Role.id
    capacity      : ∈ (0, 1]. Fraction of person's effective contribution
                    going to this role. Multi-hat persons typically have
                    capacity < 1 per role (e.g., Putin: 0.6 to President,
                    0.25 to Security Council, 0.15 to other). Capacities
                    across one person should sum to ~1.0 but the simulator
                    does not enforce this — the analyst encodes the
                    weighting.
    is_designated_successor : if True, this assignment indicates a
                              succession deputy. Reduces the role's
                              effective ST when active.
    start_date    : ISO-8601, optional
    sources       : provenance
    notes         : free-text
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


# ── Helpers for working with person-role networks ────────────────────────
def roles_held_by(person_id: str, assignments: list) -> list:
    """Return all role_ids assigned to a given person."""
    return [a.role_id for a in assignments if a.person_id == person_id]


def persons_in_role(role_id: str, assignments: list) -> list:
    """Return all person_ids assigned to a given role (usually 1)."""
    return [a.person_id for a in assignments if a.role_id == role_id]


def multi_hat_persons(assignments: list) -> dict:
    """Identify persons holding 2+ roles. Returns {person_id: [role_ids]}.

    Multi-hat persons drive the decapitation-cascade dynamic that distin-
    guishes person-centric scenarios from role-centric scenarios.
    """
    counts: dict = {}
    for a in assignments:
        counts.setdefault(a.person_id, []).append(a.role_id)
    return {pid: roles for pid, roles in counts.items() if len(roles) >= 2}
