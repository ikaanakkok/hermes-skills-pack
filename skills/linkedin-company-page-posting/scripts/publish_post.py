"""Publish a photo post to a LinkedIn company page you administer.

Designed to be exec'd inside browser_exec (helpers `new_tab`, `goto_url`, `js`,
`page_info`, `wait_for_load`, `cdp` are already in scope). It can also be imported
by a CDP driver that provides the same helper names.

Config comes from env (see below) or from the matching `--flags`, so the file itself
holds no account-specific values.

Required:
  LINKEDIN_ORG_URL    page URL, e.g. https://www.linkedin.com/company/<your-page-slug>/
                      (the /admin/page-posts/ URL is derived from it)
  LINKEDIN_IMAGES     comma-separated absolute image paths
  LINKEDIN_TEXT_FILE  UTF-8 file holding the caption
Optional:
  LINKEDIN_ORG_NAME   expected page display name; if set, the composer header must
                      contain it (this is the "did I post as the page?" gate)
  LINKEDIN_COMMIT=1   actually click the submit button. Without it the script fills the
                      composer and stops (dry run) - always dry-run first.
  CDP_URL             informational; the browser already open in browser_exec wins.

Stops on the first divergence instead of guessing, so a failure leaves the composer
untouched for inspection.
"""

import argparse
import json
import os
import sys
import time

MAX_CHARS = 3000
MAX_IMAGES = 20


class StepFailed(Exception):
    pass


def need(cond, msg):
    if not cond:
        raise StepFailed(msg)
    print("  ok:", msg)


def _args():
    p = argparse.ArgumentParser(add_help=True, description="Post to a LinkedIn company page over CDP.")
    p.add_argument("--org-url", default=os.environ.get("LINKEDIN_ORG_URL", ""))
    p.add_argument("--org-name", default=os.environ.get("LINKEDIN_ORG_NAME", ""))
    p.add_argument("--images", default=os.environ.get("LINKEDIN_IMAGES", ""))
    p.add_argument("--text-file", default=os.environ.get("LINKEDIN_TEXT_FILE", ""))
    p.add_argument("--commit", action="store_true", default=os.environ.get("LINKEDIN_COMMIT", "") == "1")
    p.add_argument("--cdp-url", default=os.environ.get("CDP_URL", "http://127.0.0.1:9222"))
    # parse_known_args: browser_exec may pass its own argv, never let that abort the run
    args, _unknown = p.parse_known_args(sys.argv[1:])
    return args


ARGS = _args()
ORG_URL = ARGS.org_url.strip().rstrip("/")
ORG_NAME = (ARGS.org_name or "").strip().lower()
IMAGES = [p.strip() for p in (ARGS.images or "").split(",") if p.strip()]
TEXT_FILE = (ARGS.text_file or "").strip()
COMMIT = bool(ARGS.commit)

if not ORG_URL:
    raise SystemExit("LINKEDIN_ORG_URL (or --org-url) is required")
if not IMAGES:
    raise SystemExit("LINKEDIN_IMAGES (or --images) is required")
if not TEXT_FILE or not os.path.exists(TEXT_FILE):
    raise SystemExit(f"LINKEDIN_TEXT_FILE not found: {TEXT_FILE!r}")

# Admin post list: accepts a bare page URL or an already-admin URL.
if "/admin/" in ORG_URL:
    ADMIN = ORG_URL if ORG_URL.endswith("/") else ORG_URL + "/"
else:
    ADMIN = ORG_URL + "/admin/page-posts/published/"

CAPTION = open(TEXT_FILE, encoding="utf-8").read()
print(f"org: {ORG_URL}  cdp: {ARGS.cdp_url}")
print(f"caption: {len(CAPTION)} chars, {len(IMAGES)} images")
need(len(CAPTION) <= MAX_CHARS, f"caption <= {MAX_CHARS} chars")
for p in IMAGES:
    need(os.path.isfile(p), f"image exists: {p}")
need(len(IMAGES) <= MAX_IMAGES, f"<= {MAX_IMAGES} images")

# --- 1. company page -> admin posts (logged in as an admin, not the feed) ---
goto_url(ADMIN)
wait_for_load()
time.sleep(4)
url = page_info().get("url", "")
need("linkedin.com" in url, f"on linkedin ({url[:80]})")
need("/login" not in url and "checkpoint" not in url and "/uas/" not in url,
     "session alive (no login/challenge redirect)")

# --- 2. open the composer ---
clicked = js("""(() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const wanted = ['create post', 'start a post', 'post', 'gönderi oluştur', 'publicar'];
  const btns = [...document.querySelectorAll('button, a, [role="button"]')].filter(vis);
  const txt = b => (b.innerText || b.getAttribute('aria-label') || '').trim().toLowerCase();
  const hit = btns.find(b => wanted.includes(txt(b))) || btns.find(b => txt(b).includes('create post'));
  if (!hit) return 'NOT_FOUND';
  hit.click();
  return 'CLICKED: ' + txt(hit);
})()""")
need(isinstance(clicked, str) and clicked.startswith("CLICKED"), f"composer trigger ({clicked})")
time.sleep(3)

# The composer is a modal. Inspect it so we never post as the personal profile.
modal = js(r"""(() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const d = [...document.querySelectorAll('[role="dialog"]')].filter(vis);
  if (!d.length) return null;
  const t = d[d.length - 1];
  return { head: (t.innerText || '').replace(/\s+/g, ' ').slice(0, 200),
           editables: t.querySelectorAll('[contenteditable="true"], [role="textbox"]').length,
           files: t.querySelectorAll('input[type=file]').length,
           buttons: [...t.querySelectorAll('button')].filter(vis).map(b => (b.innerText || b.getAttribute('aria-label') || '').trim()).filter(Boolean).slice(0, 20) };
})()""")
need(modal is not None, "composer modal visible")
print("  modal:", json.dumps(modal, ensure_ascii=False))
need(modal.get("editables", 0) >= 1, "text editor present")
need(modal.get("files", 0) >= 1, "file input present")
# identity gate: the modal header must name the page, not the person
if ORG_NAME:
    need(ORG_NAME in (modal.get("head") or "").lower(),
         f"composer header names the page ({ORG_NAME!r} in {modal.get('head', '')[:60]!r})")
else:
    print("  WARNING: LINKEDIN_ORG_NAME unset - CONFIRM the header names the PAGE before committing")

# --- 3. upload images via CDP (works for hidden inputs too) ---
doc = cdp("DOM.getDocument", depth=-1)
root = doc["root"]["nodeId"]
node = cdp("DOM.querySelector", nodeId=root, selector='input[type=file]')
file_node = node.get("nodeId")
need(bool(file_node), "located input[type=file] node")
cdp("DOM.setFileInputFiles", nodeId=file_node, files=IMAGES)
print(f"  uploaded {len(IMAGES)} file(s), waiting for thumbnails")

for _ in range(30):
    time.sleep(2)
    state = js("""(() => {
      const t = [...document.querySelectorAll('[role="dialog"]')].pop();
      if (!t) return null;
      return { progress: t.querySelectorAll('[role="progressbar"], .artdeco-loader').length,
               imgs: t.querySelectorAll('img').length };
    })()""")
    if isinstance(state, dict) and state.get("progress") == 0 and state.get("imgs", 0) >= len(IMAGES):
        print("  thumbnails ready:", state)
        break
else:
    print("  WARNING: upload did not confirm within 60s - inspect before committing")

# --- 4. caption: focus the Quill editor, then insert text via CDP ---
focused = js("""(() => {
  const t = [...document.querySelectorAll('[role="dialog"]')].pop();
  if (!t) return 'NO_MODAL';
  const ed = t.querySelector('.ql-editor[contenteditable="true"]')
          || t.querySelector('[contenteditable="true"][role="textbox"]')
          || t.querySelector('[contenteditable="true"]');
  if (!ed) return 'NO_EDITOR';
  ed.focus();
  return 'FOCUSED';
})()""")
need(focused == "FOCUSED", f"editor focused ({focused})")

if js("document.activeElement && document.activeElement.getAttribute('contenteditable')") == "true":
    # insertText keeps "\n" as real paragraph/line breaks in Quill; paste + execCommand
    # can flatten the block structure, so they are only the fallback.
    cdp("Input.insertText", text=CAPTION)
else:
    js("document.execCommand('insertText', false, " + json.dumps(CAPTION) + ")")
time.sleep(1)

readback = js(r"""(() => {
  const t = [...document.querySelectorAll('[role="dialog"]')].pop();
  const ed = t && t.querySelector('.ql-editor, [contenteditable="true"]');
  if (!ed) return null;
  return { text: (ed.innerText || '').trim(),
           blocks: ed.querySelectorAll('p, li, br').length };
})()""")
need(isinstance(readback, dict), "editor readable after insert")
typed = (readback or {}).get("text", "")
print("  editor starts:", (typed or "")[:120].replace("\n", " / "))
flat = " ".join(CAPTION.split())
need(bool(typed) and flat[:40] in " ".join(typed.split()), "caption landed in the editor")
if "\n\n" in CAPTION:
    need((readback or {}).get("blocks", 0) >= 2, "line breaks survived (>= 2 blocks)")

if not COMMIT:
    print("DRY RUN - composer filled, nothing submitted. Set LINKEDIN_COMMIT=1 to publish.")
else:
    # --- 5. submit ---
    posted = js(r"""(() => {
      const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
      const t = [...document.querySelectorAll('[role="dialog"]')].pop();
      if (!t) return 'NO_MODAL';
      const wanted = ['post', 'publish', 'gönder', 'paylaş', 'publicar'];
      const label = x => (x.innerText || x.getAttribute('aria-label') || '').trim().toLowerCase();
      const live = [...t.querySelectorAll('button')].filter(vis)
        .filter(x => !x.disabled && x.getAttribute('aria-disabled') !== 'true');
      const b = live.find(x => wanted.includes(label(x))) || live.find(x => label(x).startsWith('post'));
      if (!b) return 'NO_SUBMIT_BUTTON: ' + live.map(label).join('|').slice(0, 120);
      b.click();
      return 'CLICKED';
    })()""")
    need(posted == "CLICKED", f"submit ({posted})")
    time.sleep(8)

    # --- 6. verify against the live admin list ---
    goto_url(ADMIN)
    wait_for_load()
    time.sleep(5)
    found = js(r"""(() => {
      const first = (document.body.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
      const links = [...document.querySelectorAll('a[href*="/feed/update/"]')]
        .map(a => a.href).slice(0, 5);
      return JSON.stringify({ head: first.slice(0, 12), links });
    })()""")
    print("VERIFY:", found)
    # Match on the hook, cut at a word boundary: feed previews truncate the body, so an
    # arbitrary 40-char slice would produce false negatives.
    hook = " ".join(CAPTION.strip().splitlines()[0].split()) if CAPTION.strip() else ""
    probe = hook if len(hook) <= 32 else hook[:32].rsplit(" ", 1)[0]
    body = " ".join((found or "").split()).lower()
    need(bool(probe) and probe.lower() in body,
         f"caption hook visible on the page feed ({probe!r})")
    links = (json.loads(found).get("links") if found else None) or ["(check manually)"]
    print("PUBLISHED. permalink:", links[0])
    print("STILL TODO: open the personal profile's recent activity and confirm this "
          "caption is NOT there - a page post must not come from the personal feed.")
