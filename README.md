# Measuring the Health-Protection Gap and Pricing Informal-Sector Health Insurance under Nigeria's NHIA Act 2022

Reproduction code for the paper of that title. The analysis measures
catastrophic health expenditure in Nigeria on the 2023/24 General Household
Survey-Panel, prices the NHIA basic benefit package for informal-sector
workers, tests whether a state-level pool could stay solvent under alternative
take-up and financing designs, and asks how much of the catastrophic-spending
burden coverage would remove.

## Interactive calculator

A companion web tool runs the pricing and solvency model in the browser: move
the benefit-design, loading and pool levers and watch the premium, the
affordability gap and the pool's probability of ruin recompute. It ships the
aggregated cost distribution the model needs, never the microdata.

**https://nigeria-health-protection-gap.vercel.app**

It is a single self-contained HTML file with no build step, no framework and no
runtime data fetch, deployed as a static site.

```bash
.venv/bin/python python/export_tool_data.py   # -> tool/model_data.json
.venv/bin/python python/build_tool.py         # -> tool/index.html
cd tool && vercel deploy --prod
```

`export_tool_data.py` collapses the individual file to the distinct
(outpatient, inpatient, traditional) cost triples the model is a function of,
and asserts that the collapsed payload reproduces the paper's pure premium to
within 1e-4 before writing it. `build_tool.py` inlines that payload into
`tool/index.template.html` and wraps the result in a complete HTML document.

The browser cannot run the paper's full ruin simulation, so the page matches
the first three moments of the same claims distribution with a translated
gamma. Against the paper's own simulation the two agree to within 0.7% at the 99th
percentile and 1.1% at the 99.9th percentile of annual claims across every pool
size and take-up pattern the page offers (worst case: a 5,000-life pool).

## What the code does

| Stage | Script | Output |
|---|---|---|
| Calibration factors from wave 4, then the household and individual analysis files | `python/build_data.py` | `data/derived/*.csv`, Tables A1 |
| CHE incidence, intensity, impoverishment, concentration, observed coverage | `python/che.py` | Tables 1, 2, 3, A2, A3, A4 |
| Frequency, severity and Tweedie cost models | `python/costmodels.py` | Tables A6, A7 |
| Benefit mapping and premium build-up | `python/premium.py` | Tables 4, 5, A5 |
| Collective-risk model, minimum subsidy, take-up grid, contribution schedules, reinsurance | `python/ruin.py` | Tables 6, 7, A8, A12 |
| Coverage counterfactual with paired tests | `python/counterfactual.py` | Tables 8, A9, A10 |
| Robustness grid | `python/robustness.py` | Tables A11, A12 |
| Recall-treatment bounds and design-based bootstrap | `python/bounds.py` | Table 9 |
| Figures | `python/exhibits.py` | `output/figures/*.png`, `*.pdf` |
| Calculator payload | `python/export_tool_data.py` | `tool/model_data.json` |
| Check the prose against the tables | `python/check_manuscript.py` | pass/fail |
| Submission documents | `python/make_manuscript.py` | `manuscript/*.docx`, `*.pdf` |

Two modules are shared infrastructure rather than analysis steps:
`python/config.py` holds every analytic parameter in one place, and
`python/svy.py` implements the complex-survey estimators (Taylor-linearized
variances for a stratified single-stage cluster design, weighted quantiles,
concentration indices with the Erreygers correction and a Wagstaff
decomposition). `svy.py` is written to be survey-agnostic.

## Reproducing

```bash
python3 -m venv .venv
.venv/bin/pip install numpy pandas scipy statsmodels matplotlib pypdf
.venv/bin/python python/run_all.py
```

Runs end to end in about fifteen minutes on a laptop; most of that is the
bootstrap. The last three steps rebuild the calculator payload, verify that
every headline figure in the manuscript still matches the regenerated tables,
and produce the submission `.docx` and `.pdf`. Building the documents needs
pandoc (`brew install pandoc`); the PDF also uses headless Chrome
rather than LaTeX. Every random draw is seeded from `config.SEED`, and
`output/params_used.json` records the full parameter set and library versions
used for the run that produced the current tables.

Tested with Python 3.14, numpy 2.5, pandas 3.0, scipy 1.18, statsmodels 0.15.

## Data

The analysis uses the Nigeria General Household Survey-Panel, waves 4 (2018/19)
and 5 (2023/24), collected by the National Bureau of Statistics with the World
Bank LSMS-ISA program. **The microdata are not redistributed here.** Download
them from the World Bank Microdata Library (free registration), then unzip into:

```
data/raw/ghs_w5/    <- NGA_2023_GHSP-W5_v01_M_CSV.zip
data/raw/ghs_w4/    <- NGA_2018_GHSP-W4_v03_M_CSV.zip
```

`config.py` expects the wave-5 archive's own folder layout
(`Post Planting Wave 5/Household/...`) and the wave-4 archive's flat layout.

### Three things worth knowing before you read the results

**The wave-5 release ships no consumption aggregate, so the denominator is
rebuilt and then calibrated.** Wave 4 publishes `totcons_final.csv`; wave 5
does not. The denominator is rebuilt from the food, non-food and education
modules. Run on wave 4, the same code recovers 84% of the official level and
omits imputed rent, and on wave 4 that shortfall raises CHE at the 10%
threshold from 14.1% to 17.6% with out-of-pocket spending held fixed. The main
results therefore scale each rebuilt component by the ratio of its official to
its rebuilt wave-4 mean and add rent at the official rent share; on wave 4 the
calibrated aggregate recovers 96% of the official level and gives CHE of 15.2%
(Table A1). The uncalibrated figures are reported alongside in Table 2 and in
the robustness grid.

**Out-of-pocket spending is measured from the health module, not the
consumption module.** Wave 5's non-food module asks a single 12-month question
about health spending and gets an answer from only 17% of households, implying
an out-of-pocket share of 0.3% of consumption against 4.9% in the published
wave-4 aggregate. The health module asks every member about a specific episode
of care and its itemized cost. The consumption-module figure is reported in the
robustness grid as a data-quality note.

**The 4-week outpatient window is scaled to a year.** That assumes the other
twelve windows repeat the observed one, which maximizes the dispersion of
annual cost across households; the opposite assumption (independent 4-week
windows drawn from the fitted frequency model) is the lower bound. Both are
carried through CHE, the premium and the subsidy in Table 9. The published
wave-4 aggregate scales its own one-month health item by about twelve.

## Variable mapping

The health-module cost fields, confirmed against the Post-Planting Household
Questionnaire (World Bank Microdata catalogue 6410, document 180528):

| Variable | Question | Recall |
|---|---|---|
| `s3q12` | Consultation fee, explicitly excluding drugs | 4 weeks |
| `s3q13` | Transport to and from the facility (excluded by default) | 4 weeks |
| `s3q17` | Prescription drugs and medicines | 4 weeks |
| `s3q17a` | Non-prescription drugs and medicines | 4 weeks |
| `s3q20` | Hospital stay, including consultation, procedures and drugs | 12 months |

Informal-sector status uses employer type (`s4aq52`) and firm size (`s4aq55`),
the latter because section 14 of the NHIA Act 2022 obliges employers with five
or more staff to enrol their workers. Three alternative rules are tested in
Table A11.

## Provenance

`SOURCES.md` lists every number in this project that did not come out of the
survey: the CPI deflator and its derivation, the poverty line, each
benefit-package assumption, the published state-scheme premiums, and every
contextual statistic quoted in the paper, each with its issuing agency and a
URL. Every DOI in the manuscript was checked against the Crossref REST API.

## Citation

Babalola, O. D., Iroko, O. E., & Oyinlade, O. (2026). *Measuring the Health-Protection Gap and Actuarially
Pricing Informal-Sector Health Insurance under Nigeria's NHIA Act 2022*.
Working paper.

## License

Code is MIT-licensed. The survey microdata are governed by the World Bank
Microdata Library's terms of use and are not covered by that license.

## Authors

- Oluwatosin Dorcas Babalola, Department of Actuarial Science, University of Lagos, Lagos, Nigeria, obabalola4@student.gsu.edu (corresponding)
- Oluwakemi Elizabeth Iroko, Department of Chemistry, University of Jos, Jos, Nigeria
- Oluwakemi Oyinlade, Department of Actuarial Science, University of Lagos, Lagos, Nigeria
