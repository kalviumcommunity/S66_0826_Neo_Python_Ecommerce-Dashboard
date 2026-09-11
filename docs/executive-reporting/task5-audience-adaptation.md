# Task 5: Audience Shift — CEO vs VP of Engineering

**Question:** Your audience changes from CEO (focused on ROI and risk) to VP of Engineering (focused on technical implementation). How would you adjust the communication?

---

## Answer

The data, findings, and recommendations do not change. **Only the emphasis changes.** The CEO needs the decision framed in money and risk; the VP of Engineering needs the decision framed as scope, requirements, and milestones. Same substance, different lens.

### CEO version — money, risk, one page, zero implementation detail

> Support delays are costing us $2M a year in churn. Our data shows customers answered in under 2 hours churn at 3%; those waiting a day churn at 12% — 4x worse. Today we average 6 hours. Two hires and one process change fix the bottleneck: $200K in salaries plus $50K engineering recovers $400K in year one and stops the leak. Doing nothing costs roughly $500K per quarter. **Decision needed: approve $250K by Dec 15.**

**Framing choices:** financial metrics only, cost-of-inaction headline, explicit dollar decision request, no mention of dashboards, routing logic, or staffing mechanics. Detail level: one page max.

### VP of Engineering version — feasibility, requirements, milestones

> **Problem statement:** median first response is 6.1h; target is <2h. Three workstreams:
>
> 1. **Priority routing logic** — tag accounts >$10K ARR in the ticketing system, add queue rules to route tagged tickets to a dedicated lane with a 1h SLA alarm. Est. 2 eng-weeks; depends on CRM tier field sync (needs API contract review).
> 2. **Response-time tracking dashboard** — pipeline already exists on our analytics stack; need a webhook from the ticketing system for first-response events, one daily aggregate table, and a dashboard view. Est. 1 eng-week + analyst time.
> 3. **Staffing** — 2 support FTEs are a hiring action, not engineering work, but your input on tooling onboarding is needed for the Apr 1 productivity date.
>
> **Delivery plan:** SLA tracking live Jan 1, routing live Feb 1, load-tested before high-value accounts are switched over. **Ask: assign an owner per workstream and confirm sprint capacity by Dec 20.**

**Framing choices:** technical requirements, dependencies, estimates, and milestone dates; the ROI line survives only as one sentence of motivation. Detail level: a short design document, not a page.

### What stayed identical

- The response-time → churn relationship and all bucket numbers.
- The three recommendations and the Dec 15 / Jan 1 / Feb 1 timeline.
- The cost figures.

The CEO could approve without reading anything operational; the VP of Engineering could start scoping without asking "but how much does this matter?" — each version answers exactly the questions *that* audience would ask.
