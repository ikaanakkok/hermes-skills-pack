# Instagram comments — being visible on other accounts' posts

The alternative to cold DMs: leave **short, non-selling, on-topic** comments on posts
by accounts you want to be noticed by. The goal is a profile visit, not a sale from the
comment — and it still works when the DM quota is spent.

## 1. Find posts

The tag feed is dependable on a logged-in session:

```python
goto_url("https://www.instagram.com/explore/tags/<topic>/")
wait_for_load()
links = js("""(() => { const a=[...document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]')]
  .map(x=>x.getAttribute('href')); return JSON.stringify([...new Set(a)].slice(0,8)); })()""")
```

Read the post before commenting: `document.body.innerText` starts with author and
caption. If the caption does not match the topic you planned to comment on, do not
comment.

## 2. Comment text

- 1-2 sentences, an observation about the actual work (craft, styling, composition).
- No sales line, no link, no phone number, no "we do this too" — comments that read as
  ads get deleted and the account gets reported.
- At most 1-2 emoji, at the end.
- Never reuse the same sentence across posts; template repetition is obvious and gets
  the account flagged.

## 3. Write procedure (one tab only)

The box is `textarea[aria-label="Add a comment…"]`. Order: **focus → `Input.insertText`
→ click Post → verify**. Setting `el.value` does nothing: React state is not updated.

```python
tid = [t['targetId'] for t in cdp('Target.getTargets')['targetInfos']
       if t['type'] == 'page' and 'instagram.com' in t.get('url', '')]
need_one_tab = len(tid) == 1 and tid                    # close extras with Target.closeTarget
sid = cdp('Target.attachToTarget', targetId=tid[0], flatten=True)['sessionId']
goto_url("https://www.instagram.com/p/<shortcode>/"); wait_for_load()
js("document.querySelector('textarea[aria-label*=\"comment\"]').focus()")
cdp('Input.insertText', text="<comment>")
# then click the Post button by text and re-read the page
```

## 4. Pitfall: the comment lands on the wrong post

With several Instagram tabs open, `attach()` picks the first one and a `js()` call can
answer from a different tab than the one you navigated. The comment then goes under
**another post** — no error, and a "text is on the page" check still passes.

- Do attach → navigate → type → post → verify **in a single call**.
- Close extra Instagram targets at the start of the call; keep exactly one.
- Verification: the comment text must appear immediately above the existing comments on
  the post you opened, and the page URL must still be that post.
- If it went to the wrong post, delete it from the comment's `⋯` menu and redo it on the
  right post. Do not leave it.

## 5. Cadence

5-8 comments per day is plenty, 40-60 s apart. If you also DM and follow the same day,
keep the total actions under ~25-30 (see SKILL.md "Throttling").

## 6. Measurement

Comment impact is indirect: follower delta, profile visits (business accounts, in the
app), replies to the comments, DMs asking where you found them. Log the count per day;
do not archive every text.
