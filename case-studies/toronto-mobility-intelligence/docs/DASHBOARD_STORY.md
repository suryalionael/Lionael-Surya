# Dashboard Story

Toronto Mobility Intelligence — Phase 4. The narrative this dashboard tells, and why it's told
in this order. For every visual's technical definition (source view, axes, filters,
misinterpretation risks), see [`POWER_BI_SPEC.md`](POWER_BI_SPEC.md); for the underlying
analysis this story is built from, see [`ANALYTICAL_FINDINGS.md`](ANALYTICAL_FINDINGS.md).

## Why this order

A public-sector reader — a councillor's staffer, a transportation planner, another analyst —
does not want a data dump. They want the same sequence a good verbal briefing would follow:
*what's happening, where, then when and to whom* — with the caveats attached at the point
they're needed, not buried in an appendix nobody opens. Three pages, each answering one
question completely enough to stand alone, but building on the one before it.

---

## Page 1 — What is happening?

**The opening move is deliberately narrow.** Five KPI cards and three visuals — total KSI
collisions, how many are fatal, whether pedestrians and cyclists are disproportionately
represented, and a citywide trend line. A reader who only has 30 seconds gets the headline
here and nothing else competing for attention.

**The one number that has to be on this page, not buried later: the spatially-matched
percentage (~44.7%).** Every subsequent intersection-level claim in this dashboard inherits
this limitation, and putting it on the first page — as a KPI card, not a footnote — is a
deliberate choice to front-load the dashboard's biggest honesty requirement rather than let a
reader form an impression on Page 2's intersection map before learning it only sees fewer than
half of KSI collisions.

**The trend line carries its own caveat by design.** 2026 is a partial year — the line has to
visibly break or dash at that point, because a raw line chart would silently invite the
misreading "collisions are dropping fast in 2026," when the real explanation is simply "the
year isn't over." This is the same discipline `ANALYTICAL_FINDINGS.md` applied throughout
Phase 3, carried into the visual design instead of just the prose.

**What Page 1 deliberately withholds:** intersection names, road classes, exposure metrics,
hour-of-day detail. The small citywide map is intentionally the least detailed visual on the
page — raw collision count by neighbourhood, no ranking table, no drill-in. It exists to answer
"roughly where," and nothing more, because the full "where" story — including the fact that raw
count is actively misleading on its own — is Page 2's job, not Page 1's.

---

## Page 2 — Where is it happening?

**This page's actual thesis is methodological, not just geographic: "where" has more than one
honest answer, and picking the wrong one misleads.** The West Humber-Clairville example — #1
citywide by raw collision count, #120 of 158 once normalized by land area — isn't a side note
here, it's the page's organizing idea. The raw-count/density toggle on the choropleth map and
the side-by-side ranking table both exist specifically to make that contrast impossible to miss,
not just theoretically documented in `ANALYTICAL_FINDINGS.md`.

**The intersection hotspot map is where the Page 1 KPI (44.7% matched) becomes concrete.** A
reader who internalized "less than half of KSI collisions are spatially matched" on Page 1 now
sees exactly what that means: a real map, with a real caption reminding them what's not on it.
This is the page where the abstraction from Page 1 turns into a specific, checkable claim.

**The relative-exposure table is placed last on this page, deliberately, and is the most
heavily captioned visual in the whole dashboard.** It's also the dashboard's single highest-risk
element for misreading — "collisions per 10,000 movements" sounds like a rate, and rates sound
historical. It is neither: it's five years of collisions divided by one day's traffic count.
Putting this table at the end of Page 2, after the reader has already absorbed the raw-vs-density
lesson from earlier on the same page, means they arrive at the exposure table already primed to
ask "normalized by what, exactly, and is that denominator trustworthy?" — which is exactly the
question this metric requires.

**What Page 2 deliberately withholds:** time-of-day, day-of-week, and road-user-severity
detail — those numbers exist, but stacking a third dimension onto an already-dense geography
page would dilute the raw-vs-normalized lesson this page exists to teach. They get their own
page next.

---

## Page 3 — When & who?

**This page answers two questions together because Vision Zero treats them as one question.**
"When do collisions happen" (hour, day, month, season) and "who is involved" (pedestrians,
cyclists, motorcyclists, and their severity mix) aren't separable in a road-safety context —
knowing that pedestrian-involved collisions carry a notably higher fatal share (17.54% vs. a
14.00% citywide average, per `ANALYTICAL_FINDINGS.md`) is only actionable alongside knowing
*when* those collisions cluster (weekday evenings, per the Phase 3 hour/weekday finding).

**The heatmap leads the page because it's the single densest, most information-rich visual in
the whole dashboard — and it earns that density.** 168 cells, two full categorical dimensions,
one measure: this is exactly the shape of data a matrix visual exists for, and putting it first
on the page signals "this is the detail page" the way Page 1's five KPI cards signaled
"this is the summary page."

**The road-user severity visuals close the story loop back to Page 1's second KPI (fatal
share).** Page 1 showed the citywide fatal share as one number; Page 3's severity-by-type bar
chart breaks that same number apart by who was involved, closing the loop: a reader who started
on Page 1 wondering "is 14% fatal share high or low, and does it vary" ends on Page 3 with a
direct, specific answer (pedestrian-involved collisions run meaningfully higher; cyclist-involved
meaningfully lower) rather than being left with only the aggregate.

**What Page 3 deliberately withholds:** it does not attempt to cross hour-of-day with
neighbourhood, or road-user type with season — a 4-way cross-tab would produce a visual dense
enough to stop communicating. Those combinations remain available as drill-through/tooltip
detail if a specific investigation calls for them, not as a primary visual on this page.

---

## The fourth page isn't part of the story — and that's the point

Page 4 (Methodology & Limitations) is explicitly not one of the three narrative pages. It
exists because seven specific limitations (§8 of `POWER_BI_SPEC.md`) are load-bearing enough
that they can't just live as tooltip text scattered across 12 visuals — but burying them inside
the story pages would also mean a skimming reader misses them entirely. Keeping them on a
separate, clearly-labeled page is itself a design decision: the three story pages stay
uncluttered and confident in their claims, precisely *because* every caveat those claims depend
on has a permanent, findable home one click away, not because the caveats were minimized or
hidden. A dashboard that hides its limitations to look cleaner is dishonest; a dashboard that
buries its limitations in the flow so nobody reads them is functionally the same thing. Page 4
is the alternative to both.
