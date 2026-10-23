# Brand kit template (fill one per brand)

Copy this file to `brand/<brand-slug>-kit.md`, fill every `TODO` slot, and treat it as the single
source of truth for every asset. If a slot is unknown, pull it from the live site's CSS (see step 2
of `SKILL.md`) — never guess a hex value or a font. An unfilled kit means the asset does not start.

---

## Identity
- Brand name (exact spelling used in assets): `TODO`
- Tagline / one-line description: `TODO`
- Primary product or offer: `TODO`
- Primary call to action (≤ 4 words): `TODO`
- Website / main link: `TODO`
- Audience (who this is for): `TODO`
- Language(s) of the assets + caption: `TODO`

## Logo
- File path: `brand/logo.svg` or `brand/logo.png` — `TODO`
- Source pixels: `TODO` (e.g. 1200x1200), transparent background: yes / no
- Has a wordmark: yes / no — if **no**, typeset the brand name beside the icon at `TODO` weight,
  `TODO` px, letter-spacing `TODO` em
- Minimum width on a 1080-wide canvas: `TODO` px (typical 160-260 px)
- Clear space around the logo: `TODO` px (typical ≥ 0.5x logo height)
- Placement: `TODO` (e.g. top-left, 96 px from each edge) / `TODO` (alternate for story)
- Logo variants allowed: full color / mono dark / mono light — `TODO`
- Never: stretch, recolor outside the listed variants, place on a busy photo, add shadows

## Palette
| Slot | Hex | Used for |
|---|---|---|
| canvas | `TODO` | page background |
| ink | `TODO` | headline + body text |
| ink-soft | `TODO` | secondary text |
| muted | `TODO` | labels, captions |
| surface | `TODO` | cards, panels |
| line | `TODO` | borders, dividers |
| accent | `TODO` | CTA button, highlight |
| accent-contrast | `TODO` | text on accent |
| dark | `TODO` | dark-mode cards, overlays |

Rules:
- Max `TODO` (typical 3) colors per asset, plus neutrals.
- Text contrast against its background ≥ `TODO`:1 (target 4.5:1 for body, 3:1 for ≥ 32 px).
- UI-mockup colors (chat bubbles, inbox, sent states) if the brand mimics a real app: `TODO`.

## Typography
| Slot | Family | Weight | Size on 1080-wide | Line height |
|---|---|---|---|---|
| headline | `TODO` | `TODO` (700-800) | `TODO` px (92-140) | `TODO` (e.g. 1.02) |
| body | `TODO` | `TODO` (400-500) | `TODO` px (34-44) | `TODO` (e.g. 1.45) |
| label / chip | `TODO` | `TODO` | `TODO` px (24-30) | `TODO` |
| accent serif (optional) | `TODO` | `TODO` | `TODO` px | `TODO` |

- Font source + how it is loaded: `TODO` (self-hosted file path, or the font CDN stylesheet link)
- Letter-spacing: headline `TODO` em (typical -0.02), body `TODO` em
- Text limits: headline ≤ `TODO` (typical 8) words, body ≤ `TODO` (typical 25) words
- Fallback stack if the webfont fails: `TODO`

## Layout
- Canvas sizes in use: `TODO` (1080x1350 feed, 1080x1080 square, 1080x1920 story/reel,
  1200x627 LinkedIn)
- Margin: `TODO` px (typical 96 feed / 120 story)
- Corner radius: `TODO` px for cards, `TODO` px for chips
- Shadow / elevation: `TODO` (or "none")
- Grid: `TODO` (e.g. single column, content top-aligned, CTA anchored 96 px above the safe bottom)

## Tone of voice
- Three adjectives: `TODO`, `TODO`, `TODO`
- Person / register: `TODO` (e.g. second person, informal, no jargon)
- Sentence length: `TODO` (e.g. ≤ 14 words)
- Emoji: `TODO` (allowed / sparing / never) — note that rendered assets should not rely on emoji
  glyphs, only captions
- Sample headline in voice: `TODO`
- Sample caption in voice: `TODO`
- Localization notes (diacritics, casing, punctuation): `TODO`

## Do
- `TODO` (e.g. show the product doing the job, not abstract shapes)
- `TODO` (e.g. one idea per card, CTA repeated on the last slide only)
- `TODO` (e.g. label every mockup as an example, invent names and numbers)

## Don't
- `TODO` (e.g. no stock photos, no AI-generated faces)
- `TODO` (e.g. no real customer data, screenshots, or phone numbers)
- `TODO` (e.g. no unapproved color/font, no logo in the Reels bottom 300 px)
- `TODO` (e.g. no claims, prices or guarantees that legal has not approved)

## Asset folder for this brand
- Templates: `assets/templates/` — `TODO` file names
- Renders: `assets/renders/` — named `YYYY-MM-DD_platform_slot_slide-NN-of-MM_slug_WxH.png`
- Copy sidecars: same basename + `.caption.txt` / `.alt.txt`
- Manifest consumed by the publish step: `TODO` path, `status:"draft"|"approved"`
