"""
kpvs — Key Person Vulnerability Simulator
==========================================
MTS Research Programme · Working Paper 5 · Robert J. Green (2026)

Public API
----------
    from kpvs import Organization, Role, KPVSimulator, BenchOptimizer
    from kpvs.reporting import ConsoleReporter, JSONReporter
    from kpvs.examples import build_rare_earth_org, build_nuclear_programme_org
"""

from .models    import Organization, Role
from .simulator import KPVSimulator, SimulationResult
from .optimizer import BenchOptimizer, OptimizationResult

__version__  = "1.0.0"
__author__   = "Robert J. Green"
__email__    = "robert@rjgreenresearch.org"
__license__  = "Apache-2.0"
__citation__ = (
    "Green, R.J. (2026). 'The Irreplaceable Node: Key Person Concentration "
    "as a Compound National Security Vulnerability.' "
    "MTS Working Paper 5. SSRN: ssrn.com/author=10825096"
)

__all__ = [
    "Organization", "Role",
    "KPVSimulator", "SimulationResult",
    "BenchOptimizer", "OptimizationResult",
]
