"""Live DOM inventory of the LinkedIn share composer.

Run inside browser_exec with the composer modal visible:

    exec(open("<skill-dir>/scripts/probe_composer.py").read())

Prints visible inputs, buttons, contenteditables and dialogs so publish_post.py can be
repointed when LinkedIn ships UI changes. Read-only: it never clicks submit and never
types into the editor.
"""

import json

PROBE = r"""(() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const sel = el => {
    if (el.id && !el.id.startsWith('\u00ab')) return '#' + CSS.escape(el.id);
    const parts = [el.tagName.toLowerCase()];
    if (el.getAttribute('role')) parts.push('[role="' + el.getAttribute('role') + '"]');
    if (el.getAttribute('type')) parts.push('[type="' + el.getAttribute('type') + '"]');
    if (el.getAttribute('aria-label')) parts.push('[aria-label*="' + el.getAttribute('aria-label').slice(0, 30) + '"]');
    return parts.join('');
  };
  const rows = [];
  const all = document.querySelectorAll('input, textarea, button, [contenteditable="true"], [role="textbox"], [role="dialog"]');
  for (const el of all) {
    if (!vis(el)) continue;
    rows.push({
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute('type') || '',
      role: el.getAttribute('role') || '',
      label: (el.getAttribute('aria-label') || '').slice(0, 60),
      text: (el.innerText || el.value || '').replace(/\s+/g, ' ').slice(0, 50),
      disabled: !!(el.disabled || el.getAttribute('aria-disabled') === 'true'),
      sel: sel(el),
      cls: (el.className || '').toString().slice(0, 80),
    });
  }
  return rows;
})()"""

rows = js(PROBE)
print("url =", page_info().get("url"))
print("file inputs in DOM:", js("document.querySelectorAll('input[type=file]').length"))
print("dialogs in DOM:", js("document.querySelectorAll('[role=\"dialog\"]').length"))
print("visible elements:", len(rows) if isinstance(rows, list) else "?")
if isinstance(rows, list):
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
else:
    print(rows)
