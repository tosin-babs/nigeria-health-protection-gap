"""
Render the manuscript's tables from the analysis CSVs.

The prose cites table numbers; the tables themselves live in output/tables as
machine-written CSVs. This turns those CSVs into a formatted markdown appendix
so the submitted document and the analysis output cannot drift apart. Column
names, rounding and units are set here, once, rather than in each CSV.

Writes manuscript/tables.md.
"""

from __future__ import annotations

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
    """Format numbers, pass anything else through unchanged.

    The robustness grid mixes numeric columns with label columns, so a single
    numeric formatter cannot be applied blindly across it.
    """
    def f(x):
        if pd.isna(x):
            return ""
        if isinstance(x, (int, float)):
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


# ---------------------------------------------------------------------------
# Table A5 is not produced by the pipeline: it is a reading of the literature,
# and every row is a paper whose DOI was checked against Crossref.
LIT_MATRIX = """
| Study | Data | Method | Key finding | What it does not do |
|---|---|---|---|---|
| Xu et al. (2003) | 59 countries | Capacity-to-pay CHE | Introduces the subsistence-net denominator | No pricing |
| Wagstaff & van Doorslaer (2003) | Vietnam 1993–98 | Budget-share CHE, overshoot | Separates incidence from intensity | No pricing |
| Wagstaff et al. (2018) | 133 countries | Budget-share CHE, SDG 3.8.2 | Global monitoring baseline | Single definition |
| Cylus et al. (2018) | Europe | Both definitions compared | Definitions give different pictures of who is affected | High-income setting |
| Quintal (2019) | Portugal, 3 HBS waves | CTP-based CHE, incidence and distribution | Distribution must be reported alongside incidence | No pricing |
| Aregbeshola & Khan (2018) | Nigeria 2009/10 | Budget-share CHE, impoverishment | 16.4% at the 10% threshold | No pricing or solvency |
| Edeh (2022) | Nigeria, multiple rounds | Decomposition over time | Traces CHE dynamics | No pricing or solvency |
| Opeloyeru & Lawanson (2023) | Nigeria | Determinants regression | Identifies household correlates | No pricing or solvency |
| Aniebo et al. (2025) | Nigeria 2023/24 | Budget-share and CTP CHE | 45.5% at the 10% threshold | No pricing or solvency |
| Ipinnimo et al. (2022) | NHIA Act text | Policy analysis | Vulnerable-group financing is the open question | No quantification |
| Ahmad & Lucero-Prisno (2022) | NHIA Act text | Commentary | Mandate does not create fiscal space | No quantification |
| Adewole et al. (2021) | NHIS enrolee data | Geospatial analysis | Access shapes use even among the insured | Formal sector only |
| Artignan & Bellanger (2021) | Sub-Saharan Africa, 16 studies | Rapid review of CBHI | Reviews effect on service use and equity in use | No premium or ruin model |
| Onasanya (2020) | Informal economy | Conceptual | Enrolment mechanisms for informal workers | No quantification |
| Jofre-Bonet & Kamara (2018) | Sierra Leone informal sector | Contingent valuation | Mean WTP ≈ USD 3.6/month, ≈5% of business income | Does not cost the package the premium must fund |
| Smyth & Jørgensen (2002) | Insurance claims | Tweedie GLM | Compound Poisson–gamma for claims | Not health, not LMIC |
| Wüthrich (2015) | Theory | Ruin theory to solvency capital | Links ruin probability to capital requirement | Not applied to health in an LMIC |
| Manning et al. (1987) | RAND HIE, USA | Randomised experiment | Arc elasticity ≈ −0.2 | 1970s USA |
| Boes & Gerfin (2016) | Switzerland | Non-linear diff-in-diff | Elasticity ≈ −0.14; more people generate any cost | High-income setting |
| **This paper** | **Nigeria GHS-Panel W5** | **CHE (both) + Tweedie + ruin + counterfactual** | **Price ₦25,864 vs ₦8,571 affordable; subsidy ₦15,523–₦50,210** | — |
"""


def main():
    parts = ["# Tables\n",
             "*Generated from `output/tables/*.csv` by `python/make_tables.py`. "
             "All estimates are survey-weighted with Taylor-linearised standard "
             "errors for a stratified single-stage cluster design. Naira are in "
             f"constant {config.CPI_BASE_LABEL} prices.*\n"]

    # ---- Table 1 -----------------------------------------------------------
    t1 = pd.read_csv(T / "table1_sample.csv")
    parts += [caption(1, "Sample characteristics, weighted by household weight."),
              render(t1, ["characteristic", "overall", "overall_se", "informal",
                          "formal", "p_diff"],
                     [None, lambda x: f"{x:,.2f}", lambda x: f"{x:,.2f}",
                      lambda x: f"{x:,.2f}", lambda x: f"{x:,.2f}",
                      lambda x: f"{x:,.3f}"],
                     ["Characteristic", "Overall", "SE", "Informal", "Formal",
                      "p"])]

    # ---- Table 1b ----------------------------------------------------------
    cov = pd.read_csv(T / "table1b_coverage.csv")
    parts += [caption("1b", "Observed health-insurance coverage.",
                      "Coverage is holding cover; premium payment is reporting a "
                      "premium in the consumption module. They differ because "
                      "employer-paid and subsidised cover involves no premium the "
                      "household pays."),
              render(cov, ["dimension", "group", "hh_with_cover_pct",
                           "hh_with_cover_se", "individuals_covered_pct",
                           "hh_paid_premium_pct", "n"],
                     [None, None, lambda x: pct(x, 2), lambda x: pct(x, 2),
                      lambda x: pct(x, 2), lambda x: pct(x, 2),
                      lambda x: f"{x:,.0f}"],
                     ["Dimension", "Group", "HH covered %", "SE",
                      "Individuals covered %", "HH paying a premium %", "n"])]

    # ---- Table 2 -----------------------------------------------------------
    t2 = pd.read_csv(T / "table2_che.csv")
    parts += [caption(2, "Catastrophic health expenditure: incidence and intensity."),
              render(t2, ["measure", "dimension", "group", "incidence_pct",
                          "ci_low", "ci_high", "mean_overshoot_pct",
                          "mean_positive_overshoot_pct", "n"],
                     [None, None, None, lambda x: pct(x, 2), lambda x: pct(x, 2),
                      lambda x: pct(x, 2), lambda x: pct(x, 2),
                      lambda x: pct(x, 2), lambda x: f"{x:,.0f}"],
                     ["Measure", "Dimension", "Group", "Incidence %", "95% low",
                      "95% high", "Mean overshoot pp", "Mean positive overshoot pp",
                      "n"])]

    # ---- Table 2b / 2c -----------------------------------------------------
    imp = pd.read_csv(T / "table2b_impoverishment.csv")
    parts += [caption("2b", "Impoverishment from out-of-pocket payments."),
              render(imp, ["indicator", "estimate", "se"],
                     [None, lambda x: f"{x:,.2f}", lambda x: f"{x:,.2f}"],
                     ["Indicator", "Estimate", "SE"])]

    gaps = pd.read_csv(T / "table2c_sector_gaps.csv")
    parts += [caption("2c", "Informal versus formal sector."),
              render(gaps, ["outcome", "informal", "informal_se", "formal",
                            "formal_se", "difference_pp", "p_value"],
                     [None, lambda x: pct(x, 2), lambda x: pct(x, 2),
                      lambda x: pct(x, 2), lambda x: pct(x, 2),
                      lambda x: pct(x, 2), lambda x: num(x, 3)],
                     ["Outcome", "Informal %", "SE", "Formal %", "SE",
                      "Difference pp", "p"])]

    # ---- Table 3 -----------------------------------------------------------
    t3 = pd.read_csv(T / "table3_concentration.csv")
    parts += [caption(3, "Concentration indices, ranked on per-capita consumption.",
                      "A negative index means the outcome is concentrated among "
                      "the poor. Erreygers is the bounded correction for binary "
                      "outcomes."),
              render(t3, ["outcome", "mean", "CI", "CI_ci_low", "CI_ci_high",
                          "Erreygers", "Erreygers_se"],
                     [None, lambda x: num(x, 3), lambda x: num(x, 3),
                      lambda x: num(x, 3), lambda x: num(x, 3),
                      lambda x: num(x, 3), lambda x: num(x, 3)],
                     ["Outcome", "Mean", "CI", "95% low", "95% high",
                      "Erreygers", "SE"])]

    # ---- Table 4b ----------------------------------------------------------
    fit = pd.read_csv(T / "table4b_fit_statistics.csv")
    parts += [caption("4b", "Cost-model fit statistics."),
              render(fit, ["statistic", "value"],
                     [None, lambda x: f"{x:,.3f}"], ["Statistic", "Value"])]

    # ---- Table 5a / 5c / 5d ------------------------------------------------
    b = pd.read_csv(T / "table5a_premium_buildup.csv")
    parts += [caption("5a", "Premium build-up, naira per person per year."),
              render(b, ["step", "naira_per_person_year", "change"],
                     [None, money, money], ["Step", "Naira", "Change"])]

    g = pd.read_csv(T / "table5c_gross_premium.csv")
    parts += [caption("5c", "Gross premium by pool size and risk-margin basis."),
              render(g, ["pool_size", "risk_margin_basis", "pure_premium",
                         "risk_margin", "admin_load", "adverse_selection_load",
                         "gross_premium_per_person"],
                     [lambda x: f"{x:,.0f}", None, money, money, money, money,
                      money],
                     ["Pool size", "Risk-margin basis", "Pure premium",
                      "Risk margin", "Admin", "Selection load", "Gross premium"])]

    a = pd.read_csv(T / "table5d_affordability.csv")
    parts += [caption("5d", "Affordability of the gross premium, 20,000-life pool.",
                      "Household size is the household-weighted mean; the "
                      "population-weighted mean is shown for comparison because "
                      "quintiles rank people, not households."),
              render(a, ["quintile", "mean_consumption_per_capita",
                         "mean_household_size", "mean_household_size_pop_weighted",
                         "premium_pct_of_per_capita_consumption",
                         "premium_per_household"],
                     [None, money, lambda x: num(x, 2), lambda x: num(x, 2),
                      lambda x: pct(x, 2), money],
                     ["Quintile", "Consumption per capita", "HH size (hh-wtd)",
                      "HH size (pop-wtd)", "Premium as % of consumption",
                      "Premium per household"])]

    # ---- Table 6a / 6c -----------------------------------------------------
    aff = pd.read_csv(T / "table6a_affordable_contribution.csv")
    parts += [caption("6a", "What the target population can contribute, at 5% of "
                            "per-capita consumption."),
              render(aff, ["group", "mean_consumption_per_capita",
                           "affordable_contribution"],
                     [None, money, money],
                     ["Group", "Consumption per capita", "Affordable contribution"])]

    sub = pd.read_csv(T / "table6c_minimum_subsidy.csv")
    sub = sub[(sub["initial_capital_mult"] == 0.0) & (sub["years"] == 3)]
    parts += [caption("6c", "Minimum subsidy per enrollee for a three-year horizon, "
                            "no opening capital."),
              render(sub, ["pool_size", "take_up", "ruin_target",
                           "min_subsidy_per_enrollee",
                           "min_subsidy_pct_of_gross_premium",
                           "annual_cost_per_100k_enrollees_naira_bn"],
                     [lambda x: f"{x:,.0f}", None, lambda x: f"{x:.0%}", money,
                      lambda x: pct(x, 1), lambda x: num(x, 2)],
                     ["Pool size", "Take-up", "Ruin target", "Subsidy",
                      "% of gross premium", "₦bn per 100k enrollees"])]

    # ---- Table 7b ----------------------------------------------------------
    red = pd.read_csv(T / "table7b_reductions.csv")
    parts += [caption("7b", "Change in catastrophic expenditure under coverage "
                            "scenarios.",
                      "A negative relative reduction means catastrophic "
                      "expenditure rises."),
              render(red, ["scenario", "payment_basis", "measure", "baseline_pct",
                           "counterfactual_pct", "relative_reduction_pct",
                           "p_value"],
                     [None, None, None, lambda x: pct(x, 2), lambda x: pct(x, 2),
                      lambda x: pct(x, 1), lambda x: num(x, 3)],
                     ["Scenario", "Payment basis", "Measure", "Baseline %",
                      "Counterfactual %", "Relative reduction %", "p"])]

    # ---- Table 8 -----------------------------------------------------------
    rob = pd.read_csv(T / "table8_robustness.csv")
    parts += [caption(8, "Robustness grid.")]
    cols = list(rob.columns)
    parts += [render(rob, cols, [None] + [auto(1) for _ in cols[1:]],
                     [c.replace("_", " ").capitalize() for c in cols])]


    # ---- Table 3b ----------------------------------------------------------
    d = pd.read_csv(T / "table3b_decomposition.csv")
    parts += [caption("3b", "Decomposition of the concentration index.",
                      "Descriptive, not causal: each row is a covariate's "
                      "contribution to the measured concentration, not its "
                      "effect."),
              render(d, ["outcome", "variable", "beta", "mean_x", "CI_x",
                         "contribution", "share_pct"],
                     [None, None, auto(4), auto(3), auto(4), auto(4), auto(1)],
                     ["Outcome", "Variable", "Beta", "Mean x", "CI of x",
                      "Contribution", "Share %"])]

    # ---- Table 4 -----------------------------------------------------------
    d = pd.read_csv(T / "table4_cost_models.csv")
    parts += [caption(4, "Frequency, severity and Tweedie model estimates.",
                      "Survey-weighted, standard errors clustered on the "
                      "enumeration area. exp(coef) is the multiplicative effect "
                      "on the fitted mean."),
              render(d, ["model", "term", "coef", "se", "z", "p", "exp_coef"],
                     [None, None, auto(4), auto(4), auto(2), auto(3), auto(3)],
                     ["Model", "Term", "Coef", "SE", "z", "p", "exp(coef)"])]

    # ---- Table 5b ----------------------------------------------------------
    d = pd.read_csv(T / "table5b_risk_margins.csv")
    parts += [caption("5b", "Risk margin by pool size, on two conventions.",
                      "Both shrink with scale, which is the actuarial argument "
                      "for pooling."),
              render(d, ["pool_size", "risk_margin_sd", "risk_margin_cvar",
                         "sd_of_pool_mean"],
                     [lambda x: f"{x:,.0f}", money, money, money],
                     ["Pool size", "SD principle", "CVaR 95%",
                      "SD of the pool mean"])]

    # ---- Table 5e ----------------------------------------------------------
    d = pd.read_csv(T / "table5e_risk_classes.csv")
    parts += [caption("5e", "Risk relativities.",
                      "Relative to the community average. The premium itself is "
                      "community-rated, so these describe the risk structure "
                      "rather than a rating table."),
              render(d, ["dimension", "class", "n", "mean_insurer_cost",
                         "relativity"],
                     [None, None, lambda x: f"{x:,.0f}", money, auto(2)],
                     ["Dimension", "Class", "n", "Mean insurer cost",
                      "Relativity"])]

    # ---- Table 5f ----------------------------------------------------------
    d = pd.read_csv(T / "table5f_state_comparison.csv")
    parts += [caption("5f", "The modelled premium against published state-scheme "
                            "rates.",
                      "A plausibility check, not a like-for-like test: the Ilera "
                      "Eko package is not the NHIA basic package, and the "
                      "published rates are nominal July-2024 naira."),
              render(d, ["scheme", "annual_premium_naira",
                         "modelled_premium_per_person",
                         "ratio_modelled_to_published"],
                     [None, money, money, auto(2)],
                     ["Scheme", "Published premium", "Modelled premium",
                      "Ratio"])]

    # ---- Table 6b ----------------------------------------------------------
    d = pd.read_csv(T / "table6b_ruin_scenarios.csv")
    d = d[(d["years"] == 3) & (d["initial_capital_mult"] == 0.0)
          & (d["subsidy_fraction_of_premium"].isin([0.0, 0.25, 0.50, 0.75,
                                                    1.00, 1.50, 2.00]))]
    parts += [caption("6b", "Probability of ruin over three years, no opening "
                            "capital.",
                      "The full grid, across every pool size, take-up pattern "
                      "and capital level, is in output/tables."),
              render(d, ["pool_size", "take_up", "subsidy_fraction_of_premium",
                         "subsidy_per_enrollee", "psi", "mc_se"],
                     [lambda x: f"{x:,.0f}", None, lambda x: f"{x:.0%}", money,
                      auto(4), auto(4)],
                     ["Pool size", "Take-up", "Subsidy", "Per enrollee",
                      "Ruin probability", "MC SE"])]

    # ---- Table 6d ----------------------------------------------------------
    d = pd.read_csv(T / "table6d_inflation_stress.csv")
    parts += [caption("6d", "Medical-inflation stress."),
              render(d, ["medical_inflation_shock", "take_up", "pool_size",
                         "ruin_target", "min_subsidy_per_enrollee"],
                     [lambda x: f"{x:.0%}", None, lambda x: f"{x:,.0f}",
                      lambda x: f"{x:.0%}", money],
                     ["Shock", "Take-up", "Pool size", "Ruin target",
                      "Minimum subsidy"])]

    # ---- Table 7a ----------------------------------------------------------
    d = pd.read_csv(T / "table7a_counterfactual.csv")
    parts += [caption("7a", "Catastrophic spending under each coverage "
                            "scenario, on both payment bases."),
              render(d, ["scenario", "payment_basis",
                         "share_of_population_covered", "che10_pct",
                         "che25_pct", "che_ctp40_pct",
                         "poverty_after_payments_pct",
                         "mean_household_health_payments"],
                     [None, None, lambda x: f"{x:.1%}", auto(2), auto(2),
                      auto(2), auto(2), money],
                     ["Scenario", "Payment basis", "Covered", "CHE10 %",
                      "CHE25 %", "CTP40 %", "Poverty after %",
                      "Mean payments"])]

    # ---- Table 7c ----------------------------------------------------------
    d = pd.read_csv(T / "table7c_by_quintile.csv")
    parts += [caption("7c", "Counterfactual catastrophic spending by consumption "
                            "quintile."),
              render(d, ["scenario", "measure", "group", "estimate_pct",
                         "ci_low_pct", "ci_high_pct", "n"],
                     [None, None, None, auto(2), auto(2), auto(2),
                      lambda x: f"{x:,.0f}"],
                     ["Scenario", "Measure", "Quintile", "Estimate %",
                      "95% low", "95% high", "n"])]

    # ---- Table 8b / 8c -----------------------------------------------------
    d = pd.read_csv(T / "table8b_wave4.csv")
    parts += [caption("8b", "Wave 4 (2018/19) comparison.",
                      "Read with care: the two waves use different instruments "
                      "for out-of-pocket spending."),
              render(d, ["wave", "measure", "estimate_pct", "se", "oop_source"],
                     [None, None, auto(2), auto(2), None],
                     ["Wave", "Measure", "Estimate %", "SE", "OOP source"])]

    d = pd.read_csv(T / "table8c_poverty_lines.csv")
    parts += [caption("8c", "Impoverishment across poverty lines.",
                      "The headcount is a level and moves; the impoverishment "
                      "effect is a difference and does not."),
              render(d, ["poverty_line_naira", "multiple_of_national_line",
                         "headcount_before_pct", "headcount_after_pct",
                         "impoverishment_pp", "impoverished_millions"],
                     [money, auto(2), auto(2), auto(2), auto(2), auto(2)],
                     ["Poverty line", "x national line", "Headcount before %",
                      "Headcount after %", "Impoverishment pp",
                      "Millions"])]

    # ---- Appendix ----------------------------------------------------------
    parts += ["\n\n# Appendix tables\n"]

    a1 = pd.read_csv(T / "tableA1_aggregate_validation.csv")
    parts += [caption("A1", "Reconstructed consumption aggregate validated against "
                            "wave 4's published aggregate."),
              render(a1, ["component", "official_mean_naira", "rebuilt_mean_naira",
                          "ratio_rebuilt_to_official", "pearson_r",
                          "spearman_rho"],
                     [None, money, money, lambda x: num(x, 3),
                      lambda x: num(x, 3), lambda x: num(x, 3)],
                     ["Component", "Official mean", "Rebuilt mean", "Ratio",
                      "Pearson r", "Spearman rho"])]

    d = pd.read_csv(T / "tableA2_tweedie_profile.csv")
    parts += [caption("A2", "Profile likelihood for the Tweedie variance power."),
              render(d[d["converged"]], ["p", "loglik", "deviance"],
                     [auto(2), auto(1), auto(1)],
                     ["p", "Log-likelihood", "Deviance"])]

    a3 = pd.read_csv(T / "tableA3_lift.csv")
    parts += [caption("A3", "Observed against predicted annual cost, by decile of "
                            "prediction."),
              render(a3, ["decile", "n", "predicted_mean", "observed_mean",
                          "ratio_obs_pred", "lift"],
                     [lambda x: f"{x:,.0f}", lambda x: f"{x:,.0f}", money, money,
                      lambda x: num(x, 3), lambda x: num(x, 2)],
                     ["Decile", "n", "Predicted mean", "Observed mean",
                      "Observed / predicted", "Lift"])]

    a4 = pd.read_csv(T / "tableA4_simulation_check.csv")
    parts += [caption("A4", "Multinomial shortcut checked against direct "
                            "resampling of individuals."),
              render(a4, list(a4.columns),
                     [None] + [auto(4) for _ in a4.columns[1:]],
                     [c.replace("_", " ").capitalize() for c in a4.columns])]

    parts += [caption("A5", "The closest published studies, and what each stops "
                            "short of.",
                      "Every DOI was checked against Crossref; see the reference "
                      "list."),
              LIT_MATRIX.strip()]

    OUT.write_text("\n".join(parts) + "\n")
    n = sum(1 for line in OUT.read_text().splitlines()
            if line.startswith("**Table"))
    print(f"wrote {OUT.relative_to(config.ROOT)} with {n} tables")


if __name__ == "__main__":
    main()
