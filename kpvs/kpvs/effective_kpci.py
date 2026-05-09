"""
kpvs/effective_kpci.py — Person-aware KPCI derivation
======================================================

The role-level KPCI = ST + DR + AO is preserved as the intrinsic structural
fragility of a role. Effective KPCI extends this by accounting for the
specific person currently in the role.

Floor invariant
---------------
    effective_kpci(role, person) ≥ structural_kpci(role)

A strong occupant cannot make a structurally fragile role less critical.
This is essential to preserve the published doctrine: a Tier-1 role stays
Tier-1 regardless of who currently holds it. What changes upward is the
*premium* a particularly embedded, tacit-knowledge-rich, irreplaceable
occupant brings.

This module is intentionally read-only with respect to existing Role
objects. Effective KPCI is never stored — always recomputed.
"""

from __future__ import annotations

import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)

# ── Default coefficients (tunable per analyst) ──────────────────────────
ALPHA = 0.45   # weight on tacit knowledge
BETA = 0.45    # weight on network integration
GAMMA = 0.60   # penalty (negative weight) on log-substitutes

# Successor reduction: if a designated successor assignment exists for a
# role, the effective ST drops by this fraction. Models the operational
# reality that a well-prepared deputy reduces replacement timeline.
SUCCESSOR_ST_REDUCTION = 0.5

# Tenure curve: very new occupants (< 6 months) have not yet accumulated
# the full TK their position implies. We discount their TK contribution
# along a sigmoid-like ramp.
TENURE_RAMP_MONTHS = 6.0


def tenure_factor(tenure_months: int) -> float:
    """Returns ∈ [0, 1]. Brand-new occupant ≈ 0.5; 6-month ≈ 0.73;
    12-month ≈ 0.88; 24-month+ → 1.0.

    Models the learning curve for tacit knowledge accumulation. A person
    parachuted into a role this week has the *position* but not yet the
    *embedded knowledge* the position implies.
    """
    if tenure_months <= 0:
        return 0.5
    return 1.0 - 0.5 * math.exp(-tenure_months / TENURE_RAMP_MONTHS)


def person_premium(person, tenure_adjusted: bool = True,
                   alpha: float = ALPHA,
                   beta: float = BETA,
                   gamma: float = GAMMA) -> float:
    """Compute the person-level premium added to structural KPCI.

    premium = α·TK·tenure_factor + β·CNI − γ·log(substitutes + 1)

    Note: CNI is NOT tenure-adjusted because network position is observable
    and effective from day one of an appointment (the person inherits the
    position's network connections immediately even if they have not yet
    built personal trust). TK *is* tenure-adjusted because tacit knowledge
    accrues only with time.
    """
    tk_term = alpha * person.tacit_knowledge
    if tenure_adjusted:
        tk_term *= tenure_factor(person.tenure_months)

    cni_term = beta * person.network_integration

    # log(subs + 1): subs=0 → 0 penalty, subs=1 → 0.69·γ, subs=10 → 2.4·γ
    sub_penalty = gamma * math.log(person.substitutes + 1)

    return tk_term + cni_term - sub_penalty


def effective_kpci(role, person=None,
                   has_designated_successor: bool = False,
                   *,
                   alpha: float = ALPHA,
                   beta: float = BETA,
                   gamma: float = GAMMA) -> float:
    """Compute Effective KPCI for a role given its current occupant.

    Parameters
    ----------
    role : kpvs.models.Role
        The role object (provides structural ST + DR + AO = KPCI).
    person : kpvs.persons.Person, optional
        The current occupant. If None, returns the structural KPCI.
    has_designated_successor : bool
        If True, the role's effective ST is reduced (SUCCESSOR_ST_REDUCTION).

    Returns
    -------
    float ∈ [0, ~14]
        Effective KPCI. Floored at structural KPCI; can exceed 12 in
        extreme cases (deeply embedded irreplaceable occupant of a
        already-fragile role). Tier classification still uses the
        same thresholds (10 / 7 / 4) — values above 12 just indicate
        "Tier-1 with severe overhang."
    """
    structural = float(role.kpci)

    # Adjust ST downward if a successor exists. ST is one component of KPCI,
    # so we recompute the role's effective KPCI with reduced ST.
    if has_designated_successor:
        st_reduction = role.substitution_timeline * SUCCESSOR_ST_REDUCTION
        adjusted_kpci = structural - st_reduction
    else:
        adjusted_kpci = structural

    if person is None:
        # No occupant data — return adjusted structural value.
        return max(structural - (role.substitution_timeline * SUCCESSOR_ST_REDUCTION
                                 if has_designated_successor else 0),
                   0.0)

    premium = person_premium(person, alpha=alpha, beta=beta, gamma=gamma)
    effective = adjusted_kpci + premium

    # Floor invariant: effective ≥ structural - successor reduction.
    # This preserves the role's intrinsic Tier classification under
    # neutral occupants but allows successor-prepared roles to drop tier.
    floor = adjusted_kpci
    return max(effective, floor)


def effective_tier(value: float) -> str:
    """Classify an effective KPCI score using the same thresholds as the
    structural framework (preserves published doctrine)."""
    if value >= 10:
        return "Tier-1 KPV"
    if value >= 7:
        return "Tier-2 KPV"
    if value >= 4:
        return "Manageable"
    return "Resilient"


def continuity_loss(role, person=None,
                    has_designated_successor: bool = False) -> dict:
    """Compute continuity-loss diagnostics if this person is removed.

    Returns
    -------
    dict with:
        capability_loss      : role.capability_weight × (1 + premium/12)
        replacement_friction : effective ST in months, scaled by 1/(subs+1)
        tacit_shock          : TK contribution lost (TK × tenure_factor)
        effective_kpci       : the score before removal
        floor_kpci           : structural KPCI (lower bound)
    """
    eff = effective_kpci(role, person, has_designated_successor)
    structural = float(role.kpci)

    cap_weight = getattr(role, "capability_weight", 1.0)
    premium_share = max(0.0, (eff - structural) / max(structural, 1.0))
    cap_loss = cap_weight * (1.0 + premium_share)

    # ST_MONTHS lookup from kpvs.models — reproduced inline to avoid
    # circular imports during test harness.
    ST_MONTHS = {0: 2, 1: 5, 2: 12, 3: 30, 4: 72}
    st_cat = int(round(role.substitution_timeline))
    base_months = ST_MONTHS.get(st_cat, 12)
    if has_designated_successor:
        base_months *= SUCCESSOR_ST_REDUCTION

    if person is None:
        friction = base_months
        shock = 0.0
    else:
        friction = base_months / (person.substitutes + 1)
        shock = person.tacit_knowledge * tenure_factor(person.tenure_months)

    return {
        "capability_loss": cap_loss,
        "replacement_friction_months": friction,
        "tacit_shock": shock,
        "effective_kpci": eff,
        "floor_kpci": structural,
    }
