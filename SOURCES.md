# Sources for every external number

Every figure in this project comes from one of two places: the survey microdata,
or an external source listed below. Nothing is asserted without a traceable
origin. Numbers computed *from* the microdata are not listed here — they are
produced by the code and land in `output/tables/`.

Accessed 12 September 2026 unless stated otherwise.

---

## 1. Survey microdata

| Item | Source | Access |
|---|---|---|
| Nigeria General Household Survey-Panel, wave 5 (2023/24) | National Bureau of Statistics with the World Bank LSMS-ISA programme | [World Bank Microdata Library](https://microdata.worldbank.org/index.php/catalog/6410) — free registration; not redistributed here |
| Nigeria General Household Survey-Panel, wave 4 (2018/19) | Same | [World Bank Microdata Library](https://microdata.worldbank.org/index.php/catalog/3557) |

The wave-4 release includes the published consumption aggregate
`totcons_final.csv`, which `build_data.py` uses to validate the wave-5
reconstruction (Table A1).

---

## 2. External figures used in the analysis

### 2.1 Price deflator — `config.CPI_W4_TO_W5 = 2.31`

Converts 2018/19 naira to the August-2023 price base.

| Component | Value | Source |
|---|---|---|
| NBS all-items CPI, August 2023 (Nov 2009 = 100) | 593.6 | NBS CPI and Inflation Report, August 2023, via [Statista series](https://www.statista.com/statistics/1118891/monthly-consumer-price-index-in-nigeria) |
| All-items CPI, 2018 annual average | 240.1 | World Bank `FP.CPI.TOTL`, [API](https://api.worldbank.org/v2/country/NGA/indicator/FP.CPI.TOTL?format=json) |
| All-items CPI, 2019 annual average | 267.5 | Same |
| Fieldwork-weighted 2018/19 base | ≈ 257.5 | Derived; GHS-W4 fielded Jul–Sep 2018 and Jan–Feb 2019, NLSS Sep 2018 – Oct 2019 |
| **Ratio** | **593.6 / 257.5 = 2.31** | |

Anchoring on September 2018 alone (index ≈ 247.4) gives 2.40, so the defensible
range is about 2.3–2.4. Table 8c reruns the poverty analysis across 0.5× to 1.5×
the resulting line, which spans that uncertainty many times over.

> **Still to do before submission.** Replace the interpolated 2018/19 base with
> the published NBS monthly index for the exact month. The NBS CPI archive is at
> [nigerianstat.gov.ng/elibrary](https://www.nigerianstat.gov.ng/elibrary).

### 2.2 National poverty line — `config.POVERTY_LINE_2019 = 137,430`

₦137,430 per person per year, 2018/19 prices. Source: National Bureau of
Statistics, *Poverty and Inequality in Nigeria 2019* (May 2020),
[nigerianstat.gov.ng](https://www.nigerianstat.gov.ng/elibrary/read/1092). In
August-2023 prices this is ₦317,463.

### 2.3 Benefit-package parameters

These are **assumptions, not measurements**, because the NHIA has not published a
machine-readable tariff schedule. Each is a lever in `config.py` and each appears
in the robustness grid (Table 8).

| Parameter | Value | Basis |
|---|---|---|
| Drug co-payment | 10% | NHIA states beneficiaries pay "a 10% co-payment for drugs" — [NHIA FAQ](https://www.nhia.gov.ng/faq/); [NHIA Operational Guidelines](https://www.nhia.gov.ng/operational-guideline/) |
| Outpatient share inside package | 85% | Assumption; tested 70–100% |
| Inpatient share inside package | 90% | Assumption; tested in Table 8 |
| Drug share of outpatient spend | 86.25% | Measured from Q12, Q17 and Q17a of the health module; recomputed on every build |
| Induced-demand elasticity | −0.20 | RAND Health Insurance Experiment, Manning et al. (1987); tested −0.10 to −0.35. Applied with the arc (midpoint) formula q1/q0 = (1+x)/(1−x), x = e(p1−p0)/(p0+p1) |
| Administrative load | 15% | Assumption |
| Adverse-selection load | 10% | Assumption |
| Expense ratio | 10% | Assumption |
| Affordability ceiling | 5% of per-capita consumption | Assumption. Jofre-Bonet & Kamara (2018) find mean willingness to pay close to 5% of business income among informal workers in Sierra Leone |
| Reinsurance loading | 30% of expected ceded cost | Assumption; retentions N250,000 to N1 million |
| Take-up grid | 10% to 100% | Scenario levers for voluntary enrollment |
| Consumption calibration | food 1.158, non-food 0.892, rent 0.069 | Estimated from the wave-4 published aggregate by `build_data.calibration_factors()` (Table A1) |

### 2.4 Published state-scheme premiums (external validation only)

Not inputs to the model. Lagos State launch of the Ilera Eko "Standard Jaara"
plan, announced by Governor Babajide Sanwo-Olu, 17 July 2024:

| Plan | Annual premium |
|---|---|
| Individual | ₦15,000 |
| Family of four | ₦55,000 |
| Family of six | ₦80,000 |
| Additional dependent | ₦10,000 |

Source: [Nairametrics, 17 July 2024](https://nairametrics.com/2024/07/17/lasg-launches-n15000-n80000-yearly-ilera-eko-standard-jaara-health-insurance-plan/);
scheme site [lashma.com](https://www.lashma.com/).

> These are nominal July-2024 naira against a premium in August-2023 naira, and
> Ilera Eko's benefit package is not the NHIA basic package priced here. The
> comparison is a plausibility check, not a like-for-like test.

---

## 3. Contextual figures quoted in the manuscript

| Claim | Value | Source |
|---|---|---|
| Out-of-pocket share of current health expenditure, Nigeria, 2023 | 71.9% | WHO Global Health Expenditure Database via World Bank `SH.XPD.OOPC.CH.ZS` — [data page](https://data.worldbank.org/indicator/SH.XPD.OOPC.CH.ZS?locations=NG) |
| Same, 2015–2022 range | 71.5% – 77.4% | Same series |
| Health-insurance enrolment, Nigeria | 22.03 million (July 2026); 21.73 million at end-2025 | NHIA, reported in [Nairametrics, 7 Mar 2026](https://nairametrics.com/2026/03/07/health-insurance-coverage-in-nigeria-rises-to-21-7m-in-2025-report/) |
| Enrolment as a share of population | under 10% of about 220 million | Derived from the above |
| Coverage measured in the survey year | 1.07% of individuals; 1.98% of households | **Computed from the microdata** (Section 5A, q16-17c) — Table 1b, not an external figure |
| NHIA Act 2022 provisions | — | [Gazetted copy, nhia.gov.ng](https://www.nhia.gov.ng/wp-content/uploads/2024/03/NHIA-Act-2022-Gazetted-Copy.pdf) |

---

## 4. Citations verified on Crossref

Checked against the Crossref REST API, not from memory.

| Reference | DOI | Status |
|---|---|---|
| Aregbeshola & Khan (2018), *IJHPM* 7(9), 798–806 | `10.15171/ijhpm.2018.19` | Confirmed |
| Xu et al. (2003), *The Lancet* | `10.1016/S0140-6736(03)13861-5` | Confirmed |
| Wagstaff & van Doorslaer (2003), *Health Economics* | `10.1002/hec.776` | Confirmed |
| Wagstaff et al. (2018), *Lancet Global Health* | `10.1016/S2214-109X(17)30429-1` | Confirmed |
| Cylus et al. (2018), *Bull WHO* | `10.2471/BLT.18.209031` | Confirmed |
| Erreygers (2009), *J Health Econ* | `10.1016/j.jhealeco.2008.02.003` | Confirmed |
| Dunn & Smyth (1996), *JCGS* | `10.1080/10618600.1996.10474708` | Confirmed |
| Dunn & Smyth (2005), *Stat Comput* | `10.1007/s11222-005-4070-y` | Confirmed |
| Smyth & Jørgensen (2002), *ASTIN Bulletin* | `10.2143/AST.32.1.1020` | Confirmed |
| Lumley (2004), *J Stat Softw* | `10.18637/jss.v009.i08` | Confirmed |
| Opeloyeru & Lawanson (2023), *IJSE* | `10.1108/IJSE-02-2022-0132` | Confirmed |

Re-verify at [search.crossref.org](https://search.crossref.org) before submission.

---

## 5. Variable mapping identified from the data

### 5.1 Health-insurance type — confirmed empirically

`sect5a2_plantingw5` (Section 5A, questions 16–17c) records insurance holding,
type and covered members. The release carries no codebook, but the health type
is identifiable without one: all ten households that reported paying a
health-insurance premium in the consumption module (item 363) carry
`s5aq17a__1`, and no other type shows that correspondence. `build_data.py`
re-runs the check on every execution and prints the result, so a renumbering in
a future release surfaces immediately rather than silently repricing the paper.

The World Bank catalogue confirms the module's scope: *"Section 5A (Savings and
Insurance, questions 16-17c). This section records household-level information
on insurance coverage."*

### 5.2 Health-module cost fields — confirmed against the questionnaire

The wave-5 CSV release ships without a codebook, so the health-module cost
fields were identified from their response patterns across facility types
(consultation fees are zero at most chemist shops but positive at hospitals;
medicine spending is near-universal among those who sought care).

| Variable | Question wording | Recall |
|---|---|---|
| `s3q12` | "How much did the household pay for [NAME]'s consultation with [Q9 1st choice], **excluding drugs**?" | 4 weeks |
| `s3q13` | "How much did the household pay for [NAME]'s **transportation** to and from the [Q10]?" (excluded by default) | 4 weeks |
| `s3q16` | "In the past 4 weeks, did the household spend any money for [NAME]'s drugs or medicines?" — gate for Q17/Q17a | 4 weeks |
| `s3q17` | "How much did the household pay for [NAME]'s **prescription** drugs or medicines?" | 4 weeks |
| `s3q17a` | "How much did the household pay for [NAME]'s **non-prescription** drugs or medicines?" | 4 weeks |
| `s3q20` | "How much did the household pay for [NAME] to stay in the hospital or health facility in the last 12 months? **Include consultation costs, medical procedures and drugs/medicines**" | 12 months |

Source: Post-Planting Household Questionnaire, Section 3 (Health), pages 48–49 —
[catalogue 6410, document 180528](https://microdata.worldbank.org/catalog/6410/download/180528).

Q16/Q17/Q17a explicitly *exclude* drugs related to hospital admissions and Q20
explicitly *includes* them, so outpatient and inpatient spending do not overlap.

**One earlier reading was wrong.** `s3q17a` was read as tests and other costs; it
is non-prescription drugs. The out-of-pocket total is unaffected — the same three
fields are summed either way — but the drug share of outpatient spending is not.
It is now measured at **86.25%** (Q17+Q17a over Q12+Q17+Q17a) against an assumed
60%, and because drugs carry the co-payment and respond less to a price fall than
free-at-point-of-use services, the gross premium fell from ₦26,912 to ₦25,864 in the version of the model current at the time.
`build_data.py` recomputes the share on every run and prints it against the config
value.


If any of these five readings is wrong, the premium is wrong. Nothing else in
the pipeline depends on them.
