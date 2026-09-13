"""
Check that the manuscript's headline numbers still match the analysis output.

The prose is written by hand, so a rerun that moves an estimate leaves the text
stale unless someone notices. This reads the current tables, formats each
headline figure the way the manuscript writes it, and fails if the string is
absent from the text. It is a spelling check against the data, not a proof that
every sentence is right - but it catches the failure that actually happens.

Run after run_all.py and before make_manuscript.py.
"""

from __future__ import annotations

import re
import sys

import pandas as pd

import config

MS = config.ROOT / "manuscript" / "Paper2_manuscript.md"
T = config.TABLES


def load():
    t2 = pd.read_csv(T / "table2_che.csv")
    ov = t2[t2["dimension"] == "Overall"].set_index("measure")
    cov = pd.read_csv(T / "table1b_coverage.csv")
    covo = cov[cov["dimension"] == "Overall"].iloc[0]
    covs = cov[cov["dimension"] == "Sector"].set_index("group")
    imp = pd.read_csv(T / "table2b_impoverishment.csv").set_index("indicator")["estimate"]
    con = pd.read_csv(T / "table3_concentration.csv").set_index("outcome")
    gap = pd.read_csv(T / "table2c_sector_gaps.csv").set_index("outcome")
    b = pd.read_csv(T / "table5a_premium_buildup.csv")
    g = pd.read_csv(T / "table5c_gross_premium.csv")
    g = g[(g["pool_size"] == 20_000)
          & (g["risk_margin_basis"] == "Standard deviation")].iloc[0]
    aff = pd.read_csv(T / "table5d_affordability.csv").set_index("quintile")
    sub = pd.read_csv(T / "table6c_minimum_subsidy.csv")
    sub = sub[(sub["pool_size"] == 20_000) & (sub["years"] == 3)
              & (sub["initial_capital_mult"] == 0.0)].set_index(
                  ["take_up", "ruin_target"])

    def naira(x):
        return f"₦{x:,.0f}"

    checks = {
        "CHE 10% incidence": f'{ov.loc["Budget share > 10%", "incidence_pct"]:.1f}%',
        "CHE 10% CI low": f'{ov.loc["Budget share > 10%", "ci_low"]:.1f}',
        "CTP 40% incidence": f'{ov.loc["Capacity to pay >= 40%", "incidence_pct"]:.1f}%',
        "coverage, households": f'{covo["hh_with_cover_pct"]:.2f}%',
        "coverage, individuals": f'{covo["individuals_covered_pct"]:.2f}%',
        "coverage, informal": f'{covs.loc["Informal", "hh_with_cover_pct"]:.2f}%',
        "coverage, formal": f'{covs.loc["Formal", "hh_with_cover_pct"]:.2f}%',
        "poverty before": f'{imp["Poverty headcount before OOP (%)"]:.1f}%',
        "poverty after": f'{imp["Poverty headcount after OOP (%)"]:.1f}%',
        "concentration, budget share":
            f'+{con.loc["CHE, budget share > 10%", "CI"]:.3f}',
        "concentration, CTP":
            f'{con.loc["CHE, capacity to pay >= 40%", "CI"]:.3f}',
        "sector gap, CTP informal":
            f'{gap.loc["CHE, CTP >= 40%", "informal"]:.1f}%',
        "pure premium": naira(b["naira_per_person_year"].iloc[-1]),
        "gross premium": naira(g["gross_premium_per_person"]),
        "Q1 premium share":
            f'{aff.loc["Q1 (poorest)", "premium_pct_of_per_capita_consumption"]:.1f}%',
        "Q1 household premium": naira(aff.loc["Q1 (poorest)", "premium_per_household"]),
        "subsidy, random, 5%":
            naira(sub.loc[("Random", 0.05), "min_subsidy_per_enrollee"]),
        "subsidy, random, 1%":
            naira(sub.loc[("Random", 0.01), "min_subsidy_per_enrollee"]),
        "subsidy, strong, 5%":
            naira(sub.loc[("Strong adverse selection", 0.05),
                          "min_subsidy_per_enrollee"]),
    }
    return checks



def cross_reference():
    """Every table cited in the prose is rendered, and vice versa.

    Paper 2 shipped a draft citing twelve tables that make_tables.py never
    rendered, so a reader of the submitted document was pointed at tables that
    were not in it. This makes that failure impossible to repeat.
    """
    ms = list((config.ROOT / "manuscript").glob("Paper?_manuscript.md"))[0]
    tb = config.ROOT / "manuscript" / "tables.md"
    if not tb.exists():
        print("  tables.md not built yet; skipping the cross-reference check")
        return []
    rendered = set(re.findall(r"\*\*Table ([0-9A-Za-z]+)\.\*\*", tb.read_text()))
    cited = set()
    for m in re.finditer(r"Tables? ([0-9]+[a-f]?|A[0-9]+)"
                         r"(?:\s+and\s+([0-9]+[a-f]?|A[0-9]+))?", ms.read_text()):
        cited.add(m.group(1))
        if m.group(2):
            cited.add(m.group(2))
    problems = []
    for t in sorted(cited - rendered):
        problems.append(f"Table {t} is cited in the prose but not rendered")
    for t in sorted(rendered - cited):
        problems.append(f"Table {t} is rendered but never cited")
    print(f"  {len(rendered)} tables rendered, {len(cited)} cited"
          + ("" if not problems else f"  <-- {len(problems)} mismatch(es)"))
    for p_ in problems:
        print(f"      {p_}")
    return problems


def main():
    text = MS.read_text()
    # The manuscript writes minus as U+2212; normalise so both forms match.
    haystack = text.replace("−", "-")
    checks = load()

    bad = []
    for label, value in checks.items():
        needle = value.replace("−", "-")
        if needle not in haystack:
            bad.append((label, value))

    width = max(len(k) for k in checks)
    for label, value in checks.items():
        ok = (label, value) not in bad
        print(f"  {'ok ' if ok else 'MISSING'}  {label:<{width}}  {value}")

    xref = cross_reference()
    if bad or xref:
        if bad:
            print(f"\n{len(bad)} headline figure(s) do not appear in "
                  f"{MS.name}. Update the prose, then rebuild.")
        if xref:
            print(f"{len(xref)} table cross-reference problem(s).")
        sys.exit(1)
    print(f"\nAll {len(checks)} headline figures match the current tables.")


if __name__ == "__main__":
    main()
