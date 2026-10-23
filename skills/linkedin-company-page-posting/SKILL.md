---
name: linkedin-company-page-posting
description: "Use when posting to a LinkedIn company page as an admin."
version: 1.0.0
author: hermes-skills-pack contributors
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [linkedin, company-page, social-media, publishing, cdp, browser-automation]
    related_skills: [instagram-posting, social-media-asset-production]
---

# LinkedIn company page posting (admin view)

Publish text + photo posts to an organization page you administer, over CDP, from an
already logged-in browser session. Contract: **draft -> human approval -> publish ->
verify**.

The two failures this skill exists to prevent: the post lands on the *personal*
profile instead of the page, and the agent reports success for a post that never
landed.

## Hard rules

1. **No publish without explicit approval.** Show the exact caption + image list +
   target page name, then end the turn. A new instruction does not inherit approval
   from an earlier draft.
2. **Never type a password.** Use a credential vault for stored logins, or have the
   human log in on the machine's own screen. Never `fill_input` a password field,
   never ask for credentials in chat.
3. **Verify before claiming success.** A clicked Post button is not a published post:
   read the permalink back and confirm the caption is on the page feed.
4. **Publish immediately, do not schedule** unless a date/time was requested.
5. **Never post to a personal feed.** Assert the composer header names the page.
6. **No invented facts.** Names, numbers, dates and tags must trace to what the human
   supplied. No sponsor plugs or political content unless the org explicitly asked.

## Environment and login

- Drive an existing headful browser over CDP: `CDP_URL` (default
  `http://127.0.0.1:9222`). Do not spawn a second browser — the session cookie lives in
  the operator's profile directory.
- LinkedIn is a SPA and renders only in a **foreground** tab: `cdp('Page.bringToFront')`
  before reading or clicking; background tabs return stale nodes. Never close the user's
  other tabs — open LinkedIn in its own.
- Captcha, 2FA and "is this you?" challenges go to a human on the machine's own display
  (remote desktop). Do not loop-retry — that is how accounts get locked.

Check the session before anything else:

```python
new_tab("https://www.linkedin.com/feed/")
wait_for_load()
print(page_info()["url"])   # /feed/ = logged in, /login = not
```

If it lands on `/login`, have the human log in on the machine's own screen — the only
path that survives 2FA, and the cookie then persists so later runs are hands-off. With a
vault, fill only the **visible** identifier field; the agent never handles a password.

## Workflow

### 1. Sanity-check the images

Confirm every path exists and is non-empty first (`ls -l <path1> <path2>`) — a missing
file silently produces a text-only post.

LinkedIn limits: max **20 images**, aspect ratio between **9:16 and 16:9**, max 10 MB
each, JPEG/PNG/GIF. Mixed aspect ratios get letterboxed — warn the human, or normalise
with PIL instead of posting a broken layout. 3–6 images is the sweet spot for event
photos; skip blurry frames rather than padding the count.

### 2. Draft the caption

`references/caption-guide.md` (voice, structure, hashtags, links) and
`references/post-types.md` (announcement / event / recruitment / recap).
Cap **3000 characters**; the first ~140 decide the "see more" click. One language per
post — never mix.

### 3. Show the draft and stop

Caption verbatim + image list + page name, then end the turn. Do not pre-open the
composer; approval often comes back as edits.

### 4. Publish

Write the caption to a UTF-8 file, fill the env with **your** values, exec the script
inside `browser_exec`:

```python
import os
os.environ["LINKEDIN_ORG_URL"] = "https://www.linkedin.com/company/<your-page-slug>/"
os.environ["LINKEDIN_ORG_NAME"] = "<Page display name>"          # asserted in the modal header
os.environ["LINKEDIN_IMAGES"] = "/abs/a.jpg,/abs/b.jpg"          # absolute, no ~
os.environ["LINKEDIN_TEXT_FILE"] = "/tmp/linkedin_post.txt"
# os.environ["LINKEDIN_COMMIT"] = "1"                            # second, committing run only
exec(open("scripts/publish_post.py").read())
```

Run once **without** `LINKEDIN_COMMIT` (dry run: navigates to the admin post list, opens
the composer, uploads, inserts the caption, prints state, submits nothing). Only then
commit. The dry run is also how selectors get re-verified after a LinkedIn UI change.

If a step reports divergence, run `scripts/probe_composer.py` for a live DOM inventory
and repoint the selectors — never guess-and-click.

### 5. Verify

The committing run re-reads the admin post list, matches the caption's first line and
prints the permalink. Two checks, both mandatory:

- Caption + media are on the **page** feed (permalink quoted to the human).
- The same caption is **absent** from the personal profile's recent activity. A wrong
  identity can be caught here even after a successful page post, so check before
  calling it done.

If verification fails, say so plainly and leave the composer for inspection.

## Pitfalls: symptom -> why -> fix

| Symptom | Why | Fix |
|---|---|---|
| Composer bounces to `/login` mid-flow | session expired | re-read `page_info()["url"]` after *every* navigation |
| Submit button disabled or no-op | media still uploading; button `aria-disabled` | wait for thumbnails (progressbar count 0), check `disabled` **and** `aria-disabled` |
| Post lands on the personal profile | "posting as" persists from the last session | always enter via `/company/<slug>/admin/page-posts/published/`, then assert the page name in the modal header |
| Text never appears | `fill_input` is a no-op on Quill-style contenteditable | focus the editor, then `cdp('Input.insertText', text=...)` |
| Line breaks collapse into one block | `execCommand('insertText')`/paste flatten `\n`; `\r\n` leaves a stray char | `Input.insertText` only, `\n` only, then assert the editor's block count |
| Caption silently cut | >3000 chars truncates in the composer | count first, refuse to publish |
| Upload silently ignored | hidden file input re-rendered between query and set | fresh `DOM.getDocument` + `DOM.querySelector`, then `DOM.setFileInputFiles` |
| Upload fails on non-ASCII/space paths | CDP wants absolute, unquoted paths | `os.path.abspath` them; no `~`, no quotes |
| Wrong "Post" clicked | several buttons read "Post", plus a schedule dropdown | scope to the topmost `[role="dialog"]`, exact text match, then `aria-label` |
| Composer visible but unclickable | media editor mounts a second dialog on top | always take `[...document.querySelectorAll('[role="dialog"]')].pop()` |
| JS SyntaxError mid-publish | non-raw `js("""...""")` eats `\n` / `\s` meant for JS | `js(r"""...""")`, then `py_compile` and `new Function(<json.dumps(block)>)` |

## Editing these scripts

These scripts publish to a page real people see; a silent failure is worse than a loud
one. After any edit, in order: (1) `py_compile` both scripts, (2) parse-check every JS
block with `new Function`, (3) run `publish_post.py` **without** `LINKEDIN_COMMIT`
against the real page, (4) only then `LINKEDIN_COMMIT=1`.

## After the post

Offer to log caption + permalink (and, for events, attendance) wherever the
organization tracks content, and record any selector change back into this skill.
