# Measuring the Health-Protection Gap and Pricing Informal-Sector Health Insurance under Nigeria's NHIA Act 2022

Reproduction code for the paper of that title. The analysis measures
catastrophic health expenditure in Nigeria on the 2018/19 General Household
Survey-Panel (wave 4), prices the NHIA basic benefit package for informal-sector
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
| Household and individual analysis files from wave 4 | `python/build_data.py` | `data/derived/*.csv` |
| CHE incidence, intensity, impoverishment, concentration | `python/che.py` | Tables 1 to 3, A1 to A3 |
| Frequency, severity and Tweedie cost models | `python/costmodels.py` | Tables A5, A6 |
| Benefit mapping and premium build-up | `python/premium.py` | Table 4, A4 |
| Collective-risk model, minimum subsidy, take-up grid, contribution schedules, reinsurance | `python/ruin.py` | Tables 5, 6, A7, A11 |
| Coverage counterfactual with paired tests | `python/counterfactual.py` | Tables 7, A8, A9 |
| Robustness grid | `python/robustness.py` | Table A10 |
| Recall-treatment bounds and design-based bootstrap | `python/bounds.py` | Table 8 |
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

The analysis uses wave 4 (2018/19) of the Nigeria General Household
Survey-Panel, collected by the National Bureau of Statistics with the World Bank
LSMS-ISA program. **The microdata are not redistributed here.** Download them
from the World Bank Microdata Library (free registration), then unzip into:

```
data/raw/ghs_w4/    <- NGA_2018_GHSP-W4_v03_M_CSV.zip
```

`config.PRIMARY_WAVE` selects the analysis wave. The code for wave 5 (2023/24),
which rebuilds and calibrates a consumption aggregate because that release
ships none, is kept in `build_data.py` for comparison; set
`PRIMARY_WAVE = "w5"` and add `data/raw/ghs_w5/` to use it.

### Three things worth knowing before you read the results

**The denominator is the published consumption aggregate.** Wave 4 ships
`totcons_final.csv`, the World Bank's aggregate including imputed rent. Its
health components are replaced by health-module spending so that health
enters numerator and denominator from one instrument; using the aggregate's
own health items instead moves CHE at the 10% threshold by 0.1 points.

**Wave 4 has no insurance module.** Coverage is not measured, so it is
assigned in the counterfactual rather than estimated.

**The 4-week outpatient window is scaled to a year.** That assumes the other
twelve windows repeat the observed one, which maximizes the dispersion of
annual cost across households; the opposite assumption (independent 4-week
windows drawn from the fitted frequency model) is the lower bound. Both are
carried through CHE, the premium and the subsidy in Table 8. The published
aggregate scales its own one-month health item by about twelve.

## Variable mapping

Wave 4 health module (post-harvest visit, `sect4a_harvestw4.csv`):

| Variable | Question | Recall |
|---|---|---|
| `s4aq1` | Ill or injured | 4 weeks |
| `s4aq6a` | Who was consulted (0 nobody) | 4 weeks |
| `s4aq9` | Consultation fee | 4 weeks |
| `s4aq10` | Transport (excluded by default) | 4 weeks |
| `s4aq14` | Medicines bought, asked of everyone | 4 weeks |
| `s4aq15`, `s4aq17` | Hospitalized, and its cost | 12 months |

Answers are released as bare numeric codes. Informal-sector status uses the
wage-job employer (`s3q15`) and workplace size band (`s3q15c`) from the
planting labour module: government employers are formal, and any other
employer from the second size band up, taken as five or more workers, the
NHIA Act's threshold. Three alternative rules are tested in Table A10.

## Provenance

`SOURCES.md` lists every number in this project that did not come out of the
survey: the CPI deflator and its derivation, the poverty line, each
benefit-package assumption, and every
contextual statistic quoted in the paper, each with its issuing agency and a
URL. Every DOI in the manuscript was checked against the Crossref REST API.

## Citation

Babalola, O. D., Iroko, O. E., & Oyinlade, O. (n.d.). *Measuring the Health-Protection Gap and Actuarially
Pricing Informal-Sector Health Insurance under Nigeria's NHIA Act 2022*.
Working paper.

## License

Code is MIT-licensed. The survey microdata are governed by the World Bank
Microdata Library's terms of use and are not covered by that license.

## Authors

- Oluwatosin Dorcas Babalola, Department of Actuarial Science, University of Lagos, Lagos, Nigeria (corresponding)
- Oluwakemi Elizabeth Iroko, Department of Chemistry, University of Jos, Jos, Nigeria
- Oluwakemi Oyinlade, Department of Actuarial Science, University of Lagos, Lagos, Nigeria
