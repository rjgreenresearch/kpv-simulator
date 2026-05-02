"""
kpvs/models.py — Core data models for KPVS
============================================
Implements KPV theory: Green, R.J. (2026), MTS WP-5.

KPCI = ST + DR + AO  (each component [0, 4]; composite [0, 12])
Tier-1 KPV ≥ 10 | Tier-2 KPV ≥ 7 | Manageable ≥ 4 | Resilient < 4
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

TIER1 = 10.0
TIER2 = 7.0
MANAGEABLE = 4.0

# Substitution-Timeline category → median months to 80% effectiveness
ST_MONTHS = {0: 2, 1: 5, 2: 12, 3: 30, 4: 72}


def _validate_component(name: str, value: float) -> float:
    value = float(value)
    if not 0.0 <= value <= 4.0:
        raise ValueError(f"KPCI component '{name}' must be in [0,4]; got {value}.")
    return value


@dataclass
class Role:
    """A single node in the organizational network.

    Attributes
    ----------
    id                       : unique snake_case identifier
    title                    : display name
    substitution_timeline    : ST ∈ [0,4] — time to find & develop replacement
    documentation_ratio      : DR ∈ [0,4] — tacit-knowledge concentration
    adversarial_observability: AO ∈ [0,4] — external identifiability as target
    reports_to               : parent role id (None = root)
    critical_dependencies    : role ids this role enables
    capability_weight        : relative org-capability contribution (> 0)
    bench_depth              : identified successors in active development
    notes                    : free-text annotation
    kpci / tier              : derived, set by __post_init__
    """

    id: str
    title: str
    substitution_timeline: float
    documentation_ratio: float
    adversarial_observability: float

    reports_to: Optional[str] = None
    critical_dependencies: list = field(default_factory=list)
    capability_weight: float = 1.0
    bench_depth: int = 0
    notes: str = ""

    kpci: float = field(init=False, repr=False)
    tier: str   = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.substitution_timeline     = _validate_component(
            "substitution_timeline",    self.substitution_timeline)
        self.documentation_ratio       = _validate_component(
            "documentation_ratio",      self.documentation_ratio)
        self.adversarial_observability = _validate_component(
            "adversarial_observability", self.adversarial_observability)

        if self.capability_weight <= 0:
            raise ValueError(f"Role '{self.id}': capability_weight must be > 0.")
        if self.bench_depth < 0:
            raise ValueError(f"Role '{self.id}': bench_depth cannot be negative.")

        self.kpci = round(
            self.substitution_timeline +
            self.documentation_ratio   +
            self.adversarial_observability, 2)
        self.tier = self._classify()
        logger.debug("Role '%s': KPCI=%.1f (%s) bench=%d",
                     self.id, self.kpci, self.tier, self.bench_depth)

    def _classify(self) -> str:
        if self.kpci >= TIER1:      return "Tier-1 KPV"
        if self.kpci >= TIER2:      return "Tier-2 KPV"
        if self.kpci >= MANAGEABLE: return "Manageable"
        return "Resilient"

    @property
    def estimated_restoration_months(self) -> float:
        """Months to restore 80% capability; reduced by bench depth."""
        base = ST_MONTHS[min(4, int(round(self.substitution_timeline)))]
        return round(base * max(0.15, 1.0 - self.bench_depth * 0.35), 1)

    def to_dict(self) -> dict:
        return {
            "id":                        self.id,
            "title":                     self.title,
            "kpci":                      self.kpci,
            "tier":                      self.tier,
            "substitution_timeline":     self.substitution_timeline,
            "documentation_ratio":       self.documentation_ratio,
            "adversarial_observability": self.adversarial_observability,
            "bench_depth":               self.bench_depth,
            "capability_weight":         self.capability_weight,
            "estimated_restoration_months": self.estimated_restoration_months,
            "reports_to":               self.reports_to,
            "critical_dependencies":    self.critical_dependencies,
            "notes":                    self.notes,
        }


@dataclass
class Organization:
    """Full organizational network.

    Parameters
    ----------
    name                   : human-readable org name
    roles                  : dict[id → Role]
    mission_critical_roles : ids whose loss triggers cascade to dependents
    description            : optional annotation
    """

    name: str
    roles: dict
    mission_critical_roles: list
    description: str = ""

    def __post_init__(self) -> None:
        for mc in self.mission_critical_roles:
            if mc not in self.roles:
                raise ValueError(
                    f"mission_critical_roles references unknown role '{mc}'.")
        for r in self.roles.values():
            for dep in r.critical_dependencies:
                if dep not in self.roles:
                    raise ValueError(
                        f"Role '{r.id}' has dependency on unknown role '{dep}'.")
            if r.reports_to and r.reports_to not in self.roles:
                raise ValueError(
                    f"Role '{r.id}' reports_to unknown role '{r.reports_to}'.")
        logger.info("Organisation '%s': %d roles, %d mission-critical.",
                    self.name, len(self.roles), len(self.mission_critical_roles))

    @property
    def total_capability(self) -> float:
        return sum(r.capability_weight for r in self.roles.values())

    def get_role(self, role_id: str) -> Optional[Role]:
        return self.roles.get(role_id)

    def get_dependents(self, role_id: str) -> list:
        return [r for r in self.roles.values()
                if role_id in r.critical_dependencies]

    def get_subordinates(self, role_id: str) -> list:
        return [r for r in self.roles.values() if r.reports_to == role_id]

    def roles_by_kpci(self, descending: bool = True) -> list:
        return sorted(self.roles.values(),
                      key=lambda r: r.kpci, reverse=descending)

    def tier_summary(self) -> dict:
        counts = {"Tier-1 KPV": 0, "Tier-2 KPV": 0,
                  "Manageable": 0, "Resilient": 0}
        for r in self.roles.values():
            counts[r.tier] += 1
        return counts

    def to_dict(self) -> dict:
        return {
            "name":                   self.name,
            "description":            self.description,
            "mission_critical_roles": self.mission_critical_roles,
            "roles": [r.to_dict() for r in self.roles.values()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Organization":
        """Deserialise from a parsed JSON dict (see examples/ for schema)."""
        raw_roles = data.get("roles", [])
        if isinstance(raw_roles, dict):
            raw_roles = list(raw_roles.values())

        roles = {}
        for rd in raw_roles:
            r = Role(
                id                       = rd["id"],
                title                    = rd["title"],
                substitution_timeline    = float(rd["substitution_timeline"]),
                documentation_ratio      = float(rd["documentation_ratio"]),
                adversarial_observability= float(rd["adversarial_observability"]),
                reports_to               = rd.get("reports_to"),
                critical_dependencies    = rd.get("critical_dependencies", []),
                capability_weight        = float(rd.get("capability_weight", 1.0)),
                bench_depth              = int(rd.get("bench_depth", 0)),
                notes                    = rd.get("notes", ""),
            )
            roles[r.id] = r

        return cls(
            name                   = data["name"],
            roles                  = roles,
            mission_critical_roles = data.get("mission_critical_roles", []),
            description            = data.get("description", ""),
        )
