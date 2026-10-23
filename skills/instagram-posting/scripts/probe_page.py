"""DOM inventory for a page the automation has to click through.

Runs inside a browser session already attached to a Chrome DevTools Protocol
endpoint (default http://127.0.0.1:9222, override with env CDP_URL). The profile
behind that endpoint must already be logged in -- this probe never logs in.

Use it at any step where the publish flow diverges, then repoint the selectors:

    exec(open("scripts/probe_page.py").read())

Prints every visible input/button/textarea/contenteditable with a best-effort
selector, plus the count of file inputs (hidden ones included) and open dialogs.
Read-only: it never clicks, types or navigates.
"""

import json

PROBE = r"""(() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const sel = el => {
    const parts = [el.tagName.toLowerCase()];
    if (el.getAttribute('type')) parts.push('[type="' + el.getAttribute('type') + '"]');
    if (el.getAttribute('role')) parts.push('[role="' + el.getAttribute('role') + '"]');
    if (el.getAttribute('aria-label')) parts.push('[aria-label*="' + el.getAttribute('aria-label').slice(0, 30) + '"]');
    if (el.getAttribute('placeholder')) parts.push('[placeholder*="' + el.getAttribute('placeholder').slice(0, 25) + '"]');
    return parts.join('');
  };
  const rows = [];
  const all = document.querySelectorAll('input, textarea, button, a[role="button"], [contenteditable="true"], [role="dialog"]');
  for (const el of all) {
    if (!vis(el)) continue;
    rows.push({
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute('type') || '',
      role: el.getAttribute('role') || '',
      label: (el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').slice(0, 60),
      text: (el.innerText || el.value || '').replace(/\s+/g, ' ').slice(0, 45),
      disabled: !!(el.disabled || el.getAttribute('aria-disabled') === 'true'),
      sel: sel(el),
    });
  }
  return rows;
})()"""

rows = js(PROBE)
print("url =", page_info().get("url"))
print("visibilityState =", js("document.visibilityState"))   # 'hidden' => the dialog will not load
print("file inputs in DOM:", js("document.querySelectorAll('input[type=file]').length"))
print("dialogs:", js("document.querySelectorAll('[role=dialog]').length"))
print("visible elements:", len(rows) if isinstance(rows, list) else "?")
if isinstance(rows, list):
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
else:
    print(rows)
