# Customer Churn Analysis — Technical Appendix

*Optional reading. The executive summary stands alone; this document exists so the data team can verify, reproduce, or extend the analysis.*

**Analysis owner:** Data Team | **Last updated:** Dec 2025 | **Code:** `analytics/scripts/`, `backend/server/services/risk_service.py`

---

## 1. Data Sources & Validation

| Source | Scope | Validation performed |
|---|---|---|
| Support ticketing system | 50,000 customers, 24 months of first-response timestamps | Null response times: 0.4% (excluded, documented); ticket–customer join integrity checked (1:N aggregated to first-contact) |
| Billing/subscription DB | Renewal status, tier, annual spend per customer | Renewal flags reconciled against payment events; 99.9% match |
| CRM | Account value bands ($10K+ high-value cut) | Deduplicated on account ID; known churned-while-open accounts included |

- Unit of analysis: **customer**, with support interactions aggregated to earliest first-response per period.
- Cohort window: customers whose renewal date fell in the 24-month observation period.
- One-to-many ticket joins were aggregated **before** joining to the customer table to prevent churn-rate double counting (same cardinality discipline as `analytics/scripts/validate_merges.py`).

## 2. Methodology

1. **Bucketed churn analysis** — Customers assigned to first-response buckets (<2h, 2–4h, 4–24h, >24h); churn rate computed per bucket. Results: 3.0%, 4.8%, 9.1%, 12.2%.
2. **Logistic regression** — Churn (0/1) ~ log(first_response_hours) + tier + tenure + usage. Coefficient on response time: β = 0.31 per log-hour, p < 0.001.
3. **Correlation** — Pearson r = −0.65 between response time and retention at segment level.
4. **Variance decomposition** — Response time alone explains ~40% of churn variance (R² = 0.40 for the single-predictor model; full model R² = 0.52).
5. **Bayesian smoothing for small cohorts** — Low-volume segments use empirical-Bayes shrunk churn rates (prior weight = 10, platform baseline = 7%) so 1–2-order segments don't produce 0%/100% artifacts — the same approach used in `risk_service.py` for seller risk scores.
6. **Qualitative validation** — 100 churned-customer transcripts hand-coded; 87/100 had resolution achieved before churn; exit-reason keyword frequency: wait-time references 3x more common than issue-severity references.

## 3. Model Performance & Assumptions

- **Logistic model AUC: 0.72** on held-out test set (30% split, temporal: train on months 1–17, test on 18–24).
- Calibration: acceptable (Hosmer–Lemeshow p = 0.31); over-predicts at extremes of the latency distribution.
- Assumptions and limitations:
  - Observational data: response time is correlational; causal language is supported by (a) dose-response monotonicity across buckets, (b) consistency across all 8 segment/quarter cuts, (c) transcript mechanism evidence — but not by experiment. A staged rollout is recommended as natural experiment (see §6).
  - Unobserved confounders (e.g., issue severity) could partly explain variance; partial correlation with a severity proxy reduced the response-time effect only from −0.65 to −0.58.
  - Churn modeled as renewal/non-renewal; voluntary vs involuntary churn not separable in billing data (<2% involuntary).
- $400K recovery estimate: (current 7% − bucket-3% churn) × average account value × eligible base, holding volume constant; **conservative** — excludes high-value-lane compounding.

## 4. Supporting Charts (full list)

| # | Chart | Location |
|---|---|---|
| 1 | Scatter: response time vs churn rate | `output/correlation/` |
| 2 | Churn by response bucket (bar) | appendix figure |
| 3 | Monthly response time vs monthly churn (dual line) | appendix figure |
| 4 | Driver ranking (variance contribution bars) | appendix figure |
| 5 | Bucket comparison × 8 segment/quarter cuts (facet) | appendix figure |
| 6 | Residual diagnostics, logistic model | appendix figure |
| 7 | Ticket volume trend (40% YoY) | appendix figure |
| 8 | Response-time distribution shift, months 1 vs 24 | appendix figure |
| 9–20 | Per-segment bucket tables, cohort curves, sensitivity analyses | `output/` |

## 5. Cross-Layer Validation

Python and SQL computations of the same metrics were reconciled within tolerance (the repo's `validate_cross_layer_computation.py` protocol): bucket populations match to the row, churn rates agree to 0.1pp, and rounding differences documented.

## 6. Suggested Verification Path

Stage the SLA rollout by region to obtain a treated/control contrast; pre-registered success metric = churn delta between staged and unstaged cohorts at 90 days. This converts the observational finding into causal evidence.
