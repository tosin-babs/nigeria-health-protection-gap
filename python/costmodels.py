"""
RQ2, part one - frequency, severity and aggregate cost models.

Three models of the same underlying process, fitted so they can be compared:

  frequency  Poisson / negative binomial on the count of care episodes, with an
             offset for the length of the recall window, so coefficients are
             annual rates.
  severity   gamma / lognormal on cost per episode, among episodes that happened.
  aggregate  Tweedie compound Poisson-gamma on annual cost per person, which
             handles the point mass at zero and the right skew in one model and
             is what the pricing step actually uses.

Point estimates are survey-weighted. Standard errors are clustered on the
enumeration area, which is the primary sampling unit; that is the practical
equivalent of the design-based linearisation used elsewhere in the paper and is
what the survey-weighted GLM literature recommends when the model, rather than
a population mean, is the object of interest.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

import config

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

RHS = ("C(age_band, Treatment(reference='25-44')) + female + C(zone) + urban "
       "+ C(quintile) + chronic + hhsize")


def prepare(ind):
    """Model frame: drop rows that cannot contribute and set up weights."""
    d = ind.copy()
    d = d[d["age"].notna() & d["age_band"].notna()].copy()
    d["female"] = d["female"].fillna(0.0)
    d["chronic"] = d["chronic"].fillna(0).astype(float)
    d["quintile"] = d["quintile"].astype(int)
    d["urban"] = d["urban"].astype(float)
    # Rescale weights to average one so that statsmodels' frequency-weight
    # machinery does not inflate the apparent sample size.
    d["w"] = d["ind_weight"] / d["ind_weight"].mean()
    d["log_exposure_op"] = np.log(d["exposure_op"])
    d["cluster_id"] = d["cluster"].astype(str)
    return d


def _fit(formula, data, family, offset=None):
    m = smf.glm(formula, data=data, family=family, freq_weights=data["w"],
                offset=offset)
    return m.fit(cov_type="cluster", cov_kwds={"groups": data["cluster_id"]})


def tidy(res, model_name, extra=None):
    out = pd.DataFrame({
        "model": model_name,
        "term": res.params.index,
        "coef": res.params.values,
        "se": res.bse.values,
        "z": res.tvalues.values,
        "p": res.pvalues.values,
    })
    out["exp_coef"] = np.exp(out["coef"])
    out["ci_low"] = np.exp(out["coef"] - 1.96 * out["se"])
    out["ci_high"] = np.exp(out["coef"] + 1.96 * out["se"])
    if extra:
        for k, v in extra.items():
            out[k] = v
    return out


# ---------------------------------------------------------------------------
# Frequency
# ---------------------------------------------------------------------------
def fit_frequency(d):
    """Annual rate of outpatient contacts and of inpatient episodes.

    The survey records whether a person had contact with a provider inside a
    four-week window, not how many times. Modelling that indicator as a count
    with an offset of log(4/52) turns the fitted values into annual rates, at
    the cost of assuming contacts are not bunched within the year - an
    assumption the robustness table relaxes by rescaling the annualiser.
    """
    res = {}
    pois = _fit(f"sought_care ~ {RHS}", d, sm.families.Poisson(),
                offset=d["log_exposure_op"])
    res["outpatient_poisson"] = pois

    # Overdispersion: regress the squared Pearson residual on the fitted mean.
    mu = pois.fittedvalues
    pearson = (d["sought_care"] - mu) / np.sqrt(mu)
    aux = sm.OLS((pearson**2 - 1) * np.sqrt(2), mu / np.sqrt(2)).fit()
    res["overdispersion_t"] = float(aux.tvalues.iloc[0])
    res["overdispersion_p"] = float(aux.pvalues.iloc[0])
    res["pearson_dispersion"] = float((pearson**2).sum() / pois.df_resid)

    try:
        nb = _fit(f"sought_care ~ {RHS}", d,
                  sm.families.NegativeBinomial(alpha=1.0),
                  offset=d["log_exposure_op"])
        res["outpatient_nb"] = nb
    except Exception:
        res["outpatient_nb"] = None

    ip = _fit(f"inpatient ~ {RHS}", d, sm.families.Poisson())
    res["inpatient_poisson"] = ip
    return res


# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------
def fit_severity(d):
    """Cost per episode, among people who had one."""
    res = {}
    op = d[(d["sought_care"] == 1) & (d["op_cost_window"] > 0)].copy()
    res["n_outpatient"] = len(op)
    res["gamma_outpatient"] = _fit(
        f"op_cost_window ~ {RHS}", op,
        sm.families.Gamma(link=sm.families.links.Log()))
    op["log_cost"] = np.log(op["op_cost_window"])
    res["lognormal_outpatient"] = _fit(f"log_cost ~ {RHS}", op,
                                       sm.families.Gaussian())
    res["lognormal_sigma2_op"] = float(
        np.average((op["log_cost"] - res["lognormal_outpatient"].fittedvalues) ** 2,
                   weights=op["w"]))

    ip = d[(d["inpatient"] == 1) & (d["ip_cost_year"] > 0)].copy()
    res["n_inpatient"] = len(ip)
    if len(ip) > 60:
        # The inpatient sample is small, so the severity model is deliberately
        # leaner than the outpatient one to avoid fitting noise.
        lean = "C(age_band, Treatment(reference='25-44')) + female + urban + C(quintile)"
        res["gamma_inpatient"] = _fit(f"ip_cost_year ~ {lean}", ip,
                                      sm.families.Gamma(link=sm.families.links.Log()))
        ip["log_cost"] = np.log(ip["ip_cost_year"])
        res["lognormal_inpatient"] = _fit(f"log_cost ~ {lean}", ip,
                                          sm.families.Gaussian())
        res["lognormal_sigma2_ip"] = float(
            np.average((ip["log_cost"] - res["lognormal_inpatient"].fittedvalues) ** 2,
                       weights=ip["w"]))
    else:
        res["gamma_inpatient"] = res["lognormal_inpatient"] = None

    # Which severity distribution fits better, on the same scale.
    g = res["gamma_outpatient"]
    ll_gamma = float(g.llf)
    n = len(op)
    ll_lognorm = float(-0.5 * n * (np.log(2 * np.pi * res["lognormal_sigma2_op"]) + 1)
                       - op["log_cost"].sum())
    res["aic_gamma_op"] = 2 * len(g.params) - 2 * ll_gamma
    res["aic_lognormal_op"] = 2 * (len(res["lognormal_outpatient"].params) + 1) - 2 * ll_lognorm
    return res


# ---------------------------------------------------------------------------
# Tweedie
# ---------------------------------------------------------------------------
def tweedie_profile(d, p_grid=None, formula=None):
    """Profile the Tweedie variance power p over a grid, as tweedie.profile does."""
    if p_grid is None:
        p_grid = np.round(np.arange(1.20, 1.86, 0.05), 2)
    formula = formula or f"cost_annual ~ {RHS}"
    rows = []
    for p in p_grid:
        try:
            fam = sm.families.Tweedie(link=sm.families.links.Log(),
                                      var_power=float(p), eql=False)
            m = smf.glm(formula, data=d, family=fam, freq_weights=d["w"]).fit()
            rows.append({"p": float(p), "loglik": float(m.llf),
                         "deviance": float(m.deviance), "converged": True})
        except Exception as exc:  # a grid point can fail to converge
            rows.append({"p": float(p), "loglik": np.nan, "deviance": np.nan,
                         "converged": False, "error": str(exc)[:60]})
    prof = pd.DataFrame(rows)
    if prof["loglik"].notna().any():
        p_hat = float(prof.loc[prof["loglik"].idxmax(), "p"])
    else:
        p_hat = 1.5
        prof["note"] = "profile failed; p fixed at 1.5"
    return prof, p_hat


def fit_tweedie(d, p, formula=None):
    formula = formula or f"cost_annual ~ {RHS}"
    fam = sm.families.Tweedie(link=sm.families.links.Log(), var_power=float(p),
                              eql=False)
    return _fit(formula, d, fam)


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
def lift_table(d, fitted, n_bins=10):
    """Observed vs predicted annual cost by decile of prediction."""
    q = pd.qcut(fitted.rank(method="first"), n_bins, labels=False) + 1
    t = pd.DataFrame({"decile": q, "pred": fitted, "obs": d["cost_annual"],
                      "w": d["w"]})
    g = t.groupby("decile").apply(
        lambda x: pd.Series({
            "n": len(x),
            "predicted_mean": np.average(x["pred"], weights=x["w"]),
            "observed_mean": np.average(x["obs"], weights=x["w"]),
            "observed_zero_pct": 100 * np.average(x["obs"] == 0, weights=x["w"]),
        }), include_groups=False)
    g["ratio_obs_pred"] = g["observed_mean"] / g["predicted_mean"]
    total_obs = np.average(t["obs"], weights=t["w"])
    g["lift"] = g["observed_mean"] / total_obs
    return g.reset_index()


def quantile_residuals(d, res, p):
    """Randomised quantile residuals for the Tweedie fit (Dunn & Smyth 1996).

    Under a correct model these are standard normal, so a Shapiro-Wilk style
    check and the extreme quantiles are informative about tail fit.
    """
    from scipy.stats import norm
    mu = np.asarray(res.fittedvalues, float)
    phi = float(res.scale)
    y = d["cost_annual"].to_numpy(float)
    lam = mu ** (2 - p) / (phi * (2 - p))          # Poisson rate
    alpha = (2 - p) / (p - 1)                       # gamma shape per claim
    beta = phi * (p - 1) * mu ** (p - 1)            # gamma scale

    rng = np.random.default_rng(config.SEED)
    p0 = np.exp(-lam)
    u = np.empty_like(y)
    zero = y <= 0
    u[zero] = rng.uniform(0, p0[zero])
    pos = ~zero
    if pos.any():
        # Sum over the number of claims: P(Y<=y) = sum_n Pois(n) * Gamma(y; n*alpha, beta)
        cdf = np.zeros(pos.sum())
        yy, ll, aa, bb = y[pos], lam[pos], alpha, beta[pos]
        for n in range(1, 80):
            wgt = stats.poisson.pmf(n, ll)
            if np.all(wgt < 1e-12) and n > 5:
                break
            cdf += wgt * stats.gamma.cdf(yy, a=n * aa, scale=bb)
        u[pos] = np.clip(p0[pos] + cdf, 1e-10, 1 - 1e-10)
    return norm.ppf(np.clip(u, 1e-10, 1 - 1e-10))


# ---------------------------------------------------------------------------
def main():
    ind = pd.read_csv(config.DERIVED / "ind_w5.csv")
    d = prepare(ind)
    print(f"Model frame: {len(d):,} individuals, "
          f"{d['sought_care'].mean():.1%} with outpatient contact in 4 weeks, "
          f"{d['inpatient'].mean():.1%} hospitalised in 12 months")

    freq = fit_frequency(d)
    sev = fit_severity(d)

    print("\nFrequency (outpatient, annual rate):")
    print(f"  Pearson dispersion {freq['pearson_dispersion']:.3f}; "
          f"overdispersion test t={freq['overdispersion_t']:.2f} "
          f"(p={freq['overdispersion_p']:.3f})")
    print(f"Severity: {sev['n_outpatient']:,} outpatient episodes, "
          f"{sev['n_inpatient']:,} inpatient episodes")
    print(f"  AIC gamma {sev['aic_gamma_op']:,.0f} vs lognormal "
          f"{sev['aic_lognormal_op']:,.0f}")

    print("\nProfiling the Tweedie variance power ...")
    prof, p_hat = tweedie_profile(d)
    prof.to_csv(config.TABLES / "tableA2_tweedie_profile.csv", index=False)
    print(f"  p-hat = {p_hat:.2f}")

    tw = fit_tweedie(d, p_hat)
    d["pred_cost"] = tw.fittedvalues

    lift = lift_table(d, tw.fittedvalues)
    lift.to_csv(config.TABLES / "tableA3_lift.csv", index=False)
    print("\nObserved vs predicted annual cost by decile of prediction:")
    print(lift.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

    qr = quantile_residuals(d, tw, p_hat)
    print(f"\nRandomised quantile residuals: mean {qr.mean():.3f}, "
          f"sd {qr.std():.3f}, skew {stats.skew(qr):.3f}, "
          f"KS p-value {stats.kstest(qr, 'norm').pvalue:.3f}")

    # Table 4
    parts = [
        tidy(freq["outpatient_poisson"], "Frequency: outpatient (Poisson, annual rate)"),
        tidy(freq["inpatient_poisson"], "Frequency: inpatient (Poisson, annual rate)"),
        tidy(sev["gamma_outpatient"], "Severity: cost per outpatient episode (gamma)"),
    ]
    if sev["gamma_inpatient"] is not None:
        parts.append(tidy(sev["gamma_inpatient"],
                          "Severity: cost per inpatient episode (gamma)"))
    parts.append(tidy(tw, f"Aggregate annual cost (Tweedie, p={p_hat:.2f})"))
    table4 = pd.concat(parts, ignore_index=True)
    table4.to_csv(config.TABLES / "table4_cost_models.csv", index=False)

    fit_stats = pd.DataFrame([
        {"statistic": "Outpatient contact rate per person-year (weighted)",
         "value": float(np.average(d["sought_care"], weights=d["w"]) * config.OUTPATIENT_ANNUALISER)},
        {"statistic": "Inpatient episodes per person-year (weighted)",
         "value": float(np.average(d["inpatient"], weights=d["w"]))},
        {"statistic": "Mean cost per outpatient episode (N)",
         "value": float(np.average(d.loc[d["op_cost_window"] > 0, "op_cost_window"],
                                   weights=d.loc[d["op_cost_window"] > 0, "w"]))},
        {"statistic": "Mean cost per inpatient episode (N)",
         "value": float(np.average(d.loc[d["ip_cost_year"] > 0, "ip_cost_year"],
                                   weights=d.loc[d["ip_cost_year"] > 0, "w"]))},
        {"statistic": "Mean annual cost per person (N)",
         "value": float(np.average(d["cost_annual"], weights=d["w"]))},
        {"statistic": "Tweedie variance power p", "value": p_hat},
        {"statistic": "Tweedie dispersion phi", "value": float(tw.scale)},
        {"statistic": "Pearson dispersion, frequency model",
         "value": freq["pearson_dispersion"]},
        {"statistic": "AIC gamma severity", "value": sev["aic_gamma_op"]},
        {"statistic": "AIC lognormal severity", "value": sev["aic_lognormal_op"]},
        {"statistic": "Quantile-residual KS p-value",
         "value": float(stats.kstest(qr, "norm").pvalue)},
    ])
    fit_stats.to_csv(config.TABLES / "table4b_fit_statistics.csv", index=False)
    print("\n" + fit_stats.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))

    d[["hhid", "indiv", "age", "age_band", "female", "urban", "zone", "quintile",
       "chronic", "informal", "ind_weight", "cluster", "strata", "cost_annual",
       "op_cost_annual", "ip_cost_annual", "op_drug_annual", "sought_care",
       "inpatient", "pred_cost"]].to_csv(
        config.DERIVED / "ind_w5_scored.csv", index=False)

    return {"data": d, "freq": freq, "sev": sev, "tweedie": tw, "p": p_hat,
            "profile": prof, "lift": lift}


if __name__ == "__main__":
    main()
