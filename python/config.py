"""
Paper 2 - Nigeria health-protection gap and informal-sector insurance pricing.

Central configuration: paths, survey-design settings, and every analytic
parameter that a reviewer might want to change. Nothing here is estimated;
all of these are choices, and each one is echoed into output/params_used.json
by run_all.py so that any reported number can be traced back to its inputs.
"""

from pathlib import Path

# ---------------------------------------------------------------- paths ----
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
W5_PP = RAW / "ghs_w5" / "Post Planting Wave 5" / "Household"
W5_PH = RAW / "ghs_w5" / "Post Harvest Wave 5" / "Household"
W4 = RAW / "ghs_w4"
DERIVED = ROOT / "data" / "derived"
TABLES = ROOT / "output" / "tables"
FIGURES = ROOT / "output" / "figures"

for _p in (DERIVED, TABLES, FIGURES):
    _p.mkdir(parents=True, exist_ok=True)

SEED = 2026

# --------------------------------------------------------- survey design ----
# secta_plantingw5 releases `strata` (6 levels, = geopolitical zone) and
# `ea` (enumeration area = PSU). Households with a missing wave-5 weight were
# not interviewed in the post-planting visit and are dropped.
PSU = "ea"
STRATA = "strata"
HH_WEIGHT = "hh_weight"
LONELY_PSU = "adjust"  # centre a singleton PSU on the grand mean, as in R's survey

# -------------------------------------------------------- CHE parameters ----
CHE_BUDGET_THRESHOLDS = (0.10, 0.25, 0.40)  # OOP / total consumption
CHE_CTP_THRESHOLD = 0.40                    # OOP / capacity to pay (Xu et al. 2003)
EQ_SCALE_POWER = 0.56                       # hhsize ** 0.56, Xu et al. (2003)
SUBSISTENCE_PCTL = (0.45, 0.55)             # food-share percentile band for SE_h

# National poverty line, NBS "Poverty and Inequality in Nigeria 2019":
# N137,430 per person per year, expressed in 2018/19 prices.
POVERTY_LINE_2019 = 137_430.0

# -------------------------------------------------------------- deflation ----
# All naira amounts are expressed in constant August-2023 prices (the month
# the GHS-W5 post-planting visit opened). W4 amounts are carried forward with
# the NBS composite CPI. The two anchors below are the only external numbers
# in the pipeline; both are set in one place so they can be re-verified.
# [VERIFY] against NBS CPI releases before the manuscript goes out.
CPI_BASE_LABEL = "August 2023"
CPI_W4_TO_W5 = 3.05   # composite CPI Aug-2023 / Sep-2018, NBS  [VERIFY]

# ------------------------------------------------- health module recalls ----
OUTPATIENT_RECALL_WEEKS = 4.0     # s3q5-s3q17a: illness and care in the last 4 weeks
INPATIENT_RECALL_MONTHS = 12.0    # s3q18-s3q20: hospitalisation in the last 12 months
WEEKS_PER_YEAR = 52.0
# Annualising a 4-week window by 13 assumes the window is representative.
# Section 5.6 tests 13x against a seasonally damped 10x.
OUTPATIENT_ANNUALISER = WEEKS_PER_YEAR / OUTPATIENT_RECALL_WEEKS

# --------------------------------------------------- benefit-package rules ----
# NHIA basic minimum package. The Authority's tariff schedule is not public in
# a machine-readable form, so the package is defined transparently here as a
# share of observed spending by care type, and every share is a robustness knob.
# [VERIFY] against the NHIA Operational Guidelines before submission.
COVERED_SHARE_OUTPATIENT = 0.85   # share of outpatient spend falling inside the package
COVERED_SHARE_INPATIENT = 0.90    # share of inpatient spend inside the package
COVERED_SHARE_TRADITIONAL = 0.0   # traditional / spiritual care is excluded
COINSURANCE_DRUGS = 0.10          # NHIA 10% co-payment on drugs  [VERIFY current rule]
DRUG_SHARE_OF_OUTPATIENT = 0.60   # drugs as a share of outpatient spend (from s3q17)
INDUCED_DEMAND_ELASTICITY = -0.20  # RAND HIE arc elasticity (Manning et al. 1987)
ELASTICITY_RANGE = (-0.10, -0.20, -0.35)

# ------------------------------------------------------- premium loadings ----
ADMIN_LOAD = 0.15          # administrative expense as a share of pure premium
RISK_MARGIN_SD_MULT = 0.10  # standard-deviation principle multiplier
CVAR_LEVEL = 0.95          # CVaR / TVaR level for the alternative risk margin
ADVERSE_SELECTION_LOAD = 0.10  # explicit loading in the base premium build-up
AFFORDABILITY_THRESHOLD = 0.05  # premium above 5% of consumption is unaffordable

# ------------------------------------------------------ ruin simulation ----
POOL_SIZES = (5_000, 20_000, 100_000)
RUIN_YEARS = (1, 3)
N_SIM = 10_000
EXPENSE_RATIO = 0.10             # expenses as a share of contribution income
INITIAL_CAPITAL_MULT = (0.0, 0.10, 0.25, 0.50)  # u0 as a multiple of annual premium income
# Subsidy as a fraction of the gross premium. The grid runs past 100% because
# under adverse selection the pool's expected claim per enrollee exceeds the
# community-rated premium, so solvency needs more than the premium itself.
SUBSIDY_GRID = tuple(round(x / 100, 2) for x in range(0, 255, 5))  # 0%..250%
ADVERSE_SELECTION_STRENGTH = 2.0  # enrolment odds multiplier per SD of predicted cost
MEDICAL_INFLATION_SHOCK = 0.25    # one-off claims shock tested in the stress scenario
RUIN_TARGETS = (0.01, 0.05)

# --------------------------------------------------------------- plotting ----
FIG_DPI = 300
PALETTE = {
    "primary": "#1f4e79",
    "secondary": "#c0504d",
    "accent": "#4f81bd",
    "muted": "#7f7f7f",
    "light": "#d9d9d9",
    "green": "#548235",
    "orange": "#e36c09",
}
QUINTILE_COLORS = ["#1f4e79", "#2e75b6", "#9dc3e6", "#f4b183", "#c0504d"]
