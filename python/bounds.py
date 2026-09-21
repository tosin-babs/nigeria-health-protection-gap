"""
Uncertainty that the design-based standard errors do not capture.

Two exercises, each producing one table:

  recall_bounds()  The headline scales each person's observed 4-week outpatient
                   spending to a year, which assumes the other twelve windows
                   repeat the observed one. That is the maximum-persistence
                   case and it maximises the dispersion of annual cost across
                   households. The opposite extreme draws each person's annual
                   cost as a sum of independent 4-week windows from the fitted
                   frequency model and the observed episode-cost distribution.
                   The two cases bound the effect of the recall treatment on
                   CHE, the premium and the subsidy; the seasonal multipliers
                   (x12, x10) are carried alongside.

  bootstrap()      A Rao-Wu rescaled bootstrap over enumeration areas within
                   strata, giving percentile intervals for the pure and gross
                   premium, the affordable contribution, the expected claim
                   under each take-up pattern, and the minimum subsidy. The
                   subsidy is a function of the whole cost distribution, so no
                   linearised standard error exists for it; this is the only
                   way to put an interval on it that respects the design.
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


# ---------------------------------------------------------------------------
def _recompute_household(hh, ind):
    """Household OOP and consumption from an individual file with new costs."""
    agg = ind.groupby("hhid")[["op_cost_annual", "ip_cost_annual"]].sum()
    h = hh.set_index("hhid").copy()
    h["oop_annual"] = (agg["op_cost_annual"] + agg["ip_cost_annual"]).reindex(h.index).fillna(0.0)
    non_health = h["cons_annual"] - hh.set_index("hhid")["oop_annual"]
    h["cons_annual"] = non_health + h["oop_annual"]
    h["ctp"] = np.where(h["subsistence"] < h["food_annual"],
                        h["cons_annual"] - h["subsistence"],
                        h["cons_annual"] - h["food_annual"]).clip(1.0)
    return add_che_flags(h.reset_index())


def _pool_subsidy(mapped, contribution, gross_premium, n_sim, seed=config.SEED):
    pool = mapped[mapped["informal"] == 1]
    out = {}
    for tag, strength in [("random", 1.0), ("adverse", config.ADVERSE_SELECTION_STRENGTH)]:
        w = selection_probabilities(pool["pred_cost"], pool["ind_weight"], strength)
        v, p = cost_support(pool["insurer_cost"], w * len(pool))
        paths = claims_paths(v, p, 20_000, 3, n_sim=n_sim, seed=seed)
        out[f"expected_claim_{tag}"] = float(v @ p)
        out[f"min_subsidy_{tag}"] = minimum_subsidy_from_paths(
            paths, 20_000, contribution, 0.0, 0.05, gross_premium)
    return out


def _headline(hh, ind, n_sim=4_000):
    d = _design(hh)
    che10, _ = d.mean(hh["che10"].to_numpy(float))
    ctp40, _ = d.mean(hh["che_ctp40"].to_numpy(float))
    mapped = benefit_mapping(ind)
    _, _, gross, summary = premium_buildup(mapped)
    g = gross[(gross["pool_size"] == 20_000)
              & (gross["risk_margin_basis"] == "Standard deviation")]
    gp = float(g["gross_premium_per_person"].iloc[0])
    contribution = affordable_contribution(hh).attrs["target_contribution"]
    out = {"che10_pct": 100 * che10, "che_ctp40_pct": 100 * ctp40,
           "pure_premium": summary["pure_premium"], "gross_premium": gp,
           "affordable_contribution": contribution}
    out.update(_pool_subsidy(mapped, contribution, gp, n_sim))
    return out


def independent_windows(ind, p_hat, rng):
    """One replicate of annual outpatient cost with no within-year persistence.

    N_i ~ Poisson(13 * p_i), where p_i is the fitted 4-week contact probability,
    and each episode's cost is resampled from observed episode costs in the
    person's own consumption quintile, so the heavy tail is kept.
    """
    d = ind.copy()
    n_ep = rng.poisson(config.OUTPATIENT_ANNUALISER * p_hat)
    costs = {}
    for q, sub in d[(d["sought_care"] == 1)].groupby("quintile"):
        costs[q] = (sub["op_cost_window"].to_numpy(float),
                    sub["ind_weight"].to_numpy(float) / sub["ind_weight"].sum())
    annual = np.zeros(len(d))
    for q in costs:
        idx = np.flatnonzero((d["quintile"] == q).to_numpy())
        v, pr = costs[q]
        total = int(n_ep[idx].sum())
        if total:
            draws = rng.choice(v, size=total, p=pr)
            owner = np.repeat(np.arange(len(idx)), n_ep[idx])
            annual[idx] = np.bincount(owner, weights=draws, minlength=len(idx))
    d["op_cost_annual"] = annual
    d["op_drug_annual"] = annual * config.DRUG_SHARE_OF_OUTPATIENT
    d["cost_annual"] = d["op_cost_annual"] + d["ip_cost_annual"]
    return d


def recall_bounds(hh, ind):
    scored = costmodels.prepare(pd.read_csv(config.DERIVED / "ind_main.csv"))
    freq = costmodels.fit_frequency(scored)
    p_hat = pd.Series(np.asarray(freq["outpatient_poisson"].fittedvalues),
                      index=pd.MultiIndex.from_frame(scored[["hhid", "indiv"]]))
    key = pd.MultiIndex.from_frame(ind[["hhid", "indiv"]])
    p_i = p_hat.reindex(key).to_numpy(float)
    p_i = np.where(np.isfinite(p_i), p_i, np.nanmean(p_i))

    rows = []
    base = _headline(hh, ind)
    rows.append({"case": "x13, window scaled to a year (headline, full persistence)",
                 **base})

    # Independent windows: average the CHE rates over replicates; pool the
    # replicates for the cost distribution that prices the premium and subsidy.
    rng = np.random.default_rng(config.SEED)
    che, ctp, reps = [], [], []
    for r in range(config.RECALL_BOUND_REPLICATES):
        d_r = independent_windows(ind, p_i, rng)
        h_r = _recompute_household(hh, d_r)
        des = _design(h_r)
        che.append(des.mean(h_r["che10"].to_numpy(float))[0])
        ctp.append(des.mean(h_r["che_ctp40"].to_numpy(float))[0])
        d_r["ind_weight"] = d_r["ind_weight"] / config.RECALL_BOUND_REPLICATES
        reps.append(d_r)
    stacked = pd.concat(reps, ignore_index=True)
    mapped = benefit_mapping(stacked)
    _, _, gross, summary = premium_buildup(mapped)
    gp = float(gross[(gross["pool_size"] == 20_000)
                     & (gross["risk_margin_basis"] == "Standard deviation")]
               ["gross_premium_per_person"].iloc[0])
    contribution = base["affordable_contribution"]
    row = {"case": "x13, independent 4-week windows (no persistence)",
           "che10_pct": 100 * float(np.mean(che)),
           "che_ctp40_pct": 100 * float(np.mean(ctp)),
           "pure_premium": summary["pure_premium"], "gross_premium": gp,
           "affordable_contribution": contribution}
    row.update(_pool_subsidy(mapped, contribution, gp, 4_000))
    rows.append(row)

    from robustness import variant_annualiser
    for mult in config.RECALL_ANNUALISER_CASES[1:]:
        h_m, i_m = variant_annualiser(hh, ind, mult)
        h_m = add_che_flags(h_m)
        rows.append({"case": f"x{mult:.0f}, window scaled", **_headline(h_m, i_m)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def rao_wu_multipliers(strata, psu, rng):
    """Weight multipliers for one Rao-Wu rescaled bootstrap replicate."""
    key = pd.Series(strata).astype(str) + "|" + pd.Series(psu).astype(str)
    mult = np.ones(len(key))
    for h in pd.unique(pd.Series(strata)):
        sel = (pd.Series(strata) == h).to_numpy()
        psus = pd.unique(key[sel])
        n_h = len(psus)
        if n_h < 2:
            continue
        draw = rng.choice(psus, size=n_h - 1, replace=True)
        counts = pd.Series(draw).value_counts()
        m = key[sel].map(counts).fillna(0.0).to_numpy(float) * n_h / (n_h - 1)
        mult[sel] = m
    return mult


def bootstrap(hh, ind, B=None, n_sim=None):
    B = config.BOOT_REPLICATES if B is None else B
    n_sim = config.BOOT_N_SIM if n_sim is None else n_sim
    rng = np.random.default_rng(config.SEED + 99)
    mapped = benefit_mapping(ind)
    hh_key = hh.set_index("hhid")
    rows = []
    for b in range(B):
        m_hh = rao_wu_multipliers(hh["strata"].to_numpy(), hh["cluster"].to_numpy(), rng)
        h = hh.copy()
        h["popwt"] = h["popwt"] * m_hh
        h["hh_weight"] = h["hh_weight"] * m_hh
        m_ind = pd.Series(m_hh, index=hh["hhid"]).reindex(mapped["hhid"]).to_numpy(float)
        i = mapped.copy()
        i["ind_weight"] = i["ind_weight"] * m_ind
        i = i[i["ind_weight"] > 0]

        d = _design(h)
        che10, _ = d.mean(h["che10"].to_numpy(float))
        ctp40, _ = d.mean(h["che_ctp40"].to_numpy(float))
        w = i["ind_weight"].to_numpy(float)
        w = w / w.sum()
        pure = float(w @ i["insurer_cost"].to_numpy(float))
        sigma = float(np.sqrt(w @ (i["insurer_cost"].to_numpy(float) - pure) ** 2))
        gp = ((pure + config.RISK_MARGIN_SD_MULT * sigma / np.sqrt(20_000))
              * (1 + config.ADMIN_LOAD) * (1 + config.ADVERSE_SELECTION_LOAD))
        contribution = affordable_contribution(h).attrs["target_contribution"]
        row = {"replicate": b, "che10_pct": 100 * che10, "che_ctp40_pct": 100 * ctp40,
               "pure_premium": pure, "gross_premium": gp,
               "affordable_contribution": contribution}
        row.update(_pool_subsidy(i, contribution, gp, n_sim, seed=config.SEED + b))
        rows.append(row)
        if (b + 1) % 25 == 0:
            print(f"  bootstrap replicate {b + 1}/{B}")
    reps = pd.DataFrame(rows)

    point = _headline(hh, ind, n_sim=config.N_SIM)
    summary = []
    for col in [c for c in reps.columns if c != "replicate"]:
        v = reps[col].to_numpy(float)
        v = v[np.isfinite(v)]
        summary.append({"quantity": col, "point_estimate": point.get(col, np.nan),
                        "boot_mean": v.mean(), "boot_se": v.std(ddof=1),
                        "ci_low": np.quantile(v, 0.025),
                        "ci_high": np.quantile(v, 0.975), "n_replicates": len(v)})
    return pd.DataFrame(summary), reps


# ---------------------------------------------------------------------------
def main():
    hh = pd.read_csv(config.DERIVED / "hh_main_che.csv")
    ind = pd.read_csv(config.DERIVED / "ind_main_priced.csv")

    print("Recall-treatment bounds ...")
    rb = recall_bounds(hh, ind)
    rb.to_csv(config.TABLES / "table9_recall_bounds.csv", index=False)
    print(rb.to_string(index=False, float_format=lambda x: f"{x:,.1f}"))

    print("\nDesign-based bootstrap ...")
    summary, reps = bootstrap(hh, ind)
    summary.to_csv(config.TABLES / "table10_bootstrap.csv", index=False)
    reps.to_csv(config.TABLES / "table10b_bootstrap_replicates.csv", index=False)
    print(summary.to_string(index=False, float_format=lambda x: f"{x:,.1f}"))
    return rb, summary


if __name__ == "__main__":
    main()
