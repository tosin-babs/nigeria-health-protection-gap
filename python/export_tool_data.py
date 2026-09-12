"""
Export a compact model payload for the public premium-and-solvency calculator.

The calculator has to give the same answer as the paper for the paper's own
parameters, and a defensible answer for any other parameter set a user picks.
That rules out shipping a table of pre-computed results. Instead we ship the
inputs the model is a function of, and let the browser re-run the model.

Two observations make that cheap:

  * The whole benefit-mapping and premium build-up is a weighted mean of an
    arithmetic function of three per-person quantities - annual outpatient
    cost, annual inpatient cost, and whether the care was traditional. So the
    24,629-person file collapses losslessly to its distinct (op, ip, trad)
    triples carrying summed weights.

  * The ruin simulation draws from the distribution of insurer cost in the
    insured pool. Insurer cost is that same function of the same triples, so
    the same collapsed support serves, carrying one probability vector per
    take-up assumption (computed here, because they depend on predicted cost,
    which the browser has no way to recompute).

Writes tool/model_data.json.
"""

from __future__ import annotations

import json
import subprocess
from datetime import date

import numpy as np
import pandas as pd

import config
import premium as premium_mod
import ruin as ruin_mod
from svy import Design

OUT = config.ROOT / "tool" / "model_data.json"


def _collapse(df, weight):
    """Collapse to distinct (op, ip, trad) triples with summed weights."""
    g = (df.groupby(["op_cost_annual", "ip_cost_annual", "traditional"],
                    sort=True)[weight].sum().reset_index())
    return g


def _round_sig(x, sig=6):
    """Trim float noise so the JSON stays small without changing any result."""
    x = np.asarray(x, float)
    out = np.zeros_like(x)
    nz = x != 0
    # np.round takes one scalar `decimals`, so scale each element instead.
    scale = 10.0 ** (sig - 1 - np.floor(np.log10(np.abs(x[nz]))))
    out[nz] = np.round(x[nz] * scale) / scale
    return out


def main():
    ind = pd.read_csv(config.DERIVED / "ind_w5_priced.csv")
    hh = pd.read_csv(config.DERIVED / "hh_w5_che.csv")

    # ---------------------------------------------------- premium population --
    pop = _collapse(ind, "ind_weight")

    # -------------------------------------------------------- insured pool ----
    pool = ind[ind["informal"] == 1].copy()
    tilts = {"random": 1.0, "moderate": 1.5,
             "strong": config.ADVERSE_SELECTION_STRENGTH}
    pool_probs = {}
    for name, strength in tilts.items():
        pool["w_sel"] = ruin_mod.selection_probabilities(
            pool["pred_cost"], pool["ind_weight"], strength)
        g = _collapse(pool, "w_sel")
        pool_probs[name] = g
    # Every tilt collapses on the same key, so align them on one support.
    support = pool_probs["random"][["op_cost_annual", "ip_cost_annual",
                                    "traditional"]].copy()
    for name, g in pool_probs.items():
        merged = support.merge(g, on=["op_cost_annual", "ip_cost_annual",
                                      "traditional"], how="left")
        support[name] = merged["w_sel"].fillna(0.0).to_numpy()
        support[name] = support[name] / support[name].sum()

    # ------------------------------------------------------------ quintiles ----
    d = Design(hh, "popwt", config.STRATA, "cluster")
    dh = Design(hh, config.HH_WEIGHT, config.STRATA, "cluster")
    quintiles = []
    for q in sorted(hh["quintile"].unique()):
        mask = (hh["quintile"] == q).to_numpy()
        sub = d.subset(mask)
        cons_pc, _ = sub.mean(hh["cons_pc"].to_numpy(float))
        # Household-weighted: a premium is billed once per household, so the
        # average household is the right unit. See premium.affordability().
        size, _ = dh.subset(mask).mean(hh["hhsize"].to_numpy(float))
        informal_mask = mask & (hh["informal"] == 1).to_numpy()
        icons, _ = d.subset(informal_mask).mean(hh["cons_pc"].to_numpy(float))
        quintiles.append({
            "label": hh.loc[mask, "quintile_label"].iloc[0],
            "cons_pc": round(float(cons_pc), 1),
            "hhsize": round(float(size), 3),
            "informal_cons_pc": round(float(icons), 1),
        })

    aff = ruin_mod.affordable_contribution(hh)

    # Observed coverage today - the context the price should be read against.
    cov_tbl = pd.read_csv(config.TABLES / "table1b_coverage.csv")
    cov_row = cov_tbl[(cov_tbl["dimension"] == "Overall")].iloc[0]
    cov_inf = cov_tbl[(cov_tbl["dimension"] == "Sector")
                      & (cov_tbl["group"] == "Informal")].iloc[0]

    # ------------------------------------------------- headline paper values --
    t2 = pd.read_csv(config.TABLES / "table2_che.csv")
    overall = t2[t2["dimension"] == "Overall"].set_index("measure")
    gross_t = pd.read_csv(config.TABLES / "table5c_gross_premium.csv")

    def _headline(measure):
        r = overall.loc[measure]
        return {"pct": round(float(r["incidence_pct"]), 2),
                "lo": round(float(r["ci_low"]), 2),
                "hi": round(float(r["ci_high"]), 2)}

    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             cwd=config.ROOT, capture_output=True, text=True,
                             timeout=5).stdout.strip() or None
    except Exception:
        rev = None

    payload = {
        "meta": {
            "source": "Nigeria General Household Survey-Panel wave 5 (2023/24), "
                      "NBS / World Bank LSMS-ISA",
            "n_households": int(len(hh)),
            "n_individuals": int(len(ind)),
            "n_pool_individuals": int(len(pool)),
            "price_base": config.CPI_BASE_LABEL,
            "generated": date.today().isoformat(),
            "git_rev": rev,
        },
        "defaults": {
            "covered_op": config.COVERED_SHARE_OUTPATIENT,
            "covered_ip": config.COVERED_SHARE_INPATIENT,
            "coinsurance": config.COINSURANCE_DRUGS,
            "drug_share": config.DRUG_SHARE_OF_OUTPATIENT,
            "elasticity": config.INDUCED_DEMAND_ELASTICITY,
            "admin": config.ADMIN_LOAD,
            "sd_mult": config.RISK_MARGIN_SD_MULT,
            "as_load": config.ADVERSE_SELECTION_LOAD,
            "expense": config.EXPENSE_RATIO,
            "affordability": config.AFFORDABILITY_THRESHOLD,
            "pool_size": 20_000,
            "years": 3,
            "contribution": round(float(aff.attrs["target_contribution"]), 0),
        },
        "population": {
            "op": _round_sig(pop["op_cost_annual"]).tolist(),
            "ip": _round_sig(pop["ip_cost_annual"]).tolist(),
            "trad": pop["traditional"].round(4).tolist(),
            "w": _round_sig(pop["ind_weight"] / pop["ind_weight"].sum(),
                            8).tolist(),
        },
        "pool": {
            "op": _round_sig(support["op_cost_annual"]).tolist(),
            "ip": _round_sig(support["ip_cost_annual"]).tolist(),
            "trad": support["traditional"].round(4).tolist(),
            "p": {k: _round_sig(support[k], 8).tolist() for k in tilts},
        },
        "quintiles": quintiles,
        "paper": {
            "che10": _headline("Budget share > 10%"),
            "che25": _headline("Budget share > 25%"),
            "ctp40": _headline("Capacity to pay >= 40%"),
            "pure_premium": 21195.07,
            "gross_premium": round(float(
                gross_t[(gross_t["pool_size"] == 20_000)
                        & (gross_t["risk_margin_basis"] == "Standard deviation")]
                ["gross_premium_per_person"].iloc[0]), 2),
            "contribution": round(float(aff.attrs["target_contribution"]), 0),
            "min_subsidy_random": 16482.0,
            "min_subsidy_strong": 52573.0,
            "impoverished_millions": 5.11,
            "informal_share_pct": 81.2,
            "covered_individuals_pct": round(float(cov_row["individuals_covered_pct"]), 2),
            "covered_hh_pct": round(float(cov_row["hh_with_cover_pct"]), 2),
            "covered_informal_hh_pct": round(float(cov_inf["hh_with_cover_pct"]), 2),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":")))
    kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(config.ROOT)}  ({kb:,.0f} KB)")
    print(f"  population support: {len(payload['population']['op']):,} triples")
    print(f"  pool support:       {len(payload['pool']['op']):,} triples")

    # ----------------------------------------------------------- validation --
    # The browser must reproduce the paper. Check the collapsed support gives
    # the same pure premium as the full individual file.
    d_full = premium_mod.benefit_mapping(ind)
    w = d_full["ind_weight"].to_numpy(float)
    pure_full = float(np.average(d_full["insurer_cost"], weights=w))

    op = np.array(payload["population"]["op"])
    ip = np.array(payload["population"]["ip"])
    tr = np.array(payload["population"]["trad"])
    wp = np.array(payload["population"]["w"])
    c = config.COINSURANCE_DRUGS
    e = config.INDUCED_DEMAND_ELASTICITY
    f_d = premium_mod.induced_demand_factor(1.0, c, e)
    f_s = premium_mod.induced_demand_factor(1.0, 0.0, e)
    cov_op = op * (1 - tr) * config.COVERED_SHARE_OUTPATIENT
    cov_ip = ip * config.COVERED_SHARE_INPATIENT
    drugs = cov_op * config.DRUG_SHARE_OF_OUTPATIENT
    svcs = cov_op * (1 - config.DRUG_SHARE_OF_OUTPATIENT) + cov_ip
    insurer = drugs * f_d * (1 - c) + svcs * f_s
    pure_collapsed = float(np.sum(wp * insurer))

    rel = abs(pure_collapsed / pure_full - 1)
    print(f"\n  pure premium, full file : N{pure_full:,.2f}")
    print(f"  pure premium, collapsed : N{pure_collapsed:,.2f}  "
          f"(relative difference {rel:.2e})")
    if rel > 1e-4:
        raise SystemExit("collapsed support does not reproduce the pure premium")
    print("  OK - the calculator payload reproduces the paper.")


if __name__ == "__main__":
    main()
