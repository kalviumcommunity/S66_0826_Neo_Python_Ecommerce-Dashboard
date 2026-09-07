# Dashboard Thinking & Information Architecture Guide

This document defines the architectural guidelines and design principles implemented in the Neo Seller Risk & Trust Dashboard, adhering to human-centric dashboard thinking.

---

## 1. The Core Problem: Cognitive Overload

Analytical dashboards frequently fail not because the underlying numbers are inaccurate, but because they violate how humans perceive and process visual information:
* **Data Dumps**: Displaying dozens of unfiltered widgets on a single screen creates decision paralysis.
* **Missing Context**: Showing naked metrics (e.g. "6.8% late delivery") without comparison targets, historical baselines, or status benchmarks leaves users wondering *"Is this good or bad?"*
* **Flat Organization**: When critical alerts share equal visual weight with minor details, users cannot triage urgent problems.

---

## 2. The Solution: The 4-Level Information Pyramid

We organize analytical data in a strict hierarchical pyramid, guiding the user from macro executive health down to microscopic record audits:

```text
                  ▲
                 / \
                / L1\          Level 1: Executive Status (Core KPIs)
               /-----\         "Are we on track?" (≤ 5 metrics, 5-second scan)
              /   L2  \
             /---------\       Level 2: Longitudinal Trends
            /     L3    \      "Is it getting better or worse?" (Time-series charts)
           /-------------\
          /       L4      \    Level 3: Segment & Cohort Breakdown
         /-----------------\   "Which parts need attention?" (Tiers, Categories)
                               Level 4: Detailed Drill-Down & Audit
                               "Show me everything." (Filtered tables, CSV export)
```

### Level 1: Status (Core KPIs)
* **Goal**: Answer *"Are we on track?"* in under 5 seconds.
* **Constraints**: Maximum 5 primary cards.
* **Context Over Numbers**: Each card pairs the raw metric with:
  1. Target benchmark (e.g., `Target ≥ 4.0`, `Target < 20`).
  2. Status context badge (`On Target`, `Needs Attention`, `Within Limits`).
  3. Directional delta indicator (`-12% MoM`, `+4.2% YoY`).

### Level 2: Trends
* **Goal**: Answer *"Is it getting better or worse?"*.
* **Implementation**:
  * Line and time-series charts displaying multi-month progression.
  * Explicit benchmark reference lines (e.g., `Target 4.0` horizontal line).
  * Rolling aggregations to smooth short-term noise.

### Level 3: Segments
* **Goal**: Answer *"Which parts of the business need attention?"*.
* **Implementation**:
  * Categorical and cohort distributions (Low, Medium, High risk tiers).
  * Horizontal bar ranking of top risk categories.
  * Direct click-through interactions: clicking a segment immediately filters down to the offending cohort.

### Level 4: Detail & Drill-Down
* **Goal**: Answer *"Show me everything"*.
* **Implementation**:
  * Interactive filters across risk drivers (`Delivery Delays`, `Negative Reviews`, `Cancellations`).
  * Deep-dive seller directory with per-seller order logs and review transcripts.
  * Auditable CSV/JSON export functionality for compliance and offline analysis.

---

## 3. Designing for Human Attention

### Progressive Disclosure
* **Executive vs. Full Analytical Views**: An interactive toggle lets users switch between an ultra-concise Executive Summary (Levels 1 & 2 only) and the Full Analytical View (Levels 1–4).
* **On-Demand Detail**: Deep-dive methodology and outlier rule panels remain collapsed until explicitly opened by power users.

### Spatial Organization
* **Western Reading Pattern (F-Shaped / Z-Shaped Flow)**:
  * Top-Left: Highest priority platform status and total seller counts.
  * Top-Right: High-leverage actions (Export, View Mode toggle).
  * Center: Trajectory curves (Trends).
  * Bottom: Granular segments and drill-down panels.

### Consistent Visual Metaphors
Color cues convey immediate semantic meaning across all views:
* 🟢 **Emerald**: Healthy / Within Target ($< 30$ Risk Score, $\ge 4.0$ rating).
* 🟡 **Amber**: Warning / Moderate Risk ($30 - 70$ Risk Score, borderline metric).
* 🔴 **Rose**: Critical / High Risk ($> 70$ Risk Score, breached threshold).
* ⚪ **Slate**: Neutral / Platform Totals.

---

## 4. Audit Checklist for New Dashboard Views

When adding or revising dashboard components, ensure:
- [ ] No more than 5 KPI cards at the top level.
- [ ] Every numeric metric includes target or historical context.
- [ ] Visual charts include benchmark or goal lines.
- [ ] Color semantics strictly follow the Emerald/Amber/Rose convention.
- [ ] Granular tables are tucked behind progressive disclosure mechanisms.
