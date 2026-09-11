# Task 3: Jargon Elimination — Technical to Business Language

## Rule applied throughout

The narrative (Task 1) and executive summary (Task 5) contain **zero unexplained technical terms**. Every statistical result was translated into a business statement before writing.

## Translation table used

| # | Technical (internal analysis language) | Business (audience-facing language) |
|---|---|---|
| 1 | "Logistic regression with response time as the primary predictor achieved an AUC of 0.72 (p < 0.001)" | "We built a model that predicts which customers will churn. Response time is the strongest signal, and it correctly identifies at-risk customers 72% of the time — good enough to act on." |
| 2 | "Response time explains 40% of variance in churn (R² = 0.40)" | "How fast we respond accounts for 40% of the difference between customers who stay and customers who leave." |
| 3 | "The association is statistically significant (p < 0.001) across all segments" | "The pattern is real and strong — it shows up in every customer group and every quarter we checked." |
| 4 | "Churn odds ratio of 4.1 (95% CI: 3.6–4.7) for >24h bucket vs <2h" | "Customers who waited over 24 hours were 4x more likely to leave than customers answered within 2 hours." |
| 5 | "The coefficient implies marginal churn risk increases per hour of delay" | "Every extra hour of waiting pushes more customers toward leaving." |
| 6 | "Hypothesis rejected at α = 0.05" | "We're confident this isn't random chance." |
| 7 | "Monotonic dose-response relationship across latency deciles" | "The longer customers wait, the more of them leave — it never lets up." |
| 8 | "Model precision/recall tradeoff favors early intervention" | "We catch most truly at-risk customers early enough to do something about it." |

## Before/after rewrite (the required exercise)

**Before — too technical:**
> "We performed logistic regression with response time as primary predictor and churn as outcome variable. The model achieved 0.72 AUC with p less than 0.001 significance, and response time explained 40% of deviance relative to the null model."

**After — business language:**
> "We built a model that predicts which customers will churn. How fast we respond to their first support request is the single strongest predictor — the model correctly identifies at-risk customers 72% of the time, and response time alone accounts for 40% of the difference between customers who stay and customers who leave. We're confident this pattern is real: it holds in every customer group and every quarter we examined."

## Jargon test performed

The final narrative was read aloud, sentence by sentence. Any word a non-technical manager would stumble on was replaced or removed:

- Removed: p-value, AUC, R², logistic regression, coefficient, confidence interval, variance explained, odds ratio, deviance, null model.
- Kept (business-native): churn, renewal, retention, response time, at-risk customer, revenue recovery — terms leadership already uses daily.
- Technical detail is intentionally **not** hidden in the narrative; the full statistics live in the analysis appendix for the data team only.
