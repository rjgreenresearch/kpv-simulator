# Methodology — KPVS

Full methodological documentation for the Key Person Vulnerability
Simulator. See also: Green, R.J. (2026), MTS Working Paper 5.

## 1. The KPV Framework

A **Key Person Vulnerability (KPV)** is a human capital condition meeting
three simultaneous criteria:

1. The individual's role value is substantially tacit — residing in personal
   judgment, relationships, and accumulated experience not transferable through
   documentation or training on any operationally relevant timeline.
2. Loss of the individual produces a capability gap persisting for **>24 months**
   under optimal succession conditions.
3. The individual's criticality is **externally observable** — identifiable by
   a sophisticated adversary analysing the institutional architecture.

This definition is structurally parallel to the MTS material supply chain
dependency framework (Paper 4): the same three conditions (single source,
no viable alternative within 24 months, adversarially observable) applied
to human capital rather than material inputs.

## 2. The KPCI

**KPCI = ST + DR + AO** (composite 0–12)

| Component | Name | What It Measures |
|-----------|------|-----------------|
| ST | Substitution Timeline | Time to restore 80% effectiveness under optimal succession |
| DR | Documentation Ratio | Fraction of role value that is tacit and undocumented |
| AO | Adversarial Observability | External identifiability as a critical node |

**Tier thresholds:**
- Tier-1 KPV: KPCI ≥ 10 (critical; capability discontinuity on loss)
- Tier-2 KPV: KPCI ≥ 7 (significant; standard succession inadequate)
- Manageable: KPCI ≥ 4 (standard succession planning adequate)
- Resilient: KPCI < 4 (institutional processes provide resilience)

## 3. Monte Carlo Scenarios

### 3.1 Random Attrition (Baseline)
Removes N roles uniformly at random. Models natural turnover with no
adversarial selection. Provides the null-hypothesis distribution against
which adversarial scenarios are tested.

### 3.2 Adversarial Targeting
Removes N roles with preferential targeting of high-KPCI roles.
On each selection step, the adversary selects the highest remaining
KPCI role with probability `targeting_accuracy` (default 0.85),
and a random role otherwise. Models a sophisticated but imperfect
adversarial intelligence assessment — consistent with Thousand Talents
targeting patterns documented by the Senate PSI (2019).

**Adversarial Gap** = Random Attrition mean% − Adversarial Targeting mean%
This is the exploitation premium: the additional capability degradation
a sophisticated adversary achieves vs. random attrition.

### 3.3 Cascade Failure
Simulates loss of one mission-critical role and its stochastic propagation
to dependent roles. Each dependent role fails with probability:

    p_fail = (DR / 4.0) × 0.70 × max(0.10, 1.0 − bench_depth × 0.40)

Rationale: poorly documented roles (high DR) are more vulnerable to
upstream capability loss; bench depth reduces cascade probability.

## 4. Capability Model

**Residual capability** after losing a set of roles:

- Lost role, bench_depth > 0: `weight × min(1.0, bench_depth × 0.75)`
- Lost role, bench_depth = 0: 0
- Dependent of lost mission-critical role (not itself lost): `weight × 0.50`
- All other roles: full `capability_weight`

## 5. Bench Investment Optimizer

Greedy marginal-improvement algorithm:

1. Compute baseline adversarial mean capability.
2. For each budget unit:
   a. For each role below max_bench, temporarily add one bench unit.
   b. Re-run adversarial scenario (reduced iterations for speed).
   c. Score: `improvement × (KPCI / 12.0 + 0.05)` — weights improvement
      toward high-KPCI roles.
   d. Commit unit to highest-scoring role.
3. Return final allocation and pre/post capability metrics.

This produces the human-capital equivalent of the CAS simulator's
optimal $1B portfolio allocation.

## 6. Restoration Timeline Estimation

    months = ST_MONTHS[round(ST)] × max(0.15, 1.0 − bench_depth × 0.35)

Where `ST_MONTHS = {0:2, 1:5, 2:12, 3:30, 4:72}`.
Bench depth reduces the restoration timeline proportionally (cap: 15% floor).

## 7. Limitations

- KPCI scores are analytical estimates requiring calibration with HR data
  and subject-matter expert review. The model provides relative rankings
  and scenario distributions, not point predictions.
- The cascade failure probability formula is parsimonious (2 parameters).
  Real cascade dynamics may involve more complex dependencies.
- The optimizer is greedy (not globally optimal). A genetic algorithm or
  MILP would find better allocations at greater computational cost.
- The capability model treats all capability as fungible within the
  weighting scheme. Interdependencies between roles are captured only
  through the explicit `critical_dependencies` graph.
