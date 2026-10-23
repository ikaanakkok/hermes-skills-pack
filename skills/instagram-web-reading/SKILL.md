---
name: instagram-web-reading
description: "Use when reading an Instagram account's live state over CDP."
version: 1.0.0
author: hermes-skills-pack contributors
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [instagram, social-media, browser-automation, cdp, status-report, engagement]
    related_skills: [instagram-posting]
---

# Instagram — reading live account state

Follower, post and engagement counts plus DM-reply status from a logged-in Instagram web session
over CDP. Read-only except for the caption fix in the write-path section; publishing and outreach
belong to a posting skill. Snippets assume the Hermes browser helpers `new_tab`, `wait_for_load`,
`js`, `cdp` and `ensure_real_tab` are already imported in `browser_exec`.

## When to use

Use this to answer "how is the account doing", check for replies, and verify that a post or DM
batch landed. Not for publishing, DMing, or producing assets.

## Procedure

1. **Attach to the existing logged-in Chromium** (debug port 9222, profile `~/.hermes/chrome-debug`)
   — a fresh profile has no session and shows a login wall; never start a browser to "fix" a blank
   read. Navigate with `new_tab(url)` + `wait_for_load()`.
2. **Read counters from `body.textContent`** in a single `js()` call (snippet below).
3. **Engagement**: `/notifications/`, then `document.querySelector('main').textContent`. When empty,
   search `document.body.textContent` for `started following`, `liked your`, `commented` (plus
   localised equivalents) and slice ±150 chars around each hit — that separates "nobody engaged" from
   "the page did not render".
4. **Report** per the reporting section: absolute number, delta, evidence, one line of advice.

## Counters in one call

```python
new_tab("https://www.instagram.com/<handle>/"); wait_for_load()
print(js(r"""(() => {
 const t = document.body.textContent || '';
 const i = t.toLowerCase().indexOf('followers');
 return JSON.stringify({
   around: i > -1 ? t.slice(Math.max(0, i-160), i+40).replace(/\s+/g,' ') : null,
   posts: [...document.querySelectorAll('main a[href*="/p/"]')].length
 }, null, 1)})()"""))
```

`around` returns `... <handle> Options <display name> 2 posts 1 follower 0 following <bio>`;
parse `(\d[\d.,]*) posts?`, `([\d.,]+) followers?`, `([\d.,]+) following`. The `main a[href*="/p/"]`
length is an independent post-count cross-check — when the two disagree the anchor count usually
wins, being rendered markup rather than the header string.

## DM replies

`/direct/inbox/` often renders zero text nodes on a fully loaded page. Treat "empty" as "unread",
not "no replies": cross-check the notifications page, the sender's own send log if there is one,
and a thread opened directly via `/direct/t/<thread-id>/`. Say which evidence you used.

## Multi-tab safety

The harness leaves one tab per `new_tab()` call. With several Instagram tabs open, a `js()` can
answer from a different tab than the one you attached to, and a stale tab can hold an unsaved
dialog that looks like saved state.

```python
tid = cdp('Target.getTargets')['targetInfos']
ig  = [t for t in tid if t['type'] == 'page' and 'instagram.com' in t['url']]
sid = cdp('Target.attachToTarget', targetId=ig[0]['targetId'], flatten=True)['sessionId']
cdp('Runtime.evaluate', expression='document.body.textContent.slice(0,80)',
    sessionId=sid, returnByValue=True)
```

Keep exactly one `instagram.com` target before reading or writing; close extras with
`Target.closeTarget`. Never close the tab the harness is driving: its websocket dies with `no
close frame received` and every later helper call fails — recover with `ensure_real_tab()`.

## Scheduled account: assembling a status answer

When a cron job operates the account, use three sources in this order — never the last chat summary:

1. `~/.hermes/cron/jobs.json` — job state (`scheduled`/`enabled`), `last_status`, `next_run_at`.
2. The job's own state/log files for counts and cadence, plus the newest file in
   `~/.hermes/cron/output/<job-id>/` for what the last run claims it did.
3. The live platform, for numbers the log cannot prove.

Flag a `next_run_at` outside roughly 09:00–21:00 local: a 12-hour interval anchored at job creation
drifts to whatever hour the job was made, and posting at 04:00 wastes reach. Offer the re-anchor in
one sentence; never reschedule silently.

## Caption edit — the one write path (three traps, all verified by failure)

- The editor is a Lexical `contenteditable`. A synthetic `ClipboardEvent('paste')` fills the DOM but
  is **not** committed, so Done closes the dialog as if nothing changed. Type with real key events
  (`Input.insertText`, or `Input.dispatchKeyEvent` with `text` per character) so the editor's own
  handlers fire; `insertText` swallows `\n`, so line breaks need per-char keys.
- `element.click()` on **Done** does not submit. Resolve the button box via `DOM.getBoxModel` and
  click it with `Input.dispatchMouseEvent` (mousePressed + mouseReleased at the centre).
- Ground truth afterwards is the block immediately before `No comments yet` in `body.textContent`
  of the post page — not the edit dialog, whose contents may belong to another tab.

## Reporting

Absolute number per metric, delta against the last known values, the evidence each number came
from, then one line of recommendation. Quote exact figures ("1 follower", never "some followers")
and pair them with post and DM counts — these move in single digits per run, and a reply padded
with adjectives is worse than no reply. Mark anything unproven `unverified`. Shape:
`references/status-report-template.md`.

## Pitfalls

- **Two tabs, one answer, or a read that looks stale** → `Runtime.evaluate` without `sessionId` may
  run in a stale tab holding an unsaved dialog → attach with `Target.attachToTarget` (flatten) and
  pass `sessionId`, close non-driven targets, keep `ensure_real_tab()` in hand.
- **`innerText` returns empty** on logged-in React pages, including `header li` and `section` text
  → the visible header is built from nodes `innerText` skips, while the numbers sit unrendered in
  the SSR payload → always use `textContent`.
- **`slice(0, 600)` shows only JSON** → the SSR bootstrap blob (`__dr`, `queryName`, `Polaris…`)
  fills the first few hundred KB of `body.textContent` → locate `indexOf('followers')` or a known
  username and slice around the hit.
- **`og:description` disagrees with the header** (`0 followers` vs `1 follower`) → cached snapshot → identity only, never counts.
- **`fetch('/api/v1/users/web_profile_info/?username=…')` throws `Unexpected token '<'`** → the
  endpoint answers with the HTML shell, not JSON → do not build an audit on it.
- **A post URL bounces to the profile, or `/accounts/edit/` re-asserts itself over `Page.navigate`**
  → SPA routing rehydrates and rewrites `href` → read `location.href` back after every navigation;
  trust only data collected after it matches.

## References

- `references/status-report-template.md` — structure for an account status report.
