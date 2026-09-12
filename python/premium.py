"""
RQ2, part two - benefit mapping and the premium build-up.

Goes from what households currently spend to what an insurer would have to
charge: strip out services the NHIA basic package excludes, add the extra care
people use once the price at the point of service falls, subtract what the
member still pays as coinsurance, then load for administration, risk and
adverse selection. Every step is a separate, visible row in Table 5, and every
parameter comes from config so the robustness table can move it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config
from svy import Design, weighted_quantile


# ---------------------------------------------------------------------------
def induced_demand_factor(price_before, price_after, elasticity):
    """Utilisation response to a fall in the point-of-service price.

    Arc (midpoint) elasticity, so the answer does not depend on which price is
    called the base. Prices are expressed as the share of the full cost the
    patient pays: 1.0 uninsured, `coinsurance` once covered.
    """
    p_bar = (price_before + price_after) / 2.0
    if p_bar == 0:
        return 1.0
    pct_change_price = (price_after - price_before) / p_bar
    return 1.0 + elasticity * pct_change_price


def benefit_mapping(ind, coinsurance=None, elasticity=None,
                    covered_op=None, covered_ip=None, drug_share=None):
    """Insurer's expected cost per enrollee, person by person.

    Returns the individual file with the intermediate quantities attached so
    that the build-up can be audited row by row rather than taken on trust.
    """
    coinsurance = config.COINSURANCE_DRUGS if coinsurance is None else coinsurance
    elasticity = config.INDUCED_DEMAND_ELASTICITY if elasticity is None else elasticity
    covered_op = config.COVERED_SHARE_OUTPATIENT if covered_op is None else covered_op
    covered_ip = config.COVERED_SHARE_INPATIENT if covered_ip is None else covered_ip
    drug_share = config.DRUG_SHARE_OF_OUTPATIENT if drug_share is None else drug_share

    d = ind.copy()

    # 1. Traditional and spiritual care is outside the package entirely.
    trad = d.get("traditional", pd.Series(0, index=d.index)).fillna(0)
    d["cost_op_eligible"] = d["op_cost_annual"] * (1 - trad)
    d["cost_ip_eligible"] = d["ip_cost_annual"]

    # 2. Within eligible care, only part falls inside the basic package.
    d["covered_op"] = d["cost_op_eligible"] * covered_op
    d["covered_ip"] = d["cost_ip_eligible"] * covered_ip
    d["uncovered"] = ((d["cost_op_eligible"] * (1 - covered_op))
                      + (d["cost_ip_eligible"] * (1 - covered_ip))
                      + d["op_cost_annual"] * trad)

    # 3. Split covered outpatient care into drugs, which carry a co-payment,
    #    and everything else, which is free at the point of use.
    d["covered_drugs"] = d["covered_op"] * drug_share
    d["covered_services"] = d["covered_op"] * (1 - drug_share) + d["covered_ip"]

    # 4. Induced demand: the drug co-payment leaves a positive price, so drugs
    #    respond less than services that become free.
    f_drugs = induced_demand_factor(1.0, coinsurance, elasticity)
    f_services = induced_demand_factor(1.0, 0.0, elasticity)
    d["post_drugs"] = d["covered_drugs"] * f_drugs
    d["post_services"] = d["covered_services"] * f_services

    # 5. The insurer pays everything except the member's co-payment on drugs.
    d["insurer_cost"] = d["post_drugs"] * (1 - coinsurance) + d["post_services"]
    d["member_cost_after"] = (d["post_drugs"] * coinsurance + d["uncovered"])

    d.attrs.update({"coinsurance": coinsurance, "elasticity": elasticity,
                    "covered_op": covered_op, "covered_ip": covered_ip,
                    "drug_share": drug_share,
                    "induced_factor_drugs": f_drugs,
                    "induced_factor_services": f_services})
    return d


# ---------------------------------------------------------------------------
def premium_buildup(d, weight_col="ind_weight", pool_sizes=None,
                    admin=None, sd_mult=None, as_load=None, cvar_level=None,
                    seed=config.SEED):
    """Pure premium -> gross premium, with both risk-margin conventions."""
    pool_sizes = pool_sizes or config.POOL_SIZES
    admin = config.ADMIN_LOAD if admin is None else admin
    sd_mult = config.RISK_MARGIN_SD_MULT if sd_mult is None else sd_mult
    as_load = config.ADVERSE_SELECTION_LOAD if as_load is None else as_load
    cvar_level = config.CVAR_LEVEL if cvar_level is None else cvar_level

    w = d[weight_col].to_numpy(float)
    w = w / w.sum()

    def wmean(x):
        return float(np.sum(w * np.asarray(x, float)))

    def wsd(x):
        x = np.asarray(x, float)
        m = wmean(x)
        return float(np.sqrt(np.sum(w * (x - m) ** 2)))

    current_total = wmean(d["op_cost_annual"] + d["ip_cost_annual"])
    eligible = wmean(d["cost_op_eligible"] + d["cost_ip_eligible"])
    covered = wmean(d["covered_op"] + d["covered_ip"])
    post_induced = wmean(d["post_drugs"] + d["post_services"])
    pure = wmean(d["insurer_cost"])
    sigma = wsd(d["insurer_cost"])

    rows = [
        ("Observed out-of-pocket cost per person-year", current_total),
        ("  less traditional and spiritual care", eligible),
        (f"  less services outside the basic package "
         f"(outpatient {d.attrs['covered_op']:.0%} / inpatient "
         f"{d.attrs['covered_ip']:.0%} covered)", covered),
        (f"  plus induced demand (arc elasticity {d.attrs['elasticity']:.2f})",
         post_induced),
        (f"  less member co-payment on drugs ({d.attrs['coinsurance']:.0%})", pure),
    ]
    build = pd.DataFrame(rows, columns=["step", "naira_per_person_year"])
    build["change"] = build["naira_per_person_year"].diff()

    # Risk margin. Both conventions price the uncertainty in the pool average,
    # so both shrink with pool size; that is the whole argument for scale.
    rng = np.random.default_rng(seed)
    cost = d["insurer_cost"].to_numpy(float)
    prob = w / w.sum()
    margins = []
    for n in pool_sizes:
        sd_margin = sd_mult * sigma / np.sqrt(n)
        draws = rng.choice(cost, size=(2000, n), replace=True, p=prob).mean(axis=1)
        cvar = draws[draws >= np.quantile(draws, cvar_level)].mean()
        margins.append({
            "pool_size": n,
            "risk_margin_sd": sd_margin,
            "risk_margin_cvar": float(cvar - pure),
            "sd_of_pool_mean": float(draws.std()),
        })
    margins = pd.DataFrame(margins)

    gross = []
    for _, m in margins.iterrows():
        for kind in ["sd", "cvar"]:
            rm = m[f"risk_margin_{kind}"]
            g = (pure + rm) * (1 + admin) * (1 + as_load)
            gross.append({
                "pool_size": int(m["pool_size"]),
                "risk_margin_basis": "Standard deviation" if kind == "sd" else f"CVaR {cvar_level:.0%}",
                "pure_premium": pure,
                "risk_margin": rm,
                "admin_load": (pure + rm) * admin,
                "adverse_selection_load": (pure + rm) * (1 + admin) * as_load,
                "gross_premium_per_person": g,
            })
    gross = pd.DataFrame(gross)

    summary = {
        "pure_premium": pure, "sigma": sigma,
        "current_oop": current_total, "covered_before_induced": covered,
        "post_induced": post_induced,
        "induced_uplift_pct": 100 * (post_induced / covered - 1) if covered else np.nan,
    }
    return build, margins, gross, summary


# ---------------------------------------------------------------------------
def affordability(hh, gross_per_person, pool_size=20_000,
                  basis="Standard deviation"):
    """Premium as a share of consumption, by quintile, per person and per household.

    Two household sizes are reported, because they answer different questions and
    the quintiles here are quintiles of *people* ranked on per-capita consumption.
    The population-weighted mean is the size of the household the average person
    in the quintile lives in; the household-weighted mean is the size of the
    average household in it. In the poorest quintile these are 10.0 and 8.1 -
    poor households are large, which is much of why their per-capita consumption
    is low. A premium billed to a household is charged once per household, so
    `premium_per_household` uses the household-weighted size; the per-capita
    share, which is the affordability test, is unaffected by the choice.
    """
    d = Design(hh, "popwt", config.STRATA, "cluster")
    dh = Design(hh, config.HH_WEIGHT, config.STRATA, "cluster")
    rows = []
    for q in sorted(hh["quintile"].unique()):
        mask = (hh["quintile"] == q).to_numpy()
        sub = d.subset(mask)
        cons_pc, _ = sub.mean(hh["cons_pc"].to_numpy(float))
        size_pop, _ = sub.mean(hh["hhsize"].to_numpy(float))
        size_hh, _ = dh.subset(mask).mean(hh["hhsize"].to_numpy(float))
        rows.append({
            "quintile": hh.loc[mask, "quintile_label"].iloc[0],
            "mean_consumption_per_capita": cons_pc,
            "mean_household_size": size_hh,
            "mean_household_size_pop_weighted": size_pop,
            "premium_per_person": gross_per_person,
            "premium_per_household": gross_per_person * size_hh,
            "premium_pct_of_per_capita_consumption": 100 * gross_per_person / cons_pc,
            "exceeds_5pct_threshold":
                gross_per_person / cons_pc > config.AFFORDABILITY_THRESHOLD,
        })
    out = pd.DataFrame(rows)
    out["pool_size"] = pool_size
    out["risk_margin_basis"] = basis
    return out


def state_scheme_comparison(gross_per_person):
    """Published state-scheme premiums, for external validation.

    These are contribution rates announced by state schemes and are entered by
    hand; each is marked [VERIFY] and must be re-checked against the scheme's
    own published schedule before the manuscript is submitted. They are context
    for the modelled premium, not an input to it.
    """
    rows = [
        {"scheme": "Lagos LASHMA 'Ilera Eko', individual informal-sector plan",
         "annual_premium_naira": 40_000, "year": 2024, "source": "[VERIFY]"},
        {"scheme": "Lagos LASHMA 'Ilera Eko', family of six",
         "annual_premium_naira": 100_000, "year": 2024, "source": "[VERIFY]"},
        {"scheme": "NHIA formal-sector equivalent capitation (indicative)",
         "annual_premium_naira": 30_000, "year": 2024, "source": "[VERIFY]"},
    ]
    out = pd.DataFrame(rows)
    out["modelled_premium_per_person"] = gross_per_person
    out["ratio_modelled_to_published"] = (
        gross_per_person / out["annual_premium_naira"])
    return out


def risk_class_table(ind_scored):
    """Relative cost by risk class, for a scheme that wanted to risk-rate.

    The NHIA community-rates, so this is reported as a description of the risk
    structure the community rate is averaging over - and as the input the
    adverse-selection scenarios need.
    """
    d = ind_scored.copy()
    w = d["ind_weight"].to_numpy(float)
    overall = np.average(d["insurer_cost"], weights=w)
    rows = []
    for dim, col in [("Age band", "age_band"), ("Sex", "female"),
                     ("Residence", "urban"), ("Consumption quintile", "quintile"),
                     ("Severe functional difficulty", "chronic"),
                     ("Sector", "informal")]:
        for g, sub in d.groupby(col, observed=True):
            ws = sub["ind_weight"].to_numpy(float)
            mean = np.average(sub["insurer_cost"], weights=ws)
            label = {"female": {0: "Male", 1: "Female"},
                     "urban": {0: "Rural", 1: "Urban"},
                     "chronic": {0: "No", 1: "Yes"},
                     "informal": {0: "Formal", 1: "Informal"}}.get(col, {}).get(g, g)
            rows.append({"dimension": dim, "class": str(label),
                         "n": len(sub),
                         "mean_insurer_cost": mean,
                         "relativity": mean / overall})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    ind = pd.read_csv(config.DERIVED / "ind_w5.csv")
    scored = pd.read_csv(config.DERIVED / "ind_w5_scored.csv")
    ind = ind.merge(scored[["hhid", "indiv", "pred_cost"]], on=["hhid", "indiv"],
                    how="inner")
    hh = pd.read_csv(config.DERIVED / "hh_w5_che.csv")

    d = benefit_mapping(ind)
    build, margins, gross, summary = premium_buildup(d)

    print("\n=== RQ2: premium build-up (naira per person per year) ===")
    print(build.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))
    print(f"\nInduced demand raises covered cost by "
          f"{summary['induced_uplift_pct']:.1f}% "
          f"(drugs x{d.attrs['induced_factor_drugs']:.3f}, "
          f"services x{d.attrs['induced_factor_services']:.3f})")
    print(f"Pure premium: N{summary['pure_premium']:,.0f}   "
          f"SD of individual annual cost: N{summary['sigma']:,.0f}")
    print("\nGross premium by pool size and risk-margin basis:")
    print(gross.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

    base = gross[(gross["pool_size"] == 20_000)
                 & (gross["risk_margin_basis"] == "Standard deviation")]
    gpp = float(base["gross_premium_per_person"].iloc[0])
    aff = affordability(hh, gpp)
    print(f"\nAffordability of the N{gpp:,.0f} premium:")
    print(aff.to_string(index=False, float_format=lambda x: f"{x:,.1f}"))

    rc = risk_class_table(d)
    comp = state_scheme_comparison(gpp)

    build.to_csv(config.TABLES / "table5a_premium_buildup.csv", index=False)
    margins.to_csv(config.TABLES / "table5b_risk_margins.csv", index=False)
    gross.to_csv(config.TABLES / "table5c_gross_premium.csv", index=False)
    aff.to_csv(config.TABLES / "table5d_affordability.csv", index=False)
    rc.to_csv(config.TABLES / "table5e_risk_classes.csv", index=False)
    comp.to_csv(config.TABLES / "table5f_state_comparison.csv", index=False)
    d.to_csv(config.DERIVED / "ind_w5_priced.csv", index=False)

    print("\nRisk relativities (community rate = 1.00):")
    print(rc.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    return {"mapped": d, "build": build, "gross": gross, "summary": summary,
            "affordability": aff, "gross_per_person": gpp}


if __name__ == "__main__":
    main()
