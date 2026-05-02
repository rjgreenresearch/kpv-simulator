"""
kpvs/intelligence/org_loader.py
================================
Loads intelligence organization files and runs cross-org
comparative analysis — the core of the Case 4 capability.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from kpvs.models import Organization

logger = logging.getLogger(__name__)

# Paths relative to project root
_HERE = Path(__file__).parent.parent.parent
EXAMPLES_DIR = _HERE / "examples"
FIVE_EYES_DIR = EXAMPLES_DIR / "five_eyes"
ADVERSARIAL_DIR = EXAMPLES_DIR / "adversarial"

# Registry of all known intelligence org files
ORG_REGISTRY = {
    # U.S.
    "us_nsa": EXAMPLES_DIR / "us_national_security_architecture.json",
    # Five Eyes
    "uk":  FIVE_EYES_DIR / "uk_national_security.json",
    "ca":  FIVE_EYES_DIR / "canada_national_security.json",
    "au":  FIVE_EYES_DIR / "australia_national_security.json",
    "nz":  FIVE_EYES_DIR / "new_zealand_national_security.json",
    # Adversarial (PASS Act / NDAA designated)
    "cn":  ADVERSARIAL_DIR / "china_strategic_leadership.json",
    "ru":  ADVERSARIAL_DIR / "russia_strategic_leadership.json",
    "ir":  ADVERSARIAL_DIR / "iran_strategic_leadership.json",
    "kp":  ADVERSARIAL_DIR / "north_korea_strategic_leadership.json",
    # MTS sector examples
    "rare_earth": EXAMPLES_DIR / "rare_earth_org.json",
}

ORG_SETS = {
    "five_eyes":    ["us_nsa", "uk", "ca", "au", "nz"],
    "adversarial":  ["cn", "ru", "ir", "kp"],
    "all_intel":    ["us_nsa", "uk", "ca", "au", "nz", "cn", "ru", "ir", "kp"],
    "us_and_china": ["us_nsa", "cn"],
}


def load_org(key_or_path: str) -> Organization:
    """
    Load an organization by registry key or file path.

    Parameters
    ----------
    key_or_path : str
        Either a registry key (e.g. 'us_nsa', 'cn') or
        a path to a JSON file.
    """
    if key_or_path in ORG_REGISTRY:
        path = ORG_REGISTRY[key_or_path]
    else:
        path = Path(key_or_path)

    if not path.exists():
        raise FileNotFoundError(f"Organization file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    org = Organization.from_dict(data)

    # Flag adversarial orgs for AO inversion in reporting
    org._adversarial = data.get("adversarial_org", False)
    org._ao_note     = data.get("ao_note", "")

    logger.info("Loaded org '%s' (adversarial=%s)", org.name, org._adversarial)
    return org


def load_org_set(set_name: str) -> list[Organization]:
    """Load all organizations in a named set."""
    if set_name not in ORG_SETS:
        raise ValueError(
            f"Unknown org set '{set_name}'. "
            f"Available: {', '.join(ORG_SETS.keys())}"
        )
    keys = ORG_SETS[set_name]
    orgs = []
    for key in keys:
        try:
            orgs.append(load_org(key))
        except FileNotFoundError as e:
            logger.warning("Skipping missing org '%s': %s", key, e)
    return orgs


def available_orgs() -> dict:
    """Return registry keys and file existence status."""
    return {
        k: {"path": str(v), "exists": v.exists()}
        for k, v in ORG_REGISTRY.items()
    }


def available_org_sets() -> dict:
    return {k: v for k, v in ORG_SETS.items()}
