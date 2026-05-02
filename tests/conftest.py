"""
tests/conftest.py
=================
Shared pytest fixtures for KPVS test suite.
All test organisations use fixed seeds for deterministic output.
"""

import pytest
from kpvs.models import Role, Organization
from kpvs.simulator import KPVSimulator
from kpvs.optimizer import BenchOptimizer
from kpvs.examples import (
    build_rare_earth_org,
    build_nuclear_programme_org,
    build_pharma_org,
)

TEST_SEED = 42


@pytest.fixture(scope="session")
def rare_earth_org() -> Organization:
    return build_rare_earth_org()


@pytest.fixture(scope="session")
def nuclear_org() -> Organization:
    return build_nuclear_programme_org()


@pytest.fixture(scope="session")
def pharma_org() -> Organization:
    return build_pharma_org()


@pytest.fixture
def minimal_org() -> Organization:
    """Smallest valid organisation: 3 roles, 1 mission-critical."""
    roles = {
        "root":  Role(id="root",  title="Director",
                      substitution_timeline=3.0, documentation_ratio=3.0,
                      adversarial_observability=3.0,
                      critical_dependencies=["worker"],
                      capability_weight=2.0, bench_depth=0),
        "worker": Role(id="worker", title="Key Technical Expert",
                       substitution_timeline=4.0, documentation_ratio=4.0,
                       adversarial_observability=4.0,
                       reports_to="root",
                       critical_dependencies=[],
                       capability_weight=3.0, bench_depth=0),
        "admin":  Role(id="admin",  title="Administrator",
                       substitution_timeline=0.5, documentation_ratio=0.5,
                       adversarial_observability=0.5,
                       reports_to="root",
                       critical_dependencies=[],
                       capability_weight=0.5, bench_depth=2),
    }
    return Organization(
        name="Minimal Test Org",
        roles=roles,
        mission_critical_roles=["worker"],
    )


@pytest.fixture
def minimal_sim(minimal_org) -> KPVSimulator:
    return KPVSimulator(minimal_org, seed=TEST_SEED)


@pytest.fixture
def rare_earth_sim(rare_earth_org) -> KPVSimulator:
    return KPVSimulator(rare_earth_org, seed=TEST_SEED)
