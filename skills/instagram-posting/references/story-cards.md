# Story cards (1080x1920)

One or two stories a day keep an account visible without inflating the feed. Rendered as
PNGs and posted as a story — never dropped into the feed.

## Safe area

- Canvas 1080x1920. Leave **250 px** at the top and **~230 px** at the bottom empty: the
  story UI (account name, progress bar, reply box) covers both ends. A 150 px top
  padding puts your logo underneath the account name.
- Text block in a single left-aligned column; the CTA block pinned to the bottom
  (`margin-top:auto`).
- Keep the important line out of the middle third if the card will also be cropped for a
  highlight cover.

## Card anatomy

1. Small logo + account name at the top (56 px icon, 34 px type).
2. `kicker`: 30 px, uppercase, wide letter-spacing, grey.
3. Headline: serif, 92 px (drop to 76 px when the text passes ~30 characters), line
   height 1.08.
4. `sub`: 40 px, grey, 2-3 lines maximum.
5. Option list: white cards, 1.5 px border, 28 px radius, 38 px text.
6. CTA: solid block, centred; the phone/URL 56 px bold, a 30 px muted line beneath.

## Three-card series

1. **Hook** — one concrete moment ("The message arrived at 23:40.").
2. **Question/list** — three options the viewer recognises themselves in. Poll stickers
   cannot be placed from the web, so ask the question in the text.
3. **CTA** — what it is + phone + site.

## Rendering

Write the template with plain-text placeholders (`__HEADLINE__`) and fill it with
`.replace()`. **Do not use `str.format`**: CSS braces are parsed as format fields and you
get `KeyError: 'box-sizing'`. Convert HTML to PNG through the browser harness
(`render_html(html, png, 1080, 1920)`), not from a bare terminal — a plain headless call
often lacks the fonts you specified.

## Publishing

Web stories are a separate path from the feed. After the file is selected, **read the
dialog title**: it must say `Create story` / `Story`. If the feed dialog opened, stop —
publishing a story card to the feed damages the grid and cannot be undone by deleting
(insights and tags go with it).

Verify afterwards by the ring around the profile photo on the account's own profile, or
in Meta Business Suite. Instagram's own web UI has no story composer at all — see
`references/meta-business-suite.md` for the only working door.
