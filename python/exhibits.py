"""
The six figures, in a plain journal style.

The figures carry no "Figure N" label of their own: the manuscript numbers them
in reading order, which is not the order they are generated in, and a number
baked into the artwork would contradict its caption.

Everything is drawn from the CSVs the analysis scripts wrote, so a figure can
never disagree with the table it belongs to.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    "axes.axisbelow": True, "figure.dpi": 110,
    "legend.frameon": False, "axes.titlesize": 10, "axes.titleweight": "bold",
})
P = config.PALETTE


def _save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(config.FIGURES / f"{name}.{ext}", dpi=config.FIG_DPI,
                    bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}.png / .pdf")


# ---------------------------------------------------------------------------
def figure1_che_by_quintile():
    """CHE incidence by consumption quintile at three thresholds."""
    t2 = pd.read_csv(config.TABLES / "table2_che.csv")
    d = t2[t2["dimension"] == "Consumption quintile"]
    measures = ["Budget share > 10%", "Budget share > 25%",
                "Capacity to pay >= 40%"]
    colours = [P["primary"], P["accent"], P["secondary"]]
    order = ["Q1 (poorest)", "Q2", "Q3", "Q4", "Q5 (richest)"]

    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    width = 0.26
    x = np.arange(len(order))
    for k, (m, c) in enumerate(zip(measures, colours)):
        s = d[d["measure"] == m].set_index("group").reindex(order)
        err = [s["incidence_pct"] - s["ci_low"], s["ci_high"] - s["incidence_pct"]]
        ax.bar(x + (k - 1) * width, s["incidence_pct"], width, label=m,
               color=c, edgecolor="white", linewidth=0.5)
        ax.errorbar(x + (k - 1) * width, s["incidence_pct"], yerr=err, fmt="none",
                    ecolor="#444444", elinewidth=0.8, capsize=2)
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_ylabel("Households affected (%)")
    ax.set_title("Catastrophic health expenditure by consumption quintile")
    ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.13))
    _save(fig, "figure1_che_by_quintile")


def figure2_ruin():
    """Ruin probability against subsidy, by pool size and take-up."""
    s = pd.read_csv(config.TABLES / "table6b_ruin_scenarios.csv")
    s = s[(s["years"] == 3) & (s["initial_capital_mult"] == 0.0)]
    take_ups = ["Random", "Moderate adverse selection", "Strong adverse selection"]
    take_ups = [t for t in take_ups if t in set(s["take_up"])]
    colours = {5_000: P["secondary"], 20_000: P["primary"], 100_000: P["green"]}

    fig, axes = plt.subplots(1, len(take_ups), figsize=(9.6, 3.4), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, t in zip(axes, take_ups):
        sub = s[s["take_up"] == t]
        for n, grp in sub.groupby("pool_size"):
            grp = grp.sort_values("subsidy_per_enrollee")
            ax.plot(grp["subsidy_per_enrollee"] / 1000, 100 * grp["psi"],
                    color=colours.get(n, P["muted"]), linewidth=1.6,
                    label=f"{n:,} lives")
        for target, style in [(1, ":"), (5, "--")]:
            ax.axhline(target, color=P["muted"], linestyle=style, linewidth=0.8)
            ax.text(ax.get_xlim()[1], target, f" {target}%", va="center",
                    fontsize=7, color=P["muted"])
        ax.set_title(t, fontsize=9, fontweight="normal")
        ax.set_xlabel("Subsidy per enrollee (N '000/year)")
    axes[0].set_ylabel("Probability of ruin over 3 years (%)")
    axes[0].legend(loc="upper right")
    fig.suptitle("Pool solvency against subsidy, by take-up and pool size",
                 fontsize=10, fontweight="bold", y=1.03)
    _save(fig, "figure4_ruin_vs_subsidy")


def figure3_counterfactual():
    """Baseline vs counterfactual CHE by quintile."""
    q = pd.read_csv(config.TABLES / "table7c_by_quintile.csv")
    q = q[q["measure"] == "CHE > 10%"]
    aff = pd.read_csv(config.TABLES / "table6a_affordable_contribution.csv")
    flat = aff[aff["group"].isin([f"Informal, quintile {q}" for q in (1, 2, 3)])]
    flat = float(flat["affordable_contribution"].mean())
    keep = ["Baseline (no coverage)",
            "Informal sector, full coverage",
            "Informal sector, full coverage, Q1-Q2 exempt",
            "Informal sector, full coverage, no contribution"]
    labels = {"Baseline (no coverage)": "No coverage",
              "Informal sector, full coverage": f"Flat contribution N{flat:,.0f}",
              "Informal sector, full coverage, Q1-Q2 exempt": "Q1-Q2 exempt, Q3-Q5 graded",
              "Informal sector, full coverage, no contribution": "Fully subsidized"}
    colours = [P["muted"], P["orange"], P["accent"], P["primary"]]
    order = ["Q1 (poorest)", "Q2", "Q3", "Q4", "Q5 (richest)"]

    fig, ax = plt.subplots(figsize=(7.0, 3.7))
    width = 0.2
    x = np.arange(len(order))
    for k, (scen, c) in enumerate(zip(keep, colours)):
        s = q[q["scenario"] == scen].set_index("group").reindex(order)
        err = [s["estimate_pct"] - s["ci_low_pct"], s["ci_high_pct"] - s["estimate_pct"]]
        ax.bar(x + (k - 1.5) * width, s["estimate_pct"], width, label=labels[scen],
               color=c, edgecolor="white", linewidth=0.5)
        ax.errorbar(x + (k - 1.5) * width, s["estimate_pct"], yerr=err, fmt="none",
                    ecolor="#444444", elinewidth=0.8, capsize=2)
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_ylabel("Share above the 10% threshold (%)")
    ax.set_title("Catastrophic spending under coverage scenarios, "
                 "out-of-pocket plus contribution")
    ax.legend(loc="upper center", ncol=4, bbox_to_anchor=(0.5, -0.13), fontsize=7.5)
    _save(fig, "figure6_counterfactual")


def figure6_take_up():
    """Selection loading and required subsidy against the take-up rate."""
    tk = pd.read_csv(config.TABLES / "table6f_take_up.csv")
    colours = {"Moderate tilt": P["accent"], "Strong tilt": P["secondary"]}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 3.4))
    for tilt, grp in tk.groupby("tilt"):
        grp = grp.sort_values("take_up")
        ax1.plot(100 * grp["take_up"], grp["selection_loading_pct"], "o-",
                 color=colours[tilt], linewidth=1.6, markersize=4, label=tilt)
        ax2.plot(100 * grp["take_up"], grp["min_subsidy_per_enrollee"] / 1000, "o-",
                 color=colours[tilt], linewidth=1.6, markersize=4, label=tilt)
    ax1.set_xlabel("Take-up among informal-sector members (%)")
    ax1.set_ylabel("Expected claim above the community mean (%)")
    ax1.set_title("Selection loading", fontsize=9, fontweight="normal")
    ax1.legend(fontsize=8)
    ax2.set_xlabel("Take-up among informal-sector members (%)")
    ax2.set_ylabel("Subsidy per enrollee (N '000/year)")
    ax2.set_title("Minimum subsidy, 20,000 lives, ruin below 5%", fontsize=9,
                  fontweight="normal")
    ax2.legend(fontsize=8)
    fig.suptitle("Voluntary enrollment: what take-up does to the subsidy",
                 fontsize=10, fontweight="bold", y=1.02)
    _save(fig, "figure5_take_up")


def figure6_concentration_curves():
    """Concentration curves for the two catastrophic-expenditure definitions.

    This is the paper's central measurement finding and the one result that a
    table of indices states but does not show: the budget-share curve sits on
    the diagonal, the capacity-to-pay curve bows well above it. The curve
    points are written to a CSV so the figure stays reproducible from a table
    like every other exhibit here.
    """
    hh = pd.read_csv(config.DERIVED / "hh_main_che.csv")
    hh = hh.sort_values("cons_pc")
    w = hh["popwt"].to_numpy(float)
    # Weighted fractional rank in per-capita consumption: the midpoint of each
    # household's own weight band, which is the standard convention.
    cw = np.cumsum(w)
    rank = (cw - 0.5 * w) / w.sum()

    curves = {
        "Budget share > 10%": hh["che10"].to_numpy(float),
        "Capacity to pay >= 40%": hh["che_ctp40"].to_numpy(float),
    }
    rows, fig, ax = [], *plt.subplots(figsize=(4.6, 4.4))
    ax.plot([0, 1], [0, 1], color=P["muted"], linewidth=1.0, linestyle=":",
            label="Line of equality")
    for (name, y), colour in zip(curves.items(), [P["primary"], P["secondary"]]):
        share = np.cumsum(w * y) / (w * y).sum()
        xs = np.concatenate([[0.0], rank])
        ys = np.concatenate([[0.0], share])
        ax.plot(xs, ys, color=colour, linewidth=1.8, label=name)
        # thin the stored curve to a 201-point grid; the plot uses the full set
        grid = np.linspace(0, 1, 201)
        rows.append(pd.DataFrame({"measure": name, "cum_pop_share": grid,
                                  "cum_che_share": np.interp(grid, xs, ys)}))
    pd.concat(rows).to_csv(config.TABLES / "table3c_concentration_curve.csv",
                           index=False)

    ax.set_xlabel("Cumulative share of population,\npoorest to richest")
    ax.set_ylabel("Cumulative share of affected households")
    ax.set_title("Who bears catastrophic\nhealth expenditure")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.legend(loc="upper left", fontsize=8)
    ax.annotate("above the diagonal\n= concentrated among the poor",
                xy=(0.42, 0.60), xytext=(0.30, 0.19), fontsize=7.5,
                color=P["secondary"], ha="left",
                arrowprops=dict(arrowstyle="->", color=P["secondary"],
                                linewidth=0.8))
    _save(fig, "figure2_concentration_curves")


def figure7_premium_waterfall():
    """Premium build-up from observed spending to the gross premium."""
    b = pd.read_csv(config.TABLES / "table5a_premium_buildup.csv")
    g = pd.read_csv(config.TABLES / "table5c_gross_premium.csv")
    g = g[(g["pool_size"] == 20_000) &
          (g["risk_margin_basis"] == "Standard deviation")].iloc[0]

    labels = ["Observed\nOOP cost", "less\ntraditional", "less outside\npackage",
              "plus induced\ndemand", "less drug\nco-payment", "Pure\npremium",
              "plus risk\nmargin", "plus admin\n15%",
              "plus adverse\nselection 10%", "Gross\npremium"]
    start = b["naira_per_person_year"].iloc[0]
    deltas = list(b["change"].iloc[1:]) + [
        None, g["risk_margin"], g["admin_load"], g["adverse_selection_load"], None]

    fig, ax = plt.subplots(figsize=(9.0, 4.0))
    running = start
    for i, lab in enumerate(labels):
        if i == 0 or lab.startswith(("Pure", "Gross")):
            total = start if i == 0 else (
                b["naira_per_person_year"].iloc[-1] if lab.startswith("Pure")
                else g["gross_premium_per_person"])
            ax.bar(i, total / 1000, 0.62, color=P["primary"],
                   edgecolor="white", linewidth=0.5)
            ax.text(i, total / 1000 + 0.9, f"{total:,.0f}", ha="center",
                    fontsize=8, fontweight="bold")
            running = total
        else:
            d = deltas[i - 1]
            bottom = running if d > 0 else running + d
            colour = P["green"] if d > 0 else P["orange"]
            # A bar under about N200 is thinner than its own edge line, so mark
            # it with a rule instead of a rectangle - the risk margin at scale
            # really is that small, and the figure should show that honestly.
            if abs(d) / 1000 < 0.25:
                ax.plot([i - 0.31, i + 0.31], [running / 1000] * 2,
                        color=colour, linewidth=2.4, solid_capstyle="butt")
            else:
                ax.bar(i, abs(d) / 1000, 0.62, bottom=bottom / 1000,
                       color=colour, edgecolor="white", linewidth=0.5)
            ax.text(i, (bottom + abs(d)) / 1000 + 0.9, f"{d:+,.0f}",
                    ha="center", fontsize=7.5, color=colour)
            running += d
        if i < len(labels) - 1:
            ax.plot([i + 0.31, i + 0.69], [running / 1000] * 2,
                    color=P["muted"], linewidth=0.6, linestyle="--")

    aff = pd.read_csv(config.TABLES / "table6a_affordable_contribution.csv")
    flat = aff[aff["group"].isin([f"Informal, quintile {q}" for q in (1, 2, 3)])]
    flat = float(flat["affordable_contribution"].mean())
    ax.axhline(flat / 1000, color=P["secondary"], linewidth=1.2)
    ax.text(0.05, flat / 1000 + 0.5, "contribution ceiling for the target "
            f"population, N{flat:,.0f} per person per year",
            fontsize=7.5, color=P["secondary"], va="bottom")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.tick_params(axis="x", length=0, pad=3)
    ax.set_ylabel("Naira per person per year ('000)")
    ax.set_title("From observed spending to the gross premium "
                 "(20,000-life pool)")
    ax.set_xlim(-0.6, len(labels) - 0.4)
    ax.set_ylim(0, 33)
    _save(fig, "figure3_premium_waterfall")


# ---------------------------------------------------------------------------
def main():
    print("Drawing figures ...")
    for old in ("figure4_affordability", "figure5_model_fit", "figure5_counterfactual",
                "figure6_take_up",
                "figure6_concentration_curves", "figure7_premium_waterfall",
                "figure2_ruin_vs_subsidy", "figure3_counterfactual"):
        for ext in ("png", "pdf"):
            (config.FIGURES / f"{old}.{ext}").unlink(missing_ok=True)
    figure1_che_by_quintile()
    figure6_concentration_curves()
    figure7_premium_waterfall()
    figure2_ruin()
    figure3_counterfactual()
    figure6_take_up()


if __name__ == "__main__":
    main()
