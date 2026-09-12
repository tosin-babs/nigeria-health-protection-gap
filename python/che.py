"""
RQ1 - incidence and intensity of catastrophic health expenditure.

Produces Table 1 (sample), Table 2 (CHE by threshold and subgroup),
Table 3 (concentration indices and decomposition) and the impoverishment
estimates. Every figure is survey-weighted with a design-based 95% CI.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config
from svy import (Design, concentration_index, decompose_ci, diff_test,
                 estimate_by, ci)


# ---------------------------------------------------------------------------
def add_che_flags(hh, oop_col="oop_annual", cons_col="cons_annual"):
    """Attach budget-share and capacity-to-pay CHE indicators and overshoots."""
    hh = hh.copy()
    hh["oop_share"] = hh[oop_col] / hh[cons_col]
    hh["ctp_share"] = hh[oop_col] / hh["ctp"]

    for t in config.CHE_BUDGET_THRESHOLDS:
        tag = f"{int(t * 100)}"
        hh[f"che{tag}"] = (hh["oop_share"] > t).astype(float)
        # Wagstaff & van Doorslaer (2003): the overshoot is how far past the
        # threshold a household goes, and is zero for households below it.
        hh[f"overshoot{tag}"] = np.maximum(hh["oop_share"] - t, 0.0)

    t = config.CHE_CTP_THRESHOLD
    hh["che_ctp40"] = (hh["ctp_share"] >= t).astype(float)
    hh["overshoot_ctp40"] = np.maximum(hh["ctp_share"] - t, 0.0)
    return hh


def _design(hh):
    """Population-weighted design: household weight x household size.

    CHE is a household-level event, but the policy quantity is the share of
    *people* living in an affected household, so the population weight is used
    throughout, following WHO's SDG 3.8.2 convention.
    """
    return Design(hh, "popwt", config.STRATA, "cluster")


# ---------------------------------------------------------------------------
def table1_sample(hh):
    """Weighted sample characteristics, overall and by sector.

    Household-level characteristics use the household weight, not the
    population weight used for the CHE rates. Weighting a household
    characteristic by household size answers a different question - "how big is
    the household the average *person* lives in" - and would report a mean
    household size of 7.4 against an actual 5.3.
    """
    d = Design(hh, "hh_weight", config.STRATA, "cluster")
    rows = []

    def add(name, values, scale=1.0, fmt="mean"):
        overall = d.mean(np.asarray(values, float))
        inf = d.subset((hh["informal"] == 1).to_numpy()).mean(np.asarray(values, float))
        frm = d.subset((hh["informal"] == 0).to_numpy()).mean(np.asarray(values, float))
        _, _, p = diff_test(inf[0], inf[1], frm[0], frm[1])
        rows.append({
            "characteristic": name,
            "overall": overall[0] * scale, "overall_se": overall[1] * scale,
            "informal": inf[0] * scale, "informal_se": inf[1] * scale,
            "formal": frm[0] * scale, "formal_se": frm[1] * scale,
            "p_diff": p, "format": fmt,
        })

    add("Household size", hh["hhsize"])
    add("Head's age (years)", hh["head_age"].fillna(hh["head_age"].median()))
    add("Female-headed (%)", hh["head_female"].fillna(0), 100, "pct")
    add("Urban (%)", hh["urban"], 100, "pct")
    add("Children under 5 (n)", hh["n_under5"])
    add("Members aged 60+ (n)", hh["n_over60"])
    add("Any member with severe functional difficulty (%)", hh["any_chronic"], 100, "pct")
    add("Total annual consumption (N)", hh["cons_annual"])
    add("Consumption per capita (N)", hh["cons_pc"])
    add("Food share of consumption (%)", hh["food_share"], 100, "pct")
    add("Annual out-of-pocket health spending (N)", hh["oop_annual"])
    add("OOP as share of consumption (%)", hh["oop_share"], 100, "pct")
    add("Any member sought care in past 4 weeks (%)",
        (hh["n_visits"] > 0).astype(float), 100, "pct")
    add("Any member hospitalised in past 12 months (%)",
        (hh["n_inpatient"] > 0).astype(float), 100, "pct")
    add("Paid a health-insurance premium (%)", hh["insured_any"], 100, "pct")

    out = pd.DataFrame(rows)
    out["n_households"] = len(hh)
    out["n_informal"] = int((hh["informal"] == 1).sum())
    out["n_formal"] = int((hh["informal"] == 0).sum())
    return out


def table2_che(hh):
    """CHE incidence and intensity by threshold, overall and by subgroup."""
    d = _design(hh)
    measures = [
        ("Budget share > 10%", "che10", "overshoot10"),
        ("Budget share > 25%", "che25", "overshoot25"),
        ("Budget share > 40%", "che40", "overshoot40"),
        ("Capacity to pay >= 40%", "che_ctp40", "overshoot_ctp40"),
    ]
    subgroups = [
        ("Overall", pd.Series(["All households"] * len(hh), index=hh.index)),
        ("Sector", hh["sector_label"]),
        ("Consumption quintile", hh["quintile_label"]),
        ("Residence", hh["sector"]),
        ("Zone", hh["zone"]),
    ]

    rows = []
    for m_name, flag, over in measures:
        y = hh[flag].to_numpy(float)
        o = hh[over].to_numpy(float)
        for s_name, s_vals in subgroups:
            inc = estimate_by(d, y, s_vals, "mean")
            ovr = estimate_by(d, o, s_vals, "mean")
            # Mean positive overshoot = mean overshoot / incidence, the average
            # excess among households that actually exceed the threshold.
            for (_, a), (_, b) in zip(inc.iterrows(), ovr.iterrows()):
                rows.append({
                    "measure": m_name, "dimension": s_name, "group": a["group"],
                    "incidence_pct": 100 * a["estimate"],
                    "incidence_se": 100 * a["se"],
                    "ci_low": 100 * a["ci_low"], "ci_high": 100 * a["ci_high"],
                    "mean_overshoot_pct": 100 * b["estimate"],
                    "mean_positive_overshoot_pct":
                        100 * b["estimate"] / a["estimate"] if a["estimate"] > 0 else np.nan,
                    "n": a["n"],
                })
    return pd.DataFrame(rows)


def impoverishment(hh, poverty_line_2023=None):
    """Households pushed below the poverty line by out-of-pocket payments.

    The line is the 2019 NBS national line carried forward to the wave-5 price
    base. Levels depend on the line and on the reconstructed aggregate, so the
    quantity to read is the *change* between pre- and post-payment poverty,
    which is far less sensitive to both.
    """
    if poverty_line_2023 is None:
        poverty_line_2023 = config.POVERTY_LINE_2019 * config.CPI_W4_TO_W5
    d = _design(hh)

    gross_pc = hh["cons_pc"].to_numpy(float)
    net_pc = ((hh["cons_annual"] - hh["oop_annual"]) / hh["hhsize"]).to_numpy(float)
    pre = (gross_pc < poverty_line_2023).astype(float)
    post = (net_pc < poverty_line_2023).astype(float)

    pre_e, pre_se = d.mean(pre)
    post_e, post_se = d.mean(post)
    newly = ((pre == 0) & (post == 1)).astype(float)
    new_e, new_se = d.mean(newly)

    # Poverty gap, normalised by the line (Wagstaff & van Doorslaer 2003).
    gap_pre = np.maximum(poverty_line_2023 - gross_pc, 0) / poverty_line_2023
    gap_post = np.maximum(poverty_line_2023 - net_pc, 0) / poverty_line_2023
    gpre_e, gpre_se = d.mean(gap_pre)
    gpost_e, gpost_se = d.mean(gap_post)

    rows = [
        ("Poverty line (N per person per year, wave-5 prices)", poverty_line_2023, np.nan),
        ("Poverty headcount before OOP (%)", 100 * pre_e, 100 * pre_se),
        ("Poverty headcount after OOP (%)", 100 * post_e, 100 * post_se),
        ("Impoverished by OOP (pp)", 100 * (post_e - pre_e), np.nan),
        ("Newly impoverished households (%)", 100 * new_e, 100 * new_se),
        ("Normalised poverty gap before OOP (%)", 100 * gpre_e, 100 * gpre_se),
        ("Normalised poverty gap after OOP (%)", 100 * gpost_e, 100 * gpost_se),
        ("Increase in poverty gap (pp)", 100 * (gpost_e - gpre_e), np.nan),
    ]
    out = pd.DataFrame(rows, columns=["indicator", "estimate", "se"])
    out.attrs["newly_impoverished_millions"] = float(
        (d.w * newly).sum() / 1e6)
    return out


def table3_concentration(hh):
    """Erreygers-corrected concentration indices and a linear decomposition."""
    d = _design(hh)
    ls = hh["cons_pc"].to_numpy(float)

    rows = []
    for name, col, binary in [
        ("CHE, budget share > 10%", "che10", True),
        ("CHE, budget share > 25%", "che25", True),
        ("CHE, capacity to pay >= 40%", "che_ctp40", True),
        ("OOP share of consumption", "oop_share", False),
        ("Sought care when ill (any member)", "sought_any", True),
    ]:
        if col == "sought_any":
            y = (hh["n_visits"] > 0).astype(float).to_numpy()
        else:
            y = hh[col].to_numpy(float)
        r = concentration_index(d, y, ls, binary=binary)
        lo, hi = ci(r["CI"], r["CI_se"])
        rows.append({
            "outcome": name, "mean": r["mean"], "CI": r["CI"], "CI_se": r["CI_se"],
            "CI_ci_low": lo, "CI_ci_high": hi,
            "Erreygers": r["Erreygers"], "Erreygers_se": r["Erreygers_se"],
        })
    indices = pd.DataFrame(rows)

    covars = pd.DataFrame({
        "Rural": 1 - hh["urban"],
        "Household size": hh["hhsize"],
        "Female head": hh["head_female"].fillna(0),
        "Head aged 60+": (hh["head_age"] >= 60).astype(float).fillna(0),
        "Any child under 5": (hh["n_under5"] > 0).astype(float),
        "Any member 60+": (hh["n_over60"] > 0).astype(float),
        "Severe functional difficulty": hh["any_chronic"].astype(float),
        "Informal sector": hh["informal"].astype(float),
        "Hospitalisation in past year": (hh["n_inpatient"] > 0).astype(float),
    })
    dec = decompose_ci(d, hh["che10"].to_numpy(float), ls, covars)
    dec.insert(0, "outcome", "CHE, budget share > 10%")
    return indices, dec


def sector_gap_tests(hh):
    """Formal-informal differences with a design-based Wald test."""
    d = _design(hh)
    inf = (hh["informal"] == 1).to_numpy()
    rows = []
    for name, col in [("CHE > 10%", "che10"), ("CHE > 25%", "che25"),
                      ("CHE, CTP >= 40%", "che_ctp40"),
                      ("OOP share of consumption", "oop_share")]:
        y = hh[col].to_numpy(float)
        a = d.subset(inf).mean(y)
        b = d.subset(~inf).mean(y)
        diff, z, p = diff_test(a[0], a[1], b[0], b[1])
        rows.append({"outcome": name, "informal": 100 * a[0], "informal_se": 100 * a[1],
                     "formal": 100 * b[0], "formal_se": 100 * b[1],
                     "difference_pp": 100 * diff, "z": z, "p_value": p})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    hh = pd.read_csv(config.DERIVED / "hh_w5.csv")
    hh = add_che_flags(hh)
    hh.to_csv(config.DERIVED / "hh_w5_che.csv", index=False)

    t1 = table1_sample(hh)
    t2 = table2_che(hh)
    imp = impoverishment(hh)
    t3, dec = table3_concentration(hh)
    gaps = sector_gap_tests(hh)

    t1.to_csv(config.TABLES / "table1_sample.csv", index=False)
    t2.to_csv(config.TABLES / "table2_che.csv", index=False)
    imp.to_csv(config.TABLES / "table2b_impoverishment.csv", index=False)
    t3.to_csv(config.TABLES / "table3_concentration.csv", index=False)
    dec.to_csv(config.TABLES / "table3b_decomposition.csv", index=False)
    gaps.to_csv(config.TABLES / "table2c_sector_gaps.csv", index=False)

    print("\n=== RQ1: catastrophic health expenditure ===")
    overall = t2[t2["dimension"] == "Overall"]
    for _, r in overall.iterrows():
        print(f"  {r['measure']:26s} {r['incidence_pct']:5.2f}%  "
              f"(95% CI {r['ci_low']:.2f}-{r['ci_high']:.2f}); "
              f"mean positive overshoot {r['mean_positive_overshoot_pct']:.2f} pp")
    print("\n  By sector:")
    print(gaps.to_string(index=False, float_format=lambda x: f"{x:,.3f}"))
    print("\n  Impoverishment:")
    print(imp.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    print(f"  Newly impoverished: {imp.attrs['newly_impoverished_millions']:.2f} million people")
    print("\n  Concentration indices:")
    print(t3.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
    return hh


if __name__ == "__main__":
    main()
