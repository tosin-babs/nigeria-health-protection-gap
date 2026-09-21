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

# ---------------------------------------------------------- analysis wave ----
# "w4": GHS-Panel wave 4 (2018/19), with the published consumption aggregate.
# "w5": wave 5 (2023/24), with the rebuilt and calibrated aggregate.
PRIMARY_WAVE = "w4"

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

# Derivation, so this can be re-checked rather than taken on trust:
#   Target   NBS all-items CPI, August 2023          = 593.6  (Nov 2009 = 100)
#   Base     the 2018/19 survey period. GHS-W4 was fielded Jul-Sep 2018 and
#            Jan-Feb 2019; the NLSS that sets the poverty line ran Sep 2018 to
#            Oct 2019. Annual-average all-items CPI was 240.1 in 2018 and 267.5
#            in 2019, so a fieldwork-weighted base is about 257.5.
#   Ratio    593.6 / 257.5 = 2.31
# Anchoring instead on September 2018 alone (about 247.4) gives 2.40, so the
# plausible range is roughly 2.3-2.4. The poverty-line sensitivity in Table 8c
# spans 0.5x to 1.5x the resulting line and comfortably covers that range.
# [VERIFY] against the NBS monthly CPI series before submission - replace the
# interpolated base with the published index for the exact month.
CPI_W4_TO_W5 = 2.31

# ------------------------------------------------- health module recalls ----
OUTPATIENT_RECALL_WEEKS = 4.0     # s3q5-s3q17a: illness and care in the last 4 weeks
INPATIENT_RECALL_MONTHS = 12.0    # s3q18-s3q20: hospitalisation in the last 12 months
WEEKS_PER_YEAR = 52.0
# Annualising a 4-week window by 13 assumes the window is representative.
# Section 5.6 tests 13x against a seasonally damped 10x.
OUTPATIENT_ANNUALISER = WEEKS_PER_YEAR / OUTPATIENT_RECALL_WEEKS
# Recall-treatment bounds (bounds.py). The headline scales each person's
# observed 4-week spending to a year, which assumes the other twelve windows
# repeat the observed one (full within-year persistence) and so maximises the
# dispersion of annual cost. The lower case draws each person's annual cost as
# a sum of independent 4-week windows from the fitted frequency and severity
# models (no persistence). The truth lies between the two.
RECALL_BOUND_REPLICATES = 20      # independent-window replicates averaged
RECALL_ANNUALISER_CASES = (13.0, 12.0, 10.0)  # 12 = the monthly convention

# --------------------------------------------- consumption calibration ----
# Wave 5 publishes no consumption aggregate. The rebuilt aggregate recovers
# only part of the official wave-4 level and omits imputed rent, and on wave 4
# that shortfall raises CHE at the 10% threshold by about 3.5 points. The main
# results therefore use a calibrated aggregate: each rebuilt component is
# scaled by the ratio of its official to its rebuilt wave-4 mean, and imputed
# rent is added at the official wave-4 rent-to-non-rent ratio. The factors are
# estimated by build_data.calibration_factors() and written to
# output/tables/tableA1b_calibration.csv; the uncalibrated aggregate is kept
# as cons_annual_raw and reported alongside.
CALIBRATE_CONSUMPTION = True

# --------------------------------------------------- benefit-package rules ----
# NHIA basic minimum package. The Authority's tariff schedule is not public in
# a machine-readable form, so the package is defined transparently here as a
# share of observed spending by care type, and every share is a robustness knob.
# [VERIFY] against the NHIA Operational Guidelines before submission.
COVERED_SHARE_OUTPATIENT = 0.85   # share of outpatient spend falling inside the package
COVERED_SHARE_INPATIENT = 0.90    # share of inpatient spend inside the package
COVERED_SHARE_TRADITIONAL = 0.0   # traditional / spiritual care is excluded
COINSURANCE_DRUGS = 0.10          # NHIA 10% co-payment on drugs  [VERIFY current rule]
# Measured, not assumed. The wave-5 questionnaire separates the consultation fee
# (Q12, explicitly "excluding drugs") from prescription drugs (Q17) and
# non-prescription drugs (Q17a). Summed over all outpatient episodes with any
# spending, drugs are 86.25% of outpatient cost and the consultation fee 13.75%.
# build_data.py recomputes and prints this on every run; it is kept here as a
# lever so the robustness grid can move it.
DRUG_SHARE_OF_OUTPATIENT = 0.8613  # drugs / (consultation + drugs); wave 4: s4aq14 over s4aq9 + s4aq14
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
MEDICAL_INFLATION_SHOCK = 0.25    # permanent level shift in claims from year 2 (stress)
RUIN_TARGETS = (0.01, 0.05)
# Voluntary enrolment: take-up rates at which the selection tilt is evaluated.
# At 100% take-up everyone is in and no selection is possible, which is the
# mandatory case the Act envisages.
TAKE_UP_GRID = (0.10, 0.25, 0.50, 0.75, 1.00)
# Per-life excess-of-loss reinsurance: retentions (naira per person-year) and
# the loading on the expected ceded cost.
REINSURANCE_RETENTIONS = (250_000.0, 500_000.0, 1_000_000.0)
REINSURANCE_LOADING = 0.30
# Contribution schedules for the pool (ruin.py, counterfactual.py):
#   flat    one contribution for everyone, the Q1-Q3 affordable average
#   graded  each quintile pays the ceiling for its own quintile
#   exempt  Q1 and Q2 pay nothing (the vulnerable group), Q3-Q5 graded
CONTRIBUTION_SCHEDULES = ("flat", "graded", "exempt")
EXEMPT_QUINTILES = (1, 2)
# Design-based bootstrap for the premium and subsidy (bounds.py).
BOOT_REPLICATES = 200
BOOT_N_SIM = 2_000

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
