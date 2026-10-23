---
name: facebook-group-outreach
description: "Use when posting to Facebook groups as a personal account."
version: 1.0.0
author: hermes-skills-pack contributors
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [facebook, groups, social-media, outreach, browser-automation, approval-gated, ban-risk]
    related_skills: [instagram-posting, linkedin-company-page-posting]
---

# Facebook group outreach (personal account)

Low-volume, organic promotion of a product inside topical Facebook groups, using a personal account
with no brand Page behind it. The channel's one-sentence rule: **the goal is not to drop the same text
in many groups — it is to start permitted conversations with the people who run the businesses.**

## When to Use

- The user asks you to promote something in Facebook groups ("join some groups, post about it"), or you
  are executing or continuing a small organic-distribution plan for a product through groups.
- You need to handle group joining, posting cadence, asking a group for permission, replying to
  comments/DMs, or reporting results.
- Posting must happen from a personal account, with no brand Page available.
- Not for Page / Instagram / LinkedIn publishing, or cold outbound on another channel.

## Prerequisites

- A logged-in personal Facebook session in a persistent browser profile driven over CDP. Verify the
  session by reading the profile identity once; do not re-attempt login on every run.
- A decision-maker/approval step: the user (or a designated planner) decides *what* text, *which* group
  types, *what* cadence, and *when to stop*. The agent decides *how* to execute.
- An append-only action log (CSV is fine: `timestamp, group, action, result, evidence`) — one row per
  join, post, retraction, and stop event. ISO 8601 timestamps with timezone. Unknown numbers stay blank,
  never `0`. No contact lists, phone numbers, or customer data are stored.
- Group rules read after joining (Procedure step 4). "I couldn't find a rule" is ambiguity, not permission.

## Procedure

1. **Get one consolidated approval.** Ask once, with everything concrete: group name + exact final text
   + link yes/no. A plan approval covers execution; it does not roll forward to a different draft. When
   the user says "just post it", treat that as blanket approval for the stated list, then log the exact
   target groups and the exact text sent, and return them as a single list in your reply so the approval
   record is not lost. Do not show internal verification passes as work the user must review — run them
   silently.
2. **Find candidate groups.** Working search patterns are `"<niche> owners"`, `"<niche> owners
   solidarity"`, `"<city> <niche>"`. A bare plural job title (e.g. "plumbers") often returns zero results;
   if a term misses, drop it rather than retrying trivial variants. Expect the result list to be
   dominated by marketplace / classifieds / job-board / equipment-sales groups — those are **not**
   targets. Never post into a classifieds, second-hand, or job-listing group.
3. **Join from the group header only — never by first match on the page.** The main control on a public
   group page is labelled `Joined` once you are a member and `Join group` before. The "Related groups"
   cards in the right rail carry the *same* label, so a page-wide first-match click can enrol you in the
   wrong group; `aria-label="Join group"` commonly matches more than once. Scope the selector to the group
   header and confirm position with a fresh `getBoundingClientRect()`. If `el.click()` changes nothing, do
   not repeat it blindly: bring the tab to front, click the button centre with `click_at_xy`, wait for the
   UI to settle, re-read the header. Check `facebook.com/groups/joins/`; a wrong join is undone with
   `Joined → Leave group → confirm`, and both the join and the retraction are logged.
4. **Read the rules, then decide.** After joining, `groups/<id>/about` exposes "Group rules from the
   admins" in full, plus activity counters ("N new posts today", "N in the last month", "+N in the last
   week"). If any rule forbids advertising or commercial content, **there is no product post in that
   group**. If the rules page has no text at all, that is uncertainty, not permission; if it is genuinely
   ambiguous, ask the group once through its own channel and stop until answered.
5. **Warm up before posting.** No post in the first 72 hours after joining; contribute real, on-topic
   comments instead. A value post (no link) comes before any promotional one, and links appear only in the
   promotional post, only where rules permit.
6. **Compose the post.** Click the `div[role=button]` whose text is `Write something…` / `Bir şeyler
   yaz…`. Inside the opened `div[role=dialog]` there is exactly **one** `[contenteditable=true]`; focus it.
   Write the body with `cdp('Input.insertText', text=...)` — `fill_input` is unreliable against Facebook's
   Lexical editor and can silently drop text. Read the dialog text back, check the character count, then
   click the `aria-label="Post"` button *inside that dialog*.
7. **Read the outcome per group.** A post may go straight to the feed, or land behind `Your post is
   awaiting admin approval`. Do not assume new membership implies mandatory review, and note that the
   instant "submitted" confirmation can disappear on reload. Record the real state either way.
8. **Pace it.** One join request per day and a small fixed total per campaign. A minimum of 48 hours
   between posts in the same group; a rolling 7-day window of at most three. Volume limits are campaign
   decisions, not platform constants — do not present them as hard platform rules.

## Verification

- **Joining and posting are separate facts.** A public group will sometimes accept a composer post from
  a non-member, so a successful post is not proof of membership. Membership requires `Joined` (or a
  pending-application state) on the target group header.
- **Pending posts are invisible in the desktop feed.** "I can't see it" is not "it wasn't posted". The
  reliable read is the mobile shell: `m.facebook.com/groups/<id>` shows
  `Joined · Pending admin approval · 1 post · Manage post`. When approval lands, the post appears in the
  normal feed and its permalink can be taken from there.
- A click is not a publication. Record `pending_admin_approval` when you have waiting evidence, and
  `visible_in_group_feed` only when a reloaded feed actually shows the text. If no permalink exists, say
  so separately — do not conflate "visible in your own feed" with a verified public permalink.
- Keep the final report short: group name, join result, post's actual state — no internal file dumps.

## Pitfalls

- **Related-groups `Join group` cards share the primary button's label.** The single most reliable way to
  join the wrong group. Always anchor to the header node.
- **Hidden Unicode in served content.** Facebook serves post and comment text to non-members and in some
  feed contexts with invisible combining characters — U+00AD, U+034F, U+200B–U+200F, U+2060–U+2064, U+FEFF.
  `innerText` then renders as `SponSored`, substring matching fails, and a populated page looks empty.
  Strip that range with `replace()` before any pattern search.
- **Lexical composer + `fill_input`.** React-controlled fields discard programmatic writes. Use
  `Input.insertText` on the focused contenteditable, then verify.
- **Login form false negatives.** "We couldn't find your account" does not prove the email is only a
  recovery address; a React-controlled field may simply not have kept the value. Type with `fill_input`,
  confirm it persisted, and if needed use `/login/identify` → `Continue with password`. Never start a
  password reset or code send on your own initiative.
- **Don't over-claim from a security interstitial.** Never assert that clicking a CAPTCHA will flag the
  account or that the next step will be SMS; that is unknowable before the screen renders. Hand the step
  to the user on their own screen with one short explanation, and never ask for a one-time code in chat.

## Ethics & limits

- **No mass identical posting.** The same approved text to a small, explicitly bounded set of relevant
  groups is fine; the same text sprayed across many unrelated groups is spam and is never done. Keep an
  approved text's wording, punctuation, and link exactly as given — never prepend slogans or feature bullets.
- **No scraping, no member-list harvesting, no mass DMs.** Do not mine phone numbers out of a group.
  Direct messages only on explicit permission or an inbound DM.
- Respect each group's rules as written. If the group forbids promotion, the answer is no post.
- **Honest identity.** Answer membership questions truthfully; never imply the user owns a business they
  do not own, and never hide the relationship to the product.
- No exaggeration, no guarantees, no discount/price promises, no customer screenshots.
- Never re-post content that was removed or warned about. Never automate a CAPTCHA or security check.
- **Hard stop:** account warning, action block, suspicious-activity notice, CAPTCHA/security challenge,
  or a "post restricted" notice → **stop the entire queue immediately**. Log the evidence and timestamp,
  tell the user, and do not try another account, IP, or device, and do not "wait a bit and retry".
  Procedure gates (warm-up period, value-to-promo ratio, owner-ratio thresholds) belong to the user and
  can be waived on explicit instruction — record the waiver. The lines above cannot be waived; state the
  reason in one sentence and continue with the parts that remain legitimate.
