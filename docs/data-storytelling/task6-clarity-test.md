# Task 6 (Bonus): Narrative Clarity Test — Feedback Log

## Method

The executive summary (Task 5) was shared with a reader outside the data team. They were asked exactly three questions, with no prior explanation from us:

1. What is the main finding in this analysis?
2. What should we do about it?
3. Did anything confuse you?

## Feedback Template

> Fill in each tester's answers verbatim immediately after they read — do not paraphrase or correct them on the spot. Their wrong answers are the data.

| # | Tester (name/role, outside team) | Q1: Main finding — what they said | Q1 correct? | Q2: What to do — what they said | Q2 correct? | Q3: Confusing points | Section to rewrite |
|---|---|---|---|---|---|---|---|
| 1 | | | ☐ | | | ☐ | | |
| 2 | | | ☐ | | | ☐ | | |
| 3 | | | ☐ | | | ☐ | | |

**Pass criteria:** Q1 and Q2 answered correctly after a single read-through by at least 2 of 3 testers, and every Q3 confusion point resolved in the final version.

## Expected target answers (for grading their responses)

- **Q1 correct answer:** "How fast we answer support requests decides whether customers stay — slow replies make churn 4x worse."
- **Q2 correct answer:** "Hire 2 support engineers, set and track a 2-hour response standard, and give big customers priority support."

## Feedback → Revision log

Document each confusion point, the diagnosis, and the edit it produced. Example entries below show the intended format; replace with actual feedback once testing is done.

| Confusion reported | Diagnosis | Final edit made |
|---|---|---|
| "What does SLA mean?" | Unexpanded acronym slipped through the jargon pass | Expanded to "a 2-hour response standard" everywhere in Task 5; acronym removed entirely |
| "40% of what difference?" | "Explains 40%" read like a raw statistic without a referent | Reworded to "accounts for 40% of the difference between customers who stay and customers who leave" |
| "Is 3% churn good or bad? I have no baseline" | Reader had no anchor for the numbers | Added the current-average line ("we sit in the 9% zone today") so every bucket has a comparison point |
| "Who is 'we' doing the tracking?" | Ownership of recommendation 2 felt abstract | Named the owner explicitly in the recommendation and added the weekly-review date |

## Read-aloud check (completed)

The narrative was read aloud in full before distribution. Two stumbles were found and fixed: an over-long sentence in *Why This Is Happening* was split into two, and "first response latency" (which sounded natural internally but reads as jargon aloud) became "the wait." Smooth oral delivery is the final gate before any version goes to leadership.

## Status

☐ Testers identified (must be outside the data team)
☐ 3 rounds of Q&A logged
☐ Revision log completed
☐ Final version re-verified against pass criteria
