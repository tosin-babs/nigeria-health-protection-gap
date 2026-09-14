"""
Section 5.6 - every robustness check, driven from one scenario table.

Each check changes exactly one decision and reports the same four headline
numbers, so the reader can see at a glance which choices the paper's
conclusions depend on and which they do not:

    CHE at the 10% budget share, CHE at the 40% capacity-to-pay threshold,
    the gross premium, and the minimum subsidy for a 5% ruin probability.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config
import costmodels
from che import add_che_flags, _design
from premium import benefit_mapping, premium_buildup
from ruin import (affordable_contribution, claims_paths, cost_support,
                  minimum_subsidy_from_paths, selection_probabilities)
from svy import Design, weighted_quantile


N_SIM_ROBUST = 4_000  # smaller than the headline run; these are sensitivities


# ---------------------------------------------------------------------------
def recompute_welfare(hh):
    """Redo quintiles, equivalence scale and capacity to pay after a change."""
    from build_data import add_welfare_variables
    return add_welfare_variables(hh.drop(columns=[
        c for c in ["cons_pc", "quintile", "quintile_label", "eqsize", "popwt",
                    "food_share", "food_eq", "subsistence", "ctp"] if c in hh],
        errors="ignore"))


def headline_numbers(hh, ind, label, note="", n_sim=N_SIM_ROBUST,
                     premium_kwargs=None, tweedie_p=None):
    """CHE, premium and minimum subsidy for one variant of the analysis."""
    hh = add_che_flags(hh)
    d = _design(hh)
    che10, che10_se = d.mean(hh["che10"].to_numpy(float))
    ctp40, ctp40_se = d.mean(hh["che_ctp40"].to_numpy(float))

    mapped = benefit_mapping(ind, **(premium_kwargs or {}))
    _, _, gross, summary = premium_buildup(mapped)
    g = gross[(gross["pool_size"] == 20_000)
              & (gross["risk_margin_basis"] == "Standard deviation")]
    gross_premium = float(g["gross_premium_per_person"].iloc[0])

    aff = affordable_contribution(hh)
    contribution = aff.attrs["target_contribution"]

    pool = mapped[mapped["informal"] == 1]
    out = {"check": label, "note": note,
           "che10_pct": 100 * che10, "che10_se": 100 * che10_se,
           "che_ctp40_pct": 100 * ctp40, "che_ctp40_se": 100 * ctp40_se,
           "pure_premium": summary["pure_premium"],
           "gross_premium": gross_premium,
           "affordable_contribution": contribution}

    pred = pool["pred_cost"] if "pred_cost" in pool else pool["insurer_cost"]
    for take_up, strength in [("random", 1.0), ("adverse", config.ADVERSE_SELECTION_STRENGTH)]:
        w = selection_probabilities(pred, pool["ind_weight"], strength)
        v, p = cost_support(pool["insurer_cost"], w * len(pool))
        paths = claims_paths(v, p, 20_000, 3, n_sim=n_sim)
        s = minimum_subsidy_from_paths(paths, 20_000, contribution, 0.0, 0.05,
                                       gross_premium)
        out[f"min_subsidy_{take_up}"] = s
    if tweedie_p is not None:
        out["tweedie_p"] = tweedie_p
    return out


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
def variant_equivalence_scale(hh, ind, power):
    h = hh.copy()
    old = config.EQ_SCALE_POWER
    config.EQ_SCALE_POWER = power
    try:
        h = recompute_welfare(h)
    finally:
        config.EQ_SCALE_POWER = old
    return h, ind


def variant_annualiser(hh, ind, weeks_multiplier):
    """Rescale the 4-week outpatient window to a different annual equivalent."""
    factor = weeks_multiplier / config.OUTPATIENT_ANNUALISER
    i = ind.copy()
    for c in ["op_cost_annual", "op_drug_annual", "op_transport_annual"]:
        i[c] = i[c] * factor
    i["cost_annual"] = i["op_cost_annual"] + i["ip_cost_annual"]
    agg = i.groupby("hhid")[["op_cost_annual", "ip_cost_annual"]].sum()
    h = hh.copy().set_index("hhid")
    new_oop = (agg["op_cost_annual"] + agg["ip_cost_annual"]).reindex(h.index).fillna(0.0)
    h["cons_annual"] = h["cons_annual"] - h["oop_annual"] + new_oop
    h["oop_annual"] = new_oop
    return recompute_welfare(h.reset_index()), i


def variant_with_transport(hh, ind):
    i = ind.copy()
    i["op_cost_annual"] = i["op_cost_annual"] + i["op_transport_annual"]
    i["cost_annual"] = i["op_cost_annual"] + i["ip_cost_annual"]
    h = hh.copy()
    h["cons_annual"] = h["cons_annual"] - h["oop_annual"] + h["oop_with_transport"]
    h["oop_annual"] = h["oop_with_transport"]
    return recompute_welfare(h), i


def variant_consumption_module_oop(hh, ind):
    """Measure OOP from the consumption module instead of the health module."""
    h = hh.copy()
    h["cons_annual"] = (h["cons_annual"] - h["oop_annual"]
                        + h["oop_consumption_module"])
    h["oop_annual"] = h["oop_consumption_module"]
    return recompute_welfare(h), ind


def variant_uncalibrated(hh, ind):
    """Use the rebuilt aggregate as it comes, without the wave-4 calibration."""
    h = hh.copy()
    h["cons_annual"] = h["cons_annual_raw"]
    h["food_annual"] = h["food_annual_raw"]
    return recompute_welfare(h), ind


def variant_trim_top(hh, ind, pct=0.01):
    """Trim the top 1% of individual annual costs, which pricing should not do."""
    i = ind.copy()
    cap = i["cost_annual"].quantile(1 - pct)
    for c in ["op_cost_annual", "ip_cost_annual"]:
        i[c] = i[c].clip(upper=cap)
    i["cost_annual"] = i["op_cost_annual"] + i["ip_cost_annual"]
    agg = i.groupby("hhid")[["op_cost_annual", "ip_cost_annual"]].sum()
    h = hh.copy().set_index("hhid")
    new_oop = (agg["op_cost_annual"] + agg["ip_cost_annual"]).reindex(h.index).fillna(0.0)
    h["cons_annual"] = h["cons_annual"] - h["oop_annual"] + new_oop
    h["oop_annual"] = new_oop
    return recompute_welfare(h.reset_index()), i


def variant_informal_definition(hh, ind, column, label):
    h = hh.copy()
    h["informal"] = 1 - h[column]
    h["sector_label"] = np.where(h["informal"] == 1, "Informal", "Formal")
    i = ind.drop(columns=["informal"]).merge(
        h[["hhid", "informal"]], on="hhid", how="inner")
    return h, i


def wave4_comparison():
    """CHE in 2018/19 on the like-for-like consumption-module measure.

    Wave 4's out-of-pocket figure comes from the published consumption
    aggregate, so it is comparable with the wave-5 consumption-module variant,
    not with the wave-5 health-module headline. Reporting the pair keeps the
    trend honest about the change of instrument.
    """
    h4 = pd.read_csv(config.DERIVED / "hh_w4.csv")
    h4 = add_che_flags(h4)
    d = Design(h4, "popwt", config.STRATA, "cluster")
    rows = []
    for name, col in [("CHE > 10% (budget share)", "che10"),
                      ("CHE > 25% (budget share)", "che25"),
                      ("CHE, CTP >= 40%", "che_ctp40")]:
        e, se = d.mean(h4[col].to_numpy(float))
        rows.append({"wave": "W4 (2018/19)", "measure": name,
                     "estimate_pct": 100 * e, "se": 100 * se,
                     "oop_source": "Published consumption aggregate"})
    return pd.DataFrame(rows)


def poverty_line_sensitivity(hh):
    """Impoverishment across a grid of poverty lines.

    The reconstructed aggregate recovers 87% of the published wave-4 aggregate,
    so the *level* of the headcount is sensitive to the line. The impoverishing
    effect of out-of-pocket payments, which is the quantity the paper reports,
    is much less so - this table is the evidence for that claim.
    """
    d = _design(hh)
    base = config.POVERTY_LINE_2019 * config.CPI_W4_TO_W5
    rows = []
    for mult in (0.5, 0.75, 1.0, 1.25, 1.5):
        line = base * mult
        gross = hh["cons_pc"].to_numpy(float)
        net = ((hh["cons_annual"] - hh["oop_annual"]) / hh["hhsize"]).to_numpy()
        pre, pre_se = d.mean((gross < line).astype(float))
        post, post_se = d.mean((net < line).astype(float))
        rows.append({
            "poverty_line_naira": line, "multiple_of_national_line": mult,
            "headcount_before_pct": 100 * pre, "headcount_after_pct": 100 * post,
            "impoverishment_pp": 100 * (post - pre),
            "impoverished_millions": float(
                (d.w * ((gross >= line) & (net < line))).sum() / 1e6),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    hh0 = pd.read_csv(config.DERIVED / "hh_w5_che.csv")
    ind0 = pd.read_csv(config.DERIVED / "ind_w5_priced.csv")

    rows = [headline_numbers(hh0, ind0, "Main specification",
                             "Calibrated aggregate; health-module OOP; eq. scale "
                             "0.56; 13x annualiser; transport excluded; p profiled")]

    h, i = variant_uncalibrated(hh0, ind0)
    rows.append(headline_numbers(h, i, "Uncalibrated consumption aggregate",
                                 "Rebuilt modules only, no rent, no wave-4 scaling"))

    for power in (0.5, 0.75, 1.0):
        h, i = variant_equivalence_scale(hh0, ind0, power)
        rows.append(headline_numbers(h, i, f"Equivalence scale hhsize^{power}",
                                     "Xu et al. capacity to pay recomputed"))

    for mult, note in [(12.0, "Monthly convention"), (10.0, "Seasonally damped"),
                       (6.0, "Strongly damped")]:
        h, i = variant_annualiser(hh0, ind0, mult)
        rows.append(headline_numbers(h, i, f"Outpatient annualiser x{mult:.0f}", note))

    h, i = variant_with_transport(hh0, ind0)
    rows.append(headline_numbers(h, i, "OOP including transport",
                                 "WHO excludes transport by default"))

    h, i = variant_consumption_module_oop(hh0, ind0)
    rows.append(headline_numbers(
        h, i, "OOP from the wave-5 consumption module",
        "Data-quality check, not a credible alternative: the wave-5 non-food "
        "health items are answered by only 17% of households and imply an OOP "
        "share of 0.3% of consumption, against 5.4% in the published wave-4 "
        "aggregate"))

    h, i = variant_trim_top(hh0, ind0)
    rows.append(headline_numbers(h, i, "Top 1% of costs trimmed",
                                 "Kept in the main results: the tail is the risk"))

    for col, lab in [("any_formal_govt", "Formal = public-sector employee only"),
                     ("any_formal_anywage", "Formal = any wage employee"),
                     ("head_formal", "Sector set by the household head")]:
        if col in hh0:
            h, i = variant_informal_definition(hh0, ind0, col, lab)
            rows.append(headline_numbers(h, i, lab, "Alternative informality rule"))

    # The variance power enters through the predicted cost that drives the
    # adverse-selection tilt, so the model has to be refitted at each p rather
    # than simply relabelled.
    scored = costmodels.prepare(pd.read_csv(config.DERIVED / "ind_w5.csv"))
    for p in (1.4, 1.5, 1.7):
        fit = costmodels.fit_tweedie(scored, p)
        i = ind0.drop(columns=["pred_cost"]).merge(
            scored[["hhid", "indiv"]].assign(pred_cost=np.asarray(fit.fittedvalues)),
            on=["hhid", "indiv"], how="inner")
        rows.append({**headline_numbers(hh0, i, f"Tweedie p fixed at {p}",
                                        "Refitted; p drives the adverse-selection tilt"),
                     "tweedie_p": p})

    for e in config.ELASTICITY_RANGE:
        rows.append(headline_numbers(
            hh0, ind0, f"Induced-demand elasticity {e:.2f}",
            "RAND HIE central estimate is -0.20",
            premium_kwargs={"elasticity": e}))

    for cov in (0.70, 0.85, 1.00):
        rows.append(headline_numbers(
            hh0, ind0, f"Outpatient covered share {cov:.0%}",
            "Benefit-package breadth", premium_kwargs={"covered_op": cov}))

    for coin in (0.0, 0.10, 0.20):
        rows.append(headline_numbers(
            hh0, ind0, f"Drug co-payment {coin:.0%}",
            "NHIA reference rule is 10%", premium_kwargs={"coinsurance": coin}))

    table = pd.DataFrame(rows)
    table.to_csv(config.TABLES / "table8_robustness.csv", index=False)

    w4 = wave4_comparison()
    w4.to_csv(config.TABLES / "table8b_wave4.csv", index=False)
    pov = poverty_line_sensitivity(hh0)
    pov.to_csv(config.TABLES / "table8c_poverty_lines.csv", index=False)

    cols = ["check", "che10_pct", "che_ctp40_pct", "pure_premium",
            "gross_premium", "min_subsidy_random", "min_subsidy_adverse"]
    print("\n=== Robustness ===")
    print(table[cols].to_string(index=False, float_format=lambda x: f"{x:,.1f}"))
    print("\nWave 4 comparison (like-for-like consumption-module OOP):")
    print(w4.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    print("\nPoverty-line sensitivity:")
    print(pov.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    return table, w4, pov


if __name__ == "__main__":
    main()
