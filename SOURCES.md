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
| Nigeria General Household Survey-Panel, wave 4 (2018/19) | Same | [World Bank Microdata Library](https://microdata.worldbank.org/index.php/catalog/3557) |

Wave 4 is the analysis wave. Its release includes the published consumption
aggregate `totcons_final.csv`, which is the denominator.

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

---

## 3. Contextual figures quoted in the manuscript

| Claim | Value | Source |
|---|---|---|
| Out-of-pocket share of current health expenditure, Nigeria, 2019 | 71.5% | WHO Global Health Expenditure Database via World Bank `SH.XPD.OOPC.CH.ZS` — [data page](https://data.worldbank.org/indicator/SH.XPD.OOPC.CH.ZS?locations=NG) |
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

### 5.2 Health-module cost fields (wave 4)

The wave-4 CSV release carries bare numeric codes and no codebook in the
download, so the fields were identified from their response patterns and
skip structure, and the code lists were taken to follow the wave-5 instrument,
which the panel carries forward.

| Variable | Reading | Recall |
|---|---|---|
| `s4aq1` | Ill or injured (17.8% yes) | 4 weeks |
| `s4aq6a` | Who was consulted for the illness; 0 = nobody, 8 and 11 = pharmacist or chemist | 4 weeks |
| `s4aq7` | Where care was sought; 10 = traditional healer | 4 weeks |
| `s4aq9` | Consultation fee, asked of those who consulted | 4 weeks |
| `s4aq10` | Transport (excluded by default) | 4 weeks |
| `s4aq13`, `s4aq14` | Bought medicines, and the amount, asked of everyone | 4 weeks |
| `s4aq15`, `s4aq16`, `s4aq17` | Hospitalized, nights, and cost | 12 months |
| `s4aq23` to `s4aq33` | Washington Group short set; 3 and 4 = severe difficulty | current |

