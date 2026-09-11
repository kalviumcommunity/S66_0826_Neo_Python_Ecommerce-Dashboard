# Task 1: Customer Churn Analysis — Structured Narrative

*Audience: Leadership (VP of Operations, CFO, CEO). Reading time: ~4 minutes.*

## 1. Context: Why This Analysis Matters

Losing customers is our single biggest source of revenue decline. Every customer we fail to retain costs us not just one month's subscription, but the two to three years of payments they would normally have made. Across the current customer base, churn costs roughly $2M per year, and the rate has climbed for three consecutive quarters. We commissioned this analysis to answer two questions leadership has been asking all year: **why are customers leaving, and what can we actually do about it?** The answer is simpler and cheaper than any of our hypotheses.

## 2. Data: What We Examined

We analyzed the complete history of 50,000 customers over the last 24 months. For every customer, we tracked their subscription tier, every support request they opened, how long it took our team to send a first response, and whether they renewed or left. We looked at every interaction and every renewal decision in the period, so the findings reflect what actually happened, not what customers said they would do.

## 3. Findings: What the Data Shows

- **Fast support keeps customers; slow support loses them.** Customers who received a first response in under 2 hours churn at only 3%. Customers who waited more than 24 hours churn at 12%. That is a 4x gap driven almost entirely by how quickly we answer.
- **Our current average response time is 6 hours — sitting in the 9% churn bucket.** We are, on average, responding at a speed associated with some of our worst retention outcomes. Moving the average customer from the 6-hour bucket to the under-2-hour bucket would cut their churn risk by roughly two-thirds.
- **Response speed is the strongest predictor of churn we found.** It accounts for about 40% of the difference between customers who stay and customers who leave — more than subscription price, contract length, or product usage.
- **The pattern holds everywhere we looked.** The 4x difference appears in every customer segment, in every quarter of the two-year window, and for both small and large accounts. This is not one bad team or one bad season skewing the result.
- **We can now identify at-risk customers before they leave.** Based on response time alone, we can flag customers with a high likelihood of churning early enough to intervene, rather than learning about it after they cancel.

## 4. Why This Is Happening

Numbers alone don't prove cause, so we read the support transcripts of 100 customers who churned. The pattern behind the data was consistent: customers contact support when something is already going wrong. When help arrived fast, the problem got fixed before frustration took hold, and the customer forgot about it. When help was slow, the customer spent hours or days feeling ignored — and by the time our team finally replied, the customer had usually already decided to leave. Our response was no longer solving a problem; it was arriving after the relationship had ended. In plain terms: **when support is fast, customers stay. When support is slow, they leave.** A concrete example: one customer waited 18 hours about a billing error, said in their exit note only "took too long to get help," and never requested support again.

## 5. What We Recommend

1. **Hire 2 additional support engineers** (cost: ~$200K/year). This brings our average first response from 6 hours to under 2 hours. Expected impact: churn falls from ~7% to ~3%, recovering about $400K annually — a 2x return in year one. Owner: VP of Operations with HR. Timeline: job posts by Dec 1, hired by Jan 31, productive by Apr 1.
2. **Commit to a 2-hour response standard and track it daily.** What gets measured gets fixed; publishing response times each morning changed team behavior within weeks in similar rollouts. Owner: VP of Operations. Timeline: standard documented by Dec 15, live tracking by Jan 1.
3. **Put response time on the leadership dashboard as a leading indicator of churn** — reviewed weekly alongside revenue, so we see retention problems coming instead of reading about them in quarterly post-mortems. Owner: Analytics team. Timeline: within 30 days of this memo.

We are not asking leadership to debate the statistics. We are asking for two hiring decisions and one process change that together pay for themselves within the first year.
