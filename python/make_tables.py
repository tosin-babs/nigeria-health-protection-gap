"""
Render the manuscript's tables from the analysis CSVs.

The prose cites table numbers; the tables themselves live in output/tables as
machine-written CSVs. This turns those CSVs into formatted markdown so the
submitted document and the analysis output cannot drift apart. Column names,
rounding and units are set here, once, rather than in each CSV.

Main-text tables are numbered 1-8; appendix tables A1-A13. check_manuscript.py
verifies that every rendered table is cited and every cited table rendered.

Writes manuscript/tables.md.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config

OUT = config.ROOT / "manuscript" / "tables.md"
T = config.TABLES


def money(x):
    return "" if pd.isna(x) else f"{x:,.0f}"


def pct(x, d=1):
    return "" if pd.isna(x) else f"{x:,.{d}f}"


def num(x, d=3):
    return "" if pd.isna(x) else f"{x:,.{d}f}"


def auto(d=1):
    """Format numbers, pass anything else through unchanged."""
    def f(x):
        if pd.isna(x):
            return ""
        if isinstance(x, (int, float, np.integer, np.floating)):
            return f"{x:,.{d}f}"
        return str(x)
    return f


def render(df, cols, fmts, headers=None):
    """A markdown table from selected columns with per-column formatters."""
    out = pd.DataFrame({c: df[c].map(f) if f else df[c].astype(str)
                        for c, f in zip(cols, fmts)})
    out.columns = headers or cols
    align = ["---" if i == 0 else "---:" for i in range(len(out.columns))]
    lines = ["| " + " | ".join(out.columns) + " |",
             "|" + "|".join(align) + "|"]
    for _, r in out.iterrows():
        lines.append("| " + " | ".join(str(v) for v in r) + " |")
    return "\n".join(lines)


def caption(n, title, note=None):
    s = f"\n**Table {n}.** {title}\n"
    if note:
        s += f"\n*{note}*\n"
    return s


def main():
    parts = ["# Tables\n",
             "*Generated from output/tables/*.csv by python/make_tables.py. "
             "All estimates are survey-weighted with Taylor-linearized standard "
             "errors for a stratified single-stage cluster design. Naira are in "
             f"constant {config.CPI_BASE_LABEL} prices. Consumption is the "
             "calibrated aggregate unless a row says otherwise.*\n"]

    # ---- Table 1: sample -----------------------------------------------------
    t1 = pd.read_csv(T / "table1_sample.csv")
    parts += [caption(1, "Sample characteristics, weighted by household weight.",
                      "p is a design-based Wald test of the informal-formal "
                      "difference."),
              render(t1, ["characteristic", "overall", "overall_se", "informal",
                          "formal", "p_diff"],
                     [None, lambda x: f"{x:,.2f}", lambda x: f"{x:,.2f}",
                      lambda x: f"{x:,.2f}", lambda x: f"{x:,.2f}",
                      lambda x: f"{x:,.3f}"],
                     ["Characteristic", "Overall", "SE", "Informal", "Formal", "p"])]

    # ---- Table 2: CHE --------------------------------------------------------
    t2 = pd.read_csv(T / "table2_che.csv")
    keep = ["Overall", "Overall (household-weighted)", "Sector", "Consumption quintile"]
    t2m = t2[t2["dimension"].isin(keep)].copy()
    cal = pd.read_csv(T / "table2d_calibration.csv")
    unc = cal[(cal["aggregate"] == "Uncalibrated")
              & (cal["measure"] != "Mean consumption per capita (N)")].copy()
    unc = unc.rename(columns={"se": "incidence_se"})
    unc["dimension"] = "Overall, uncalibrated aggregate"
    unc["group"] = "All households"
    unc["mean_overshoot_pct"] = np.nan
    unc["mean_positive_overshoot_pct"] = np.nan
    unc["n"] = int(t2m["n"].max())
    t2m = pd.concat([t2m, unc[t2m.columns]], ignore_index=True)
    order = {"Overall": 0, "Overall (household-weighted)": 1,
             "Overall, uncalibrated aggregate": 2, "Sector": 3,
             "Consumption quintile": 4}
    t2m["o"] = t2m["dimension"].map(order)
    t2m = t2m.sort_values(["measure", "o"], kind="stable")
    parts += [caption(2, "Catastrophic health expenditure: incidence and intensity.",
                      "Population-weighted rates are the share of people living "
                      "in an affected household; the household-weighted row is "
                      "the share of households. Uncalibrated rows use the rebuilt "
                      "consumption aggregate without the wave-4 calibration. "
                      "Zone and residence breakdowns are in Table A2."),
              render(t2m, ["measure", "dimension", "group", "incidence_pct",
                           "ci_low", "ci_high", "mean_positive_overshoot_pct", "n"],
                     [None, None, None, lambda x: pct(x, 1), lambda x: pct(x, 1),
                      lambda x: pct(x, 1), lambda x: pct(x, 1), lambda x: f"{x:,.0f}"],
                     ["Measure", "Dimension", "Group", "Incidence %", "95% low",
                      "95% high", "Mean positive overshoot pp", "n"])]

    # ---- Table 3: concentration and sector gaps ------------------------------
    t3 = pd.read_csv(T / "table3_concentration.csv")
    gaps = pd.read_csv(T / "table2c_sector_gaps.csv")
    parts += [caption(3, "Concentration indices and the informal-formal gap.",
                      "Indices are ranked on per-capita consumption; a negative "
                      "value means the outcome is concentrated among the poor. "
                      "Erreygers is the bounded correction for binary outcomes. "
                      "The sector gap is tested with a design-based Wald test; the "
                      "bottom panel reports the informal coefficient from a "
                      "population-weighted linear probability model with standard "
                      "errors clustered on the enumeration area."),
              render(t3, ["outcome", "mean", "CI", "CI_ci_low", "CI_ci_high",
                          "Erreygers", "Erreygers_se"],
                     [None, lambda x: num(x, 3), lambda x: num(x, 3),
                      lambda x: num(x, 3), lambda x: num(x, 3),
                      lambda x: num(x, 3), lambda x: num(x, 3)],
                     ["Outcome", "Mean", "CI", "95% low", "95% high",
                      "Erreygers", "SE"]),
              "",
              render(gaps, ["outcome", "informal", "informal_se", "formal",
                            "formal_se", "difference_pp", "p_value"],
                     [None, lambda x: pct(x, 1), lambda x: pct(x, 1),
                      lambda x: pct(x, 1), lambda x: pct(x, 1),
                      lambda x: pct(x, 1), lambda x: num(x, 3)],
                     ["Outcome (%)", "Informal", "SE", "Formal", "SE",
                      "Difference pp", "p"]),
              "",
              render(pd.read_csv(T / "table2e_adjusted_gap.csv"),
                     ["outcome", "controls", "informal_coef_pp", "se_pp", "p_value"],
                     [None, None, lambda x: pct(x, 1), lambda x: pct(x, 1),
                      lambda x: num(x, 3)],
                     ["Outcome", "Controls", "Informal coefficient pp", "SE", "p"])]

    # ---- Table 4: premium build-up -------------------------------------------
    b = pd.read_csv(T / "table5a_premium_buildup.csv")
    g = pd.read_csv(T / "table5c_gross_premium.csv")
    g20 = g[g["pool_size"] == 20_000]
    a = pd.read_csv(T / "table5d_affordability.csv")
    aff = pd.read_csv(T / "table6a_affordable_contribution.csv")
    parts += [caption(4, "From observed spending to the gross premium, and what "
                         "households can pay.",
                      "Naira per person per year. Second panel: loadings for a "
                      "20,000-life pool on the two risk-margin conventions (other "
                      "pool sizes in Table A5). Third panel: the gross premium "
                      "against per-capita consumption by quintile; quintiles rank "
                      "people, and household size is the household-weighted mean "
                      "since a premium is billed once per household. Fourth panel: "
                      "the contribution ceiling, 5% of the mean per-capita "
                      "consumption of informal-sector members of each quintile."),
              render(b, ["step", "naira_per_person_year", "change"],
                     [None, money, money], ["Step", "Naira", "Change"]),
              "",
              render(g20, ["risk_margin_basis", "pure_premium", "risk_margin",
                           "admin_load", "adverse_selection_load",
                           "gross_premium_per_person"],
                     [None, money, money, money, money, money],
                     ["Risk-margin basis", "Pure premium", "Risk margin",
                      "Admin 15%", "Selection 10%", "Gross premium"]),
              "",
              render(a, ["quintile", "mean_consumption_per_capita",
                         "mean_household_size",
                         "premium_pct_of_per_capita_consumption",
                         "premium_per_household"],
                     [None, money, lambda x: num(x, 1), lambda x: pct(x, 1), money],
                     ["Quintile", "Consumption per capita", "Household size",
                      "Premium as % of consumption", "Premium per household"]),
              "",
              render(aff, ["group", "mean_consumption_per_capita",
                           "affordable_contribution"],
                     [None, money, money],
                     ["Informal-sector group", "Consumption per capita",
                      "Contribution ceiling (5%)"])]

    # ---- Table 6: subsidy ----------------------------------------------------
    sub = pd.read_csv(T / "table6c_minimum_subsidy.csv")
    sub = sub[(sub["initial_capital_mult"] == 0.0) & (sub["years"] == 3)]
    tk = pd.read_csv(T / "table6f_take_up.csv")
    parts += [caption(5, "Minimum subsidy per enrollee for a ruin probability below "
                         "the target over three years, no opening capital.",
                      "Upper panel: by pool size and take-up pattern, at the flat "
                      "contribution. Lower panel: a 20,000-life pool by take-up "
                      "rate, where enrollment probability rises with predicted cost "
                      "by the tilt factor per standard deviation of log predicted "
                      "cost; at 100% take-up everyone enrolls and no selection is "
                      "possible."),
              render(sub, ["pool_size", "take_up", "ruin_target",
                           "min_subsidy_per_enrollee",
                           "min_subsidy_pct_of_gross_premium",
                           "annual_cost_per_100k_enrollees_naira_bn"],
                     [lambda x: f"{x:,.0f}", None, lambda x: f"{x:.0%}", money,
                      lambda x: pct(x, 0), lambda x: num(x, 2)],
                     ["Pool size", "Take-up", "Ruin target", "Subsidy",
                      "% of gross premium", "N bn per 100,000 enrollees"]),
              "",
              render(tk, ["tilt", "take_up", "expected_claim_per_enrollee",
                          "selection_loading_pct", "min_subsidy_per_enrollee",
                          "min_subsidy_pct_of_gross_premium"],
                     [None, lambda x: f"{x:.0%}", money, lambda x: pct(x, 0),
                      money, lambda x: pct(x, 0)],
                     ["Tilt", "Take-up", "Expected claim", "Selection loading %",
                      "Subsidy, ruin < 5%", "% of gross premium"])]

    # ---- Table 7: financing designs ------------------------------------------
    sch = pd.read_csv(T / "table6e_contribution_schedules.csv")
    sch["schedule"] = sch["schedule"].map({
        "flat": "Flat (Q1-Q3 ceiling for all)",
        "graded": "Graded (each quintile's own ceiling)",
        "exempt": "Q1-Q2 exempt, Q3-Q5 graded"})
    ri = pd.read_csv(T / "table6g_reinsurance.csv")
    ri["retention"] = ri["retention"].map(lambda x: "None" if pd.isna(x) else f"{x:,.0f}")
    parts += [caption(6, "Financing designs for a 20,000-life pool: contribution "
                         "schedules and per-life excess-of-loss reinsurance.",
                      "Minimum subsidy holds the three-year ruin probability below "
                      "5%. Reinsurance cedes each person's annual cost above the "
                      "retention for a premium of 1.3 times the expected ceded "
                      "cost."),
              render(sch, ["schedule", "take_up", "mean_contribution_per_enrollee",
                           "expected_claim_per_enrollee", "min_subsidy_per_enrollee",
                           "subsidy_share_of_cost"],
                     [None, None, money, money, money, lambda x: f"{x:.0%}"],
                     ["Contribution schedule", "Take-up", "Mean contribution",
                      "Expected claim", "Minimum subsidy", "Subsidy share"]),
              "",
              render(ri, ["take_up", "retention", "reinsurance_premium_per_enrollee",
                          "sd_pool_claims_per_enrollee", "p99_pool_claims_per_enrollee",
                          "min_subsidy_per_enrollee"],
                     [None, None, money, money, money, money],
                     ["Take-up", "Retention", "Reinsurance premium",
                      "SD of claims per enrollee", "p99 of claims per enrollee",
                      "Minimum subsidy"])]

    # ---- Table 8: counterfactual ---------------------------------------------
    red = pd.read_csv(T / "table7b_reductions.csv")
    red = red[red["measure"].isin(["che10", "che_ctp40"])].copy()
    red["measure"] = red["measure"].map({"che10": "Budget share > 10%",
                                         "che_ctp40": "Capacity to pay >= 40%"})
    parts += [caption(7, "Change in catastrophic expenditure under coverage "
                         "scenarios.",
                      "Paired design-based test of the change on the same "
                      "households. A negative reduction means catastrophic "
                      "expenditure rises. Levels for every scenario and quintile "
                      "are in Tables A9 and A10."),
              render(red, ["scenario", "payment_basis", "measure", "baseline_pct",
                           "counterfactual_pct", "reduction_pp", "reduction_se",
                           "p_value"],
                     [None, None, None, lambda x: pct(x, 1), lambda x: pct(x, 1),
                      lambda x: pct(x, 1), lambda x: pct(x, 1), lambda x: num(x, 3)],
                     ["Scenario", "Payment basis", "Measure", "Baseline %",
                      "Counterfactual %", "Reduction pp", "SE", "p"])]

    # ---- Table 9: recall bounds and bootstrap --------------------------------
    rb = pd.read_csv(T / "table9_recall_bounds.csv")
    bs = pd.read_csv(T / "table10_bootstrap.csv")
    labels = {"che10_pct": "CHE, budget share > 10% (%)",
              "che_ctp40_pct": "CHE, capacity to pay >= 40% (%)",
              "pure_premium": "Pure premium (N)", "gross_premium": "Gross premium (N)",
              "affordable_contribution": "Flat contribution (N)",
              "expected_claim_random": "Expected claim, random take-up (N)",
              "expected_claim_adverse": "Expected claim, strong selection (N)",
              "min_subsidy_random": "Minimum subsidy, random take-up (N)",
              "min_subsidy_adverse": "Minimum subsidy, strong selection (N)"}
    bs["quantity"] = bs["quantity"].map(labels).fillna(bs["quantity"])
    parts += [caption(8, "Recall-treatment bounds and design-based bootstrap "
                         "intervals.",
                      "Upper panel: the 4-week outpatient window scaled to a year "
                      "(full within-year persistence) against annual cost drawn as "
                      "independent 4-week windows from the fitted frequency model "
                      "(no persistence), and two smaller annualizers. Subsidies "
                      "are for a 20,000-life pool over three years, ruin below 5%. "
                      f"Lower panel: Rao-Wu rescaled bootstrap over enumeration "
                      f"areas within strata, {config.BOOT_REPLICATES} replicates, "
                      "percentile intervals."),
              render(rb, ["case", "che10_pct", "che_ctp40_pct", "pure_premium",
                          "gross_premium", "min_subsidy_random", "min_subsidy_adverse"],
                     [None, lambda x: pct(x, 1), lambda x: pct(x, 1), money, money,
                      money, money],
                     ["Recall treatment", "CHE10 %", "CTP40 %", "Pure premium",
                      "Gross premium", "Subsidy, random", "Subsidy, strong selection"]),
              "",
              render(bs, ["quantity", "point_estimate", "boot_se", "ci_low", "ci_high"],
                     [None, auto(1), auto(1), auto(1), auto(1)],
                     ["Quantity", "Point estimate", "Bootstrap SE", "2.5%", "97.5%"])]

    # ---- Appendix ------------------------------------------------------------
    parts += ["\n\n# Appendix tables\n"]

    a1 = pd.read_csv(T / "tableA1_aggregate_validation.csv")
    a1c = pd.read_csv(T / "tableA1c_calibration_check.csv")
    a1b = pd.read_csv(T / "tableA1b_calibration.csv")
    parts += [caption("A1", "The rebuilt consumption aggregate against wave 4's "
                            "published aggregate, and the calibration check.",
                      "Upper panel: component means. Lower panel: CHE on wave 4 "
                      "computed with the official aggregate, the rebuilt aggregate "
                      "and the calibrated rebuilt aggregate, holding out-of-pocket "
                      f"spending fixed. Calibration factors: food "
                      f"{a1b['food_factor'].iloc[0]:.3f}, non-food "
                      f"{a1b['nonfood_factor'].iloc[0]:.3f}, rent to non-rent "
                      f"{a1b['rent_ratio'].iloc[0]:.4f}."),
              render(a1, ["component", "official_mean_naira", "rebuilt_mean_naira",
                          "ratio_rebuilt_to_official", "pearson_r", "spearman_rho"],
                     [None, money, money, lambda x: num(x, 3),
                      lambda x: num(x, 3), lambda x: num(x, 3)],
                     ["Component", "Official mean", "Rebuilt mean", "Ratio",
                      "Pearson r", "Spearman rho"]),
              "",
              render(a1c, ["aggregate", "mean_naira", "ratio_to_official",
                           "spearman_vs_official", "che10_pct", "che25_pct",
                           "mean_oop_share_pct"],
                     [None, money, lambda x: num(x, 3), lambda x: num(x, 3),
                      lambda x: pct(x, 1), lambda x: pct(x, 1), lambda x: pct(x, 1)],
                     ["Wave-4 aggregate", "Mean", "Ratio to official",
                      "Spearman", "CHE10 %", "CHE25 %", "Mean OOP share %"])]

    t2a = t2[t2["dimension"].isin(["Residence", "Zone"])
             & t2["measure"].isin(["Budget share > 10%", "Capacity to pay >= 40%"])]
    cov = pd.read_csv(T / "table1b_coverage.csv")
    parts += [caption("A2", "Catastrophic expenditure by residence and zone, and "
                            "observed health-insurance coverage.",
                      "The 25% and 40% budget-share thresholds are in "
                      "output/tables/table2_che.csv."),
              render(t2a, ["measure", "dimension", "group", "incidence_pct",
                           "ci_low", "ci_high", "n"],
                     [None, None, None, lambda x: pct(x, 1), lambda x: pct(x, 1),
                      lambda x: pct(x, 1), lambda x: f"{x:,.0f}"],
                     ["Measure", "Dimension", "Group", "Incidence %", "95% low",
                      "95% high", "n"]),
              "",
              render(cov, ["dimension", "group", "hh_with_cover_pct",
                           "hh_with_cover_se", "individuals_covered_pct",
                           "hh_paid_premium_pct", "n"],
                     [None, None, lambda x: pct(x, 2), lambda x: pct(x, 2),
                      lambda x: pct(x, 2), lambda x: pct(x, 2), lambda x: f"{x:,.0f}"],
                     ["Dimension", "Group", "Households covered %", "SE",
                      "Individuals covered %", "Households paying a premium %", "n"])]

    imp = pd.read_csv(T / "table2b_impoverishment.csv")
    pov = pd.read_csv(T / "table8c_poverty_lines.csv")
    parts += [caption("A3", "Impoverishment from out-of-pocket payments, and its "
                            "sensitivity to the poverty line.",
                      "The headcount is a level and depends on the line and on the "
                      "consumption aggregate; the impoverishing effect is a "
                      "difference and moves much less."),
              render(imp, ["indicator", "estimate", "se"],
                     [None, lambda x: f"{x:,.2f}", lambda x: f"{x:,.2f}"],
                     ["Indicator", "Estimate", "SE"]),
              "",
              render(pov, ["poverty_line_naira", "multiple_of_national_line",
                           "headcount_before_pct", "headcount_after_pct",
                           "impoverishment_pp", "impoverished_millions"],
                     [money, auto(2), auto(1), auto(1), auto(2), auto(2)],
                     ["Poverty line", "x national line", "Headcount before %",
                      "Headcount after %", "Impoverishment pp", "Millions"])]

    d = pd.read_csv(T / "table3b_decomposition.csv")
    parts += [caption("A4", "Decomposition of the concentration indices.",
                      "Descriptive, not causal. Contributions are in index units; "
                      "shares are not shown for the budget-share index because it "
                      "is not distinguishable from zero and shares of a near-zero "
                      "total are not interpretable."),
              render(d, ["outcome", "variable", "beta", "mean_x", "CI_x",
                         "contribution"],
                     [None, None, auto(4), auto(3), auto(4), auto(4)],
                     ["Outcome", "Variable", "Beta", "Mean x", "CI of x",
                      "Contribution"])]

    g = pd.read_csv(T / "table5c_gross_premium.csv")
    rm = pd.read_csv(T / "table5b_risk_margins.csv")
    rc = pd.read_csv(T / "table5e_risk_classes.csv")
    sc = pd.read_csv(T / "table5f_state_comparison.csv")
    parts += [caption("A5", "Gross premium by pool size, risk margins, risk "
                            "relativities and the comparison with a published "
                            "state-scheme rate.",
                      "Relativities are relative to the community average; the "
                      "premium itself is community-rated. The Lagos comparison is "
                      "a plausibility check: the Ilera Eko package is not the NHIA "
                      "basic package, and its rates are nominal July-2024 naira."),
              render(g, ["pool_size", "risk_margin_basis", "risk_margin",
                         "gross_premium_per_person"],
                     [lambda x: f"{x:,.0f}", None, money, money],
                     ["Pool size", "Risk-margin basis", "Risk margin", "Gross premium"]),
              "",
              render(rm, ["pool_size", "risk_margin_sd", "risk_margin_cvar",
                          "sd_of_pool_mean"],
                     [lambda x: f"{x:,.0f}", money, money, money],
                     ["Pool size", "SD principle", "CVaR 95%", "SD of the pool mean"]),
              "",
              render(rc, ["dimension", "class", "n", "mean_insurer_cost", "relativity"],
                     [None, None, lambda x: f"{x:,.0f}", money, auto(2)],
                     ["Dimension", "Class", "n", "Mean insurer cost", "Relativity"]),
              "",
              render(sc, ["scheme", "annual_premium_naira",
                          "modelled_premium_per_person", "ratio_modelled_to_published"],
                     [None, money, money, auto(2)],
                     ["Scheme", "Published premium", "Modeled premium", "Ratio"])]

    d = pd.read_csv(T / "table4_cost_models.csv")
    d["cell"] = d.apply(lambda r: f"{r['exp_coef']:.3f}"
                        + ("*" if r["p"] < 0.05 else ""), axis=1)
    d["term"] = (d["term"].str.replace(r"C\((\w+)(?:, Treatment\(reference='[^']*'\))?\)\[T\.([^\]]+)\]",
                                       r"\1 \2", regex=True))
    short = {"Frequency: outpatient (Poisson, annual rate)": "Outpatient rate",
             "Frequency: inpatient (Poisson, annual rate)": "Inpatient rate",
             "Severity: cost per outpatient episode (gamma)": "Outpatient cost",
             "Severity: cost per inpatient episode (gamma)": "Inpatient cost",
             "Aggregate annual cost (Tweedie, p=1.65)": "Annual cost (Tweedie)"}
    order = [t for t in d["term"].unique()]
    w = (d.assign(model=d["model"].map(short))
          .pivot_table(index="term", columns="model", values="cell", aggfunc="first")
          .reindex(order).reindex(columns=list(short.values())).fillna("").reset_index())
    parts += [caption("A6", "Frequency, severity and Tweedie model estimates, as "
                            "multiplicative effects on the fitted mean.",
                      "exp(coef); * marks p < 0.05. Survey-weighted, standard "
                      "errors clustered on the enumeration area. Coefficients, "
                      "standard errors and z statistics are in "
                      "output/tables/table4_cost_models.csv. Reference "
                      "categories: age 25-44, North Central, quintile 1."),
              render(w, ["term"] + list(short.values()), [None] * 6,
                     ["Term"] + list(short.values()))]

    fit = pd.read_csv(T / "table4b_fit_statistics.csv")
    prof = pd.read_csv(T / "tableA2_tweedie_profile.csv")
    lift = pd.read_csv(T / "tableA3_lift.csv")
    parts += [caption("A7", "Cost-model fit statistics, the Tweedie profile "
                            "likelihood near its maximum, and calibration by "
                            "decile of prediction.",
                      "The full profile is in output/tables/tableA2_tweedie_profile.csv."),
              render(fit, ["statistic", "value"], [None, lambda x: f"{x:,.3f}"],
                     ["Statistic", "Value"]),
              "",
              render(prof[prof["converged"]].sort_values("loglik", ascending=False).head(7).sort_values("p"),
                     ["p", "loglik", "deviance"],
                     [auto(2), auto(1), auto(1)], ["p", "Log-likelihood", "Deviance"]),
              "",
              render(lift, ["decile", "n", "predicted_mean", "observed_mean",
                            "ratio_obs_pred", "lift"],
                     [lambda x: f"{x:,.0f}", lambda x: f"{x:,.0f}", money, money,
                      lambda x: num(x, 3), lambda x: num(x, 2)],
                     ["Decile", "n", "Predicted mean", "Observed mean",
                      "Observed / predicted", "Lift"])]

    d = pd.read_csv(T / "table6b_ruin_scenarios.csv")
    d = d[(d["years"] == 3) & (d["initial_capital_mult"] == 0.0)
          & (d["pool_size"] == 20_000)
          & (d["subsidy_fraction_of_premium"].isin([0.0, 0.50, 1.00, 1.50, 2.00]))]
    st = pd.read_csv(T / "table6d_inflation_stress.csv")
    parts += [caption("A8", "Probability of ruin over three years for a "
                            "20,000-life pool with no opening capital, and the "
                            "medical-inflation stress.",
                      "The full grid across pool sizes of 5,000 to 100,000, "
                      "take-up patterns, subsidy levels in 5% steps, horizons and "
                      "capital multiples is in output/tables/table6b_ruin_scenarios.csv. "
                      "The stress is a permanent 25% rise in claims from year 2."),
              render(d, ["pool_size", "take_up", "subsidy_fraction_of_premium",
                         "subsidy_per_enrollee", "psi", "mc_se"],
                     [lambda x: f"{x:,.0f}", None, lambda x: f"{x:.0%}", money,
                      auto(4), auto(4)],
                     ["Pool size", "Take-up", "Subsidy", "Per enrollee",
                      "Ruin probability", "MC SE"]),
              "",
              render(st, ["medical_inflation_shock", "take_up", "min_subsidy_per_enrollee"],
                     [lambda x: f"{x:.0%}", None, money],
                     ["Claims shock", "Take-up", "Minimum subsidy"])]

    d = pd.read_csv(T / "table7a_counterfactual.csv")
    parts += [caption("A9", "Catastrophic spending under each coverage scenario, on "
                            "both payment bases."),
              render(d, ["scenario", "payment_basis", "share_of_population_covered",
                         "che10_pct", "che25_pct", "che_ctp40_pct",
                         "poverty_after_payments_pct", "mean_household_health_payments"],
                     [None, None, lambda x: f"{x:.1%}", auto(1), auto(1), auto(1),
                      auto(1), money],
                     ["Scenario", "Payment basis", "Covered", "CHE10 %", "CHE25 %",
                      "CTP40 %", "Poverty after %", "Mean payments"])]

    d = pd.read_csv(T / "table7c_by_quintile.csv")
    w = (d.pivot_table(index=["scenario", "measure"], columns="group",
                       values="estimate_pct", aggfunc="first").reset_index())
    qcols = [c for c in w.columns if c not in ("scenario", "measure")]
    parts += [caption("A10", "Counterfactual catastrophic spending by consumption "
                             "quintile, out-of-pocket plus contribution basis "
                             "(percent).",
                      "Design-based 95% intervals for every cell are in "
                      "output/tables/table7c_by_quintile.csv."),
              render(w, ["scenario", "measure"] + qcols,
                     [None, None] + [auto(1)] * len(qcols),
                     ["Scenario", "Measure"] + [str(c) for c in qcols])]

    rob = pd.read_csv(T / "table8_robustness.csv")
    parts += [caption("A11", "Robustness grid.",
                      "Each row changes one decision. Subsidies are for a "
                      "20,000-life pool over three years, ruin below 5%, "
                      "4,000 simulations."),
              render(rob, ["check", "che10_pct", "che_ctp40_pct", "pure_premium",
                           "gross_premium", "affordable_contribution",
                           "min_subsidy_random", "min_subsidy_adverse"],
                     [None, auto(1), auto(1), money, money, money, money, money],
                     ["Check", "CHE10 %", "CTP40 %", "Pure premium", "Gross premium",
                      "Contribution", "Subsidy, random", "Subsidy, strong selection"])]

    w4 = pd.read_csv(T / "table8b_wave4.csv")
    a4 = pd.read_csv(T / "tableA4_simulation_check.csv")
    parts += [caption("A12", "Wave 4 (2018/19) on the published aggregate, and the "
                             "multinomial simulation shortcut checked against direct "
                             "resampling.",
                      "The wave-4 out-of-pocket measure comes from the published "
                      "aggregate, which annualizes a one-month health recall by "
                      "about twelve; it is not the wave-5 health-module measure."),
              render(w4, ["wave", "measure", "estimate_pct", "se"],
                     [None, None, auto(1), auto(1)],
                     ["Wave", "Measure", "Estimate %", "SE"]),
              "",
              render(a4, list(a4.columns), [None] + [auto(4) for _ in a4.columns[1:]],
                     [c.replace("_", " ").capitalize() for c in a4.columns])]

    OUT.write_text("\n".join(parts) + "\n")
    n = sum(1 for line in OUT.read_text().splitlines() if line.startswith("**Table"))
    print(f"wrote {OUT.relative_to(config.ROOT)} with {n} tables")


if __name__ == "__main__":
    main()
