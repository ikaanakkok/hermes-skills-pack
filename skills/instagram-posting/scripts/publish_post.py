"""Publish a photo post or carousel to Instagram over CDP.

Drives a Chrome DevTools Protocol endpoint (default http://127.0.0.1:9222, override
with env CDP_URL) and requires a profile that is ALREADY LOGGED IN to Instagram --
this script never touches credentials.

Exec it inside the browser harness so `js`, `cdp`, `page_info`, `goto_url` and
`wait_for_load` are in scope (running it as a plain `python3 file.py` fails with
`cdp is not defined`):

    exec(open("scripts/publish_post.py").read())

Configuration (placeholders -- set your own values):
  IG_IMAGES       comma-separated absolute image paths, order = carousel order
  IG_TEXT_FILE    UTF-8 file holding the caption
  IG_COMMIT=1     actually click Share; without it the script stops on the final
                  screen (dry run -- always dry-run first)
  IG_HANDLE       handle to publish to and verify on (required, without the at-sign)
  IG_API_CAPTION  "0" disables the post-publish caption API fallback (default on)

Labels are matched in English and Turkish: the composer follows the account locale.
Every step asserts what it expects and raises StepFailed on divergence instead of
clicking blind.
"""

import json
import os
import time

# --- configuration (placeholders: fill in from env or edit here) ------------
IMAGES = [p.strip() for p in os.environ.get("IG_IMAGES", "").split(",") if p.strip()]
TEXT_FILE = os.environ.get("IG_TEXT_FILE", "").strip()
COMMIT = os.environ.get("IG_COMMIT", "") == "1"
API_CAPTION = os.environ.get("IG_API_CAPTION", "1") != "0"
HANDLE = os.environ.get("IG_HANDLE", "").strip()

NEXT = ["next", "ileri"]
SHARE = ["share", "paylaş"]
CREATE = ["create", "oluştur"]
POST_ITEM = ["post", "gönderi"]          # submenu item on professional accounts
CAPTION_LIMIT = 2200
MAX_IMAGES = 10


class StepFailed(Exception):
    pass


def need(cond, msg):
    if not cond:
        raise StepFailed(msg)
    print("  ok:", msg)


def wait_until(fn, seconds, what):
    deadline = time.time() + seconds
    while time.time() < deadline:
        val = fn()
        if val:
            return val
        time.sleep(2)
    raise StepFailed(f"timed out waiting for {what}")


def click_button(labels, scope="dialog"):
    """Click the first enabled, visible button/role=button whose text matches."""
    return js(
        "(() => {\n"
        "  const wanted = " + json.dumps(labels) + ";\n"
        "  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };\n"
        "  const root = " + json.dumps(scope) + " === 'dialog'\n"
        "    ? ([...document.querySelectorAll('[role=\"dialog\"]')].pop() || null)\n"
        "    : document;\n"
        "  if (!root) return 'NO_DIALOG';\n"
        "  const els = [...root.querySelectorAll('button, [role=\"button\"], div[tabindex]')].filter(vis);\n"
        "  const hit = els.find(b => wanted.includes((b.innerText || '').trim().toLowerCase())\n"
        "                            && !b.disabled && b.getAttribute('aria-disabled') !== 'true');\n"
        "  if (!hit) return 'NOT_FOUND';\n"
        "  hit.click();\n"
        "  return 'CLICKED: ' + (hit.innerText || '').trim();\n"
        "})()"
    )


def dialog_text():
    return js(r"""(() => {
      const d = [...document.querySelectorAll('[role="dialog"]')].pop();
      return d ? (d.innerText || '').replace(/\s+/g, ' ') : '';
    })()""")


def caption_field():
    return js(r"""(() => {
      const d = [...document.querySelectorAll('[role="dialog"]')].pop() || document;
      const el = d.querySelector('textarea[aria-label]') || d.querySelector('textarea')
              || d.querySelector('[contenteditable="true"]') || d.querySelector('[role="textbox"]');
      if (!el) return '';
      el.focus();
      return el.tagName === 'TEXTAREA' ? 'TEXTAREA' : 'CONTENTEDITABLE';
    })()""")


def profile_permalinks():
    return js(r"""(() => {
      return [...new Set([...document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]')]
        .map(a => (a.getAttribute('href') || '').split('?')[0])
        .filter(h => /^\/(p|reel)\/[^\/]+\/$/.test(h)))].slice(0, 24);
    })()""") or []


def api_set_caption(code, text):
    """Rewrite a published caption. Returns a short status string."""
    expr = r"""(() => {
      const code = __CODE__, text = __TEXT__;
      return fetch('/p/' + code + '/', {credentials: 'same-origin'})
        .then(r => r.text())
        .then(html => {
          const m = html.match(/"media_id":"(\d+)"/);
          if (!m) return 'NO_MEDIA_ID';
          const csrf = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
          return fetch('/api/v1/media/' + m[1] + '/edit_media/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {'content-type': 'application/json',
                      'x-csrftoken': csrf,
                      'x-ig-app-id': '936619743392459'},
            body: JSON.stringify({caption_text: text}),
          }).then(r => 'HTTP ' + r.status);
        })
        .catch(e => 'ERR ' + e.message);
    })()"""
    expr = expr.replace("__CODE__", json.dumps(code)).replace("__TEXT__", json.dumps(text))
    try:
        out = cdp("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
        return str(out.get("result", {}).get("value"))
    except Exception as exc:                     # noqa: BLE001 - report, never abort here
        return f"ERR {exc}"


# --- 0. validate input ------------------------------------------------------
if not IMAGES:
    raise SystemExit("IG_IMAGES is required")
if not TEXT_FILE or not os.path.exists(TEXT_FILE):
    raise SystemExit(f"IG_TEXT_FILE not found: {TEXT_FILE!r}")
if not HANDLE:
    raise SystemExit("IG_HANDLE is required (the handle you publish to, without the at-sign)")

CAPTION = open(TEXT_FILE, encoding="utf-8").read()
print(f"caption: {len(CAPTION)} chars, {len(IMAGES)} image(s), target profile: {HANDLE}")
need(len(CAPTION) <= CAPTION_LIMIT, f"caption <= {CAPTION_LIMIT} chars")
need(len(IMAGES) <= MAX_IMAGES, f"<= {MAX_IMAGES} images (carousel)")
for p in IMAGES:
    need(os.path.isfile(p), f"image exists: {p}")

# --- 1. baseline: what the profile already shows (pre-publish truth) --------
goto_url(f"https://www.instagram.com/{HANDLE}/")
wait_for_load()
time.sleep(4)
need("accounts/login" not in (page_info().get("url") or ""), "session alive")
BEFORE = set(profile_permalinks())
print(f"  existing permalinks on profile: {len(BEFORE)}")

# --- 2. open the create flow ------------------------------------------------
goto_url("https://www.instagram.com/")
wait_for_load()
time.sleep(4)

# a fresh session opens a notifications modal that swallows every later click
js("""(() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const b = [...document.querySelectorAll('button')].filter(vis)
    .find(x => ['not now', 'şimdi değil'].includes((x.innerText || '').trim().toLowerCase()));
  if (b) b.click();
  return !!b;
})()""")
time.sleep(1)

clicked = click_button(CREATE, scope="document")
need(str(clicked).startswith("CLICKED"), f"create menu opened ({clicked})")
time.sleep(3)

# professional accounts open a submenu: Post / Live video / Ad. Without the Post
# click no dialog ever appears and no file input is rendered.
try:
    wait_until(lambda: js("document.querySelectorAll('[role=\"dialog\"]').length"), 6, "dialog")
except StepFailed:
    print("  submenu ->", click_button(POST_ITEM, scope="document"))
    time.sleep(2)

# some builds only render the input after the "select from computer" tile
if js("document.querySelectorAll('input[type=file]').length") == 0:
    print("  picker ->", click_button(["select from computer", "bilgisayarınızdan seç"], scope="document"))

# --- 3. upload via CDP (ignore the misleading accept="image/*") -------------
wait_until(lambda: js("document.querySelectorAll('input[type=file]').length"), 30, "file input")

doc = cdp("DOM.getDocument", depth=-1)
root = doc["root"]["nodeId"]
node = cdp("DOM.querySelector", nodeId=root,
           selector='[role="dialog"] input[type=file]')
if not node.get("nodeId"):
    node = cdp("DOM.querySelector", nodeId=root, selector='input[type=file]')
need(bool(node.get("nodeId")), "located input[type=file]")
cdp("DOM.setFileInputFiles", nodeId=node["nodeId"], files=IMAGES)
print(f"  uploading {len(IMAGES)} file(s)")

# gate on the crop screen, not on a fixed sleep
wait_until(lambda: bool(js(r"""(() => {
  const t = (document.querySelector('[role="dialog"]') || {}).innerText || '';
  return /crop|kırp/i.test(t) && /next|ileri/i.test(t);
})()""")), 120, "crop screen")

# --- 4. walk to the edit screen (one or two Next screens depending on build) -
for step in (1, 2):
    if js(r"""(() => {
        const d = document.querySelector('[role="dialog"]') || document;
        return !!(d.querySelector('textarea, [contenteditable="true"], [role="textbox"]'));
    })()"""):
        break
    res = wait_until(
        lambda: (lambda r: r if str(r).startswith("CLICKED") else None)(click_button(NEXT)),
        60, f"next #{step} enabled")
    print(f"  next #{step}: {res}")
    time.sleep(3)

# --- 5. caption -------------------------------------------------------------
field = caption_field()
need(field in ("TEXTAREA", "CONTENTEDITABLE"), f"caption field focused ({field})")
if field == "TEXTAREA":
    cdp("Input.insertText", text=CAPTION)
else:
    # Lexical: Input.insertText drops newlines; per-line inserts keep the breaks
    js("document.activeElement.focus()")
    for i, line in enumerate(CAPTION.split("\n")):
        if i:
            cdp("Input.dispatchKeyEvent", type="rawKeyDown", key="Enter",
                windowsVirtualKeyCode=13, nativeVirtualKeyCode=13)
            cdp("Input.dispatchKeyEvent", type="keyUp", key="Enter",
                windowsVirtualKeyCode=13, nativeVirtualKeyCode=13)
        if line:
            cdp("Input.insertText", text=line)
time.sleep(1)

typed = js(r"""(() => {
  const d = [...document.querySelectorAll('[role="dialog"]')].pop() || document;
  const el = d.querySelector('textarea') || d.querySelector('[contenteditable="true"]');
  return el ? (el.value || el.innerText || '').trim() : '';
})()""")
print("  caption field head:", (typed or "")[:100].replace("\n", " / "))
need(len(typed or "") >= min(40, len(CAPTION.strip())), "caption text landed in the editor")

# --- 6. dry run stops here --------------------------------------------------
if not COMMIT:
    print("DRY RUN - on the final share screen, nothing published. Set IG_COMMIT=1.")
    raise SystemExit(0)

res = click_button(SHARE)
need(str(res).startswith("CLICKED"), f"share ({res})")
print("  waiting for the post to land")

# --- 7. verify: a NEW permalink on the profile, not a toast -----------------
time.sleep(10)
goto_url(f"https://www.instagram.com/{HANDLE}/")
wait_for_load()

def new_link():
    fresh = [h for h in profile_permalinks() if h not in BEFORE]
    return fresh[0] if fresh else None

try:
    rel = wait_until(new_link, 120, "a new permalink on the profile")
except StepFailed:
    print("PUBLISH UNCONFIRMED - no new permalink appeared. Check the app before retrying.")
    raise
shortcode = rel.strip("/").split("/")[-1]
permalink = f"https://www.instagram.com{rel}"
print("PUBLISHED:", permalink)

# --- 8. caption fallback: typed captions often do not survive publish -------
if API_CAPTION:
    head = " ".join(CAPTION.split())[:40]
    seen = js("document.body.innerText")
    if head and head not in " ".join((seen or "").split()):
        print("  caption missing from the published post -> API edit:", api_set_caption(shortcode, CAPTION))
        goto_url(permalink)
        wait_for_load()
        time.sleep(4)
        fixed = js("document.body.innerText") or ""
        need(" ".join(CAPTION.split())[:40] in " ".join(fixed.split()), "caption present after API edit")
    else:
        print("  caption already present on the published post")
