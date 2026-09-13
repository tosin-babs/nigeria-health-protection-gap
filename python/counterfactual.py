"""
RQ4 - how much catastrophic spending would coverage actually remove.

This is a transparent accounting simulation, not a causal estimate. Each person
is moved onto the benefit package modelled in premium.py: their covered care
becomes free or co-paid, their utilisation rises by the induced-demand factor,
and what they still pay - co-payments plus everything outside the package -
becomes their new out-of-pocket cost. CHE is then recomputed on the same
households.

Two things keep the exercise honest. First, induced demand is included, so the
reduction is smaller than a naive "coverage removes OOP" calculation. Second,
the member contribution is a real payment, so results are reported both on
out-of-pocket spending alone (the SDG 3.8.2 convention) and on total household
health payments including the contribution, which is what a household actually
feels.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config
from che import add_che_flags, _design
from svy import estimate_by, diff_test


SCENARIOS = [
    dict(name="Baseline (no coverage)", covered="none", contribution=0.0),
    dict(name="Vulnerable group only, fully subsidised",
         covered="q1q2", contribution=0.0),
    dict(name="Informal sector, 50% take-up", covered="informal",
         take_up=0.50, contribution=None),
    dict(name="Informal sector, full coverage", covered="informal",
         contribution=None),
    dict(name="Informal sector, full coverage, no contribution",
         covered="informal", contribution=0.0),
    dict(name="Universal coverage", covered="all", contribution=None),
]


def assign_coverage(ind, hh, scenario, rng):
    """Which individuals are covered under this scenario."""
    covered = pd.Series(False, index=ind.index)
    kind = scenario["covered"]
    if kind == "none":
        return covered
    if kind == "all":
        covered[:] = True
    elif kind == "informal":
        covered = ind["informal"] == 1
    elif kind == "q1q2":
        covered = (ind["informal"] == 1) & ind["quintile"].isin([1, 2])
    if scenario.get("take_up", 1.0) < 1.0:
        # Take-up is applied at household level: families enrol together.
        hhids = ind.loc[covered, "hhid"].unique()
        chosen = set(rng.choice(hhids, size=int(len(hhids) * scenario["take_up"]),
                                replace=False))
        covered = covered & ind["hhid"].isin(chosen)
    return covered


def apply_scenario(ind, hh, scenario, contribution, rng):
    """Recompute household OOP, contributions and consumption under coverage."""
    covered = assign_coverage(ind, hh, scenario, rng)
    d = ind.copy()
    d["covered_flag"] = covered.astype(int)

    # Uncovered people keep their observed spending; covered people pay the
    # co-payment plus whatever the package does not include, on the higher
    # utilisation that free care induces.
    baseline_oop = d["op_cost_annual"] + d["ip_cost_annual"]
    d["oop_new"] = np.where(covered, d["member_cost_after"], baseline_oop)

    c = scenario["contribution"] if scenario["contribution"] is not None else contribution
    d["contribution_paid"] = np.where(covered, c, 0.0)

    agg = d.groupby("hhid").agg(
        oop_new=("oop_new", "sum"),
        contribution_paid=("contribution_paid", "sum"),
        n_covered=("covered_flag", "sum"),
    )
    out = hh.merge(agg, left_on="hhid", right_index=True, how="left")
    for c_ in ["oop_new", "contribution_paid", "n_covered"]:
        out[c_] = out[c_].fillna(0.0)

    # Non-health consumption is what is held fixed; the total moves with health
    # payments. Baseline consumption already contains observed out-of-pocket
    # spending, so that component is swapped out for the counterfactual one and
    # any premium is added, exactly as the survey's own consumption module
    # treats a health-insurance premium (non-food item 363).
    #
    # One consequence is worth flagging: on the out-of-pocket-only basis a
    # contributory scheme scores *better* than the same scheme fully
    # subsidised, because the premium enlarges the denominator while leaving
    # the numerator alone. That is an artefact of the SDG 3.8.2 convention, not
    # a real gain, and it is why the paper reports both payment bases.
    out["cons_new"] = (out["cons_annual"] - out["oop_annual"] + out["oop_new"]
                       + out["contribution_paid"]).clip(lower=1.0)
    out["health_payments_new"] = out["oop_new"] + out["contribution_paid"]

    # Capacity to pay moves with total consumption; subsistence is unchanged.
    out["ctp_new"] = np.where(out["subsistence"] < out["food_annual"],
                              out["cons_new"] - out["subsistence"],
                              out["cons_new"] - out["food_annual"]).clip(1.0)
    return out


def che_under(out, payments_col, cons_col, ctp_col):
    """CHE flags for an arbitrary numerator/denominator pair."""
    share = out[payments_col] / out[cons_col]
    return {
        "che10": (share > 0.10).astype(float).to_numpy(),
        "che25": (share > 0.25).astype(float).to_numpy(),
        "che_ctp40": ((out[payments_col] / out[ctp_col]) >= 0.40)
        .astype(float).to_numpy(),
    }


def run(ind, hh, contribution):
    rng = np.random.default_rng(config.SEED)
    d = _design(hh)

    poverty_line = config.POVERTY_LINE_2019 * config.CPI_W4_TO_W5
    results, by_quintile = [], []

    for scen in SCENARIOS:
        out = apply_scenario(ind, hh, scen, contribution, rng)
        for basis, col in [("Out-of-pocket only", "oop_new"),
                           ("OOP plus member contribution", "health_payments_new")]:
            flags = che_under(out, col, "cons_new", "ctp_new")
            row = {"scenario": scen["name"], "payment_basis": basis,
                   "share_of_population_covered":
                       float(np.average(out["n_covered"] / out["hhsize"],
                                        weights=out["popwt"]))}
            for k, y in flags.items():
                e, se = d.mean(y)
                row[f"{k}_pct"] = 100 * e
                row[f"{k}_se"] = 100 * se
            net_pc = ((out["cons_new"] - out[col]) / out["hhsize"]).to_numpy()
            post = (net_pc < poverty_line).astype(float)
            e, se = d.mean(post)
            row["poverty_after_payments_pct"] = 100 * e
            row["poverty_after_payments_se"] = 100 * se
            row["mean_household_health_payments"] = float(
                np.average(out[col], weights=out["popwt"]))
            results.append(row)

            if basis == "OOP plus member contribution":
                q = estimate_by(d, flags["che10"], hh["quintile_label"], "mean")
                q["scenario"] = scen["name"]
                q["measure"] = "CHE > 10%"
                by_quintile.append(q)
                q2 = estimate_by(d, flags["che_ctp40"], hh["quintile_label"], "mean")
                q2["scenario"] = scen["name"]
                q2["measure"] = "CHE, CTP >= 40%"
                by_quintile.append(q2)

    res = pd.DataFrame(results)
    quint = pd.concat(by_quintile, ignore_index=True)
    quint["estimate_pct"] = 100 * quint["estimate"]
    quint["ci_low_pct"] = 100 * quint["ci_low"]
    quint["ci_high_pct"] = 100 * quint["ci_high"]

    # Reductions relative to baseline, with a test on the difference.
    base = res[res["scenario"] == "Baseline (no coverage)"].set_index("payment_basis")
    red = []
    for _, r in res[res["scenario"] != "Baseline (no coverage)"].iterrows():
        b = base.loc[r["payment_basis"]]
        for m in ["che10", "che25", "che_ctp40"]:
            diff, z, p = diff_test(r[f"{m}_pct"], r[f"{m}_se"],
                                   b[f"{m}_pct"], b[f"{m}_se"])
            red.append({
                "scenario": r["scenario"], "payment_basis": r["payment_basis"],
                "measure": m, "baseline_pct": b[f"{m}_pct"],
                "counterfactual_pct": r[f"{m}_pct"],
                "reduction_pp": -diff,
                "relative_reduction_pct": -100 * diff / b[f"{m}_pct"]
                if b[f"{m}_pct"] else np.nan,
                "z": z, "p_value": p,
            })
    return res, pd.DataFrame(red), quint


# ---------------------------------------------------------------------------
def main():
    ind = pd.read_csv(config.DERIVED / "ind_w5_priced.csv")
    hh = pd.read_csv(config.DERIVED / "hh_w5_che.csv")
    aff = pd.read_csv(config.TABLES / "table6a_affordable_contribution.csv")
    contribution = float(
        aff[aff["group"].isin(["Informal, quintile 1", "Informal, quintile 2",
                               "Informal, quintile 3"])]["affordable_contribution"].mean())

    res, red, quint = run(ind, hh, contribution)
    res.to_csv(config.TABLES / "table7a_counterfactual.csv", index=False)
    red.to_csv(config.TABLES / "table7b_reductions.csv", index=False)
    quint.to_csv(config.TABLES / "table7c_by_quintile.csv", index=False)

    print("\n=== RQ4: CHE under coverage scenarios ===")
    show = res[["scenario", "payment_basis", "share_of_population_covered",
                "che10_pct", "che25_pct", "che_ctp40_pct",
                "poverty_after_payments_pct"]]
    print(show.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    print("\nReduction vs baseline:")
    print(red[red["payment_basis"] == "OOP plus member contribution"]
          [["scenario", "measure", "baseline_pct", "counterfactual_pct",
            "reduction_pp", "relative_reduction_pct", "p_value"]]
          .to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    return res, red, quint


if __name__ == "__main__":
    main()
