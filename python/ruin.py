"""
RQ3 - solvency of a state-level informal-sector pool.

A discrete-time collective risk model. Each year the pool receives contributions
and a subsidy, pays claims and expenses, and carries the surplus forward:

    U_t = U_{t-1} + n * (C + s) * (1 - expense) - S_t

Ruin is U_t < 0 at any t up to the horizon. The question the paper asks is not
"is the premium right" - the premium is unaffordable, which is the finding of
RQ2 - but "given a contribution the target population can actually pay, how
large a subsidy keeps the pool solvent".

Simulating the aggregate claims of a 100,000-life pool ten thousand times is
three billion individual draws if done naively. Instead the empirical cost
distribution is collapsed to its distinct values and each pool-year is drawn as
one multinomial over that support, which is exact - not an approximation - and
roughly three orders of magnitude faster. verify_multinomial_shortcut() checks
it against direct resampling.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config
from svy import Design


# ---------------------------------------------------------------------------
# Aggregate-claims simulation
# ---------------------------------------------------------------------------
def cost_support(values, weights):
    """Collapse a weighted sample to (distinct value, probability) pairs."""
    s = pd.Series(np.asarray(weights, float)).groupby(
        pd.Series(np.asarray(values, float))).sum()
    v = s.index.to_numpy(float)
    p = s.to_numpy(float)
    return v, p / p.sum()


def selection_probabilities(pred_cost, base_weights, strength):
    """Enrolment probabilities that rise with predicted cost.

    strength is the multiplier on the enrolment odds per standard deviation of
    log predicted cost, so strength = 1 is random take-up.
    """
    if strength <= 1.0:
        w = np.asarray(base_weights, float)
        return w / w.sum()
    z = np.log(np.maximum(np.asarray(pred_cost, float), 1.0))
    z = (z - z.mean()) / z.std()
    tilt = np.exp(np.log(strength) * z)
    w = np.asarray(base_weights, float) * tilt
    return w / w.sum()


def simulate_pool_claims(values, probs, n, n_draws, rng, chunk=2000):
    """Draw `n_draws` realisations of the aggregate claims of an n-life pool."""
    out = np.empty(n_draws)
    values = np.asarray(values, float)
    i = 0
    while i < n_draws:
        m = min(chunk, n_draws - i)
        counts = rng.multinomial(n, probs, size=m)
        out[i:i + m] = counts @ values
        i += m
    return out


def verify_multinomial_shortcut(values, probs, n=5_000, n_draws=2_000,
                                seed=config.SEED):
    """Check the multinomial route against direct resampling of individuals."""
    rng = np.random.default_rng(seed)
    fast = simulate_pool_claims(values, probs, n, n_draws, rng)
    rng2 = np.random.default_rng(seed + 1)
    direct = rng2.choice(values, size=(n_draws, n), replace=True, p=probs).sum(axis=1)
    return pd.DataFrame([{
        "statistic": s,
        "multinomial": f(fast),
        "direct_resampling": f(direct),
        "relative_difference": (f(fast) - f(direct)) / abs(f(direct)),
    } for s, f in [("mean", np.mean), ("sd", np.std),
                   ("p95", lambda x: np.quantile(x, 0.95)),
                   ("p99", lambda x: np.quantile(x, 0.99))]])


# ---------------------------------------------------------------------------
# Surplus process
# ---------------------------------------------------------------------------
def claims_paths(values, probs, n, years, n_sim=config.N_SIM, seed=config.SEED):
    """An (n_sim x years) matrix of annual aggregate claims for one pool.

    Claims do not depend on the contribution, the subsidy or the opening
    capital, so they are drawn once per pool and reused across the whole
    financing grid. That is a large speed-up and it also means every financing
    scenario faces the *same* simulated experience - common random numbers -
    so differences between them are signal rather than Monte Carlo noise.
    """
    rng = np.random.default_rng(seed)
    return np.column_stack([
        simulate_pool_claims(values, probs, n, n_sim, rng) for _ in range(years)
    ])


def ruin_from_paths(paths, n, contribution, subsidy, u0,
                    expense=config.EXPENSE_RATIO, inflation_shock=0.0):
    """Evaluate the surplus process on pre-drawn claims."""
    years = paths.shape[1]
    claims = paths
    if inflation_shock:
        # A permanent level shift in claims from year 2 onwards: contributions
        # and subsidy are fixed in advance, claims are not.
        factors = np.array([1.0 if t == 1 else 1 + inflation_shock
                            for t in range(1, years + 1)])
        claims = paths * factors

    income = n * (contribution + subsidy) * (1 - expense)
    surplus = u0 + income * np.arange(1, years + 1) - np.cumsum(claims, axis=1)
    ruined = (surplus < 0).any(axis=1)
    # Once ruined the pool cannot trade on, so the terminal surplus reported for
    # a ruined path is its value at ruin, not a later recovery.
    terminal = np.where(ruined, surplus.min(axis=1), surplus[:, -1])

    psi = float(ruined.mean())
    return {
        "psi": psi,
        "mc_se": float(np.sqrt(psi * (1 - psi) / len(ruined))),
        "mean_terminal_surplus": float(terminal.mean()),
        "p05_terminal_surplus": float(np.quantile(terminal, 0.05)),
        "income_per_enrollee": contribution + subsidy,
    }


def minimum_subsidy_from_paths(paths, n, contribution, u0, target,
                               gross_premium, expense=config.EXPENSE_RATIO,
                               inflation_shock=0.0):
    """Smallest subsidy per enrollee holding the ruin probability below `target`.

    The ruin probability is monotone decreasing in the subsidy on a fixed set of
    claim paths, so bisection is exact up to the grid tolerance.
    """
    def psi(s):
        return ruin_from_paths(paths, n, contribution, s, u0, expense,
                               inflation_shock)["psi"]

    lo, hi = 0.0, max(gross_premium * 3.0, contribution * 3.0 + 1.0)
    if psi(lo) <= target:
        return 0.0
    if psi(hi) > target:
        return np.nan
    for _ in range(24):
        mid = (lo + hi) / 2
        if psi(mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------------------
def affordable_contribution(hh, quintiles=(1, 2, 3)):
    """The most the target population can pay, at the 5%-of-consumption ceiling.

    RQ2 shows the actuarial premium is far above this, which is exactly why the
    subsidy question is the one that matters.
    """
    d = Design(hh, "popwt", config.STRATA, "cluster")
    mask = (hh["informal"] == 1).to_numpy()
    sub = d.subset(mask)
    overall, _ = sub.mean(hh["cons_pc"].to_numpy(float))
    rows = [{"group": "All informal households",
             "mean_consumption_per_capita": overall,
             "affordable_contribution": overall * config.AFFORDABILITY_THRESHOLD}]
    for q in sorted(hh["quintile"].unique()):
        m = mask & (hh["quintile"] == q).to_numpy()
        e, _ = d.subset(m).mean(hh["cons_pc"].to_numpy(float))
        rows.append({"group": f"Informal, quintile {q}",
                     "mean_consumption_per_capita": e,
                     "affordable_contribution": e * config.AFFORDABILITY_THRESHOLD})
    out = pd.DataFrame(rows)
    target = out[out["group"].isin([f"Informal, quintile {q}" for q in quintiles])]
    out.attrs["target_contribution"] = float(target["affordable_contribution"].mean())
    return out


def take_up_probabilities(pred_cost, base_weights, strength, take_up):
    """Enrolment probability per person at a given take-up rate and tilt.

    q_i = min(1, k * tilt_i), with k chosen so the weighted mean of q_i equals
    the take-up rate. At 100% take-up everyone enrols and no selection is
    possible; at low take-up with a strong tilt the pool is the sick. Returns
    the enrolled distribution as probabilities over the individuals.
    """
    w = np.asarray(base_weights, float)
    if strength <= 1.0 or take_up >= 1.0:
        q = np.full(len(w), take_up)
    else:
        z = np.log(np.maximum(np.asarray(pred_cost, float), 1.0))
        z = (z - z.mean()) / z.std()
        tilt = np.exp(np.log(strength) * z)
        lo, hi = 0.0, 1e6
        for _ in range(100):
            k = (lo + hi) / 2
            q = np.minimum(1.0, k * tilt)
            if (w * q).sum() / w.sum() < take_up:
                lo = k
            else:
                hi = k
        q = np.minimum(1.0, (lo + hi) / 2 * tilt)
    p = w * q
    return p / p.sum()


def contribution_per_person(ind, hh, schedule, aff):
    """Contribution each informal-sector person would be billed under a schedule.

    flat    the Q1-Q3 affordable average for everyone (the headline design)
    graded  5% of the mean per-capita consumption of the person's own quintile
    exempt  nothing in the exempt quintiles, graded above them
    """
    by_q = aff.set_index("group")["affordable_contribution"]
    flat = aff.attrs["target_contribution"]
    q = ind["quintile"].astype(int)
    if schedule == "flat":
        return np.full(len(ind), flat)
    graded = q.map(lambda k: by_q[f"Informal, quintile {k}"]).to_numpy(float)
    if schedule == "graded":
        return graded
    if schedule == "exempt":
        return np.where(q.isin(config.EXEMPT_QUINTILES), 0.0, graded)
    raise ValueError(schedule)


def reinsured_support(values, probs, retention, loading=None):
    """Per-life excess-of-loss: the pool keeps min(X, R) and pays a loaded
    reinsurance premium equal to (1 + loading) * E[(X - R)+] per enrollee."""
    loading = config.REINSURANCE_LOADING if loading is None else loading
    values = np.asarray(values, float)
    ceded = float(np.sum(probs * np.maximum(values - retention, 0.0)))
    kept = np.minimum(values, retention)
    s = pd.Series(probs).groupby(kept).sum()
    return s.index.to_numpy(float), s.to_numpy(float) / s.sum(), ceded * (1 + loading)


def build_path_cache(pools, seed=config.SEED):
    """Pre-draw claim paths for every (pool size, take-up) combination."""
    max_years = max(config.RUIN_YEARS)
    cache = {}
    for i, (take_up, (v, p)) in enumerate(pools.items()):
        for n in config.POOL_SIZES:
            cache[(n, take_up)] = claims_paths(v, p, n, max_years,
                                               seed=seed + 1000 * i + n)
    return cache


def scenario_table(cache, contribution, gross_premium):
    """Ruin probability across pool size, take-up, subsidy, capital and horizon."""
    rows = []
    for (n, take_up), paths in cache.items():
        for years in config.RUIN_YEARS:
            sub_paths = paths[:, :years]
            for cap_mult in config.INITIAL_CAPITAL_MULT:
                for sub_frac in config.SUBSIDY_GRID:
                    subsidy = sub_frac * gross_premium
                    u0 = cap_mult * n * (contribution + subsidy)
                    r = ruin_from_paths(sub_paths, n, contribution, subsidy, u0)
                    rows.append({
                        "pool_size": n, "take_up": take_up, "years": years,
                        "initial_capital_mult": cap_mult,
                        "subsidy_fraction_of_premium": sub_frac,
                        "subsidy_per_enrollee": subsidy,
                        "member_contribution": contribution,
                        "initial_capital": u0, **r,
                    })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    ind = pd.read_csv(config.DERIVED / "ind_w5_priced.csv")
    hh = pd.read_csv(config.DERIVED / "hh_w5_che.csv")
    gross = pd.read_csv(config.TABLES / "table5c_gross_premium.csv")
    gross_premium = float(gross[(gross["pool_size"] == 20_000)
                                & (gross["risk_margin_basis"] == "Standard deviation")]
                          ["gross_premium_per_person"].iloc[0])

    # The pool insures informal-sector members.
    pool = ind[ind["informal"] == 1].copy()
    pools = {}
    for name, strength in [("Random", 1.0),
                           ("Moderate adverse selection", 1.5),
                           ("Strong adverse selection",
                            config.ADVERSE_SELECTION_STRENGTH)]:
        w = selection_probabilities(pool["pred_cost"], pool["ind_weight"], strength)
        pools[name] = cost_support(pool["insurer_cost"], w * len(pool))

    v_rand, p_rand = pools["Random"]
    mean_rand = float(v_rand @ p_rand)
    print("Expected claim per enrollee:")
    for name, (v, p) in pools.items():
        m = float(v @ p)
        print(f"  {name:28s} N{m:>10,.0f}  ({100 * (m / mean_rand - 1):+6.1f}%)")
    print(f"Support size: {len(v_rand):,} distinct annual cost values")

    check = verify_multinomial_shortcut(v_rand, p_rand)
    check.to_csv(config.TABLES / "tableA4_simulation_check.csv", index=False)
    print("\nSimulation shortcut check (5,000-life pool, 2,000 draws):")
    print(check.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))

    aff = affordable_contribution(hh)
    contribution = aff.attrs["target_contribution"]
    aff.to_csv(config.TABLES / "table6a_affordable_contribution.csv", index=False)
    print(f"\nAffordable member contribution (5% of consumption, informal Q1-Q3): "
          f"N{contribution:,.0f} vs gross premium N{gross_premium:,.0f}")

    print("\nDrawing claim paths ...")
    cache = build_path_cache(pools)

    print("Running the scenario grid ...")
    scen = scenario_table(cache, contribution, gross_premium)
    scen.to_csv(config.TABLES / "table6b_ruin_scenarios.csv", index=False)
    print(f"  {len(scen):,} scenarios evaluated")

    # Minimum subsidy for each target, by pool size, take-up and horizon.
    rows = []
    for (n, take_up), paths in cache.items():
        for years in config.RUIN_YEARS:
            sub_paths = paths[:, :years]
            for cap_mult in (0.0, 0.25):
                for target in config.RUIN_TARGETS:
                    u0 = cap_mult * n * (contribution + gross_premium)
                    s = minimum_subsidy_from_paths(sub_paths, n, contribution,
                                                   u0, target, gross_premium)
                    rows.append({
                        "pool_size": n, "take_up": take_up, "years": years,
                        "initial_capital_mult": cap_mult,
                        "ruin_target": target,
                        "min_subsidy_per_enrollee": s,
                        "min_subsidy_pct_of_gross_premium":
                            100 * s / gross_premium if np.isfinite(s) else np.nan,
                        "total_income_per_enrollee": contribution + s,
                        "annual_cost_per_100k_enrollees_naira_bn":
                            s * 100_000 / 1e9 if np.isfinite(s) else np.nan,
                    })
    mins = pd.DataFrame(rows).sort_values(
        ["pool_size", "take_up", "years", "initial_capital_mult", "ruin_target"])
    mins.to_csv(config.TABLES / "table6c_minimum_subsidy.csv", index=False)
    print("\nMinimum subsidy per enrollee (naira per year), no opening capital:")
    show = mins[mins["initial_capital_mult"] == 0.0].copy()
    show["ruin_target"] = show["ruin_target"].map(lambda t: f"{t:.0%}")
    print(show.drop(columns=["initial_capital_mult"]).to_string(
        index=False, float_format=lambda x: f"{x:,.1f}"))

    # Stress test: a one-off medical-inflation shock.
    stress = []
    for shock in (0.0, config.MEDICAL_INFLATION_SHOCK):
        for take_up in pools:
            paths = cache[(20_000, take_up)][:, :3]
            s = minimum_subsidy_from_paths(paths, 20_000, contribution, 0.0,
                                           0.05, gross_premium,
                                           inflation_shock=shock)
            stress.append({"medical_inflation_shock": shock, "take_up": take_up,
                           "pool_size": 20_000, "ruin_target": 0.05,
                           "min_subsidy_per_enrollee": s})
    stress = pd.DataFrame(stress)
    stress.to_csv(config.TABLES / "table6d_inflation_stress.csv", index=False)
    print("\nMedical-inflation stress (20,000 lives, 3 years, psi<5%):")
    st = stress.copy()
    st["medical_inflation_shock"] = st["medical_inflation_shock"].map(lambda x: f"{x:.0%}")
    st["ruin_target"] = st["ruin_target"].map(lambda x: f"{x:.0%}")
    print(st.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

    # ---- Contribution schedules: flat, graded, vulnerable group exempt ------
    rows = []
    for schedule in config.CONTRIBUTION_SCHEDULES:
        c_i = contribution_per_person(pool, hh, schedule, aff)
        for name, strength in [("Random", 1.0),
                               ("Strong adverse selection",
                                config.ADVERSE_SELECTION_STRENGTH)]:
            p_sel = selection_probabilities(pool["pred_cost"], pool["ind_weight"], strength)
            mean_c = float(np.sum(p_sel * c_i))
            v, pr = pools[name]
            paths = cache[(20_000, name)][:, :3]
            s_min = minimum_subsidy_from_paths(paths, 20_000, mean_c, 0.0, 0.05,
                                               gross_premium)
            rows.append({"schedule": schedule, "take_up": name,
                         "mean_contribution_per_enrollee": mean_c,
                         "expected_claim_per_enrollee": float(v @ pr),
                         "min_subsidy_per_enrollee": s_min,
                         "subsidy_share_of_cost":
                             s_min / (mean_c + s_min) if np.isfinite(s_min) else np.nan})
    sched = pd.DataFrame(rows)
    sched.to_csv(config.TABLES / "table6e_contribution_schedules.csv", index=False)
    print("\nContribution schedules (20,000 lives, 3 years, psi<5%):")
    print(sched.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

    # ---- Voluntary enrolment: selection loading against take-up -------------
    rows = []
    for strength, lab in [(1.5, "Moderate tilt"), (config.ADVERSE_SELECTION_STRENGTH, "Strong tilt")]:
        for take_up in config.TAKE_UP_GRID:
            p_enr = take_up_probabilities(pool["pred_cost"], pool["ind_weight"],
                                          strength, take_up)
            v, pr = cost_support(pool["insurer_cost"], p_enr * len(pool))
            m = float(v @ pr)
            paths = claims_paths(v, pr, 20_000, 3, n_sim=4_000,
                                 seed=config.SEED + int(100 * take_up))
            s_min = minimum_subsidy_from_paths(paths, 20_000, contribution, 0.0,
                                               0.05, gross_premium)
            rows.append({"tilt": lab, "tilt_strength": strength, "take_up": take_up,
                         "expected_claim_per_enrollee": m,
                         "selection_loading_pct": 100 * (m / mean_rand - 1),
                         "min_subsidy_per_enrollee": s_min,
                         "min_subsidy_pct_of_gross_premium": 100 * s_min / gross_premium})
    tk = pd.DataFrame(rows)
    tk.to_csv(config.TABLES / "table6f_take_up.csv", index=False)
    print("\nSelection loading by take-up rate (20,000 lives, 3 years, psi<5%):")
    print(tk.to_string(index=False, float_format=lambda x: f"{x:,.1f}"))

    # ---- Per-life excess-of-loss reinsurance --------------------------------
    rows = []
    for name in ["Random", "Strong adverse selection"]:
        v, pr = pools[name]
        for R in (np.inf,) + tuple(config.REINSURANCE_RETENTIONS):
            if np.isfinite(R):
                v_r, p_r, ri_prem = reinsured_support(v, pr, R)
            else:
                v_r, p_r, ri_prem = v, pr, 0.0
            paths = claims_paths(v_r, p_r, 20_000, 3, n_sim=4_000,
                                 seed=config.SEED + 7) + 20_000 * ri_prem
            s_min = minimum_subsidy_from_paths(paths, 20_000, contribution, 0.0,
                                               0.05, gross_premium)
            annual = paths[:, 0] / 20_000
            rows.append({"take_up": name,
                         "retention": R if np.isfinite(R) else np.nan,
                         "reinsurance_premium_per_enrollee": ri_prem,
                         "expected_retained_claim_per_enrollee": float(v_r @ p_r),
                         "sd_pool_claims_per_enrollee": float(annual.std()),
                         "p99_pool_claims_per_enrollee": float(np.quantile(annual, 0.99)),
                         "min_subsidy_per_enrollee": s_min})
    ri = pd.DataFrame(rows)
    ri.to_csv(config.TABLES / "table6g_reinsurance.csv", index=False)
    print("\nPer-life excess-of-loss reinsurance (20,000 lives):")
    print(ri.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

    return {"scenarios": scen, "minimum_subsidy": mins, "contribution": contribution,
            "gross_premium": gross_premium, "stress": stress,
            "expected_claims": {k: float(v @ p) for k, (v, p) in pools.items()}}


if __name__ == "__main__":
    main()
