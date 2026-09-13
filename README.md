# Measuring the Health-Protection Gap and Pricing Informal-Sector Health Insurance under Nigeria's NHIA Act 2022

Reproduction code for Paper 2 of the *Health-Cost Risk and Financial Protection*
research programme. The analysis measures catastrophic health expenditure in
Nigeria, prices a basic benefit package for informal-sector workers, tests
whether a state-level pool could stay solvent, and asks how much of the
catastrophic-spending burden coverage would actually remove.

## Interactive calculator

A companion web tool runs this model live in the browser: move the benefit-design,
loading and pool levers and watch the premium, the affordability gap and the pool's
probability of ruin recompute. It ships the aggregated cost distribution the model
needs, never the microdata.

**https://nigeria-health-protection-gap.vercel.app**

It is a single self-contained HTML file with no build step, no framework and no
runtime data fetch, deployed as a static site.

```bash
.venv/bin/python python/export_tool_data.py   # -> tool/model_data.json
.venv/bin/python python/build_tool.py         # -> tool/index.html
cd tool && vercel deploy --prod
```

`export_tool_data.py` collapses the individual file to the 875 distinct
(outpatient, inpatient, traditional) cost triples the model is a function of, and
asserts that the collapsed payload reproduces the paper's pure premium to within
1e-4 before writing it. `build_tool.py` inlines that payload into
`tool/index.template.html` and wraps the result in a complete HTML document.

The browser cannot run the paper's ruin simulation - 10,000 multinomial draws over
750 cost values per pool-year - so the page matches the first three moments of the
same distribution with a translated gamma. Against the paper's own simulation the
two agree to within 0.35% at the 99.9th percentile of annual claims for every pool
size and take-up pattern the page offers.

## What the code does

| Stage | Script | Output |
|---|---|---|
| Build household and individual analysis files from raw CSVs | `python/build_data.py` | `data/derived/*.csv`, Table A1 |
| RQ1 CHE incidence, intensity, impoverishment, concentration, observed coverage | `python/che.py` | Tables 1, 1b, 2, 2b, 2c, 3, 3b |
| RQ2a Frequency, severity and Tweedie cost models | `python/costmodels.py` | Tables 4, 4b, A2, A3 |
| RQ2b Benefit mapping and premium build-up | `python/premium.py` | Tables 5a-5f |
| RQ3 Collective-risk model and minimum subsidy | `python/ruin.py` | Tables 6a-6d, A4 |
| RQ4 Coverage counterfactual | `python/counterfactual.py` | Tables 7a-7c |
| Section 5.6 robustness grid | `python/robustness.py` | Tables 8, 8b, 8c |
| Figures | `python/exhibits.py` | `output/figures/*.png`, `*.pdf` |
| Calculator payload | `python/export_tool_data.py` | `tool/model_data.json` |
| Check the prose against the tables | `python/check_manuscript.py` | pass/fail |
| Submission documents | `python/make_manuscript.py` | `manuscript/*.docx`, `*.pdf` |

Two modules are shared infrastructure rather than analysis steps:
`python/config.py` holds every analytic parameter in one place, and
`python/svy.py` implements the complex-survey estimators (Taylor-linearised
variances for a stratified single-stage cluster design, weighted quantiles,
concentration indices with the Erreygers correction and a Wagstaff
decomposition). `svy.py` is written to be survey-agnostic and is the piece
Papers 3-6 reuse on US data.

## Reproducing

```bash
python3 -m venv .venv
.venv/bin/pip install numpy pandas scipy statsmodels matplotlib
.venv/bin/python python/run_all.py
```

Runs end to end in about ten minutes on a laptop; most of that is the
robustness grid. The last three steps rebuild the calculator payload, verify
that every headline figure in the manuscript still matches the regenerated
tables, and produce the submission `.docx` and `.pdf`. Building the documents
needs pandoc (`brew install pandoc`); the PDF additionally uses headless Chrome
rather than LaTeX. Every random draw is seeded from `config.SEED`, and
`output/params_used.json` records the full parameter set and library versions
used for the run that produced the current tables.

Tested with Python 3.14, numpy 2.5, pandas 3.0, scipy 1.18, statsmodels 0.15.

## Data

The analysis uses the Nigeria General Household Survey-Panel, waves 4 (2018/19)
and 5 (2023/24), collected by the National Bureau of Statistics with the World
Bank LSMS-ISA programme. **The microdata are not redistributed here.** Download
them from the World Bank Microdata Library (free registration), then unzip into:

```
data/raw/ghs_w5/    <- NGA_2023_GHSP-W5_v01_M_CSV.zip
data/raw/ghs_w4/    <- NGA_2018_GHSP-W4_v03_M_CSV.zip
```

`config.py` expects the wave-5 archive's own folder layout
(`Post Planting Wave 5/Household/...`) and the wave-4 archive's flat layout.

### Two things worth knowing before you read the results

**The wave-5 release ships no consumption aggregate.** Wave 4 publishes
`totcons_final.csv`; wave 5 does not, so the denominator is rebuilt from the
food, non-food and education modules. The same code is run on wave 4 and
compared with the published aggregate (Table A1): it recovers 87% of the
official level, with a rank correlation of 0.80, and puts 92% of households
within one quintile of their official position. Consumption *levels* should
therefore be read with care; ratios and rankings, which is what CHE depends on,
hold up.

**Out-of-pocket spending is measured from the health module, not the
consumption module.** Wave 5's non-food module asks a single 12-month question
about health spending and gets an answer from only 17% of households, implying
an out-of-pocket share of 0.3% of consumption against 5.4% in the published
wave-4 aggregate. The health module asks every member about a specific episode
of care and its itemised cost, and yields 6.0% - consistent with wave 4 and with
national health-accounts data. The consumption-module figure is reported in
Table 8 as a data-quality note.

## Variable mapping

The CSV release ships without a codebook, so the health-module cost fields were
identified from their response patterns across facility types and are marked
`[VERIFY]` in the code against the questionnaire:

| Variable | Interpretation | Recall |
|---|---|---|
| `s3q12` | Fee paid at the place of care | 4 weeks |
| `s3q13` | Transport to the place of care (excluded by default) | 4 weeks |
| `s3q17` | Spending on medicines and treatment | 4 weeks |
| `s3q17a` | Other spending, e.g. tests | 4 weeks |
| `s3q20` | Total paid for hospitalisation | 12 months |

Informal-sector status uses employer type (`s4aq52`) and firm size (`s4aq55`),
the latter because section 14 of the NHIA Act 2022 obliges employers with five
or more staff to enrol their workers. Three alternative rules are tested in
Table 8.

## Provenance

`SOURCES.md` lists every number in this project that did not come out of the
survey: the CPI deflator and its derivation, the poverty line, each
benefit-package assumption, the published state-scheme premiums, and every
contextual statistic quoted in the paper — each with its issuing agency and a
URL. Every DOI in the manuscript was checked against the Crossref REST API
rather than from memory. Two items remain open and are flagged both there and in
the paper: the five health-module cost variables, and the exact NBS monthly
index behind the deflator.

## Citation

Babalola, O. D. (2026). *Measuring the Health-Protection Gap and Actuarially
Pricing Informal-Sector Health Insurance under Nigeria's NHIA Act 2022*.
Working paper.

## Licence

Code is MIT-licensed. The survey microdata are governed by the World Bank
Microdata Library's terms of use and are not covered by that licence.

## The research programme

This repository is one of six in *Health-Cost Risk and Financial Protection*, a
programme of actuarial research on how households and health-financing systems
absorb the cost of illness.

| # | Repository | Subject |
|---|---|---|
| 2 | [`nigeria-health-protection-gap`](https://github.com/tosin-babs/nigeria-health-protection-gap) | Nigeria's protection gap and informal-sector pricing |
| 3 | [`us-nigeria-health-cost-tail-risk`](https://github.com/tosin-babs/us-nigeria-health-cost-tail-risk) | Harmonized US-Nigeria comparison of tail risk |
| 4 | [`aca-risk-pool-subsidy-cliff`](https://github.com/tosin-babs/aca-risk-pool-subsidy-cliff) | ACA individual-market selection after the subsidy cliff |
| 5 | [`medicare-cost-of-aging`](https://github.com/tosin-babs/medicare-cost-of-aging) | Multi-state model of lifetime Medicare cost |
| 6 | [`fair-ml-health-risk-adjustment`](https://github.com/tosin-babs/fair-ml-health-risk-adjustment) | Fair, interpretable ML for risk adjustment |

## Author

Oluwatosin Dorcas Babalola — Georgia State University — obabalola4@student.gsu.edu
