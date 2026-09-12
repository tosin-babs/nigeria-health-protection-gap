# Measuring the Health-Protection Gap and Actuarially Pricing Informal-Sector Health Insurance under Nigeria's NHIA Act 2022: A Frequency–Severity and Ruin-Probability Approach

**Oluwatosin Dorcas Babalola**¹ *(corresponding author)*

¹ Department of Risk Management and Insurance, Robinson College of Business, Georgia State University, Atlanta, GA, USA. obabalola4@student.gsu.edu *[confirm department and postal address before submission]*

**Word count.** ~6,500 excluding abstract, tables and references.

---

## Abstract

**Background.** Nigeria's National Health Insurance Authority Act 2022 makes health insurance mandatory and creates a Vulnerable Group Fund, but the informal sector — the large majority of Nigerian workers — remains almost entirely uncovered. Catastrophic health expenditure has been measured repeatedly in Nigeria; no study has combined that measurement with an actuarial price for the coverage the Act promises, a solvency test of the pool that would provide it, and a counterfactual for how much protection it would buy.

**Methods.** Using the nationally representative General Household Survey-Panel wave 5 (2023/24; 4,685 households, 24,629 individuals, grossing to 40.6 million households and 211.4 million people), we estimate catastrophic health expenditure at 10%, 25% and 40% budget-share thresholds and at the 40% capacity-to-pay threshold, with full survey design and Erreygers-corrected concentration indices. We fit Poisson frequency, gamma severity and Tweedie compound Poisson–gamma models of annual health-care cost, map them onto a basic benefit package with coinsurance and induced demand, and build a premium from pure to gross. A collective-risk simulation estimates the probability of ruin for a state-level informal pool under alternative take-up, adverse-selection and subsidy scenarios.

**Results.** Catastrophic expenditure affects 16.7% of households at the 10% threshold (95% CI 14.9–18.4) and 11.3% at the 40% capacity-to-pay threshold (9.9–12.8); out-of-pocket payments push a further 2.4 percentage points, or 5.1 million people, below the national poverty line. The budget-share measure is distributionally uninformative (concentration index +0.045, ns) while the capacity-to-pay measure is sharply pro-poor (−0.185, 95% CI −0.248 to −0.121) and shows a significant informal-sector penalty (12.5% vs 6.6%, p<0.001). The actuarially fair premium for the basic package is ₦21,195 per person per year and the gross premium ₦26,912 — 26.5% of per-capita consumption in the poorest quintile and above the 5% affordability ceiling for four quintiles out of five. Against a contribution the target population could actually pay (₦8,571), a 20,000-life pool needs a subsidy of ₦16,482 per enrollee (61% of the gross premium) to hold the three-year ruin probability below 5% under random take-up, rising to ₦52,573 (195%) under strong adverse selection. Full, fully subsidised coverage of the informal sector would cut catastrophic expenditure from 16.7% to 5.2%; the same coverage financed by a flat member contribution would cut it only to 12.4%, and would *raise* capacity-to-pay catastrophic expenditure to 14.0%.

**Conclusions.** Nigeria's protection gap is real but smaller than recent outlier estimates suggest, and it is concentrated where the capacity-to-pay measure looks rather than where the budget-share measure looks. The price of closing it is not in doubt: coverage cannot be sold to informal workers at a price they can pay, so the Vulnerable Group Fund's size, not its existence, is the binding policy question. A flat community contribution is itself catastrophic for poor households and undoes most of the protection coverage is meant to deliver.

**Keywords.** catastrophic health expenditure; informal sector; health insurance pricing; Tweedie GLM; ruin probability; universal health coverage; Nigeria

---

## 1. Introduction

Nigerians pay for health care mostly out of their own pockets, at the moment they are ill. Out-of-pocket payments finance roughly seven in every ten naira of current health expenditure, one of the highest shares recorded anywhere `[VERIFY: WHO Global Health Expenditure Database, latest year]`. Because that spending is unpredictable and uninsured, an episode of illness is also a financial event, and for a substantial minority of households it is a ruinous one.

The National Health Insurance Authority Act 2022 was designed to change this. It makes health insurance mandatory, obliges every state to run a State Health Insurance Scheme, requires employers with five or more staff to enrol their workers, and creates a Vulnerable Group Fund to pay for those who cannot pay for themselves. Four years on, coverage estimates still range from about 2% to about 13% of the population depending on the source `[VERIFY]`, and the gap is concentrated in the informal sector, which accounts for the large majority of Nigerian employment `[VERIFY: NBS Labour Force Survey]`.

An earlier assessment of Nigeria's social-insurance architecture, on which the present author worked, concluded that the country's social-protection instruments were failing to reach informal workers and identified health costs as the largest uncovered exposure (Sogunro et al., n.d.). This paper takes that qualitative finding and puts a price on it.

There is a substantial Nigerian literature measuring catastrophic health expenditure. Aregbeshola and Khan (2018) put incidence at 16.4% in 2009/10; Opeloyeru and Lawanson (2023) analyse its determinants; a 2025 study reports 45.5% at the 10% threshold in post-pandemic data (doi:10.1007/s40609-025-00423-4) `[VERIFY authors]`. What none of this work does is take the next step. Measuring a gap does not tell a regulator what to charge, how large a pool must be to survive its own claims volatility, or how much of the gap coverage would actually close once the newly insured start using more care. Those are actuarial questions, and they are the questions a State Health Insurance Scheme has to answer before it can enrol anyone.

This paper answers them. It makes three contributions.

**First, a measurement contribution with a methodological edge.** We estimate catastrophic expenditure on nationally representative 2023/24 data with the full survey design, and we show that the choice between the budget-share and capacity-to-pay definitions is not a technicality: the two measures disagree about *who* is affected. The budget-share measure, which is the SDG 3.8.2 convention, produces a concentration index indistinguishable from zero — it identifies the households that spend a lot on health, which are disproportionately households that can afford to. The capacity-to-pay measure, which nets out subsistence needs, is strongly pro-poor and is the only one of the two that detects the informal-sector penalty. Monitoring frameworks that rely on the budget-share measure alone will not see the population this Act is meant to protect.

**Second, an actuarial contribution.** We fit frequency, severity and Tweedie models to individual annual health-care cost and build a transparent premium from observed spending through benefit exclusions, induced demand and coinsurance to a loaded gross premium, and we test it against published state-scheme contributions. To our knowledge this is the first published actuarial price for the NHIA basic package for informal-sector individuals.

**Third, a solvency and counterfactual contribution.** We embed the fitted cost distribution in a collective-risk model and ask what a state pool would need — in contribution income, subsidy and opening capital — to keep its probability of ruin below 1% and 5% over one and three years, under random and adverse take-up. We then run the coverage forward and recompute catastrophic expenditure, with induced demand included, so that the protection benefit is measured on the same footing as its cost.

The results reframe the policy problem. The binding constraint is not that Nigeria lacks a pricing methodology; it is that the actuarially fair price of the benefit package the Act promises is several times what its intended beneficiaries can pay, so the scheme is a public-finance question wearing an insurance costume. Quantifying that gap precisely — and showing what a flat community contribution does to the households it is supposed to protect — is what this paper adds.

The methods are deliberately general. Catastrophic-expenditure measurement, Tweedie cost modelling and ruin simulation are the same tools needed to study underinsured households in the United States, the individual-market risk pool, and Medicare's exposure to population ageing. This paper builds and validates that toolkit on a setting where the protection gap is largest.

## 2. Background

**Health financing in Nigeria.** Nigeria's health system is financed predominantly by households. Public spending on health has remained a small share of government expenditure, well below the 15% Abuja commitment `[CITE]`, and the resulting reliance on direct payments is the mechanism through which illness translates into impoverishment. The Basic Health Care Provision Fund, established under the National Health Act 2014, was the first substantial attempt to create a pooled, tax-financed stream for primary care.

**The NHIA Act 2022.** Signed in May 2022, the Act replaced the National Health Insurance Scheme with an Authority and changed the legal architecture in four ways that matter here. Coverage became mandatory rather than voluntary. Every state was required to establish a State Health Insurance Scheme, making the state, not the federation, the operative risk-bearing unit. Employers with five or more staff were obliged to enrol their workers — a threshold we use directly in our definition of formal-sector employment. And the Act created the Vulnerable Group Fund, financed in part by the Basic Health Care Provision Fund and a health-insurance levy, to subsidise those who cannot contribute. The Act also recognises Mutual Health Associations and third-party administrators, which is the legal space an informal-sector pool would occupy.

The Act is therefore explicit that some enrollees will be subsidised. It is not explicit about how much subsidy, for how many people, or on what actuarial basis — which is the gap this paper fills.

**State schemes.** Several states have launched schemes with published contribution rates for informal-sector members; Lagos State's LASHMA "Ilera Eko" plan is the most visible `[VERIFY current amounts]`. These rates are set administratively rather than actuarially, and comparing them with a modelled premium is one of the external validity checks we report.

**Prior evidence on catastrophic expenditure.** International measurement rests on two traditions. The budget-share approach flags a household when health spending exceeds a fixed share of total consumption; it underpins SDG indicator 3.8.2 at 10% and 25% thresholds (Wagstaff et al. 2018). The capacity-to-pay approach of Xu et al. (2003) instead compares health spending with consumption net of subsistence needs, on the reasoning that a household spending most of its budget on food has almost no capacity to absorb a medical bill. Cylus et al. (2018) show the two can give materially different pictures of who is affected in Europe; our results show the same for Nigeria, in a stronger form.

For Nigeria specifically, published estimates at the 10% threshold span a wide range, from 16.4% for 2009/10 (Aregbeshola and Khan 2018) to 45.5% for 2023/24 in one recent study. That spread is too large to be a real change over time, and is more plausibly explained by differences in the instrument used to measure out-of-pocket spending and in the consumption denominator. We return to this in the discussion, because our own estimate falls squarely in the lower part of the range and the reason matters for anyone using these numbers.

## 3. Data

**Source.** The analysis uses the Nigeria General Household Survey-Panel (GHS-Panel), collected by the National Bureau of Statistics with the World Bank's LSMS-ISA programme. Wave 5 (2023/24) is the main analysis file; wave 4 (2018/19) provides a trend comparison. We use the post-planting visit, which carries the health, labour and consumption modules, and the post-harvest education module.

**Sample and weights.** After dropping households without a cross-sectional weight, the analysis file contains 4,685 households and 24,629 individuals. Wave 5 releases three weights; we use `wt_cross_wave5`, the cross-sectional weight, which grosses up to 40.6 million households and 211.4 million people, matching Nigeria's population. The two panel weights gross to 27.0 and 29.7 million households respectively and would understate national totals by a third. Estimation treats enumeration areas as primary sampling units and the released six-level stratum variable as strata; population-level rates weight households by household size, following the WHO convention for SDG 3.8.2.

**Out-of-pocket spending.** Wave 5 offers two instruments and they do not agree. The non-food consumption module asks one household-level question about health spending over twelve months; only 17% of households report any, implying an out-of-pocket share of 0.3% of consumption. The health module asks every household member whether they sought care in the past four weeks, where, and what they paid — separating the fee at the place of care, medicines and treatment, other costs such as tests, and transport — and asks separately about hospitalisation and its cost over twelve months. It yields an out-of-pocket share of 6.0%, consistent with the 5.4% recorded in wave 4's published consumption aggregate and with national health-accounts evidence. We therefore use the health module, and report the consumption-module figure as a data-quality note (Table 8). Following WHO practice, out-of-pocket spending is defined as direct payments to providers and pharmacies and excludes transport; including transport is a robustness check. Insurance premiums are prepayment, not out-of-pocket spending, and are tracked separately.

The CSV release ships without a codebook, so the cost fields were identified from their response patterns across facility types — consultation fees are zero at most chemist shops but positive at hospitals, medicine spending is near-universal among those who sought care — and are marked for verification against the questionnaire before submission.

**Consumption.** Wave 5 publishes no consumption aggregate, so one is constructed from the food module (seven-day recall, with own production and gifts valued at the median unit value implied by other households' purchases of the same item in the same unit and size, taken from the finest geography with support), the three non-food modules (seven-day, thirty-day and twelve-month recalls, annualised), and the education module. Health spending enters the total once, from the health module.

Because the reconstruction involves judgement, we validate it. The identical code is run on wave 4, where the World Bank publishes an aggregate (`totcons_final.csv`), and the two are compared (Table A1). The reconstruction recovers 87% of the official level, with a Spearman rank correlation of 0.80 and 92% of households placed within one quintile of their official position. Consumption *levels* from wave 5 should therefore be treated as approximate; the ratios and rankings that catastrophic-expenditure measurement depends on are reliable. This matters most for the poverty headcount, which is a level, and least for the impoverishment *effect*, which is a difference — Table 8c shows the effect is stable across a wide grid of poverty lines while the headcount is not.

**Informal-sector definition.** A worker is classified formal when the employer is a public body, state-owned enterprise, NGO or international organisation, or a private firm with five or more staff — the threshold at which section 14 of the NHIA Act obliges enrolment. Everyone else in work is informal, and a household is informal if it contains no formal worker. On this rule 81.2% of households are informal (80.0% of the population). Three alternatives (public-sector employees only; any wage employee; the household head's status alone) are tested in Table 8.

**Limitations.** Recall periods differ between outpatient and inpatient care, and annualising a four-week window by 13 assumes care-seeking is not bunched within the year; robustness tests damped multipliers of 10 and 6. Households that forgo care report zero out-of-pocket spending, so catastrophic-expenditure measures understate unmet need. Wave 5 fieldwork spans a period of very high inflation; all wave-4 comparisons are deflated to the wave-5 price base, and the deflator is a single composite CPI ratio that should be re-verified. Imputed housing rent is not in the reconstructed aggregate, which is part of why it sits below the official wave-4 level.

## 4. Methods

### 4.1 Notation

Let *h* index households and *i* individuals. OOP*ₕ* is annual out-of-pocket health spending, C*ₕ* total annual consumption, SE*ₕ* subsistence spending, and τ a catastrophic-expenditure threshold. For the cost models, *N* is the number of care episodes in a year, *X* the cost per episode, and *S* = *X*₁ + … + *X_N* the annual aggregate cost per person. π denotes a premium, π₀ = E[*S*] the pure premium, ψ(*u*) the probability of ruin from initial capital *u*, and *s* the subsidy per enrollee.

### 4.2 Catastrophic expenditure

Under the budget-share definition, CHE*ₕ*(τ) = 1 if OOP*ₕ*/C*ₕ* > τ, evaluated at τ = 10%, 25% and 40%. Under the capacity-to-pay definition (Xu et al. 2003), household size is equivalised as hhsize^0.56; subsistence spending per equivalent adult is the weighted mean food spending of households whose food share falls between the 45th and 55th percentiles; capacity to pay is C*ₕ* − SE*ₕ*, or C*ₕ* − food spending where that is smaller; and a household is catastrophic if OOP*ₕ* exceeds 40% of it.

Intensity is measured by the overshoot O*ₕ* = max(OOP*ₕ*/C*ₕ* − τ, 0), reported as a mean over all households and as a mean over affected households only (Wagstaff and van Doorslaer 2003). Impoverishment compares the poverty headcount using consumption gross and net of out-of-pocket payments, against the 2019 national line of ₦137,430 per person per year carried forward to the wave-5 price base, and is reported alongside the normalised poverty gap.

Inequality is summarised by the concentration index, computed from the convenient covariance identity CI = 2·cov*w*(*y*, *r*)/mean*w*(*y*) where *r* is the weighted fractional rank in per-capita consumption. For binary outcomes we report the Erreygers (2009) correction, E = 4·mean(*y*)·CI, which restores the [−1, 1] bounds the raw index loses when the mean is far from a half. Standard errors are design-based, obtained by linearising the index as a smooth function of totals. A linear Wagstaff-style decomposition attributes the index to observable characteristics; it is descriptive, not causal.

**Variance estimation.** All standard errors are Taylor-linearised for a stratified single-stage cluster design, with singleton strata centred on the grand mean. Domain estimates zero the weights outside the domain rather than dropping rows, so that the randomness in the number of sampled clusters within a domain is preserved. The implementation is in `python/svy.py` and reproduces the estimators in Lumley (2004).

### 4.3 Cost models

The unit is the individual-year. Three models are fitted, survey-weighted, with standard errors clustered on the enumeration area.

*Frequency.* The survey records whether a person had contact with a provider within a four-week window, not how many times. Modelling that indicator as a count with an offset of log(4/52) converts the fitted values into annual contact rates. Overdispersion is tested by regressing the squared Pearson residual on the fitted mean, and a negative binomial alternative is fitted. Inpatient episodes are modelled over a twelve-month window with no offset.

*Severity.* Cost per outpatient episode and per inpatient episode is modelled with gamma and lognormal GLMs with a log link, compared by AIC on a common scale. The inpatient severity model uses a leaner specification because the episode count is small.

*Aggregate cost.* Annual cost per person is modelled with a Tweedie compound Poisson–gamma GLM with a log link, which accommodates the point mass at zero and the right skew in a single model. The variance power *p* is chosen by profile likelihood over a grid from 1.20 to 1.85. Covariates throughout are age band, sex, zone, urban/rural, consumption quintile, an indicator of severe functional difficulty from the Washington Group short set, and household size.

Diagnostics are randomised quantile residuals (Dunn and Smyth 1996), which are standard normal under a correct model, and an observed-versus-predicted lift table by decile of prediction.

### 4.4 Benefit mapping and the premium

The NHIA tariff schedule is not public in machine-readable form, so the benefit package is defined transparently by parameters, each of which is a robustness knob. Traditional and spiritual care is excluded entirely. Of remaining spending, 85% of outpatient and 90% of inpatient costs are assumed to fall inside the basic package. Covered outpatient spending is split into drugs, which carry the NHIA's 10% co-payment, and services, which are free at the point of use.

Induced demand is applied with an arc (midpoint) elasticity, so the answer does not depend on which price is treated as the base. The point-of-service price falls from 1.0 (uninsured) to the coinsurance rate for drugs and to zero for services; at the RAND Health Insurance Experiment's central elasticity of −0.20 (Manning et al. 1987) this raises drug utilisation by 32.7% and service utilisation by 40.0%. Elasticities of −0.10 and −0.35 are tested.

The insurer's expected cost per enrollee is the pure premium. Two risk-margin conventions are reported: the standard-deviation principle, θ·σ/√*n*, and a CVaR margin at the 95% level obtained by simulating the pool mean. Both shrink with pool size, which is the actuarial argument for scale. The gross premium adds an administrative load of 15% and an explicit adverse-selection load of 10%. Affordability is assessed against a ceiling of 5% of per-capita consumption.

### 4.5 Pool solvency

A discrete-time collective-risk model tracks the surplus of a pool of *n* enrollees:

  *U_t* = *U_{t−1}* + *n*·(*C* + *s*)·(1 − *e*) − *S_t*

where *C* is the member contribution, *s* the subsidy per enrollee, *e* the expense ratio (10%), and *S_t* the pool's aggregate claims in year *t*. Ruin occurs if *U_t* < 0 at any *t* up to the horizon (one and three years). Aggregate claims are drawn by resampling individual annual insurer costs from the informal-sector population with survey weights.

Because the question the paper asks is what subsidy is needed given what people can pay, the member contribution is fixed at the affordability ceiling for informal households in the bottom three quintiles, and the subsidy is swept from zero to three times the gross premium. The minimum subsidy achieving a target ruin probability is found by bisection on a fixed set of simulated claim paths, so that every financing scenario faces the same simulated experience.

Take-up is modelled three ways: random, and adverse selection in which enrolment odds rise by a factor of 1.5 or 2.0 per standard deviation of predicted log cost. A one-off 25% medical-inflation shock is tested as a stress scenario. Ten thousand simulations are run per configuration with a fixed seed, and Monte Carlo standard errors are reported.

*Computational note.* Simulating a 100,000-life pool ten thousand times over three years is three billion individual draws if done naively. Instead the empirical cost distribution is collapsed to its 703 distinct values and each pool-year is drawn as a single multinomial over that support. This is exact rather than approximate, and Table A4 confirms it against direct resampling (mean within 0.04%, 99th percentile within 0.5%).

### 4.6 Coverage counterfactual

Covered individuals pay the co-payment on covered drugs plus the full cost of anything outside the package, on the higher utilisation that induced demand implies; uncovered individuals keep their observed spending. Total consumption is held fixed except for the change in health payments: money no longer spent on care is spent on something else, and any member contribution is a new call on the same budget. Catastrophic expenditure is then recomputed.

Results are reported on two bases: out-of-pocket payments alone, which is the SDG 3.8.2 convention, and out-of-pocket payments plus the member contribution, which is what a household actually pays. The distinction turns out to matter more than any other modelling choice in the paper.

## 5. Results

### 5.1 Sample and the scale of out-of-pocket payment (RQ1)

Table 1 describes the weighted sample. Mean household size is 5.2, mean annual household consumption ₦1.73 million, and out-of-pocket health payments average 5.6% of consumption. Just over a fifth of individuals had contact with a provider in the four weeks before interview and 3.0% had been hospitalised in the preceding year. Only 0.20% of households reported paying a health-insurance premium — an independent confirmation, from the consumption module, of how little of the population the current system reaches. **81.2% of households contain no formal-sector worker** (80.0% of the population). Informal-sector households are poorer (per-capita consumption ₦451,633 vs ₦536,250, p<0.001), more rural (34.3% vs 60.1% urban, p<0.001), more likely to be female-headed (22.7% vs 11.4%, p<0.001) and more likely to contain someone with a severe functional difficulty (10.5% vs 6.7%, p<0.001).

Household-level characteristics in Table 1 are weighted by the household weight; the catastrophic-expenditure rates that follow use the population weight (household weight × household size), following the WHO convention for SDG 3.8.2.

**Catastrophic expenditure.** Table 2 reports incidence and intensity at every threshold, overall and by sector, quintile, zone and urban/rural; Figure 1 plots the quintile gradient. 16.7% of households (95% CI 14.9–18.4) spend more than 10% of consumption on health, 4.6% (3.6–5.7) more than 25%, and 1.1% (0.7–1.6) more than 40%. Under the capacity-to-pay definition, 11.3% (9.9–12.8) exceed the 40% threshold. Intensity is substantial: among affected households the mean overshoot is 11.2 percentage points at the 10% budget-share threshold and 20.3 percentage points at the capacity-to-pay threshold — households that cross the line do not cross it narrowly.

Out-of-pocket payments raise the poverty headcount from 76.8% to 79.2% (Table 2b), an impoverishment effect of 2.4 percentage points, or **5.1 million people**, and widen the normalised poverty gap by 2.3 points. The headcount *levels* are higher than official poverty statistics, for the reasons set out in Section 3; Table 8c shows the impoverishment effect ranges only between 1.2 and 3.5 percentage points across poverty lines from half to one and a half times the national line, so the finding does not depend on where the line is drawn.

### 5.2 The two definitions disagree about who is affected

This is the measurement result that matters most. Table 3 reports the concentration indices and Table 3b decomposes them. The concentration index for budget-share catastrophic expenditure at 10% is +0.045 (95% CI −0.007 to +0.097) — statistically indistinguishable from zero and, if anything, pro-rich. The concentration index for capacity-to-pay catastrophic expenditure is **−0.185 (95% CI −0.248 to −0.121)**, strongly and significantly pro-poor. The Erreygers-corrected values are +0.030 and −0.084 respectively. Figure 6 shows why the indices differ: the budget-share concentration curve tracks the line of equality almost exactly, while the capacity-to-pay curve bows clearly above it across the whole distribution.

The same divergence appears in the sector comparison (Table 2c). On the budget-share measure, informal-sector households are no more likely to face catastrophic spending than formal-sector households (16.7% vs 16.4%, p = 0.89). On the capacity-to-pay measure they are nearly twice as likely: **12.5% vs 6.6%, a gap of 6.0 percentage points (p < 0.001)**.

The reason is mechanical but consequential. The budget-share measure divides by total consumption, and rich households both consume more and buy more health care, so the ratio does not sort households by hardship. The capacity-to-pay measure divides by consumption net of subsistence, which is close to zero for poor households, so the same naira of medical spending registers as a much larger shock. Hypothesis H1 — that incidence would exceed 40% and be concentrated among the poor and informal — is therefore only half supported: incidence is well below 40%, and concentration among the poor and informal appears only under the capacity-to-pay definition.

### 5.3 Cost models (RQ2)

Individuals average 2.75 outpatient contacts and 0.030 inpatient episodes per year. Mean cost is ₦6,977 per outpatient episode and ₦43,985 per inpatient episode, giving a mean annual cost of **₦19,675 per person**, with 78% of individuals recording no cost at all.

Table 4 reports the three fitted models and Table 4b their fit statistics. The frequency model shows a Pearson dispersion of 0.775 — under- rather than overdispersion, which is expected when a binary contact indicator is modelled as a count, and means the negative binomial adds nothing. For severity, the lognormal fits better than the gamma (AIC 95,274 vs 98,072), consistent with the heavy right tail of Nigerian medical bills.

The profile likelihood (Table A2) selects a Tweedie variance power of **p = 1.60** (Figure 5), comfortably inside the compound Poisson–gamma range and toward the gamma end, again reflecting a skewed severity distribution. Calibration is good: across deciles of predicted cost the observed-to-predicted ratio stays between 0.85 and 1.13, and the model separates a bottom decile averaging ₦2,961 from a top decile averaging ₦83,153, a lift of 4.2 (Table A3, Figure 5). Randomised quantile residuals have mean 0.09, standard deviation 1.00 and skew −0.14; the formal normality test rejects, as it will at *n* = 24,629, but the shape is close to the model's prediction.

Risk relativities (Table 5e) are large. Relative to the community average, people aged 60 or over cost 3.31 times as much, and those with a severe functional difficulty 6.41 times. Costs rise steeply with consumption quintile (0.26 in Q1 to 2.60 in Q5) — a demand effect, not a morbidity effect, and a reminder that observed spending understates the health needs of the poor.

### 5.4 The premium, and what it costs relative to what people have

Table 5a and Figure 7 trace the build-up. Observed out-of-pocket cost of ₦19,675 per person-year falls to ₦19,320 once traditional and spiritual care is excluded and to ₦16,487 once services outside the basic package are removed. Induced demand then adds ₦5,927 — a **35.9% increase** — taking covered cost to ₦22,414, and the member's drug co-payment returns ₦1,219, leaving a **pure premium of ₦21,195**. Figure 7 sets the whole build-up against the affordability ceiling: every stage of it, including the raw observed spending the package is priced from, sits far above what the target population can pay.

Loadings take the gross premium to **₦26,912 per person per year** for a 20,000-life pool on the standard-deviation risk margin (₦28,885 on the CVaR basis; Tables 5b and 5c). The risk margin itself is small and shrinks quickly with scale — ₦159 at 5,000 lives, ₦36 at 100,000 — because idiosyncratic claims risk diversifies away; administration and adverse selection, not volatility, are what make the gross premium exceed the pure premium.

Affordability is where the analysis turns (Table 5d, Figure 4). Measured against per-capita consumption, the gross premium is **26.5% in the poorest quintile**, 15.5% in Q2, 11.1% in Q3, 7.5% in Q4 and 3.4% in Q5. It exceeds the 5% affordability ceiling for four quintiles out of five. Hypothesis H2 — that the loaded premium would exceed 5% of consumption for the bottom two quintiles — is confirmed, and comfortably: the true reach of the problem is the bottom four. At the household level the premium for an average household in Q1 would be **₦218,924** a year. Two household sizes matter here and they answer different questions: the average household in the poorest quintile contains 8.1 people, while the average *person* in that quintile lives in a household of 10.0. Quintiles are ranked on per-capita consumption, so large households sort into the bottom of the distribution almost mechanically — which is itself part of why a per-person premium bears so heavily on them.

The modelled premium is roughly two-thirds of Lagos LASHMA's published individual informal-sector rate of ₦40,000 `[VERIFY]` (Table 5f), which is reassuring for the model: an administratively set rate somewhat above the actuarial price is what one would expect from a scheme that must be conservative and that covers a self-selected population.

### 5.5 Pool solvency (RQ3)

Five percent of per-capita consumption for informal households in the bottom three quintiles is **₦8,571 per person per year** (Table 6a). That is what the target population can pay. The gross premium is ₦26,912. The gap is the policy problem, and the subsidy has to close it.

Adverse selection makes it much worse. Tilting enrolment toward higher predicted cost raises expected claims per enrollee from ₦21,084 to ₦35,692 under moderate selection (**+69%**) and ₦52,506 under strong selection (**+149%**).

Table 6c gives the minimum subsidy. For a 20,000-life pool over three years with no opening capital:

| Take-up | Subsidy for ψ < 5% | As % of gross premium | Subsidy for ψ < 1% |
|---|---|---|---|
| Random | ₦16,482 | 61% | ₦17,143 |
| Moderate adverse selection | ₦33,339 | 124% | ₦34,199 |
| Strong adverse selection | ₦52,573 | 195% | ₦53,647 |

Table 6b gives the full grid of ruin probabilities behind it. Three features stand out. First, the subsidy required is large in every scenario: even with random take-up the state must find roughly ₦1.6 billion a year per 100,000 enrollees. Second, moving the ruin target from 5% to 1% costs very little — ₦661 per enrollee under random take-up — because the pool mean is tightly distributed once *n* is in the tens of thousands; capital and prudence are cheap, and adverse selection is expensive. Third, pool size helps but not enough: going from 5,000 to 100,000 lives cuts the required subsidy under random take-up from ₦18,231 to ₦15,568, a 15% saving, while a shift from random to strong adverse selection roughly triples it. **The dominant solvency risk is who enrols, not how many** (Figure 2).

A one-off 25% medical-inflation shock (Table 6d) raises the required subsidy from ₦16,482 to ₦22,375 under random take-up and from ₦52,573 to ₦67,619 under strong selection — a material but second-order effect next to selection.

Hypothesis H3 is supported: without subsidy, a voluntary pool charging what its members can afford is insolvent with near-certainty, and the subsidy that restores solvency is quantifiable and large.

### 5.6 How much protection would coverage buy? (RQ4)

Table 7 and Figure 3 give the counterfactual, and the answer depends entirely on who pays the contribution.

Table 7a reports every scenario on both payment bases, Table 7b the reductions and their significance, and Table 7c the results by quintile. Measured on out-of-pocket payments alone, coverage works as advertised. Full coverage of the informal sector cuts catastrophic expenditure at the 10% threshold from 16.7% to **4.9%**, and universal coverage cuts it to 1.7%. Capacity-to-pay catastrophic expenditure falls from 11.3% to 2.1%.

Measured on total household health payments — out-of-pocket plus the ₦8,571 member contribution — the picture changes sharply. Full coverage of the informal sector cuts catastrophic expenditure only to **12.4%**, and capacity-to-pay catastrophic expenditure **rises**, from 11.3% to 14.0%. A flat contribution that is affordable on average is catastrophic for the households at the bottom of the distribution, and it lands on them every year rather than only in years they fall ill.

Full coverage financed entirely by subsidy is what delivers the protection: catastrophic expenditure falls to **5.2% at the 10% threshold (a 69% reduction, p < 0.001)** and to 3.3% on the capacity-to-pay measure (a 71% reduction). Subsidising only the vulnerable group — the bottom two quintiles of informal households, 35% of the population — achieves a 27% reduction at the 10% threshold and a 37% reduction on the capacity-to-pay measure, at a fraction of the cost.

Hypothesis H4 — that coverage reduces catastrophic expenditure substantially but by less than naive estimates once induced demand is included — is supported, and the mechanism is sharper than anticipated: induced demand costs about 12 percentage points of the naive reduction, but the financing of the contribution costs far more than that.

### 5.7 Robustness

Table 8 reports 25 variants. The headline conclusions are stable under every change that is a genuine analytic choice, and move only under changes that alter what is being measured.

Equivalence-scale variants (0.5 to 1.0) move capacity-to-pay incidence by less than 0.3 percentage points. Alternative informal-sector definitions change the required subsidy by under 5%. Fixing the Tweedie variance power at 1.4, 1.5 or 1.7, refitting the model each time, changes nothing material. Including transport raises catastrophic-expenditure incidence from 16.7% to 17.8% and the gross premium by 7%.

The annualiser matters, as expected: damping the four-week outpatient window from 13× to 10× lowers incidence from 16.7% to 13.1% and the gross premium from ₦26,912 to ₦21,186, and 6× lowers them to 7.3% and ₦13,551. This is the single most consequential measurement assumption in the paper and it should be read as a genuine uncertainty band rather than a sensitivity footnote.

Trimming the top 1% of costs lowers the gross premium by 20% and the required subsidy by 37%. We keep the tail in the main results: for a pricing and solvency exercise, the tail *is* the risk.

Benefit-design parameters behave monotonically and sensibly. Widening outpatient coverage from 70% to 100% raises the gross premium from ₦22,533 to ₦31,292; raising the drug co-payment from 0% to 20% lowers it from ₦29,308 to ₦24,799; the elasticity range from −0.10 to −0.35 spans gross premiums of ₦23,340 to ₦32,270.

Wave 4 (2018/19) gives catastrophic expenditure of 14.2% at the 10% threshold, 2.5% at 25% and 6.7% on the capacity-to-pay measure, against 16.7%, 4.6% and 11.3% in wave 5 (Table 8b). The comparison suggests a real deterioration, most pronounced on the capacity-to-pay measure, which is what one would expect during a period when food prices rose faster than incomes. It should be read with care: the two waves use different instruments for out-of-pocket spending, and the wave-5 denominator is reconstructed.

## 6. Discussion

**What the numbers mean for the NHIA and state schemes.** Three figures are directly usable. The actuarially fair premium for the basic package is about **₦21,000 per person per year** and the gross premium about **₦27,000**, in 2023/24 prices, for a community-rated informal-sector pool. The affordability ceiling for the population the Vulnerable Group Fund is meant to reach is about **₦8,600**. The gap — roughly **₦16,500 to ₦18,000 per enrollee per year under random take-up, and two to three times that if enrolment is adversely selected** — is the subsidy a state scheme needs. For a state enrolling 100,000 informal-sector members, that is ₦1.6 to ₦5.3 billion a year.

These are large numbers, and they are the point. The NHIA Act's mandate is not self-financing for the population it most needs to reach. Debating contribution rates for informal workers is, on this evidence, largely beside the point; the operative question is the size and reliability of the Vulnerable Group Fund.

**Design implications.** Two findings bear directly on scheme design. First, the dominant solvency risk is selection, not scale. A state scheme that enrols voluntarily, one household at a time, will attract the sick; the same scheme enrolling whole groups — cooperatives, market associations, transport unions, which is precisely what the Act's recognition of Mutual Health Associations enables — faces a required subsidy roughly a third as large. Group enrolment is worth more to solvency than tripling the pool.

Second, a flat community contribution undermines the protection it finances. Our counterfactual shows capacity-to-pay catastrophic expenditure *rising* when coverage is paid for by a uniform ₦8,571 contribution, because a flat payment is regressive against a distribution in which the poorest quintile's per-capita consumption is ₦101,550. If contributions are to be charged at all, they should be graduated, and the bottom two quintiles should be fully subsidised — which is close to what the Act's vulnerable-group provisions envisage, and our results quantify what that provision is worth: a 27% reduction in catastrophic expenditure at the 10% threshold and 37% on the capacity-to-pay measure.

**On measurement.** Our estimate of 16.7% at the 10% threshold is close to Aregbeshola and Khan's 16.4% for 2009/10 and well below the 45.5% reported recently for post-pandemic data. We do not think the difference is a real change. Our own robustness table shows that the annualisation of a four-week recall window alone moves the estimate between 7.3% and 16.7%, and the choice of instrument for out-of-pocket spending moves it between 0.1% and 16.7%. Estimates of catastrophic expenditure in Nigeria are dominated by measurement choices, and papers reporting them should publish the full sensitivity rather than a single headline. This is not a minor methodological point: SDG 3.8.2 monitoring, and any subsidy calculation built on it, inherits that fragility.

The stronger and more portable finding is the divergence between definitions. A monitoring framework using the budget-share measure alone would conclude that informal-sector households in Nigeria face no more financial hardship from health care than formal-sector households. The capacity-to-pay measure shows they face nearly twice as much. Where a country's poor spend most of their budget on subsistence, the budget-share measure is close to uninformative about hardship, and both should be reported.

**Transferability, including to the United States.** The framework — measure the gap on capacity-to-pay as well as budget-share terms, fit a Tweedie cost model, price the benefit with induced demand, and test the pool's solvency under adverse selection — is not Nigeria-specific. It applies wherever coverage is being extended to workers outside standard employment: community-based schemes across sub-Saharan Africa, Indonesia's and the Philippines' informal-sector segments, and, in a different institutional dress, the United States. Roughly the same structural problem appears in the US individual market, where gig and self-employed workers buy coverage voluntarily, selection is the dominant pricing risk, and subsidy design determines both take-up and pool stability. The finding that a flat contribution can raise measured financial hardship among low-income enrollees has a direct analogue in debates over deductibles and premium contributions in subsidised US coverage. The measurement and modelling toolkit built here is the one applied to US data in the next paper of this programme.

**Limitations.** The counterfactual is an accounting simulation, not a causal estimate; it holds total consumption fixed, applies a single elasticity from a US experiment conducted four decades ago, and assumes the benefit package is delivered as specified. The benefit-package parameters are assumptions, not the NHIA's published schedule, and should be replaced when that schedule becomes available. Out-of-pocket spending is measured from a four-week window for outpatient care, and the annualiser is the paper's largest single uncertainty. The consumption denominator is reconstructed and recovers 87% of wave 4's published aggregate, so consumption levels — and therefore poverty headcounts — should be treated as approximate. Households that forgo care entirely appear as zero spenders, so all catastrophic-expenditure measures understate unmet need; the 149% claims uplift we find under strong adverse selection is a modelled scenario, not an observed take-up pattern. Finally, wave 5 offers no direct measure of insurance status usable for a coverage analysis, so the counterfactual assigns coverage rather than observing it.

## 7. Conclusion

Catastrophic health expenditure affects 16.7% of Nigerian households at the 10% budget-share threshold and 11.3% at the 40% capacity-to-pay threshold, and out-of-pocket payments push 5.1 million people below the national poverty line each year; the burden falls on poor and informal-sector households, but only the capacity-to-pay measure detects it. The actuarially fair premium for the NHIA basic package is ₦21,195 per person per year and the gross premium ₦26,912, against an affordability ceiling of ₦8,571 for the population the Act intends to protect. A state pool charging what its members can afford needs a subsidy of ₦16,482 per enrollee to hold its three-year ruin probability below 5% under random take-up, and ₦52,573 under strong adverse selection.

Closing Nigeria's health-protection gap is affordable only as public expenditure, not as insurance sold to informal workers; the policy choice is how large the Vulnerable Group Fund must be, and how enrolment is organised so that selection does not multiply its cost.

---

## Declarations

**Data availability.** The GHS-Panel microdata are publicly available from the World Bank Microdata Library subject to registration and are not redistributed. All analysis code is available at https://github.com/tosin-babs/nigeria-health-protection-gap and will be archived with a Zenodo DOI on submission. An interactive calculator that reruns the pricing and solvency model in the browser is available at https://nigeria-health-protection-gap.vercel.app.

**Code availability.** Complete, seeded reproduction code in Python at https://github.com/tosin-babs/nigeria-health-protection-gap; see the repository README for the script order and environment.

**Funding.** *[to be completed]*

**Competing interests.** None declared.

**Ethics.** The analysis uses de-identified secondary survey data and did not require ethical approval.

**AI-assistance disclosure.** Generative AI (Claude, Anthropic) was used to assist with code development, code review and language editing. The author designed the study, specified all models and parameters, verified and interpreted all results, and takes full responsibility for the content. AI systems are not authors and are not listed as such.

**CRediT statement.** **Oluwatosin Dorcas Babalola**: conceptualisation, methodology, software, formal analysis, data curation, writing — original draft, writing — review and editing.

---

## References

1. Aregbeshola, B. S., & Khan, S. M. (2018). Out-of-pocket payments, catastrophic health expenditure and poverty among households in Nigeria 2010. *International Journal of Health Policy and Management*, 7(9), 798–806. `[VERIFY DOI]`
2. Cylus, J., Thomson, S., & Evetovits, T. (2018). Catastrophic health spending in Europe: equity and policy implications of different calculation methods. *Bulletin of the World Health Organization*, 96(9), 599–609. doi:10.2471/BLT.18.209031
3. Dunn, P. K., & Smyth, G. K. (1996). Randomized quantile residuals. *Journal of Computational and Graphical Statistics*, 5(3), 236–244. doi:10.1080/10618600.1996.10474708
4. Dunn, P. K., & Smyth, G. K. (2005). Series evaluation of Tweedie exponential dispersion model densities. *Statistics and Computing*, 15, 267–280. doi:10.1007/s11222-005-4070-y
5. Erreygers, G. (2009). Correcting the concentration index. *Journal of Health Economics*, 28(2), 504–515. doi:10.1016/j.jhealeco.2008.02.003
6. Federal Republic of Nigeria (2022). *National Health Insurance Authority Act, 2022*. Available at nhia.gov.ng.
7. Klugman, S. A., Panjer, H. H., & Willmot, G. E. (2019). *Loss Models: From Data to Decisions* (5th ed.). Wiley. ISBN 978-1-119-52378-9
8. Lumley, T. (2004). Analysis of complex survey samples. *Journal of Statistical Software*, 9(8). doi:10.18637/jss.v009.i08
9. Manning, W. G., Newhouse, J. P., Duan, N., Keeler, E. B., Leibowitz, A., & Marquis, M. S. (1987). Health insurance and the demand for medical care: evidence from a randomized experiment. *American Economic Review*, 77(3), 251–277.
10. O'Donnell, O., van Doorslaer, E., Wagstaff, A., & Lindelow, M. (2008). *Analyzing Health Equity Using Household Survey Data*. Washington, DC: World Bank. ISBN 978-0-8213-6933-3
11. Opeloyeru, O. S., & Lawanson, A. O. (2023). Determinants of catastrophic household health expenditure in Nigeria. *International Journal of Social Economics*, 50(6), 876–892. doi:10.1108/IJSE-02-2022-0132
12. Smyth, G. K., & Jørgensen, B. (2002). Fitting Tweedie's compound Poisson model to insurance claims data: dispersion modelling. *ASTIN Bulletin*, 32(1), 143–157. doi:10.2143/AST.32.1.1020
13. Sogunro, A. B., Olaniyan, S. M., Udobi-Owolaja, P. I., & Babalola, O. D. (n.d.). An assessment of social insurance as a strategy for enhancing social protection effectiveness in Nigeria. *Global Journal of Accounting*, 8(2), 1–15. (Includes the present author; cited once as formative work.) `[VERIFY year, pagination and the published form of the author's name]`
14. Wagstaff, A., & van Doorslaer, E. (2003). Catastrophe and impoverishment in paying for health care: with applications to Vietnam 1993–1998. *Health Economics*, 12(11), 921–934. doi:10.1002/hec.776
15. Wagstaff, A., Flores, G., Hsu, J., et al. (2018). Progress on catastrophic health spending in 133 countries: a retrospective observational study. *The Lancet Global Health*, 6(2), e169–e179. doi:10.1016/S2214-109X(17)30429-1
16. WHO & World Bank (2023). *Tracking Universal Health Coverage: 2023 Global Monitoring Report*. Geneva: WHO. ISBN 978-92-4-008037-9
17. Xu, K., Evans, D. B., Kawabata, K., Zeramdini, R., Klavus, J., & Murray, C. J. L. (2003). Household catastrophic health expenditure: a multicountry analysis. *The Lancet*, 362(9378), 111–117. doi:10.1016/S0140-6736(03)13861-5
18. *[Authors]* (2025). The burden and socioeconomic inequality in catastrophic out-of-pocket health expenditure in post-pandemic Nigeria. *Global Social Welfare*. doi:10.1007/s40609-025-00423-4 `[VERIFY authors]`

*Sources marked `[VERIFY]` or `[CITE]` must be confirmed on Crossref or the publisher site before submission. Three claims in Sections 1–3 — the WHO out-of-pocket share, the national insurance-coverage range, and the informal-employment rate — are placeholders pending verification against the primary source.*
