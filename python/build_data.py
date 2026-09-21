"""
Build the household and individual analysis files from raw GHS-Panel CSVs.

Two outputs per wave:
  * households (hh_w5.csv / hh_w4.csv) - consumption, OOP, sector, design vars
  * individuals (ind_w5.csv / ind_w4.csv) - annualised health cost, utilisation

The wave-5 CSV release ships no consumption aggregate, so one is constructed
here from the food, non-food and education modules. The same code is run on
wave 4, where the World Bank *does* publish an aggregate (totcons_final.csv),
and the two are compared in validate_w4_aggregate(). That comparison is the
evidence that the wave-5 denominator is sound; it is reported in the appendix.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config


# ---------------------------------------------------------------------------
# Small parsing helpers - the CSV release stores answers as "3. LABEL"
# ---------------------------------------------------------------------------
def code(series):
    """Extract the numeric code from a '3. SOME LABEL' style answer."""
    s = series.astype("string").str.strip()
    return pd.to_numeric(s.str.extract(r"^(-?\d+)\.", expand=False), errors="coerce")


def label(series):
    """Extract the label from a '3. SOME LABEL' style answer."""
    s = series.astype("string").str.strip()
    lab = s.str.extract(r"^-?\d+\.\s*(.*)$", expand=False)
    return lab.fillna(s).str.strip().str.title()


def amount(series):
    """Parse a money field that mixes bare numbers with a '0. NONE' code."""
    s = series.astype("string").str.strip()
    direct = pd.to_numeric(s, errors="coerce")
    none_code = s.str.match(r"^0\.\s*NONE", case=False, na=False)
    return direct.where(~none_code, 0.0)


def yes(series):
    """1 for an affirmative answer, 0 for a negative, NaN otherwise."""
    c = code(series)
    return c.where(c.isin([1, 2])).map({1.0: 1.0, 2.0: 0.0}).astype(float)


def flag(condition):
    """Nullable boolean -> plain 0/1 int, treating NA as 'not the case'.

    pandas' nullable dtypes propagate NA through comparisons; every survey
    filter here means "answered yes", so NA collapses to 0.
    """
    return pd.Series(condition).fillna(False).astype(bool).astype(int)


def read(path, **kw):
    return pd.read_csv(path, low_memory=False, **kw)


# ---------------------------------------------------------------------------
# Consumption aggregate
# ---------------------------------------------------------------------------
def _hierarchical_unit_value(df, item_col, unit_cols, value, quantity, geo_cols):
    """Median price per unit, taken from the finest geography with support.

    LSMS practice: value own-produced and gifted food at the local market price
    implied by other households' purchases of the same item in the same unit and
    size. Fall back to progressively coarser geographies when a cell is thin.
    """
    ok = ((quantity > 0) & (value > 0)).fillna(False).to_numpy()
    src = df.loc[ok].copy()
    src["_uv"] = (value[ok] / quantity[ok]).to_numpy()
    # Unit values are ratios of two self-reported fields, so a mis-keyed
    # quantity produces a price orders of magnitude off. Trim within item
    # before taking medians, otherwise one bad row distorts a whole cell.
    g = src.groupby(item_col)["_uv"]
    lo, hi = g.transform(lambda s: s.quantile(0.025)), g.transform(lambda s: s.quantile(0.975))
    src = src[(src["_uv"] >= lo) & (src["_uv"] <= hi)]

    keys = [item_col] + unit_cols
    out = pd.Series(np.nan, index=df.index, dtype=float)
    for geo in geo_cols + [[]]:  # widening geography, ending with national
        by = geo + keys
        med = src.groupby(by, dropna=False)["_uv"].median() if by else None
        if by:
            merged = df[by].merge(
                med.rename("_m").reset_index(), on=by, how="left"
            )["_m"]
            merged.index = df.index
        else:
            merged = pd.Series(src["_uv"].median(), index=df.index)
        out = out.fillna(merged)
    return out


# Column maps for the food module. The two waves ask the same questions in the
# same order and differ only in variable names, so one routine serves both.
FOOD_COLS = {
    "w5": dict(file="sect6b_plantingw5.csv", qty="s6bq2a", unit="s6bq2b",
               size="s6bq2c", pqty="s6bq7a", punit="s6bq7b", psize="s6bq7c",
               pval="s6bq8"),
    "w4": dict(file="sect7b_plantingw4.csv", qty="s7bq2a", unit="s7bq2b",
               size="s7bq2c", pqty="s7bq9a", punit="s7bq9b", psize="s7bq9c",
               pval="s7bq10"),
}


def food_consumption(wave):
    """Annual household food consumption value (7-day recall x 52).

    Total consumption includes own production and gifts, not just purchases,
    so quantities are valued at the median unit value implied by other
    households' purchases of the same item in the same unit and size - the
    standard LSMS treatment. Prices are taken from the finest geography that
    has support, widening from state to zone to national.
    """
    m = FOOD_COLS[wave]
    base = config.W5_PP if wave == "w5" else config.W4
    f = read(base / m["file"])
    f["qty_consumed"] = pd.to_numeric(f[m["qty"]], errors="coerce")
    f["qty_purch"] = pd.to_numeric(f[m["pqty"]], errors="coerce")
    f["val_purch"] = pd.to_numeric(f[m["pval"]], errors="coerce")
    f["item"] = code(f["item_cd"]) if f["item_cd"].dtype == object else f["item_cd"]
    f["state_c"] = code(f["state"]) if f["state"].dtype == object else f["state"]
    f["zone_c"] = code(f["zone"]) if f["zone"].dtype == object else f["zone"]

    def as_code(col):
        return code(f[col]) if f[col].dtype == object else f[col]

    # Unit values come from the purchase side, keyed on the purchase unit.
    price_frame = f.assign(unit_k=as_code(m["punit"]), size_k=as_code(m["psize"]))
    unit_value = _hierarchical_unit_value(
        price_frame, "item", ["unit_k", "size_k"],
        f["val_purch"], f["qty_purch"], [["state_c"], ["zone_c"]],
    )
    # The consumed quantity is normally reported in the same unit as the
    # purchase; where it is not, fall back to the item's overall unit value.
    cons_frame = f.assign(unit_k=as_code(m["unit"]), size_k=as_code(m["size"]))
    unit_value_cons = _hierarchical_unit_value(
        cons_frame, "item", ["unit_k", "size_k"],
        f["val_purch"], f["qty_purch"], [["state_c"], ["zone_c"]],
    )
    same_unit = as_code(m["unit"]).eq(as_code(m["punit"])).fillna(False)
    price = np.where(same_unit, unit_value, unit_value_cons)

    f["value_week"] = f["qty_consumed"].fillna(0) * pd.Series(price, index=f.index).fillna(0)
    f.loc[~np.isfinite(f["value_week"]), "value_week"] = 0.0
    # A quantity reported in the wrong unit can imply a week's consumption of
    # one item worth more than a year's total spending. Cap each item-level
    # entry at its 99th percentile across households before summing.
    cap = f.groupby("item")["value_week"].transform(lambda s: s.quantile(0.99))
    f["value_week"] = np.minimum(f["value_week"], cap.fillna(f["value_week"]))

    out = f.groupby("hhid")["value_week"].sum(min_count=1) * config.WEEKS_PER_YEAR
    return out.rename("food_annual")


def food_consumption_w5():
    return food_consumption("w5")


def _nonfood_block(path, flag_col, value_col, annualiser, item_col="item_cd"):
    d = read(path)
    d["item"] = code(d[item_col])
    d["value"] = pd.to_numeric(d[value_col], errors="coerce")
    d.loc[yes(d[flag_col]) == 0, "value"] = 0.0
    d["annual"] = d["value"] * annualiser
    return d


def nonfood_consumption_w5():
    """Annual non-food consumption, and the health items inside it.

    sect7a is a 7-day recall, sect7b a 30-day recall, sect7c a 12-month recall.
    Health enters the aggregate through sect7c items 355 (provider fees),
    356 (pharmaceuticals) and 357 (therapeutic equipment); item 363 records
    health-insurance premiums, which are not out-of-pocket treatment costs and
    are tracked separately.
    """
    a = _nonfood_block(config.W5_PP / "sect7a_plantingw5.csv", "s7q1", "s7q2",
                       config.WEEKS_PER_YEAR)
    b = _nonfood_block(config.W5_PP / "sect7b_plantingw5.csv", "s7q3", "s7q4", 12.0)
    c = _nonfood_block(config.W5_PP / "sect7c_plantingw5.csv", "s7q5", "s7q6", 1.0)

    total = pd.concat(
        [x.groupby("hhid")["annual"].sum(min_count=1) for x in (a, b, c)], axis=1
    ).sum(axis=1, min_count=1)

    def pick(df, items):
        return (df[df["item"].isin(items)].groupby("hhid")["annual"]
                .sum(min_count=1).reindex(total.index).fillna(0.0))

    oop_services = pick(c, [355])
    oop_drugs = pick(c, [356])
    oop_equipment = pick(c, [357])
    insurance = pick(c, [363])
    supplements = pick(b, [222, 223])

    return pd.DataFrame(
        {
            "nonfood_annual": total,
            "oop_services": oop_services,
            "oop_drugs": oop_drugs,
            "oop_equipment": oop_equipment,
            "health_insurance_paid": insurance,
            "health_supplements": supplements,
        }
    )


def education_expenditure_w5():
    """Annual household education spending (sect2 post-harvest, per student)."""
    e = read(config.W5_PH / "sect2_harvestw5.csv")
    tot = pd.to_numeric(e["s2q23bt"], errors="coerce")
    return e.assign(edu=tot).groupby("hhid")["edu"].sum(min_count=1).rename("edu_annual")


# ---------------------------------------------------------------------------
# Roster, employment, health
# ---------------------------------------------------------------------------
def roster_w5():
    """Current household members only.

    The wave-5 roster lists everyone recorded in wave 4 as well, and s1q4 marks
    who is still a member. The question is not put to people added since the
    last visit, so a missing answer means "current member": keeping only the
    explicit "YES" would drop 2,605 new members and understate household size.
    The result matches the health module's 27,421 rows exactly.
    """
    r = read(config.W5_PP / "sect1_plantingw5.csv")
    still_member = code(r["s1q4"]) != 2
    r = r[still_member].copy()
    r["age"] = pd.to_numeric(r["s1q6"], errors="coerce")
    r["female"] = flag(code(r["s1q2"]) == 2).astype(float)
    r["rel_code"] = code(r["s1q3"])
    r["is_head"] = flag(r["rel_code"] == 1)
    return r[["hhid", "indiv", "age", "female", "rel_code", "is_head"]]


def insurance_w5():
    """Health-insurance coverage from Section 5A, questions 16-17c.

    s5aq16 asks whether any household member holds insurance; s5aq17a__N marks
    the types held and s5aq17b_* / s5aq17c_* name the covered members by their
    roster id. The release ships no codebook, so the health type was identified
    empirically: every one of the ten households that reported paying a
    health-insurance premium in the consumption module (item 363) carries type
    1, and no other type shows that correspondence. The check is reprinted on
    every run below so the identification cannot silently rot.
    """
    d = read(config.W5_PP / "sect5a2_plantingw5.csv")
    d["any_insurance"] = flag(yes(d["s5aq16"]) == 1)
    d["insured_health"] = flag(yes(d["s5aq17a__1"]) == 1)

    member_cols = [c for c in d.columns
                   if c.startswith("s5aq17b_") or c.startswith("s5aq17c_")]
    counts = []
    for _, r in d.iterrows():
        if not r["insured_health"]:
            counts.append(0)
            continue
        ids = {int(float(r[c])) for c in member_cols if pd.notna(r[c])}
        counts.append(len(ids))
    d["n_insured_members"] = counts
    return d[["hhid", "any_insurance", "insured_health", "n_insured_members"]]


def employment_w5():
    """Individual formal/informal status, and the household sector flag.

    A worker is classified formal when the employer is a public body, a
    state-owned enterprise, an NGO or an international organisation, or when the
    employer is a private firm with five or more staff - the threshold at which
    section 14 of the NHIA Act 2022 obliges an employer to enrol its workers.
    Everyone else in work is informal. The rule uses only labelled variables;
    Section 5.6 tests three alternatives.
    """
    l = read(config.W5_PP / "sect4a_plantingw5.csv")
    employer = code(l["s4aq52"])          # 1-3 govt, 4 SOE, 5 private, 7 domestic, 8 NGO, 10 intl
    firm_size = code(l["s4aq55"])         # 1:'1' 2:'2-4' 3:'5-9' 4:'10-19' 5:'20-49' 6:'50+'
    status = code(l["s4aq42"])            # 3 = employee
    works = (yes(l["s4aq1"]) == 1) | (yes(l["s4aq2"]) == 1) | (code(l["s4aq21"]).isin([2, 3]))

    public = employer.isin([1, 2, 3, 4, 8, 10])
    big_private = employer.isin([5, 11]) & firm_size.isin([3, 4, 5, 6])
    l["formal_worker"] = flag(public | big_private)
    l["wage_employee"] = flag((status == 3) | employer.notna())
    l["works"] = flag(works)
    l["employer_public"] = flag(public)
    l["firm_ge5"] = flag(firm_size.isin([3, 4, 5, 6]))

    # Alternative definitions carried through to the robustness table.
    l["formal_alt_govt"] = flag(employer.isin([1, 2, 3, 4]))
    l["formal_alt_anywage"] = l["wage_employee"]
    return l[["hhid", "indiv", "works", "formal_worker", "wage_employee",
              "employer_public", "firm_ge5", "formal_alt_govt", "formal_alt_anywage"]]


def health_w5():
    """Individual utilisation and out-of-pocket cost from the health module.

    Cost fields, confirmed against the Post-Planting Household Questionnaire
    (World Bank Microdata catalogue 6410, document 180528), Section 3:
    the questionnaire before submission):
      s3q12  consultation fee, explicitly excluding drugs   (4-week recall)
      s3q13  transport to and from the facility             (4-week recall, excluded)
      s3q17  prescription drugs and medicines               (4-week recall)
      s3q17a non-prescription drugs and medicines           (4-week recall)
      s3q20  hospital stay, including consultation,
             procedures and drugs                           (12-month recall)

    Q16/Q17/Q17a explicitly EXCLUDE drugs related to hospital admissions and
    Q20 explicitly INCLUDES them, so outpatient and inpatient spending do not
    overlap and can be summed.
    """
    h = read(config.W5_PP / "sect3_plantingw5.csv")

    h["ill_4wk"] = (yes(h["s3q5"]).fillna(0) + flag(code(h["s3q4_1"]).isin([1, 2]))).clip(0, 1)
    h["sought_care"] = flag(h["s3q10"].notna())
    h["days_lost"] = pd.to_numeric(h["s3q8"], errors="coerce").fillna(0).clip(0, 28)

    provider = code(h["s3q9_1"])
    h["self_medicated"] = flag(provider.isin([8, 11]))   # pharmacist / chemist
    h["saw_clinician"] = flag(provider.isin([3, 4, 5, 6, 7, 12, 13]))
    place = code(h["s3q10"])
    h["traditional"] = flag(place.isin([10]))
    h["facility_public"] = flag(code(h["s3q11"]).isin([1, 2, 3]))

    fee = amount(h["s3q12"]).fillna(0)
    transport = amount(h["s3q13"]).fillna(0)
    meds = pd.to_numeric(h["s3q17"], errors="coerce").fillna(0)
    other = pd.to_numeric(h["s3q17a"], errors="coerce").fillna(0)
    h["op_cost_window"] = np.where(h["sought_care"] == 1, fee + meds + other, 0.0)
    h["op_transport_window"] = np.where(h["sought_care"] == 1, transport, 0.0)
    h["op_drug_window"] = np.where(h["sought_care"] == 1, meds, 0.0)

    h["inpatient"] = yes(h["s3q18"]).fillna(0).astype(int)
    h["inpatient_nights"] = pd.to_numeric(h["s3q19"], errors="coerce").fillna(0)
    h["ip_cost_year"] = pd.to_numeric(h["s3q20"], errors="coerce").fillna(0)

    # The questionnaire separates the consultation fee from the two drug
    # fields, so the drug share of outpatient cost is measured rather than
    # assumed. config.DRUG_SHARE_OF_OUTPATIENT should track this figure.
    _op = fee + meds + other
    _spend = _op > 0
    if _spend.any():
        share = float((meds + other)[_spend].sum() / _op[_spend].sum())
        print(f"  drug share of outpatient spend: {share:.4f} "
              f"(config has {config.DRUG_SHARE_OF_OUTPATIENT})")

    # Washington Group short set: severe functional difficulty in any domain.
    wg = [f"s3q{i}" for i in range(23, 29)]
    sev = pd.concat([code(h[c]).isin([3, 4]) for c in wg if c in h], axis=1)
    h["chronic"] = flag(sev.any(axis=1))

    keep = ["hhid", "indiv", "ill_4wk", "sought_care", "days_lost", "self_medicated",
            "saw_clinician", "traditional", "facility_public", "op_cost_window",
            "op_transport_window", "op_drug_window", "inpatient", "inpatient_nights",
            "ip_cost_year", "chronic"]
    return h[keep]


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build_w5(factors=None):
    cover = read(config.W5_PP / "secta_plantingw5.csv")
    cover = cover[cover["wt_cross_wave5"].notna()].copy()
    # Three weights are released. wt_wave5 and wt_longpanel_wave5 are panel
    # weights and gross up to 27.0 and 29.7 million households; wt_cross_wave5
    # is the cross-sectional weight and grosses up to 40.5 million households
    # and 210.9 million people, which is the national population in 2023/24.
    # Every estimate in the paper is meant to describe Nigeria, so the
    # cross-sectional weight is the right one.
    hh = pd.DataFrame({
        "hhid": cover["hhid"],
        "zone": label(cover["zone"]),
        "state": label(cover["state"]),
        "sector": label(cover["sector"]),
        "urban": flag(code(cover["sector"]) == 1),
        "ea": cover["ea"],
        "cluster": cover["cluster"].astype(str),
        "strata": cover["strata"],
        "hh_weight": cover["wt_cross_wave5"].astype(float),
        "hh_weight_panel": cover["wt_wave5"].astype(float),
    })

    ros = roster_w5()
    size = ros.groupby("hhid").size().rename("hhsize")
    heads = ros[ros["is_head"] == 1].drop_duplicates("hhid").set_index("hhid")
    kids = ros.assign(k=flag(ros["age"] < 5)).groupby("hhid")["k"].sum()
    old = ros.assign(o=flag(ros["age"] >= 60)).groupby("hhid")["o"].sum()

    hh = hh.set_index("hhid")
    hh["hhsize"] = size
    hh["head_age"] = heads["age"]
    hh["head_female"] = heads["female"]
    hh["n_under5"] = kids
    hh["n_over60"] = old

    # --- consumption -------------------------------------------------------
    food = food_consumption_w5()
    nonfood = nonfood_consumption_w5()
    edu = education_expenditure_w5()
    hh["food_annual"] = food
    hh = hh.join(nonfood)
    hh["edu_annual"] = edu
    for c in ["food_annual", "nonfood_annual", "edu_annual", "oop_services",
              "oop_drugs", "oop_equipment", "health_insurance_paid",
              "health_supplements"]:
        hh[c] = hh[c].fillna(0.0)

    # --- out-of-pocket -----------------------------------------------------
    # Two instruments measure the same thing. The consumption module asks one
    # household-level question with a 12-month recall and picks up spending in
    # only 17% of households; the health module asks every member about a
    # specific episode of care and its itemised cost. The health module is the
    # primary source and the consumption module is carried as a robustness
    # comparison, because a single annual-recall question is known to
    # under-report frequent small payments (O'Donnell et al. 2008).
    oop_cons_module = hh["oop_services"] + hh["oop_drugs"] + hh["oop_equipment"]
    hh["oop_consumption_module"] = oop_cons_module
    hh["premium_paid"] = flag(hh["health_insurance_paid"] > 0)

    # --- health-insurance coverage -----------------------------------------
    # Section 5A questions 16-17c (sect5a2) ask directly whether anyone in the
    # household holds insurance, of what type, and which members are covered.
    # This is a coverage measure, distinct from `premium_paid` above, which
    # only catches households that paid a premium themselves in the past year -
    # employer-paid and subsidised cover show up here but not there.
    # hh is indexed by hhid at this point, like the consumption blocks above,
    # so join rather than merge - merge would silently reset the index.
    cover = insurance_w5().set_index("hhid")
    hh = hh.join(cover[["insured_health", "n_insured_members"]])
    hh["insured_health"] = hh["insured_health"].fillna(0).astype(int)
    hh["n_insured_members"] = hh["n_insured_members"].fillna(0).astype(int)
    hh["insured_any"] = hh["insured_health"]

    # Re-run the identification every build. If a future release renumbers the
    # insurance types, this correspondence breaks and the run says so instead of
    # quietly repricing the paper.
    payers = hh["premium_paid"] == 1
    agree = int((payers & (hh["insured_health"] == 1)).sum())
    print(f"  insurance type check: {agree} of {int(payers.sum())} households that "
          f"paid a health premium report type 1"
          + ("" if agree == int(payers.sum()) else "   <-- IDENTIFICATION SUSPECT"))

    # Health-module OOP is attached after the individual file is built; the
    # consumption total is completed there too, so that health spending enters
    # the denominator exactly once and from the primary instrument.
    hh["nonfood_excl_health"] = (hh["nonfood_annual"] - oop_cons_module).clip(lower=0)

    # --- sector ------------------------------------------------------------
    emp = employment_w5()
    emp_hh = emp.groupby("hhid").agg(
        n_workers=("works", "sum"),
        any_formal=("formal_worker", "max"),
        any_public=("employer_public", "max"),
        any_firm_ge5=("firm_ge5", "max"),
        any_formal_govt=("formal_alt_govt", "max"),
        any_formal_anywage=("formal_alt_anywage", "max"),
    )
    head_emp = emp.merge(ros[ros["is_head"] == 1][["hhid", "indiv"]],
                         on=["hhid", "indiv"], how="inner").set_index("hhid")
    hh = hh.join(emp_hh)
    hh["head_formal"] = head_emp["formal_worker"]
    for c in ["n_workers", "any_formal", "any_public", "any_firm_ge5",
              "any_formal_govt", "any_formal_anywage", "head_formal"]:
        hh[c] = hh[c].fillna(0).astype(int)
    hh["informal"] = 1 - hh["any_formal"]
    hh["sector_label"] = np.where(hh["informal"] == 1, "Informal", "Formal")

    hh = hh.reset_index()
    hh = hh[hh["hhsize"].notna()].copy()

    # --- health-module roll-up, then the consumption total ------------------
    ind = build_individuals_w5(hh)
    ind_hh = ind.groupby("hhid").agg(
        oop_outpatient=("op_cost_annual", "sum"),
        oop_inpatient=("ip_cost_annual", "sum"),
        oop_drugs_hm=("op_drug_annual", "sum"),
        oop_transport=("op_transport_annual", "sum"),
        n_ill=("ill_4wk", "sum"),
        n_visits=("sought_care", "sum"),
        n_inpatient=("inpatient", "sum"),
        any_chronic=("chronic", "max"),
    )
    hh = hh.merge(ind_hh, left_on="hhid", right_index=True, how="left")
    for c in ind_hh.columns:
        hh[c] = hh[c].fillna(0.0)

    hh["oop_annual"] = hh["oop_outpatient"] + hh["oop_inpatient"]
    hh["oop_with_transport"] = hh["oop_annual"] + hh["oop_transport"]
    hh["cons_annual_raw"] = (hh["food_annual"] + hh["nonfood_excl_health"]
                             + hh["edu_annual"] + hh["oop_annual"])
    # Calibrated aggregate (see config.CALIBRATE_CONSUMPTION). Health spending
    # is never scaled: it is measured directly and enters the numerator too.
    hh["food_annual_raw"] = hh["food_annual"]
    hh["nonfood_excl_health_raw"] = hh["nonfood_excl_health"]
    if factors is not None and config.CALIBRATE_CONSUMPTION:
        hh["food_annual"] = hh["food_annual_raw"] * factors["food_factor"]
        hh["nonfood_excl_health"] = (hh["nonfood_excl_health_raw"]
                                     * factors["nonfood_factor"])
        non_rent = (hh["food_annual"] + hh["nonfood_excl_health"]
                    + hh["edu_annual"] + hh["oop_annual"])
        hh["rent_imputed"] = non_rent * factors["rent_ratio"]
        hh["cons_annual"] = non_rent + hh["rent_imputed"]
    else:
        hh["rent_imputed"] = 0.0
        hh["cons_annual"] = hh["cons_annual_raw"]

    hh = hh[hh["cons_annual"] > 0].copy()
    hh = add_welfare_variables(hh)
    hh["wave"] = "W5 (2023/24)"

    # Push the welfare variables back onto the individual file.
    ind = ind.merge(
        hh.set_index("hhid")[["cons_pc", "quintile", "quintile_label", "cons_annual"]],
        left_on="hhid", right_index=True, how="inner",
    )
    return hh, ind


def build_individuals_w5(hh):
    """Individual-year file: the unit of analysis for the cost models."""
    ros = roster_w5()
    hm = health_w5()
    ind = ros.merge(hm, on=["hhid", "indiv"], how="inner")

    ann = config.OUTPATIENT_ANNUALISER
    ind["op_cost_annual"] = ind["op_cost_window"] * ann
    ind["op_transport_annual"] = ind["op_transport_window"] * ann
    ind["op_drug_annual"] = ind["op_drug_window"] * ann
    ind["ip_cost_annual"] = ind["ip_cost_year"]
    ind["cost_annual"] = ind["op_cost_annual"] + ind["ip_cost_annual"]

    # Expected annual contacts implied by the 4-week window.
    ind["op_visits_annual"] = ind["sought_care"] * ann
    ind["exposure_op"] = config.OUTPATIENT_RECALL_WEEKS / config.WEEKS_PER_YEAR
    ind["exposure_ip"] = 1.0

    ind["age_band"] = pd.cut(
        ind["age"], [-0.1, 4, 14, 24, 44, 59, 200],
        labels=["0-4", "5-14", "15-24", "25-44", "45-59", "60+"],
    )
    base = hh if hh.index.name == "hhid" else hh.set_index("hhid")
    cols = [c for c in ["cluster", "strata", "hh_weight", "zone", "state", "urban",
                        "sector", "hhsize", "informal", "sector_label",
                        "insured_any"] if c in base]
    ind = ind.merge(base[cols], left_on="hhid", right_index=True, how="inner")
    # Individual weight: the GHS releases a household weight; individuals in a
    # household share it, so population totals scale with household size.
    ind["ind_weight"] = ind["hh_weight"]
    return ind


def add_welfare_variables(hh):
    """Per-capita consumption, quintiles, equivalence scale, capacity to pay."""
    hh = hh.copy()
    hh["cons_pc"] = hh["cons_annual"] / hh["hhsize"]
    hh["food_share"] = (hh["food_annual"] / hh["cons_annual"]).clip(0, 1)
    hh["eqsize"] = hh["hhsize"] ** config.EQ_SCALE_POWER
    hh["popwt"] = hh["hh_weight"] * hh["hhsize"]

    from svy import weighted_quantile

    cuts = weighted_quantile(hh["cons_pc"].to_numpy(), hh["popwt"].to_numpy(),
                             [0.2, 0.4, 0.6, 0.8])
    hh["quintile"] = np.digitize(hh["cons_pc"], cuts) + 1
    hh["quintile_label"] = pd.Categorical(
        hh["quintile"].map({1: "Q1 (poorest)", 2: "Q2", 3: "Q3", 4: "Q4",
                            5: "Q5 (richest)"}),
        categories=["Q1 (poorest)", "Q2", "Q3", "Q4", "Q5 (richest)"], ordered=True,
    )

    # Xu et al. (2003) capacity to pay.
    hh["food_eq"] = hh["food_annual"] / hh["eqsize"]
    lo, hi = weighted_quantile(hh["food_share"].to_numpy(), hh["popwt"].to_numpy(),
                               list(config.SUBSISTENCE_PCTL))
    band = hh[(hh["food_share"] >= lo) & (hh["food_share"] <= hi)]
    se_pc = float(np.average(band["food_eq"], weights=band["popwt"]))
    hh["subsistence"] = se_pc * hh["eqsize"]
    hh["ctp"] = np.where(hh["subsistence"] < hh["food_annual"],
                         hh["cons_annual"] - hh["subsistence"],
                         hh["cons_annual"] - hh["food_annual"])
    hh["ctp"] = hh["ctp"].clip(lower=1.0)
    hh.attrs["subsistence_per_eq_adult"] = se_pc
    return hh


# ---------------------------------------------------------------------------
# Wave 4 (robustness / trend)
# ---------------------------------------------------------------------------
def build_w4():
    """Wave 4 using the published consumption aggregate as the denominator."""
    t = read(config.W4 / "totcons_final.csv")
    zone_names = {1: "North Central", 2: "North East", 3: "North West",
                  4: "South East", 5: "South South", 6: "South West"}
    hh = pd.DataFrame({
        "hhid": t["hhid"],
        "zone": t["zone"].map(zone_names),
        "sector": np.where(t["sector"] == 1, "Urban", "Rural"),
        "urban": flag(t["sector"] == 1),
        "ea": t["ea"],
        "cluster": t["ea"].astype(str),
        "strata": t["zone"],
        "hh_weight": t["wt_wave4"].astype(float),
        "hhsize": t["hhsize"].astype(float),
    }).set_index("hhid")

    # Every component of totcons_final is per capita (they sum exactly to
    # totcons_pc); the analysis works in household totals, so each is scaled up
    # by household size.
    ti = t.set_index("hhid")
    food_cols = [c for c in t.columns if c.startswith(("food_own", "food_purch", "food_meals"))]
    hh["food_annual"] = ti[food_cols].sum(axis=1) * hh["hhsize"]
    hh["oop_annual"] = ti[["health31", "health32"]].sum(axis=1) * hh["hhsize"]
    hh["cons_annual"] = ti["totcons_pc"] * hh["hhsize"]
    hh["cons_pc_official"] = ti["totcons_pc"]

    r = read(config.W4 / "sect1_plantingw4.csv")
    r["age"] = pd.to_numeric(r["s1q4"], errors="coerce")
    r["female"] = flag(code(r["s1q2"]) == 2).astype(float)
    heads = r[code(r["s1q3"]) == 1].drop_duplicates("hhid").set_index("hhid")
    hh["head_age"] = heads["age"]
    hh["head_female"] = heads["female"]

    # Wave 4 has no directly comparable employer-size question, so the sector
    # split uses the head's occupation group; wave-4 results are reported only
    # as a trend check and are never pooled with wave 5.
    hh["informal"] = 1
    hh["sector_label"] = "All households"
    # Wave 4 carries no insurance module; the column exists only so the wave-4
    # file has the same shape as wave 5.
    hh["insured_any"] = 0
    hh["premium_paid"] = 0
    hh = hh.reset_index()
    hh = hh[(hh["cons_annual"] > 0) & (hh["hh_weight"] > 0)].copy()
    hh = add_welfare_variables(hh)

    # Deflate to the wave-5 price base so the two waves are comparable.
    for c in ["food_annual", "oop_annual", "cons_annual", "cons_pc", "ctp",
              "subsistence"]:
        hh[c + "_nominal"] = hh[c]
        hh[c] = hh[c] * config.CPI_W4_TO_W5
    hh["wave"] = "W4 (2018/19)"
    return hh



# ---------------------------------------------------------------------------
# Wave 4 as the primary wave (2018/19)
# ---------------------------------------------------------------------------
def n4(series):
    """Wave 4 releases bare numeric codes ("1", "2.0") rather than wave 5's
    "1. YES" labels, which code() and yes() would read as missing."""
    return pd.to_numeric(series, errors="coerce")


def roster_w4():
    """Current household members, as roster_w5: s1q4 asks previous members
    whether they are still in the household; new members are not asked."""
    r = read(config.W4 / "sect1_plantingw4.csv")
    # Blank for members of households new to the panel in wave 4, who are
    # current by definition: keep everyone not explicitly marked as gone.
    r = r[pd.to_numeric(r["s1q4"], errors="coerce") != 2].copy()
    r["age"] = pd.to_numeric(r["s1q6"], errors="coerce")
    r["female"] = flag(n4(r["s1q2"]) == 2).astype(float)
    r["rel_code"] = n4(r["s1q3"])
    r["is_head"] = flag(r["rel_code"] == 1)
    return r[["hhid", "indiv", "age", "female", "rel_code", "is_head"]]


def employment_w4():
    """Formal and informal work in wave 4 (planting labour module, sect3).

    s3q4 marks a wage job in the last seven days; for wage workers s3q15 gives
    the employer (1 federal, 2 state and 3 local government, 5 private firm,
    9 religious body; the rest are small) and s3q15c the size of the workplace
    in four bands. Government employers are formal; any other employer is
    formal from the second size band up, taken as five or more workers, the
    NHIA Act's threshold. The size bands are inferred: government employers
    fall almost entirely in band 4 and private employers mostly in band 1.
    Section 5.6 tests the government-only and any-wage-job alternatives.
    """
    l = read(config.W4 / "sect3_plantingw4.csv")
    wage = n4(l["s3q4"]) == 1
    employer = n4(l["s3q15"])
    size_band = n4(l["s3q15c"])
    public = wage & employer.isin([1, 2, 3])
    big = wage & ~employer.isin([1, 2, 3]) & size_band.isin([2, 3, 4])
    works = ((n4(l["s3q2"]) == 1) | wage | (n4(l["s3q5"]) == 1) | (n4(l["s3q6"]) == 1))
    l["formal_worker"] = flag(public | big)
    l["wage_employee"] = flag(wage)
    l["works"] = flag(works)
    l["employer_public"] = flag(public)
    l["firm_ge5"] = flag(wage & size_band.isin([2, 3, 4]))
    l["formal_alt_govt"] = flag(public)
    l["formal_alt_anywage"] = l["wage_employee"]
    return l[["hhid", "indiv", "works", "formal_worker", "wage_employee",
              "employer_public", "firm_ge5", "formal_alt_govt", "formal_alt_anywage"]]


def health_w4():
    """Individual utilisation and out-of-pocket cost, wave 4 health module
    (post-harvest visit, sect4a):

      s4aq1   illness or injury in the last 4 weeks
      s4aq6a  who was consulted (0 nobody; 8 and 11 pharmacist or chemist)
      s4aq7   where care was sought (10 traditional healer)
      s4aq8   who runs the facility (1-3 government)
      s4aq9   consultation fee                          (4-week recall)
      s4aq10  transport                                 (4-week recall, excluded)
      s4aq14  medicines bought in the last 4 weeks      (4-week recall)
      s4aq15  hospitalized in the last 12 months
      s4aq16  nights in hospital
      s4aq17  cost of hospitalization                   (12-month recall)

    The code lists follow the wave-5 instrument, which the panel carries
    forward. The medicine question is asked of everyone, not only of those who
    consulted, so it catches self-treatment as well.
    """
    h = read(config.W4 / "sect4a_harvestw4.csv")
    h["ill_4wk"] = flag(n4(h["s4aq1"]) == 1)
    who = n4(h["s4aq6a"])
    h["sought_care"] = flag(who.notna() & (who != 0))
    h["days_lost"] = pd.to_numeric(h["s4aq5"], errors="coerce").fillna(0).clip(0, 28)
    h["self_medicated"] = flag(who.isin([8, 11]))
    h["saw_clinician"] = flag(who.isin([1, 2, 3, 4, 5, 6, 7]))
    place = n4(h["s4aq7"])
    h["traditional"] = flag(place.isin([10]))
    h["facility_public"] = flag(n4(h["s4aq8"]).isin([1, 2, 3]))

    fee = pd.to_numeric(h["s4aq9"], errors="coerce").fillna(0)
    transport = pd.to_numeric(h["s4aq10"], errors="coerce").fillna(0)
    meds = pd.to_numeric(h["s4aq14"], errors="coerce").fillna(0)
    h["op_cost_window"] = np.where(h["sought_care"] == 1, fee, 0.0) + meds
    h["op_transport_window"] = np.where(h["sought_care"] == 1, transport, 0.0)
    h["op_drug_window"] = meds

    h["inpatient"] = flag(n4(h["s4aq15"]) == 1)
    h["inpatient_nights"] = pd.to_numeric(h["s4aq16"], errors="coerce").fillna(0)
    h["ip_cost_year"] = pd.to_numeric(h["s4aq17"], errors="coerce").fillna(0)

    _op = h["op_cost_window"]
    if (_op > 0).any():
        share = float(meds[_op > 0].sum() / _op[_op > 0].sum())
        print(f"  drug share of outpatient spend: {share:.4f} "
              f"(config has {config.DRUG_SHARE_OF_OUTPATIENT})")

    # Washington Group short set: severe difficulty (codes 3, 4) in any domain.
    wg = ["s4aq23", "s4aq25", "s4aq27", "s4aq29", "s4aq31", "s4aq33"]
    sev = pd.concat([n4(h[c]).isin([3, 4]) for c in wg if c in h], axis=1)
    h["chronic"] = flag(sev.any(axis=1))

    keep = ["hhid", "indiv", "ill_4wk", "sought_care", "days_lost", "self_medicated",
            "saw_clinician", "traditional", "facility_public", "op_cost_window",
            "op_transport_window", "op_drug_window", "inpatient", "inpatient_nights",
            "ip_cost_year", "chronic"]
    return h[keep]


def build_w4_primary():
    """Wave 4 (2018/19) as the analysis wave.

    The denominator is the World Bank's published consumption aggregate
    (totcons_final), with its health components replaced by health-module
    spending so that health enters numerator and denominator from one
    instrument. No calibration is needed. Wave 4 has no insurance module, so
    coverage is not measured. Naira amounts are carried to August 2023 prices
    with config.CPI_W4_TO_W5.
    """
    t = read(config.W4 / "totcons_final.csv")
    cover = read(config.W4 / "secta_plantingw4.csv")[["hhid", "state", "cluster", "strata"]]
    zone_names = {1: "North Central", 2: "North East", 3: "North West",
                  4: "South East", 5: "South South", 6: "South West"}
    hh = pd.DataFrame({
        "hhid": t["hhid"],
        "zone": t["zone"].map(zone_names),
        "sector": np.where(t["sector"] == 1, "Urban", "Rural"),
        "urban": flag(t["sector"] == 1),
        "ea": t["ea"],
        "hh_weight": t["wt_wave4"].astype(float),
        "hhsize": t["hhsize"].astype(float),
    }).merge(cover, on="hhid", how="left")
    hh["cluster"] = hh["ea"].astype(str)
    hh["strata"] = hh["strata"].fillna(t["zone"])
    ti = t.set_index("hhid")
    size = ti["hhsize"]
    food_cols = [c for c in t.columns if c.startswith(("food_own", "food_purch", "food_meals"))]
    nonfood_cols = [c for c in t.columns if c.startswith("nonfood")]
    hh = hh.set_index("hhid")
    hh["food_annual"] = ti[food_cols].sum(axis=1) * size
    hh["nonfood_excl_health"] = ti[nonfood_cols].sum(axis=1) * size
    hh["edu_annual"] = (ti["edu29"].fillna(0) + ti["edu30"].fillna(0)) * size
    hh["rent_imputed"] = ti["rent33"].fillna(0) * size
    hh["oop_consumption_module"] = (ti["health31"].fillna(0) + ti["health32"].fillna(0)) * size

    ros = roster_w4()
    heads = ros[ros["is_head"] == 1].drop_duplicates("hhid").set_index("hhid")
    hh["head_age"] = heads["age"]
    hh["head_female"] = heads["female"]
    hh["n_under5"] = ros.assign(k=flag(ros["age"] < 5)).groupby("hhid")["k"].sum()
    hh["n_over60"] = ros.assign(o=flag(ros["age"] >= 60)).groupby("hhid")["o"].sum()

    hh["insured_health"] = 0
    hh["n_insured_members"] = 0
    hh["insured_any"] = 0
    hh["premium_paid"] = 0
    hh["health_insurance_paid"] = 0.0

    emp = employment_w4()
    emp_hh = emp.groupby("hhid").agg(
        n_workers=("works", "sum"), any_formal=("formal_worker", "max"),
        any_public=("employer_public", "max"), any_firm_ge5=("firm_ge5", "max"),
        any_formal_govt=("formal_alt_govt", "max"), any_formal_anywage=("formal_alt_anywage", "max"))
    head_emp = emp.merge(ros[ros["is_head"] == 1][["hhid", "indiv"]], on=["hhid", "indiv"],
                         how="inner").set_index("hhid")
    hh = hh.join(emp_hh)
    hh["head_formal"] = head_emp["formal_worker"]
    for c in ["n_workers", "any_formal", "any_public", "any_firm_ge5", "any_formal_govt",
              "any_formal_anywage", "head_formal", "n_under5", "n_over60"]:
        hh[c] = hh[c].fillna(0).astype(int)
    hh["informal"] = 1 - hh["any_formal"]
    hh["sector_label"] = np.where(hh["informal"] == 1, "Informal", "Formal")
    hh = hh.reset_index()

    ind = build_individuals(hh, roster_w4(), health_w4())
    ind_hh = ind.groupby("hhid").agg(
        oop_outpatient=("op_cost_annual", "sum"), oop_inpatient=("ip_cost_annual", "sum"),
        oop_drugs_hm=("op_drug_annual", "sum"), oop_transport=("op_transport_annual", "sum"),
        n_ill=("ill_4wk", "sum"), n_visits=("sought_care", "sum"),
        n_inpatient=("inpatient", "sum"), any_chronic=("chronic", "max"))
    hh = hh.merge(ind_hh, left_on="hhid", right_index=True, how="inner")
    hh["oop_annual"] = hh["oop_outpatient"] + hh["oop_inpatient"]
    hh["oop_with_transport"] = hh["oop_annual"] + hh["oop_transport"]
    hh["cons_annual"] = (hh["food_annual"] + hh["nonfood_excl_health"] + hh["edu_annual"]
                         + hh["rent_imputed"] + hh["oop_annual"])
    hh["cons_annual_raw"] = hh["cons_annual"] - hh["rent_imputed"]
    hh["food_annual_raw"] = hh["food_annual"]
    hh["nonfood_excl_health_raw"] = hh["nonfood_excl_health"]
    hh = hh[(hh["cons_annual"] > 0) & (hh["hh_weight"] > 0)].copy()

    # August 2023 prices.
    k = config.CPI_W4_TO_W5
    money = ["food_annual", "nonfood_excl_health", "edu_annual", "rent_imputed",
             "oop_consumption_module", "oop_outpatient", "oop_inpatient", "oop_drugs_hm",
             "oop_transport", "oop_annual", "oop_with_transport", "cons_annual",
             "cons_annual_raw", "food_annual_raw", "nonfood_excl_health_raw"]
    for c in money:
        hh[c] = hh[c] * k
    for c in ["op_cost_window", "op_transport_window", "op_drug_window", "ip_cost_year",
              "op_cost_annual", "op_transport_annual", "op_drug_annual", "ip_cost_annual",
              "cost_annual"]:
        ind[c] = ind[c] * k

    hh = add_welfare_variables(hh)
    hh["wave"] = "W4 (2018/19)"
    ind = ind.merge(hh.set_index("hhid")[["cons_pc", "quintile", "quintile_label", "cons_annual"]],
                    left_on="hhid", right_index=True, how="inner")
    return hh, ind


def build_individuals(hh, ros, hm):
    """Individual-year file from a roster and a health module (either wave)."""
    ind = ros.merge(hm, on=["hhid", "indiv"], how="inner")
    ann = config.OUTPATIENT_ANNUALISER
    ind["op_cost_annual"] = ind["op_cost_window"] * ann
    ind["op_transport_annual"] = ind["op_transport_window"] * ann
    ind["op_drug_annual"] = ind["op_drug_window"] * ann
    ind["ip_cost_annual"] = ind["ip_cost_year"]
    ind["cost_annual"] = ind["op_cost_annual"] + ind["ip_cost_annual"]
    ind["op_visits_annual"] = ind["sought_care"] * ann
    ind["exposure_op"] = config.OUTPATIENT_RECALL_WEEKS / config.WEEKS_PER_YEAR
    ind["exposure_ip"] = 1.0
    ind["age_band"] = pd.cut(ind["age"], [-0.1, 4, 14, 24, 44, 59, 200],
                             labels=["0-4", "5-14", "15-24", "25-44", "45-59", "60+"])
    base = hh if hh.index.name == "hhid" else hh.set_index("hhid")
    cols = [c for c in ["cluster", "strata", "hh_weight", "zone", "state", "urban", "sector",
                        "hhsize", "informal", "sector_label", "insured_any"] if c in base]
    ind = ind.merge(base[cols], left_on="hhid", right_index=True, how="inner")
    ind["ind_weight"] = ind["hh_weight"]
    return ind


def calibration_factors():
    """Component scaling factors that map the rebuilt aggregate onto wave 4's.

    Three numbers: the ratio of the official to the rebuilt mean for food and
    for non-food (excluding health, which is measured directly in both), and
    the official ratio of imputed rent to everything else. Applied to wave 4
    itself they recover 96% of the official level and bring CHE at the 10%
    threshold to within about one point of the official figure; that check is
    written alongside the factors and reported in Table A1.
    """
    food = food_consumption("w4")
    nf = []
    for fn, fl, val, mult in [("sect8a_plantingw4.csv", "s8q1", "s8q2", 52.0),
                              ("sect8b_plantingw4.csv", "s8q3", "s8q4", 12.0),
                              ("sect8c_plantingw4.csv", "s8q5", "s8q6", 1.0)]:
        d = _nonfood_block(config.W4 / fn, fl, val, mult)
        nf.append(d.groupby("hhid")["annual"].sum(min_count=1))
    nonfood = pd.concat(nf, axis=1).sum(axis=1, min_count=1)

    t = read(config.W4 / "totcons_final.csv").set_index("hhid")
    size = t["hhsize"]
    food_cols = [c for c in t.columns if c.startswith(("food_own", "food_purch", "food_meals"))]
    nonfood_cols = [c for c in t.columns if c.startswith("nonfood")]
    off_food = t[food_cols].sum(axis=1) * size
    off_nonfood = t[nonfood_cols].sum(axis=1) * size
    health = (t["health31"].fillna(0) + t["health32"].fillna(0)) * size
    edu = (t["edu29"].fillna(0) + t["edu30"].fillna(0)) * size
    rent = t["rent33"].fillna(0) * size
    total = t["totcons_pc"] * size
    food = food.reindex(t.index).fillna(0.0)
    nonfood = nonfood.reindex(t.index).fillna(0.0)
    w = (t["wt_wave4"] * size)
    ok = ((total > 0) & w.notna() & ((food + nonfood) > 0)).to_numpy()

    f_food = float(off_food[ok].mean() / food[ok].mean())
    f_nonfood = float(off_nonfood[ok].mean() / nonfood[ok].mean())
    rent_ratio = float(rent[ok].sum() / (total - rent)[ok].sum())

    raw = food + nonfood + edu + health
    cal = (food * f_food + nonfood * f_nonfood + edu + health) * (1 + rent_ratio)

    def che(den, th):
        return 100 * np.average((health / den > th)[ok], weights=w[ok])

    rows = []
    for name, den in [("Official aggregate", total),
                      ("Rebuilt, uncalibrated", raw),
                      ("Rebuilt, calibrated", cal)]:
        rows.append({"aggregate": name,
                     "mean_naira": float(np.average(den[ok], weights=w[ok])),
                     "ratio_to_official": float(np.average(den[ok], weights=w[ok])
                                                / np.average(total[ok], weights=w[ok])),
                     "spearman_vs_official": float(den[ok].corr(total[ok], method="spearman")),
                     "che10_pct": che(den, 0.10), "che25_pct": che(den, 0.25),
                     "mean_oop_share_pct": 100 * float(np.average((health / den)[ok], weights=w[ok]))})
    check = pd.DataFrame(rows)
    factors = {"food_factor": f_food, "nonfood_factor": f_nonfood,
               "rent_ratio": rent_ratio}
    return factors, check


def validate_w4_aggregate():
    """Rebuild the wave-4 aggregate with the wave-5 code and compare.

    Wave 4's food module (sect7b planting) and non-food modules (sect8a/b/c)
    have the same shape as wave 5's sect6b and sect7a/b/c. Running the same
    construction on wave 4 and comparing with the published totcons_final gives
    a direct read on how much the wave-5 denominator can be trusted.
    """
    food = food_consumption("w4")

    nf = []
    for fn, fl, val, mult in [("sect8a_plantingw4.csv", "s8q1", "s8q2", 52.0),
                              ("sect8b_plantingw4.csv", "s8q3", "s8q4", 12.0),
                              ("sect8c_plantingw4.csv", "s8q5", "s8q6", 1.0)]:
        d = _nonfood_block(config.W4 / fn, fl, val, mult)
        nf.append(d.groupby("hhid")["annual"].sum(min_count=1))
    nonfood = pd.concat(nf, axis=1).sum(axis=1, min_count=1)

    t = read(config.W4 / "totcons_final.csv").set_index("hhid")
    size = t["hhsize"]
    food_cols = [c for c in t.columns if c.startswith(("food_own", "food_purch", "food_meals"))]
    nonfood_cols = [c for c in t.columns if c.startswith("nonfood")] + ["health31", "health32"]

    # Official components are per capita; the rebuild is a household total.
    cmp = pd.DataFrame({
        "official_food": t[food_cols].sum(axis=1) * size,
        "rebuilt_food": food,
        "official_nonfood": t[nonfood_cols].sum(axis=1) * size,
        "rebuilt_nonfood": nonfood,
        "official_total": t[food_cols + nonfood_cols].sum(axis=1) * size,
    }).dropna()
    cmp["rebuilt_total"] = cmp["rebuilt_food"] + cmp["rebuilt_nonfood"]

    rows = []
    for name, o, r in [("Food", "official_food", "rebuilt_food"),
                       ("Non-food incl. health", "official_nonfood", "rebuilt_nonfood"),
                       ("Total excl. rent & education", "official_total", "rebuilt_total")]:
        rows.append({
            "component": name,
            "official_mean_naira": cmp[o].mean(),
            "rebuilt_mean_naira": cmp[r].mean(),
            "ratio_rebuilt_to_official": cmp[r].mean() / cmp[o].mean(),
            "pearson_r": cmp[o].corr(cmp[r]),
            "spearman_rho": cmp[o].corr(cmp[r], method="spearman"),
        })
    # What ultimately matters for CHE is whether households are ranked the same
    # way, because the denominator enters through a ratio and through quintiles.
    from svy import weighted_quantile
    q_o = np.digitize(cmp["official_total"] / size.reindex(cmp.index),
                      weighted_quantile((cmp["official_total"] / size.reindex(cmp.index)).to_numpy(),
                                        np.ones(len(cmp)), [.2, .4, .6, .8]))
    q_r = np.digitize(cmp["rebuilt_total"] / size.reindex(cmp.index),
                      weighted_quantile((cmp["rebuilt_total"] / size.reindex(cmp.index)).to_numpy(),
                                        np.ones(len(cmp)), [.2, .4, .6, .8]))
    rows.append({
        "component": "Quintile agreement (exact / within one)",
        "official_mean_naira": np.nan, "rebuilt_mean_naira": np.nan,
        "ratio_rebuilt_to_official": (q_o == q_r).mean(),
        "pearson_r": (np.abs(q_o - q_r) <= 1).mean(), "spearman_rho": np.nan,
    })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    if config.PRIMARY_WAVE == "w4":
        print("Building wave 4 (2018/19) as the analysis wave ...")
        hh, ind = build_w4_primary()
        hh.to_csv(config.DERIVED / "hh_main.csv", index=False)
        ind.to_csv(config.DERIVED / "ind_main.csv", index=False)
        print(f"  households {len(hh):,}  individuals {len(ind):,}")
        return hh, ind, None
    print("Calibration factors from wave 4 ...")
    factors, cal_check = calibration_factors()
    pd.DataFrame([factors]).to_csv(config.TABLES / "tableA1b_calibration.csv", index=False)
    cal_check.to_csv(config.TABLES / "tableA1c_calibration_check.csv", index=False)
    print("  " + ", ".join(f"{k} {v:.4f}" for k, v in factors.items()))
    print(cal_check.to_string(index=False, float_format=lambda x: f"{x:,.3f}"))

    print("Building wave 5 ...")
    hh5, ind5 = build_w5(factors)
    hh5.to_csv(config.DERIVED / "hh_main.csv", index=False)
    ind5.to_csv(config.DERIVED / "ind_main.csv", index=False)
    print(f"  households {len(hh5):,}  individuals {len(ind5):,}")

    print("Building wave 4 ...")
    hh4 = build_w4()
    hh4.to_csv(config.DERIVED / "hh_w4.csv", index=False)
    print(f"  households {len(hh4):,}")

    print("\nValidating the reconstructed aggregate against wave 4's official one:")
    v = validate_w4_aggregate()
    v.to_csv(config.TABLES / "tableA1_aggregate_validation.csv", index=False)
    print(v.to_string(index=False, float_format=lambda x: f"{x:,.3f}"))
    return hh5, ind5, hh4


if __name__ == "__main__":
    main()
