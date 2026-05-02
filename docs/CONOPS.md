# Concept of Operations
# Key Person Vulnerability Simulator (KPVS)

**Document ID:** KPVS-CONOPS-001  
**Version:** 1.2.0  
**Status:** Released  
**Date:** May 2026  
**Author:** Robert J. Green, MTS Research Programme  
**Classification:** Unclassified / Public Release

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Background and Strategic Context](#2-background-and-strategic-context)
3. [The Problem KPVS Solves](#3-the-problem-kpvs-solves)
4. [Operational Concept](#4-operational-concept)
5. [User Roles and Responsibilities](#5-user-roles-and-responsibilities)
6. [Operational Scenarios](#6-operational-scenarios)
7. [System Interfaces and Information Flows](#7-system-interfaces-and-information-flows)
8. [Operational Constraints and Limitations](#8-operational-constraints-and-limitations)
9. [Intelligence Community Application](#9-intelligence-community-application)
10. [Transition to Classified Deployment](#10-transition-to-classified-deployment)
11. [Measures of Effectiveness](#11-measures-of-effectiveness)
12. [Glossary](#12-glossary)

---

## 1. Purpose and Scope

### 1.1 Purpose

This Concept of Operations (CONOPS) describes how the Key Person Vulnerability
Simulator (KPVS) is used in practice — who uses it, in what contexts, for what
decisions, and with what expected outputs. It is intended for:

- **Policy analysts and intelligence professionals** evaluating whether KPVS
  is appropriate for a given assessment task
- **Organizational security officers** considering KPVS for internal resilience
  assessment
- **Research institution administrators** determining how to integrate KPVS
  into existing analytical workflows
- **Programme sponsors** at defence, intelligence, and academic institutions
  considering adoption or extension

This document does not describe how to install or operate the software. For
installation and CLI/API usage, see `docs/user_guide.md`. For the theoretical
basis of the KPCI framework, see MTS Working Paper 5.

### 1.2 Scope

KPVS operates in the unclassified domain using publicly available data.
Section 10 describes the pathway to classified deployment for intelligence
community applications where higher-fidelity data would significantly alter
findings. The open-source tool described in this document is appropriate for:

- Academic research and publication
- Policy analysis and Congressional briefing
- Allied coordination and resilience assessment
- Organizational self-assessment by critical sector entities
- Adversarial org structure analysis from open-source data

KPVS is **not** a personnel tracking system, a clearance adjudication tool,
or a replacement for classified intelligence assessments. It is an analytical
modelling framework that quantifies concentration risk from data the user
supplies.

---

## 2. Background and Strategic Context

### 2.1 The Compound Vulnerability Architecture

The Mutual Threshold Saturation (MTS) research programme documents a
compound vulnerability architecture across the United States national
security apparatus: the simultaneous concentration of critical national
capabilities in single sources — whether material (a sole rare earth processor),
institutional (a single regulatory pathway), or human (an irreplaceable
technical expert). The compound condition exists when multiple such
concentrations coexist, each exploitable independently and each amplifying
the fragility of the others.

The material dimension of this architecture is documented in MTS Paper 4:
1,637 discrete single-source dependencies across pharmaceutical, rare earth,
semiconductor, agricultural, energy, and defence sectors. KPVS addresses
the human capital dimension: the condition in which those material supply
chains, nuclear weapons programmes, diplomatic relationships, and defence
acquisition programmes depend on specific, identifiable, irreplaceable
individuals whose loss cannot be substituted on any operationally relevant
timeline.

### 2.2 The Adversarial Exploitation Precedent

The adversarial exploitation of key person vulnerabilities is not theoretical.
China's Thousand Talents Programme has systematically mapped and recruited
U.S. scientific and technical key persons since 2008. The Department of Justice
has documented over 1,000 active investigations. Prosecuted cases span rare
earth processing chemistry, pharmaceutical synthesis, nuclear engineering, and
semiconductor design — precisely the domains where the MTS programme documents
the highest material supply chain concentration.

The 2020 assassination of Iranian nuclear weapons programme chief Mohsen
Fakhrizadeh demonstrated that physical targeting of irreplaceable technical
nodes is a live operational doctrine for state actors in acute technology
competition. As of April 2026, the FBI is investigating a pattern of deaths
and disappearances among U.S. scientists connected to nuclear and aerospace
programmes — a real-time case study in the absence of institutional KPV
monitoring architecture.

### 2.3 The Institutional Gap

No U.S. government agency currently maintains a cross-domain key person
registry equivalent to a national security asset inventory. The FBI
investigation into the nuclear and aerospace scientists pattern was
initiated reactively — in response to public attention and Congressional
pressure — rather than by a standing monitoring function that had flagged
anomalous loss rates in a critical technical community. This institutional
absence is itself a KPV finding: the architecture required to detect,
assess, and respond to potential coordinated key person targeting campaigns
does not exist as a unified function.

KPVS is designed to provide the analytical instrument that would support
such an architecture, beginning with the open-source, unclassified baseline.

---

## 3. The Problem KPVS Solves

### 3.1 The Pipeline vs. Concentration Distinction

Existing workforce vulnerability assessments in national security contexts
are almost entirely organised around pipeline analysis: are there enough
nuclear engineers, cleared analysts, or critical manufacturing technicians?
The policy response to pipeline vulnerabilities is investment in educational
throughput, retention bonuses, and clearance process reform. These are
genuine interventions for a genuine problem.

They do not address the structurally different problem that KPVS is designed
to quantify. The Chief Separation Process Chemist at the only domestic rare
earth processing facility of consequence may be working within a perfectly
healthy pipeline of chemical engineers. That pipeline is irrelevant to the
question of whether the specific individual in that role — with twenty years
of tacit knowledge about separation chemistry for heavy rare earth elements,
an established co-investment relationship with the DoD DPA Title III programme
office, and a relationship with the Australian allied supplier that no document
captures — can be replaced in less than six years if they are recruited by a
Chinese competitor, neutralised by litigation, or lost to any other cause.

KPVS quantifies this distinction: not "how many" but "which specific person,
and what happens to the network when that person is gone."

### 3.2 The Adversarial Targeting Gap

The central quantitative finding that KPVS produces is the **adversarial
targeting gap**: the difference in expected organisational capability between
an adversary who selects targets randomly and an adversary who selects them
by KPCI rank. In the canonical rare earth processing simulation
(N=10,000, seed=20260501), random loss of two roles leaves the organisation
at 86.7% mean capability. An adversary targeting the two highest-KPCI roles
leaves it at 68.7%. The adversarial targeting gap is 17.9 percentage points.

This gap is the exploitation premium of strategic intelligence: what a
sophisticated adversary gains by knowing which people to target. It
translates directly to the value of closing the intelligence gap on
adversarial organisations — the same gap, measured against their structure,
is the analytical yield of a successful KPCI mapping operation.

### 3.3 The Bench Investment Case

The bench investment optimiser answers the organisational question that
follows from the gap finding: given a fixed budget of succession-depth
investments, which roles should receive them? The rare earth simulation
shows that allocating two bench units to the Chief Separation Process Chemist
and one to the Heavy REE Extraction Specialist raises adversarial scenario
capability from 68.5% to 91.7% — a 23.2 percentage point improvement from
three targeted investments. This is the human capital equivalent of the Cost-
Asymmetry Simulator's optimal weapons procurement portfolio: the specific
allocation of limited resources that produces the maximum resilience per
unit of investment.

---

## 4. Operational Concept

### 4.1 The Basic Use Case

The fundamental KPVS operation is:

1. **Define the organisation** — Construct a role graph in JSON format
   describing the roles relevant to the capability of interest, with KPCI
   scores estimated from subject-matter expert assessment, institutional
   knowledge, or open-source research.

2. **Run the simulation** — Execute 10,000 Monte Carlo iterations under
   three scenarios (random attrition, adversarial targeting, cascade failure)
   to produce capability retention distributions.

3. **Interpret the adversarial gap** — The difference between random and
   adversarial scenario means quantifies the exploitation premium available
   to a sophisticated adversary. A large gap indicates high KPV concentration;
   a near-zero gap on an adversarial org indicates an allied intelligence gap.

4. **Apply the optimiser** — Given a specific budget of succession investments,
   the optimiser identifies the priority allocation. This is the actionable
   output for programme managers and HR directors.

5. **Generate the report** — The self-contained HTML report is the
   dissemination artefact: shareable with non-technical stakeholders,
   embeddable in policy documents, and citable by run ID and seed.

### 4.2 The Two Modes of Use

**Defensive mode — assessing allied and domestic organisations:**
KPVS identifies which roles in a friendly organisation constitute genuine
national security single points of failure, estimates the capability gap their
loss would create, and recommends priority succession investments. AO scores
reflect visibility of each role to a foreign adversary. High KPVS scores in
this mode drive protective action: succession planning, tacit knowledge
documentation, physical security protocols for high-AO individuals.

**Offensive/analytical mode — assessing adversarial organisations:**
KPVS maps the exploitable key person vulnerabilities in adversarial
organisational structures from open-source data, identifies intelligence gaps
where AO scores are low (and closed-source data would significantly change
the analysis), and quantifies the adversarial targeting premium available
to allied intelligence if the gap is closed. AO scores in this mode reflect
allied OSINT visibility of each adversarial role. Near-zero adversarial
targeting gaps are intelligence gap findings, not resilience findings.

The same simulation engine and the same KPCI mathematics serve both modes.
The analytical interpretation differs; the `adversarial_org` flag in the
JSON file and the AO inversion documented in `docs/intelligence_orgs.md`
are the only operational distinctions.

### 4.3 The Simulation as a Briefing Instrument

The HTML report is designed as a briefing product, not a technical document.
The colour-coded KPCI table, the adversarial gap dashboard card, and the
priority recommendations are written for a Congressional staffer, a CSIS
analyst, or a defence contractor security officer — not for the researcher
who built the model. The gap between 86.7% and 68.7% capability, visualised
as a distribution comparison chart with a prominent "17.9 pp adversarial gap"
card, communicates the central finding in fifteen seconds to a non-technical
audience.

This is intentional. The tool's analytical value is only realised if its
findings reach decision-makers. The pipeline from simulation to decision is:
model → simulate → HTML report → briefing → investment or policy action.

---

## 5. User Roles and Responsibilities

### 5.1 KPCI Assessor

**Who:** Subject-matter expert with deep knowledge of the organisation being
assessed — a programme manager, a counterintelligence analyst, a sector
specialist, or a security officer.

**Primary responsibility:** Assign KPCI component scores (ST, DR, AO) for
each role. This is the highest-value and highest-risk step in the workflow.
Accurate KPCI scores produce actionable findings; poorly calibrated scores
produce spurious rankings.

**How to assess ST:** How long would it actually take, under optimal
conditions, to replace this specific person in this specific role at 80% of
their current operational effectiveness? Not "how long to hire a replacement"
but "how long until the replacement can do what this person does." For roles
requiring 20 years of tacit knowledge accumulation, the answer may be the
same as the substitution timeline.

**How to assess DR:** What fraction of this role's operational value would
survive if the person left tomorrow? If every critical process is documented
in SOPs, DR is low. If the role's value is primarily in personal relationships,
judgment built from years of experience, and knowledge that no document
captures, DR is high.

**How to assess AO for allied orgs:** How visible is this individual, in this
role, to a foreign intelligence service conducting systematic open-source
mapping? Published papers, conference presentations, LinkedIn profiles, patent
filings, government directory listings, and budget exhibit references all
increase AO. Administrative staff in undocumented positions have low AO.

**How to assess AO for adversarial orgs (inverted):** How visible is this
individual, in this role, to allied OSINT analysts? Publicly announced
appointments, state media coverage, academic publications, and conference
appearances increase AO. Roles in covert or operational directorates with
no public record have low AO — and that low score is the intelligence gap finding.

### 5.2 Simulation Operator

**Who:** A technical user comfortable with command-line tools or the web
interface — a research assistant, a data analyst, or the KPCI assessor
themselves.

**Primary responsibility:** Load the org JSON, configure simulation parameters,
execute the run, and produce the HTML report. For canonical paper citations,
the operator must use the documented seed (20260501) and iteration count
(10,000).

**Critical parameter decision — n_losses:** The default is 20% of org size
per iteration. For a 13-role organisation this is 2 losses per iteration,
which is appropriate for modelling a sustained adversarial campaign over
a multi-year period. For a single-event scenario (one targeted action), use
`--n-losses 1`. The choice should be documented alongside the citation.

### 5.3 Report Consumer

**Who:** The policy official, programme manager, Congressional staffer,
or think tank analyst who receives the HTML report and must act on it.

**Primary responsibility:** Interpret the adversarial gap as a priority signal,
not a precise prediction. A 17.9 pp gap means the organisation is meaningfully
more vulnerable to a sophisticated targeted adversary than to natural attrition.
The priority recommendations identify where succession investment produces the
most resilience per unit of cost.

**What the report does not tell you:** It does not tell you whether your
specific Tier-1 KPV individual is actually being targeted. It does not predict
individual behaviour. It does not account for classified information about
adversarial intentions or capabilities. It is a structural vulnerability map,
not a threat assessment.

### 5.4 System Administrator (Web Deployment)

**Who:** IT staff managing a shared KPVS deployment on an analysis network.

**Primary responsibility:** Ensure the web server is bound to appropriate
network interfaces (localhost for single-user; internal network with
authentication proxy for shared use), that `runs/` and `reports/` directories
are on appropriately protected storage, and that log rotation is configured.

---

## 6. Operational Scenarios

### Scenario A: Defence Acquisition Programme KPV Assessment

**Context:** A programme executive office for a major weapons system wants
to assess whether its acquisition programme management team has unacceptable
key person concentration risk following a planned senior PM retirement.

**Operation:**
1. The programme's senior security officer constructs an org JSON covering
   the PM team: the outgoing PM, the deputy PM, key technical directors,
   the chief systems engineer, and the prime contractor relationship lead.
2. KPCI scores are assigned based on programme institutional knowledge.
   The outgoing PM has been on the programme for 18 years: ST=4 (10+ year
   succession), DR=3.5 (most value is tacit), AO=3.0 (named in budget
   exhibits). KPCI=10.5.
3. The simulation is run at N=10,000. The adversarial gap is 14.2 pp.
   The cascade failure from PM loss shows 76.3% mean residual capability
   with a 24-month restoration estimate even with bench.
4. The optimiser, given a budget of 2 succession investments, recommends
   placing both on the outgoing PM role (one immediate deputy designation,
   one junior officer shadow programme) rather than distributing across
   lower-KPCI roles.
5. The HTML report is shared with the programme director, who uses it to
   justify a 24-month overlap period and a tacit knowledge documentation
   sprint before the PM's departure date.

**Key output:** The adversarial gap and cascade analysis justify a specific,
costed investment in succession overlap — a decision that would not have been
supported by standard workforce planning metrics.

---

### Scenario B: Five Eyes Comparative Resilience Assessment

**Context:** An allied coordination working group wants to compare KPV
architecture across the Five Eyes national security senior leadership,
identify the most vulnerable partner, and develop a coordinated resilience
recommendation for the next FVEY ministers' meeting.

**Operation:**
1. The working group analyst runs the built-in Five Eyes org set:
   `python main.py --org-set five_eyes --iterations 10000 --budget 5 --html-dir reports/`
2. The comparative HTML report shows:
   - New Zealand has the highest adversarial targeting gap (10.9 pp)
     reflecting its smallest and most concentrated architecture
   - Australia and UK show 5.5 pp and 9.0 pp gaps respectively
   - The U.S. NSA architecture shows 2.1 pp — the most distributed of
     the Five Eyes partners, with the most institutional redundancy
3. The optimiser identifies that New Zealand's GCSB Director and NZSIS
   Director roles both carry zero bench depth. Three succession investments
   in those two roles close the gap from 10.9 pp to approximately 4.2 pp.
4. The comparative report is used in a pre-ministerial briefing to support
   a bilateral NZ-AU succession planning agreement and a joint Five Eyes
   key personnel security working group proposal.

**Key output:** The comparative adversarial gap chart in the HTML report
provides an immediately intelligible cross-partner vulnerability ranking that
drives a specific multilateral policy proposal.

---

### Scenario C: Adversarial KPV Mapping — Open-Source Baseline

**Context:** An open-source intelligence analyst wants to apply systematic
KPV thinking to the Chinese rare earth processing architecture, producing a
baseline assessment of which Chinese roles represent the highest-value
targeting nodes from an allied perspective, and identifying where classified
data would most change the assessment.

**Operation:**
1. The analyst reviews the built-in China strategic leadership org file,
   noting that the MIIT Rare Earth Division Director (AO=3.5) is highly
   visible through public announcements and regulatory filings, while the
   chief rare earth separation chemist at BGRIMM (AO=2.0) is partially
   visible but inadequately mapped.
2. The simulation is run:
   `python main.py --intel-org cn --iterations 10000 --skip-optimizer`
3. The adversarial targeting gap for the China org is 2.0 pp — near-zero.
   The analyst correctly interprets this as an intelligence gap finding:
   the model cannot differentiate targets effectively because too many
   high-KPCI roles have low AO scores.
4. The analyst annotates the report with the specific roles where classified
   data (signals intelligence, defector reporting, imagery of facility
   access patterns) would raise AO scores and thus open the adversarial
   gap. The annotated report identifies the BGRIMM separation chemistry
   team as the highest-priority intelligence collection target — not because
   the open-source data says so, but because it is the role where the
   intelligence gap is largest relative to strategic importance.

**Key output:** The near-zero adversarial gap and the AO gap map constitute
an intelligence requirements document — a systematic statement of what
classified data collection would most improve the allied analytical picture.

---

### Scenario D: KPVS as a Policy Briefing Instrument

**Context:** A researcher presents KPVS findings at a CSIS programme on
critical minerals security. The audience includes Congressional staff,
DoD programme officials, and allied embassy defence attachés.

**Operation:**
1. The researcher runs the rare earth org at canonical parameters
   (seed=20260501, N=10,000) and opens the HTML report.
2. The presentation covers three findings from the report:
   - The three Tier-1 KPVs with zero bench depth are the organisational
     equivalent of the single-source API vulnerabilities in MTS Paper 4.
   - The 17.9 pp adversarial gap quantifies the intelligence premium: an
     adversary with knowledge of the KPCI ranking gains 17.9 pp of
     additional capability degradation over random interference.
   - Three targeted succession investments (the optimiser allocation) raise
     adversarial scenario capability by 23.2 pp — a better return on
     resilience investment than most material stockpiling alternatives.
3. The DoD DPA Title III programme director in the audience asks whether
   the model can be run against the actual programme. The researcher
   provides the org JSON schema and offers to support a calibrated
   assessment with programme-specific KPCI scores.

**Key output:** The briefing converts a simulation output into a policy
conversation and a potential institutional adoption pathway.

---

## 7. System Interfaces and Information Flows

### 7.1 Input Sources

| Source | Format | Description |
|--------|--------|-------------|
| User-constructed org JSON | JSON file | Primary input; constructed from organisational knowledge and OSINT |
| Built-in example orgs | JSON files in `examples/` | Reference implementations; calibrated to published data |
| Intelligence org files | JSON files in `examples/five_eyes/` and `examples/adversarial/` | Open-source KPV assessments; all data publicly sourced |
| Web UI editor | Browser input fields | Interactive org editing; produces same JSON structure |

### 7.2 Output Artefacts

| Artefact | Format | Intended Recipient |
|----------|--------|--------------------|
| KPCI Report | JSON + console table | Technical analyst |
| Scenario Results | JSON | Research pipeline / downstream tools |
| Summary JSON | JSON | HTML reporter; archival; inter-tool exchange |
| HTML Report (single org) | HTML | Policy briefing; non-technical decision-maker |
| HTML Report (comparative) | HTML | Multi-org briefing; allied coordination |
| Console output | Terminal text | Researcher / simulation operator |
| Log file | Rotating plaintext | System administrator; debugging |

### 7.3 Downstream Use

KPVS outputs are designed to integrate with three downstream contexts:

**Academic publication** — The summary JSON contains all data needed to
reproduce findings. The run ID, seed, and KPVS version are embedded. A
reader can clone the repository, load the same org JSON, run with the same
parameters, and replicate the result.

**Policy documents** — The HTML report is portable (single file, no server)
and printable. Chart.js charts export cleanly to print layouts. The report
footer includes the full citation string.

**Intelligence workflows** — The summary JSON is structured for ingestion
by automated analysis pipelines. The KPCI scores, tier classifications, and
adversarial gap metric are all available as machine-readable fields, enabling
bulk comparison across multiple organisations or time-series tracking of
KPCI changes as an organisation evolves.

---

## 8. Operational Constraints and Limitations

### 8.1 The KPCI Is an Analytical Estimate

KPCI scores are not objective measurements. They reflect the assessor's
judgment about substitution difficulty, documentation adequacy, and adversarial
visibility. Two assessors applying the framework to the same role will produce
different scores. The simulation then amplifies the differences between
high- and low-KPCI scores; a role scored ST=4 vs. ST=3.5 by different
assessors will produce materially different results.

**Mitigation:** Use structured elicitation when multiple assessors are
available. Calibrate against observable outcomes (actual succession timelines,
documented knowledge transfer completeness) where historical data exists.
Treat KPVS output as directional — it identifies which roles are most
vulnerable relative to others, not the precise magnitude of each role's
individual risk.

### 8.2 The Model Does Not Know What It Does Not Know

KPVS cannot model the tacit knowledge it cannot see. The Documentation Ratio
component captures the fraction of role value the assessor believes is tacit.
But the assessor may not fully appreciate how tacit a role is until after the
key person is gone. This is the fundamental challenge of tacit knowledge:
you often cannot fully enumerate what you don't know until the person who
held it is no longer available.

**Mitigation:** When in doubt, score DR higher. The cost of a false negative
(underestimating tacit knowledge concentration) is missing a critical
succession investment. The cost of a false positive (overestimating it)
is an unnecessary but harmless succession planning effort.

### 8.3 The Open-Source Adversarial Assessment Is a Floor

The adversarial org assessments bundled with KPVS are open-source baselines.
The near-zero adversarial targeting gaps on Russia and North Korea are
intelligence gap findings, not resilience findings. A classified implementation
with IC-quality AO data would produce materially different results.

This is a documented feature, not a limitation to be hidden. The CONOPS
makes the intelligence gap finding explicit because it constitutes an
analytical argument for the investment in collecting the classified data
that would improve the assessment.

### 8.4 The Capability Model Is Parsimonious

KPVS models capability as a weighted sum of roles, with partial coverage
from bench depth and cascade degradation from mission-critical role loss.
Real organisations have more complex capability interdependencies than this
model captures: informal knowledge networks, undocumented mentoring
relationships, the tacit organisational knowledge that exists in the team
as a whole rather than in any individual. The model is a useful simplification,
not a complete representation.

**Mitigation:** Use KPVS for relative ranking and directional assessment.
Do not use KPVS output as a precise prediction of post-loss capability
levels. The adversarial gap is more robust than the absolute capability
percentages.

---

## 9. Intelligence Community Application

### 9.1 The Symmetric Capability Argument

China's Thousand Talents Programme is, in operational terms, a systematic
KPVS-like capability applied to U.S. critical technical communities. It
identifies which individuals hold the most irreplaceable knowledge and
relationships in domains of strategic interest. It scores them on what
amounts to a KPCI equivalent — substitution difficulty (how hard to replace
this person's knowledge), documentation ratio (how transferable is the
knowledge without the person), and adversarial observability (how accessible
is this person to recruitment or compromise). It then prioritises recruitment
efforts accordingly.

KPVS is the symmetric analytical instrument. It enables allied analysts to
map adversarial organisational KPV architecture systematically, using the
same logic — identifying which roles in Chinese, Russian, Iranian, and DPRK
organisations hold the most concentrated strategic capability, and where the
open-source AO data is insufficient to close the analytical gap.

### 9.2 KPVS as an Intelligence Requirements Generator

The most operationally significant output of running KPVS against adversarial
organisations is not the simulation results themselves — it is the intelligence
gap map. When the adversarial targeting gap on North Korea's nuclear programme
is near-zero despite the presence of roles with KPCI scores of 12.0, the
finding is that the model cannot differentiate targets because it cannot see
the structure. The `notes` fields in the org JSON identify which specific
roles have AO=1.0 or AO=1.5 and why — the nuclear warhead design lead, the
Lazarus Group cyber operations director, the Rocket Force programme manager.
Those are the intelligence collection requirements the KPVS analysis generates.

### 9.3 The Classified Implementation Pathway

A classified KPVS deployment would require three modifications to the
open-source release:

1. **Replace open-source org JSON files** with classified versions containing
   higher-fidelity AO scores derived from HUMINT, SIGINT, and IMINT collection
   against adversarial targets. The simulation mathematics are unchanged.

2. **Expand the role graph** to include compartmented positions not visible in
   open sources. The JSON schema supports unlimited role depth; the only
   constraint is analyst knowledge of the structure.

3. **Integrate with existing IC data infrastructure.** The summary JSON output
   format is designed for downstream ingestion. A classified deployment could
   feed KPVS output into existing threat assessment or target development
   workflows.

The open-source tool demonstrates the analytical architecture. The classified
deployment operationalises it with IC-quality data.

### 9.4 Operational Security Considerations

Even in the open-source deployment, analysts working on adversarial org
assessments should consider:

- **Operational security of KPCI scores:** The scores assigned to specific
  adversarial roles may reflect collection or analytical judgements that
  should not be publicly associated with the tool. Do not commit classified
  or sensitive KPCI assessments to a public repository.
- **Attribution:** The `notes` fields in org JSON files can contain
  analytical judgements that may be sensitive. Sanitise notes fields before
  distributing reports outside appropriate security domains.
- **The report URL:** HTML reports written to `reports/` are served by the
  web interface. In a shared deployment, all users can access all reports.
  Consider access controls at the infrastructure level for sensitive
  assessments.

---

## 10. Transition to Classified Deployment

### 10.1 Decision Criteria

A transition to classified deployment is warranted when:

- Open-source AO data for high-priority adversarial roles is insufficient to
  produce actionable adversarial gap findings (near-zero gap on high-KPCI orgs)
- The assessment is being used to support targeting development or collection
  planning rather than academic research or policy analysis
- Organisational data being modelled includes compartmented roles not
  appropriately described in unclassified documents

### 10.2 Technical Transition Requirements

The simulation core (`kpvs/models.py`, `kpvs/simulator.py`, `kpvs/optimizer.py`)
requires no modification for classified deployment. The transition involves:

1. **Data classification:** All org JSON files containing classified KPCI
   scores, role descriptions, or AO assessments must be handled at appropriate
   classification levels.
2. **Infrastructure:** The web interface must be deployed on a classified
   network segment with appropriate authentication and audit logging.
3. **Output handling:** HTML reports containing classified findings must be
   handled as classified documents. The `--no-log-file` flag should be
   considered to prevent inadvertent logging of sensitive parameters.
4. **OPSEC review:** The `notes` fields of all org JSON files should be
   reviewed by a security officer before the files are used in a classified
   context.

### 10.3 Recommended Sponsoring Architecture

The appropriate institutional home for a classified KPVS deployment is the
ODNI National Counterintelligence and Security Center (NCSC), which has
existing authority for key personnel security functions and the cross-agency
mandate to address the institutional gap documented in this CONOPS. The
National Key Person Registry recommended in MTS Working Paper 5 Section 7.1
would be the natural classified data source feeding a classified KPVS
deployment.

---

## 11. Measures of Effectiveness

### 11.1 Tool Effectiveness Measures

These measures assess whether KPVS is performing its analytical function correctly:

| Measure | Standard | Assessment Method |
|---------|----------|-------------------|
| Adversarial gap magnitude | Gap > 5 pp indicates exploitable concentration | Canonical run output |
| Reproducibility | Identical output across platforms for same seed | Cross-platform test suite |
| Tier-1 identification accuracy | Roles independently assessed as critical by SME should score KPCI ≥ 10 | Expert calibration exercise |
| Intelligence gap detection | Near-zero gap on genuinely opaque adversarial orgs | Comparison with classified assessments (classified context only) |

### 11.2 Policy Effectiveness Measures

These measures assess whether KPVS is producing the intended policy impact:

| Measure | Indicator |
|---------|-----------|
| Succession investment triggered | Organisation implements succession programme for Tier-1 KPVs following assessment |
| Intelligence collection initiated | Assessment identifies specific roles for enhanced OSINT or classified collection |
| Allied coordination enabled | Comparative Five Eyes assessment produces specific bilateral or multilateral resilience agreement |
| Tacit knowledge documentation | Organisation launches documentation programme for high-DR roles following assessment |
| Academic adoption | KPVS methodology cited in peer-reviewed publications beyond MTS series |

### 11.3 Organisational Resilience Improvement

The before/after metric for KPVS use is the adversarial targeting gap before
and after implementing the optimiser's recommended succession investments.
In the canonical rare earth simulation, the optimiser closes the gap from
17.9 pp to approximately 4.2 pp through three targeted investments — a 76%
reduction in adversarial exploitation premium. This is the return on investment
metric for succession planning as national security infrastructure.

---

## 12. Glossary

| Term | Definition |
|------|-----------|
| **Adversarial Gap** | The difference in mean organisational capability retention between random attrition and adversarial targeting scenarios; the exploitation premium of strategic intelligence |
| **AO (Adversarial Observability)** | KPCI component; for allied orgs: visibility to a foreign adversary; for adversarial orgs (inverted): visibility to allied OSINT |
| **Bench Depth** | Number of identified successors in active development for a given role |
| **Cascade Failure** | Stochastic propagation of capability loss from a mission-critical role to its dependent network |
| **DR (Documentation Ratio)** | KPCI component; fraction of role value residing in tacit knowledge rather than transferable documentation |
| **Intelligence Gap Finding** | A near-zero adversarial targeting gap on an adversarial org, indicating insufficient allied OSINT coverage to differentiate targets — not a finding about adversarial resilience |
| **KPCI (Key Person Concentration Index)** | Composite vulnerability score: ST + DR + AO (0–12); measures the degree to which critical capability is concentrated in a specific individual |
| **KPV (Key Person Vulnerability)** | Structural condition meeting three criteria: (1) role value substantially tacit; (2) 24+ month capability gap on loss; (3) externally observable |
| **Mission-Critical Role** | A role whose loss triggers cascade degradation to dependent roles in the simulation |
| **MTS (Mutual Threshold Saturation)** | Parent research framework; compound vulnerability condition in which multiple critical capabilities are simultaneously threatened through shared structural mechanisms |
| **ST (Substitution Timeline)** | KPCI component; estimated time to restore 80% operational effectiveness under optimal succession |
| **Tacit Knowledge** | Knowledge that is embodied in practice and judgment rather than encoded in documentation; cannot be fully transferred through instruction (Polanyi, 1966) |
| **Tier-1 KPV** | KPCI ≥ 10; critical concentration — capability discontinuity on loss; requires immediate succession action |
| **Tier-2 KPV** | KPCI 7–9; significant concentration — standard succession planning inadequate |
| **Thousand Talents Programme** | PRC systematic talent recruitment programme targeting U.S. scientific and technical key persons; the adversarial KPV mapping operation that KPVS is designed to counter symmetrically |

---

*KPVS CONOPS-001 v1.2.0 — MTS Research Programme — Robert J. Green — May 2026*  
*All KPVS output is analytical and must be calibrated with subject-matter expert review.*  
*No classified materials were used in the development of this tool or its documentation.*
