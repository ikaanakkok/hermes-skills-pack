# Meta Business Suite — the story and insights door

Instagram's own web app has no story composer and no view counts. The supported route is
indirect: **link the Instagram business account to a Facebook Page, then use Meta
Business Suite.** The Page home screen exposes `Create story`, `Create post`,
`Create reel` and `Connect Instagram`; story publishing and (through the Graph API)
reach/insight data sit behind that link.

## 1. Create the Facebook Page

`facebook.com/pages/creation/` — three fields: Page name, Category, Bio.

- **Name policy:** stylised capitalisation is rejected and the form suggests a plain
  spelling ("The name … is invalid. We suggest …"). Accept the suggestion; it is a
  capitalisation rule, not a block.
- **Category is a typeahead.** Setting a native value plus an `input` event leaves the
  button `aria-disabled="true"` and `Create Page` does nothing. The sequence that works:
  1. `fill_input('input[aria-label*="Category"]', '<sector>')` — `fill_input` does work
     in this field (unlike Instagram's login field); the list filters.
  2. Find the option by `innerText` inside `div[role="option"]` and click it with a **real
     coordinate click** (`Input.dispatchMouseEvent` mousePressed + mouseReleased). JS
     `.click()` does not update React state here.
  3. Verify `Input Category (required) is valid.` appears and `Create Page` no longer
     carries `aria-disabled`.
- Name and Bio fill with a native value setter plus `input`/`change`; they are not
  typeaheads.

Success signal: `Step 1 of 5 — Success! You've created <name>.` The remaining steps
(phone, address, hours) are optional — the phone field defaults to a US country code and
rejects numbers from other countries; leave it empty or change the code.

## 2. Business Suite

`business.facebook.com/latest/home` — without a Page it says "does not have access to any
Facebook Pages". Once a Page exists, `?asset_id=<page_id>` opens the Page home and the
story/post/reel buttons render.

`Connect Instagram` did not open a visible dialog with either JS `.click()` or a
coordinate click in a tested session (no new tab either). Remaining entry points, in
order of preference:

1. Business Suite → Settings → **Instagram accounts**.
2. `facebook.com/<page>/settings/` → **Linked accounts**.
3. `accountscenter.instagram.com` → add accounts.

Two things to verify the moment the link exists: the Page shows up under Instagram
Settings → linked accounts, and Business Suite's `Create story` really publishes an
Instagram story (not a Page story). Do not claim story publishing works before that
check.

## 3. Heavy Facebook pages lock the tab

Facebook and Business Suite pages can block the main thread with an open modal or a hung
request: even `js("1+1")` returns `Runtime.evaluate timed out` while CDP still looks
alive (`curl 127.0.0.1:9222/json/version` answers). Fix:

```bash
systemctl --user restart <browser-unit> && sleep 12
```

The Instagram cookie session survives in the profile; on the next call open the profile
and confirm `Edit Profile` is visible. Closing the tab alone is not enough — the harness
can still attach to the locked one.

## 4. Why it is worth it

The same link opens the Instagram Graph API: `media_type=STORIES` publishing, media
insights (reach/views) and an ad account. Views are the one number the web UI cannot
show, so "which reel worked" is only answerable through this path.
