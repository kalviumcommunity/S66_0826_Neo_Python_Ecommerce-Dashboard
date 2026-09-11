# Task 4: Three Actionable Recommendations

Each recommendation specifies **What, Why, Impact, Owner, Timeline** — complete enough to act on without follow-up questions.

---

## Recommendation 1: Hire 2 Support Engineers

- **Action:** Open recruitment for 2 additional support specialists, targeting Q1 start dates. Approve ~$200K/year in payroll.
- **Why it will work:** Our current team averages a 6-hour first response — the zone where customers churn at 9%. Based on the response-time/churn relationship in our analysis, adding this capacity moves the average customer into the under-2-hour zone, where churn runs at 3%.
- **Expected impact:** Churn drops from ~7% to ~3%, recovering about **$400K in annual revenue**. The hires pay for themselves roughly 2x over in year one.
- **Owner:** VP of Operations (hiring bar + onboarding) with HR (recruitment pipeline).
- **Timeline:** Post job descriptions by **Dec 1** → offers signed by **Jan 31** → fully productive by **Apr 1**. First measurable churn effect visible by end of Q2.

---

## Recommendation 2: Implement a 2-Hour Response Time SLA

- **Action:** Document an internal service standard — first response to every support request within 2 hours during business hours — and publish actual response times on a daily dashboard visible to the support team and leadership.
- **Why it will work:** Measurement creates accountability. Teams prioritize what they measure; our own data showed churn spiking precisely in the months when response times drifted. A public daily number makes drift impossible to ignore.
- **Expected impact:** SLA tracking alone should pull average response time down by 1–2 hours within **30 days**, immediately shifting a large share of customers out of the 9% churn bucket even before the new hires arrive.
- **Owner:** VP of Operations.
- **Timeline:** SLA documented and agreed by **Dec 15** → daily tracking live by **Jan 1** → reviewed weekly in the ops meeting from **Jan 8**.

---

## Recommendation 3: Route High-Value Customers to a Priority Queue

- **Action:** Implement automatic priority routing so customers spending over $10K/year reach a dedicated fast-response lane (target: under 1 hour) the moment they open a support request.
- **Why it will work:** High-value customers are the least tolerant of slow support and the most expensive to lose; every hour of delay puts the largest revenue block at risk. This is the cheapest protection available because it redirects existing capacity rather than adding any.
- **Expected impact:** Based on the 4x response-time effect concentrated on the accounts that generate the most revenue, we expect high-value customer churn to fall by about **50% within 60 days**, protecting our top revenue tier while Recommendations 1 and 2 roll out company-wide.
- **Owner:** CTO (routing implementation) with VP of Operations (staffing the dedicated lane).
- **Timeline:** Scoping complete by **Dec 20** → implementation live by **Feb 1** → churn effect measured by **Apr 1**.

---

## Combined effect

| Recommendation | Cost | Expected annual impact | Live by |
|---|---|---|---|
| 1. Hire 2 engineers | $200K | +$400K recovered churn | Apr 1 |
| 2. 2-hour SLA | ~$0 (process) | 1–2 hr response cut in 30 days | Jan 1 |
| 3. Priority queue | Low (config) | ~50% high-value churn cut in 60 days | Feb 1 |

All three target the same proven lever — first response speed — through capacity, accountability, and prioritization, so their effects reinforce rather than overlap.
