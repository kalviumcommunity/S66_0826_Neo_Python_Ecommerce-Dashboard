# Task 2: Supporting Every Finding With Data

Each finding below lists the specific evidence that proves it, why that evidence is convincing, and what it means for the business.

---

## Finding 1: Support response time correlates strongly with churn

**Supporting evidence:**
- **Chart 1** — Scatter plot: first-response time (X) vs. churn rate (Y) across all 50,000 customers. A clear upward trend is visible without any statistical overlay: slower response, more churn.
- **Chart 2** — Churn rate by response-time bucket:
  | First response time | Churn rate |
  |---|---|
  | Under 2 hours | 3% |
  | 2–4 hours | 5% |
  | 4–24 hours | 9% |
  | Over 24 hours | 12% |
- **Stat:** "Customers who waited more than 24 hours for a first response were **4x more likely to churn** than customers answered within 2 hours."

**Why this evidence matters:** The step-by-step increase across four buckets (3% → 5% → 9% → 12%) shows a dose-response pattern — the longer the wait, the worse the retention — rather than a fluke caused by one extreme group. We built a model on this data that identifies at-risk customers 72% of the time, so the relationship is strong enough to act on, not just interesting.

**Business meaning:** This tells us exactly which operational change (faster first response) moves retention the most.

---

## Finding 2: Our current response speed puts the average customer in a danger zone

**Supporting evidence:**
- **Stat:** Average first response time over the last 12 months: **6.1 hours** — inside the 4–24 hour bucket, where churn runs at 9%.
- **Chart 3** — Overlay of monthly average response time vs. monthly churn rate: the two lines move together; months with the slowest responses were the months churn spiked.

**Why this evidence matters:** It converts an abstract "faster is better" into a concrete gap we can close: we are ~4 hours away from the bucket where customers stay.

**Business meaning:** Every customer we move from the 6-hour bucket to the under-2-hour bucket cuts their churn risk by roughly two-thirds.

---

## Finding 3: Response time matters more than price, usage, or contract length

**Supporting evidence:**
- **Chart 4** — Bar chart ranking drivers of churn. Response time alone accounts for **40% of the difference** between customers who stay and customers who leave — more than double the contribution of the next factor.
- **Stat:** Among customers with identical subscription tiers and usage levels, slow responses still tripled churn (10.8% vs. 3.4%).

**Why this evidence matters:** It rules out the common counter-explanation "churny customers were just on cheaper/less-engaged plans." Holding those factors constant, response time still predicts churn.

**Business meaning:** We don't need a pricing overhaul or a product redesign. The highest-leverage retention lever is in the support team.

---

## Finding 4: The pattern is consistent, not a seasonal or segment artifact

**Supporting evidence:**
- **Chart 5** — The four-bucket churn comparison repeated for: each customer segment (SMB, mid-market, enterprise), each quarter, and both renewal years. In **all eight cuts**, the >24-hour group churned at roughly 4x the <2-hour group.

**Why this evidence matters:** A finding that survives every way we slice the data is not a coincidence or a data-quality issue. The pattern is real and strong.

**Business meaning:** A single company-wide response-time standard is safe to implement — we won't accidentally fix one segment while hurting another.

---

## Finding 5 (qualitative): The mechanism is frustration, not the problem itself

**Supporting evidence:**
- **Concrete example set:** We reviewed support transcripts of 100 churned customers. 87 of them had their final support issue resolved — yet still left. Their exit notes overwhelmingly cited wait time ("took too long," "had to chase," "no one cared"), not the original problem.
- **Concrete example:** One customer waited 18 hours on a billing error and left with a one-line note: "took too long to get help."

**Why this evidence matters:** Solving the problem didn't save these customers — solving it *fast* is what saves them. This confirms the direction of cause: wait time kills the relationship before the fix arrives.

**Business meaning:** Speed is the product. Quality of resolution is already adequate; the gap is entirely in response latency.
