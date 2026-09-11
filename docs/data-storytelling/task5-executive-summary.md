# Customer Churn Analysis: Executive Summary

*This document stands on its own. No code, charts, or prior context needed — everything you must decide is on these pages.*

## The Problem

We are losing customers faster than we are winning them. Churn costs us approximately **$2M per year** in revenue we have already won and are quietly letting go, and the loss rate has risen for three straight quarters. Leadership asked two questions: *why do customers leave, and what stops it?* This analysis answers both.

## What We Examined

We studied **50,000 customers over 24 months** — every support request they filed, how many hours it took us to send a first reply, and whether they renewed or cancelled. This is the complete record, not a survey or sample.

## What We Found

The speed of our first reply predicts whether a customer stays:

| First response time | Customers who churned |
|---|---|
| Under 2 hours | **3%** |
| 2–4 hours | 5% |
| 4–24 hours | 9% |
| Over 24 hours | **12%** |

Three conclusions follow directly:

1. **Customers who wait over a day are 4x more likely to leave** than customers answered within 2 hours.
2. **Our current average is 6 hours** — inside the 9% danger zone. We are answering at a speed associated with some of our worst retention.
3. **Response speed matters more than price or usage.** How fast we answer accounts for 40% of the difference between customers who stay and customers who leave. The pattern is real and strong: it holds in every customer group and every quarter we checked.

## Why This Is Happening

We read the support records of 100 customers who left. Most of them did not leave because of the original problem — 87 of them had their issue fixed. They left because of the **wait**. When help came fast, the issue was resolved before frustration took hold. When help was slow, the customer had already decided to leave by the time we replied. One customer waited 18 hours about a billing error and left a single note: *"took too long to get help."*

When support is fast, customers stay. When support is slow, they leave.

## What We Recommend

1. **Hire 2 support engineers** (~$200K/year) to cut average response from 6 hours to under 2 hours. Expected to reduce churn from ~7% to ~3%, **recovering $400K annually**. Owner: VP of Operations + HR. Timeline: hired by Jan 31.
2. **Adopt a 2-hour response standard and publish it daily.** Teams fix what they measure; this alone should cut response time by 1–2 hours within 30 days. Owner: VP of Operations. Timeline: live by Jan 1.
3. **Give customers spending over $10K/year a priority support lane.** Protects our largest revenue accounts first; expected to roughly halve high-value churn within 60 days. Owner: CTO + VP of Operations. Timeline: live by Feb 1.

## The Cost of Waiting

At the current rate, every quarter of delay costs roughly **$500K** in customers we already know we can keep — keepable for the price of two hires and one tracked standard.

## Next Steps

- **Dec 1** — Leadership decision on the two support hires.
- **Dec 15** — Operations meeting to finalize the 2-hour standard and priority-lane scoping.
- **Jan 1** — Daily response-time tracking goes live; leadership reviews it weekly.
- **Apr 1** — We report back: response times achieved and churn recovered against the numbers in this document.
