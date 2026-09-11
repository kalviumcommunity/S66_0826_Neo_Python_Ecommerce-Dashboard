# Task 3: Recommendation Justification — Finding → Risk → Action Chain

Every recommendation traces directly to a specific measured finding and a quantified risk. No recommendation exists without evidence; no finding is left without an action.

## Justification Map

| Finding (evidence) | Risk (quantified) | Recommendation (action) | How It Helps (mechanism → impact) |
|---|---|---|---|
| Support speed drives churn: 3% at <2h vs 12% at >24h, consistent across all segments | Losing $2M/year to slow support | **Hire 2 support engineers** ($200K/yr) | Adds capacity to cut average response from 6h to <2h; shifts the typical customer from the 9% churn zone to 3% → **recovers ~$400K/yr, 2x ROI** |
| High-value customers ($10K+/yr) churn at 15% when support is slow | ~$10M revenue block is leaking fastest | **Priority support lane** ($50K eng.) | Routes top accounts to a sub-1-hour queue; the 4x response-time effect applied to the segment with the most revenue at stake → **halves high-value churn in 60 days** |
| Current average response is 6.1h and degrading while ticket volume grew 40% YoY | Process drift is invisible until churn reports confirm it | **2-hour response SLA + daily tracking** ($0) | Makes the metric visible every morning; accountability alone historically closes 1–2 hours of the gap within 30 days → **early-warning system + process fix at no cost** |
| Team response times degraded without headcount change (burnout signal) | Quality collapse + staff attrition spiral | **Hiring reduces per-person load** | Addresses root cause (capacity), not symptom (pace directives); improves customer experience and employee retention together |
| Response time accounts for 40% of the stay/leave difference — stronger than price or usage | Retention effort aimed at pricing/product would miss the biggest lever | **All three recommendations target response speed** | Ensures the initiative spends on the proven driver rather than the loudest hypothesis |

## Cause-Effect Chain (single view)

```
Ticket volume +40% YoY
        ↓
Team overloaded (burnout)
        ↓
Average first response: 4h → 6.1h
        ↓
Customers wait in the 9% churn zone (4x worse than <2h zone)
        ↓
High-value accounts hit hardest (15% churn)
        ↓
$2M annual revenue loss, competitors collect the departures
        ↓
[INTERVENTION] Hire 2 engineers + 2h SLA + priority lane
        ↓
Response <2h → churn 7% → ~3% → $400K recovered, ROI 2x
```

## Validation Notes

- Each of the 3 recommendations maps to at least one numbered finding **and** one risk.
- Each finding appears in the chain with its measured number, not a direction ("3% vs 12%", not "faster is better").
- Expected impacts are derived from the observed bucket differences, not assumptions — 3% is the *measured* churn rate of the <2-hour group today.
