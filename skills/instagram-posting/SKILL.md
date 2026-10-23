---
name: instagram-posting
description: "Use when publishing posts, Reels, stories or DMs on Instagram web."
version: 1.0.0
author: hermes-skills-pack contributors
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [instagram, social-media, publishing, cdp, browser-automation, reels, stories, dm]
    related_skills: [instagram-web-reading, social-media-asset-production]
---

# Instagram — posts, Reels, stories, DMs

Write side of an Instagram operation over the Chrome DevTools Protocol: feed posts, carousels, Reels, stories, comments and cold DMs on a browser profile that is already logged in. `instagram-web-reading` owns the read side.

## When to use

- The user hands over images or a video to publish on an account.
- A story card, comment pass or DM batch has to go out.
- A publish "worked" but nothing appeared — start at Pitfalls.
- Not for reading account state, producing assets, or scraping.

## Prerequisites

- A browser already listening on CDP (default `http://127.0.0.1:9222`, override with env `CDP_URL`) whose profile is logged in to the target account. Never start a fresh browser to "fix" a login wall — a new profile has no session.
- Helpers in scope: `new_tab`, `goto_url`, `wait_for_load`, `js`, `cdp`, `page_info`.
- **One Instagram tab.** Not tidiness — see Multi-tab discipline.

## Hard rules

1. **Approval gate.** Caption verbatim + image order + tags + target account, then wait for an explicit go. Approval never carries over to a new draft; on a single-operator account this is a self-check — keep it.
2. **Never type a password.** Vault, or the user logs in on the machine's own screen. A pasted password can carry a trailing space and the vault stores it verbatim.
3. **Verify before reporting success.** Read the profile back and quote the real permalink (`/p/<shortcode>/`). A clicked Share button is not a post.
4. **Image order is the message.** The first image is the carousel cover — confirm it.
5. **Feed, carousel and Reels all work over CDP.** Video was only ever blocked by an info modal.

## Login

```python
goto_url("https://www.instagram.com/"); wait_for_load()
print(page_info()["url"])      # feed = logged in, /accounts/login = not
```

Preferred: the user logs in on the machine's own screen — Instagram throws a challenge or an email code quickly, they clear it there, and the session stays in the profile. Alternative: a vault `login` item with origin exactly `https://www.instagram.com`.

- The identifier field is React-controlled: **`fill_input` leaves it empty** (reads back `""` after the re-render). Focus with JS, then `cdp('Input.insertText', text=...)`.
- **Never insert the identifier twice.** A second `insertText` *appends* (`user` → `useruser`) and the server answers a generic "login information is incorrect", which reads like a wrong password. Clear with select-all + `Input.dispatchKeyEvent` Backspace, re-read `.value`, then submit — and check both `.value.length` first: a password length of 0 means the vault fill never landed.
- Live page: `input[name="email"]` (type=text) + `input[name="pass"]`, submitted by `div[role="button"][aria-label="Log in"]`; a hidden `input[type=submit]` also exists.
- **Wrong handle vs wrong password:** read the public profile logged out — if `og:title` names the account, the handle exists and the stored password is wrong. That is a finding, not a retry case; `og:description` is cached, so use it for identity only, never for counts.

## Workflow

**1. Images** — up to 10 per carousel, JPEG/PNG, ≤ 8 MB, paths verified. The feed crops to **4:5** (1080x1350 safe, 1080x1080 always safe); say when a photo will be cut instead of silently posting a crop. Mixed phone snapshots → normalise with PIL into one consistent 4:5.

**2. Caption** — `references/caption-guide.md`; the account's language; cap **2200 characters**; 5-10 hashtags after a blank line.

**3. Draft and stop** — send caption, image order, tags, target, then end the turn.

**4. Publish** — dry run first (no `IG_COMMIT`), then commit:

```python
import os
os.environ.update(IG_HANDLE="<handle>", IG_IMAGES="/abs/a.jpg,/abs/b.jpg",  # order = carousel order
                  IG_TEXT_FILE="/tmp/instagram_post.txt")                   # add IG_COMMIT="1" to publish
exec(open("scripts/publish_post.py").read())
```

Selectors are text/role based (class names are obfuscated). When a step diverges, run `scripts/probe_page.py` and repoint; the first run on a new account skin is discovery.

**5. Verify** — the script diffs the profile's permalinks before and after the upload and reports only the new one. A toast is informational, a new permalink is proof; no new permalink → report "unconfirmed", never retry blind.

## Reels

File → **"Video posts are now shared as reels" modal → OK** → Crop → Next → Cover/Trim → Next → Share → `"Your reel has been shared."` → Done.

- The modal has no error styling; without OK the flow stands still and looks like a failed upload.
- The dialog's `input[type=file]` may advertise `accept="image/jpeg"` and still take an mp4 — ignore the attribute, use `cdp('DOM.setFileInputFiles', nodeId=..., files=[...])`.
- Gate the wait on `configure_to_clips` answering **200** plus the literal "Your reel has been shared.", not a timer. Encoding is slow; a fixed sleep moves on early and then clicks a dead button.

## Stories

Instagram web has **no story composer**: `/create/story/` redirects to the feed and the profile's `New` opens a *highlight* picker.

- Working door: **Meta Business Suite** on a Facebook Page → `Create story`, which needs the Instagram business account linked to that Page (`references/meta-business-suite.md`). Until then, render the cards (`references/story-cards.md`) and hand the PNGs to the user for the app.
- Read the dialog title after picking the file: `Create story` / `Story`. If the feed dialog opened, stop — a story card in the feed wrecks the grid. Verify from the ring around the profile photo afterwards.

## Captions do not survive publish

Symptom: the editor shows your text and the counter rises, yet the published post has no caption and no error. Cause: the create payload is built from Lexical editor state, which `Input.insertText`/focus emulation never commits.

Fix after the post exists: resolve the numeric media id (`fetch('/p/<code>/')` → `"media_id":"(\d+)"`), then `POST /api/v1/media/<id>/edit_media/` with `content-type: application/json`, headers `x-csrftoken` (cookie) and `x-ig-app-id: 936619743392459`, body `{"caption_text": "..."}`. The field must be **`caption_text`** — `caption` returns 200 and writes nothing. Verify on the permalink (`og:description` lags minutes behind for fresh posts).

- **Newlines:** `Input.insertText` swallows `\n`; a synthetic `ClipboardEvent('paste')` fills the DOM but is never committed, so Done closes as if nothing changed. Send per-line `Input.insertText` with real `Enter` key events between lines.
- **Done ignores `element.click()`.** Resolve it via `DOM.getBoxModel` and click with `Input.dispatchMouseEvent` (mousePressed + mouseReleased at the centre).
- The caption box is a `contenteditable` on newer builds, a `textarea` on older ones — branch on `document.activeElement.tagName`.

## Cadence

- **≤ 5 DMs per session**, 45-90 s apart, varied wording; ≤ 15-20 per day, one session. 5-8 comments per day, 40-60 s apart; total actions ≲ 25-30/day.
- No `Message` button → follow first, re-check. Type with `Input.insertText`, read the composer back, click `div[aria-label="Send"]`, re-read (0-1 chars = sent). Refusals ("can't receive your message because they don't allow new message requests") are their privacy setting, not your quota.
- Procedure, name-extraction trap, corrections: `references/dm-outreach.md`; comments: `references/engagement-comments.md`.

## Multi-tab discipline

`js()` can answer from a **different tab** than the one you navigated: `location.href` came back as an unrelated page mid-login and every field read `null`, while neither `Page.bringToFront` nor `Target.activateTarget` rebound it — so `click_at_xy` fires into whatever is frontmost. In write flows that means a comment under the wrong post or a caption on the wrong draft.

```python
tid = [t["targetId"] for t in cdp("Target.getTargets")["targetInfos"]
       if t["type"] == "page" and t.get("url", "").startswith("https://www.instagram.com")]
sid = cdp("Target.attachToTarget", targetId=tid[0], flatten=True)["sessionId"]
cdp("Runtime.evaluate", session_id=sid, expression="location.href", returnByValue=True)
```

Keep exactly one Instagram target; close extras with `Target.closeTarget` — never the one the harness drives, its websocket dies. Navigate → act → verify inside one call.

## Daily operation

- **Do not touch the browser while a scheduled run is active** — two agents on one tab write to the wrong post. Check the job's output file; absent = still running.
- `ts` on every record (`publish_state.json`, `dm_log.json`, `follows_log.json`); count today from today's rows, not the total, or the target looks met. Keep the queue idempotent and pre-render.
- Never `str.format` an HTML/CSS template — braces are read as fields (`KeyError: 'box-sizing'`).

## Pitfalls

**Session.** **401 `require_login` / bouncing to `/accounts/login`** → soft limit from a burst of posts, DMs or scans on a young account while the UI still looks fine → stop the run; retrying widens the block. **Never fall back to internal endpoints** (`web_profile_info`, `friendships/create`) when a button is missing → those calls return 401 and mark the session → skip that profile. **`sessionid` is HttpOnly** → a missing cookie is not a logged-out session.

**Create flow.**
- **`New post` does nothing, no `input[type=file]` appears** → professional accounts open a submenu (`Post / Live video / Ad`) → find the item by `innerText === "Post"` and click it. Not "restricted".
- **Dialog never loads** → `document.visibilityState` is `hidden` → `Page.bringToFront` first.
- **Fixed sleeps miss the dialog** (10+ s late) → poll `!!document.querySelector('input[type=file]')` for ~30 s, then gate on the crop screen text (`Crop` + `Next`).
- **A notifications modal swallows clicks** → dismiss `Not now` / `Şimdi değil` before starting.
- **`Next` or the file input does nothing** → `Next` is disabled until the upload finishes, and some builds render the input only after the "select from computer" tile; with several inputs in the DOM take the one inside `[role="dialog"]`.

**Captioning.** **Never caption "the newest post"** — if the dialog never opened, that is the *previous* post and gets overwritten; gate on the crop screen or a new permalink, else abort. A typed caption missing from the published post is the API case above.

**Long runs.** **`browser_exec` is cut at ~420 s** → a multi-post run cannot be one call → budgeted script (~360 s), exit cleanly, continue next call. From a shell it fails with `cdp is not defined`.

**UI quirks.**
- **Follow/message buttons:** coordinate clicks silently do nothing → find by `innerText`, click with JS, verify from the label (`Following` / `Requested`).
- **Display name is absent from `/accounts/edit/`** (bio and site only; it moved to Meta Accounts Center) → capture `POST /api/v1/web/accounts/edit/` from a bio save via the `Network` domain and replay it with `first_name` changed; `external_url` there is silently ignored.
- **`Emulation.setUserAgentOverride` / mobile metrics drop the session** → never change the UA; restart the browser unit and the cookie comes back logged in.
- **`browser_vault fill` refuses with "Could not determine the current page origin"** → it is looking at another tab → foreground the login tab, retry once; the vault is fine.
- **JS escaping**: keep blocks raw (`js(r"""…""")`) and run `python3 -W error::SyntaxWarning -m py_compile scripts/*.py` after edits.

## After the post

Report the permalink; offer to log caption + permalink + date in the user's calendar, and write new selector discoveries back into this skill. Never claim a story, Reel or DM landed without the platform-side evidence above.

## References

- `references/caption-guide.md` — register, structure, length, newline handling.
- `references/story-cards.md` — 1080x1920 safe areas, card anatomy, series logic.
- `references/meta-business-suite.md` — Page, IG link, story publishing, insights.
- `references/engagement-comments.md` — comment pass on other accounts' posts.
- `references/dm-outreach.md` — cold-DM gates, name extraction, cadence, corrections.
