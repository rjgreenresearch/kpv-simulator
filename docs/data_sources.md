# Data Sources — KPVS

All KPCI component estimates in the built-in example organisations are
derived from publicly available sources. No classified materials were consulted.

## KPCI Component Calibration Basis

### Substitution Timeline (ST)

| ST Value | Empirical Basis |
|----------|----------------|
| 4 (72+ mo) | JASON (2009) JSR-09-334: nuclear warhead design physicist succession estimate; DoD IG DODIG-2021-089: acquisition PM tacit knowledge retention studies |
| 3 (30 mo)  | GAO-20-262: defence PM transitions; rare earth process chemistry career trajectory data from ACS member surveys |
| 2 (12 mo)  | Standard executive search data (Spencer Stuart, Korn Ferry CEO succession benchmarks) |
| 1 (5 mo)   | SHRM succession planning benchmarks for technical managerial roles |
| 0 (2 mo)   | SHRM benchmarks for well-documented, process-driven roles |

### Documentation Ratio (DR)

| DR Value | Empirical Basis |
|----------|----------------|
| 4 (<10% documented) | JASON (2009) on stockpile stewardship tacit knowledge; Polanyi (1966) tacit knowledge theory; weapons design oral history programme assessments |
| 3 (10-40%) | DOE programme documentation audits (GAO-21-xxx series); pharmaceutical process chemistry SOPs vs. experimental tacit content |
| 2 (40-70%) | Standard ISO 9001 process documentation coverage in manufacturing |
| 1 (70-90%) | Well-managed acquisition programmes with formal knowledge management |
| 0 (>90%)   | Fully procedurised roles (finance, HR, standard operations) |

### Adversarial Observability (AO)

| AO Value | Empirical Basis |
|----------|----------------|
| 4 (publicly documented) | CEO/Lab Director/Programme Executive — public record; Senate testimony; press releases |
| 3 (high)  | Senior scientists with publication records; programme managers named in DoD budget exhibits |
| 2 (moderate) | Mid-level technical experts; conference presenters; patent filers |
| 1 (low)   | Operational staff; internally visible but not externally profiled |
| 0 (effectively anonymous) | Administrative, support, and procedurised roles |

## Sources by Domain

### Nuclear Stockpile Stewardship
- JASON Advisory Group. 2009. "The United States Nuclear Weapons Program: The Role of the Laboratories." JSR-09-334 (unclassified).
- Rhodes, R. 2007. Arsenals of Folly. Alfred A. Knopf.
- National Nuclear Security Administration (NNSA). Annual Stockpile Stewardship and Management Plan (unclassified summary).

### Rare Earth Processing
- Green, R.J. 2026a. "Mapping Critical Supply Chain Dependencies." SSRN doi.org/10.2139/ssrn.6454618.
- USGS. 2025. Mineral Commodity Summaries 2025.
- IEA. 2025. Critical Minerals Data Explorer.
- DOJ. 2020. United States v. Zheng (Ames Laboratory Thousand Talents case).

### Defence Acquisition Programme Management
- GAO. 2020. GAO-20-262: Defence Acquisitions — Programme Manager Tenures.
- DoD IG. 2021. DODIG-2021-089: Assessment of Acquisition Workforce Management.
- Defense Acquisition University (DAU) PM career path data.

### Pharmaceutical KSM Synthesis
- Green, R.J. 2026a. SSRN 6454618, Section 3.3 (pharmaceutical API).
- BARDA/HHS. Continuus Pharmaceuticals contract data (public).
- APIIC. 2024. "A Bold Goal: Reshoring 25% of Small Molecule API."

### Adversarial Exploitation
- U.S. Senate PSI. 2019. "Threats to the U.S. Research Enterprise: China's Talent Recruitment Plans."
- FBI. 2022. "China: The Risk to Academia."
- DOJ Thousand Talents prosecutions: United States v. Lieber (2022); United States v. Zheng (2019); United States v. Ye (2020).

### Cascade Failure Probability Model
The Documentation Ratio × 0.70 cascade failure probability formula is derived from:
- Reason, J. 1990. Human Error. Cambridge University Press (Swiss cheese model).
- Perrow, C. 1984. Normal Accidents. Basic Books (tight coupling / complex interaction).
- Bench depth reduction factor (0.40 per unit) calibrated against SHRM succession readiness benchmarks.

## Canonical Run Parameters

| Parameter | Value |
|-----------|-------|
| Random seed | 20260501 |
| N iterations | 10,000 |
| Targeting accuracy | 0.85 |
| Default n_losses | 20% of org size |
| Max bench per role | 5 |

Cite as: `KPVS v1.0.0, run_YYYYMMDD_HHMMSS, seed=20260501`
