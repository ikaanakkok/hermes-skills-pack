# Cold DM discipline

Rules for opening a conversation with an account that does not know you. The failure mode
is never one bad message — it is a batch that reads like a template and gets the account
reported or rate-limited.

## 1. Before sending

- **The CTA must be live.** If the message says "reply X" or "message us on WhatsApp",
  confirm something actually answers that channel before sending a batch into it. Traffic
  into a dead funnel looks like "the offer did not work".
- Keep a candidate list and a send log as JSON. Read the log first and skip any account
  already marked sent — never message an account twice.
- No scraping for phone numbers or addresses; the public bio is enough.

## 2. Get the name right — the one real pitfall

The profile header's `innerText` lines are **not in a stable order**:
`[username, display name, "N posts", "25.7k followers", "N following", bio…]`.
A fixed index (e.g. `lines[3]`) grabs the counter line, and the message goes out as
"Hi 25.7k followers 👋" — an unrecoverable first impression.

Take the **first plausible** line from `lines[1:]`, skipping counters, the username and
separator lines:

```python
COUNTER = re.compile(r"^[\d.,]+\s*[km]?\s*(posts?|followers?|following)", re.I)

def profile_name(lines, username):
    for ln in lines[1:]:
        s = ln.strip()
        if not s or len(s) > 40 or s.lower() == username.lower() or COUNTER.match(s):
            continue
        if re.fullmatch(r"[·•\s]+", s):
            continue
        return s
    return username.replace("_", " ").replace(".", " ")
```

Gate the send on it: if the resolved name still matches `COUNTER`, **skip that target**.

Two more clean-ups, both visible in the message text:

- Location/separator suffix: `Salon X | Ankara` → `re.split(r"\s*[|•·]\s*", s)[0]`.
- Trailing emoji stack: `Studio Y 🏆🏆🏆` → strip `[\s\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+$`.

## 3. Context

Look for a city or a niche word in the bio. If it is there, open with it ("for studios in
<city>…"); if not, use a city-free sentence. Never invent a location or a detail.

## 4. Send and verify gates

1. If the profile has no `Message` button, **follow first and look again** — on many
   accounts the inbox only opens to followers. This is not the DM quota; tell the two
   apart by the `require_login`/401 signal. If the button is still missing, skip the
   target.
   - A separate case: *"This account can't receive your message because they don't allow
     new message requests from everyone."* That is their privacy setting, not your quota —
     drop the account and continue with others the same day.
2. Type with `Input.insertText`, then **read the composer back**: `innerText.length` must
   match what you sent (roughly > 80 chars for a normal message).
3. Click `div[aria-label="Send"]`; 3-4 s later read the composer again — **0-1 characters
   left means sent**, the full text still sitting there means it did not go.
4. Do not write `ok: true` to the log until all three signals agree.

Message skeleton (keep it short): who you are → what you do in one sentence → one
question or one CTA. No claims, no prices, no superlatives.

### Follow: coordinate clicks silently fail

Clicking the header `Follow` button with `Input.dispatchMouseEvent` often does nothing —
the button still reads `Follow` and there is no error (six attempts in a row produced
nothing). Find the button by text, click it with JS, and verify from the button label:

```js
(() => { const b=[...document.querySelectorAll('button,div[role="button"]')]
  .find(x=>/^(Follow|Following|Requested)$/i.test((x.innerText||'').trim())); if(!b) return 'none'; b.click(); return 'ok'; })()
// verify: label now reads Following / Requested
```

Wait 25-40 s between follows and log each one with a `ts` field.

### Two message variants (measure reply rate)

- `variant=1`: introduction + explicit CTA.
- `variant=2`: **ends with a question** the recipient can answer in one line — the
  shortest path to a reply on a cold DM.
- Store `variant` on every log row and compare after ~20 sends each. An auto-reply
  ("we received your message") is not a reply: mark it `type: auto_reply`.

## 5. When a message goes out wrong

- Do not chase **unsend**: in `/direct/inbox/` the thread rows do not match
  `a[href^="/direct/t/"]`, coordinate clicks land on the profile, and you burn the run.
- Instead return to the profile and send **one** short correction: "my previous message
  had the wrong name, sorry" + the correct one-liner + CTA. One message, then stop.
- Fix the log row (real name in `name`, note that a correction went out). Never leave a
  silent `ok: true` behind.

## 6. Quota

15-20 DMs per day, 45-90 s between actions, one session per day. End the run at the first
401/429/`require_login` signal (see SKILL.md, "Throttling").

## 7. Finding the endpoint behind a broken button

If a click does nothing, listen to the network instead of guessing endpoints:

```js
window.__netlog = [];
const of = window.fetch;
window.fetch = function(...a){ window.__netlog.push({m:(a[1]&&a[1].method)||'GET',
  u:String(a[0]), b:(a[1]&&a[1].body)?String(a[1].body):''}); return of.apply(this,a); };
// wrap XHR open/send the same way, then click, then:
JSON.stringify(window.__netlog)
```

This reveals the real request and its **payload field names**. Use it once to learn the
call — replaying it repeatedly is what grows a throttle.
