# Status report template (Instagram account)

A status answer is a short document with numbers that can be audited, not a narrative.
Fill every field from evidence collected in this session; write `unverified` rather
than a guess.

## Shape

```
Account:  <handle>            Window: <run timestamp> vs <previous run timestamp>
Source:   live profile read + notifications page + <job log / send log>, <n> tabs verified

Metric        Now     Previous   Delta    Evidence
posts         12      11         +1       profile header text + main a[href*="/p/"] = 12
followers     87      84         +3       profile header text
following     41      41          0       profile header text
engagement    6       4          +2       notifications page hits since previous run
DM replies    2       1          +1       notifications page + thread open (inbox list empty, unread)

Last run:   <job id> <status>, <what it claims> (<output file>)
Next run:   <next_run_at> — <inside / outside> the 09:00–21:00 local window
Blockers:   <one line each; "none" if none>
Next step:  <one actionable sentence>
```

## Rules

- **Absolute numbers, then delta.** "87 followers, +3 since the last run", never
  "growing nicely". A reader must be able to recompute the delta from two reports.
- **One evidence cell per number.** Name the read that produced it: profile header
  string, anchor count, notifications page, job log, send log. If two sources disagree,
  show both and say which you trust and why.
- **`unverified` beats an estimate.** An unreachable page or an unrendered list is a
  finding, not a zero. Zero is only usable when a source that would show a non-zero
  value actually rendered and was empty.
- **Deltas need a baseline.** If no previous snapshot exists, say "first measurement"
  and omit the delta rather than inventing one.
- **Cadence hygiene belongs in the report.** A `next_run_at` in the middle of the night
  means the next publish or message batch has no audience; flag it as an option, do not
  reschedule on your own.
- **Blockers are concrete.** "Web video upload stalls at the processing step; posts must
  come from mobile" beats "upload issues".

## Worked example (numbers illustrative)

```
Metric        Now    Previous  Delta  Evidence
posts         12     11        +1     profile header + 12 post anchors
followers     87     84        +3     profile header text
following     41     41         0     profile header text
DM replies    2      1         +1     notifications page; inbox list rendered 0 nodes
Unverified    —      —         —      story views (no web surface for account)
```

Reading: 12 posts published, one added this run; +3 followers on 12 posts means roughly
0.25 followers per post, so distribution, not content volume, is the constraint. Next
step: test three outbound messages to accounts that already follow, then re-measure
followers after 24 h.
