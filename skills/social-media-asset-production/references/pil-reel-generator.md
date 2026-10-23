# PIL scene-timeline Reels (no browser in the loop)

Alternative to the HTML + `setT(t)` + CDP-capture path. Use it when the video is typography, flat
cards and simple shapes (chat bubbles, calendar rows, CTA end cards) — i.e. when there is no CSS
layout worth keeping. It renders 1080x1920 (or 1080x1350) in pure Pillow, so it is immune to browser
load and keeps working while the same browser is busy elsewhere. Roughly 0.13 s per frame
(480 frames / 16 s ≈ 60-90 s, output 150-400 KB).

Palette, fonts and copy live in the config block at the top: change those five lines per brand and
nothing else. The script below is complete and runs with Pillow only (`pip install pillow`).

## File shape

```python
#!/usr/bin/env python3
"""Scene-timeline Reel generator. Pillow only."""
import os
import glob
from PIL import Image, ImageDraw, ImageFont

# ── CONFIG: replace with the brand kit values ─────────────────────────────────
SIZE      = (1080, 1920)      # (1080, 1350) feed 4:5 | (1080, 1920) story/reel
FPS, DUR  = 30, 16.0
FRAMES    = "frames"          # per-reel dir, cleared on every run
CANVAS, INK, MUTED  = "#FFFFFF", "#111111", "#666666"
SURFACE, ACCENT     = "#F5F5F5", "#2563EB"
ON_ACCENT, DARK     = "#FFFFFF", "#000000"
MARGIN   = 96 if SIZE[1] == 1350 else 120     # side padding in px
RADIUS   = 28                                 # card corner radius in px
SAFE_TOP, SAFE_BOT = (0, 0) if SIZE[1] == 1350 else (180, 300)  # platform UI in px
EYEBROW  = "01 — INTRO"
HEADLINE = ["One idea", "per card."]        # break headlines by hand, never auto-wrap
SUBHEAD  = "A short supporting line, two lines at most."
HEAD_PX, BODY_PX = 120, 42
CARDS    = [("Step one", "what it does"), ("Step two", "why it matters"), ("Step three", "what next")]
CTA      = "Start today"

W, H = SIZE

def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

CANVAS, INK, MUTED = rgb(CANVAS), rgb(INK), rgb(MUTED)
SURFACE, ACCENT, ON_ACCENT, DARK = rgb(SURFACE), rgb(ACCENT), rgb(ON_ACCENT), rgb(DARK)

# ── Fonts: first match wins, so ship a ttf next to the script if the OS has none ──
DIRS = ["/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/truetype/liberation/",
        "/System/Library/Fonts/", "/Library/Fonts/", "C:/Windows/Fonts/", "./fonts/"]
FILES = {"bold": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "arialbd.ttf"],
         "regular": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "arial.ttf"],
         "serif": ["DejaVuSerif.ttf", "LiberationSerif-Regular.ttf", "times.ttf"]}
_CACHE = {}

def F(kind, size):
    """Cached font. Raises a readable error instead of dying mid-render."""
    key = (kind, size)
    if key not in _CACHE:
        path = next((d + f for d in DIRS for f in FILES[kind] if os.path.exists(d + f)), None)
        if path is None:
            raise OSError("no %s font found in %s — add a .ttf to ./fonts/" % (kind, DIRS))
        _CACHE[key] = ImageFont.truetype(path, size)
    return _CACHE[key]

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3

def local(t, start, end):
    """0..1 progress inside a scene window; guards end <= start."""
    return 1.0 if end <= start else clamp((t - start) / (end - start))

def scene_alpha(t, start, end, fade=0.5):
    """Fade in/out envelope, or None when the scene is outside its window."""
    if t < start or t > end:
        return None
    return min(clamp((t - start) / fade), clamp((end - t) / fade))

def wrap(font, text, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.getlength(trial) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def fits(font, lines, maxw):
    """True when every line is inside the text column — run it on hand-broken headlines."""
    return all(font.getlength(ln) <= maxw for ln in lines)

def text(d, xy, s, font, color, alpha=1.0, anchor="la"):
    d.text(xy, s, font=font, fill=color + (int(255 * clamp(alpha)),), anchor=anchor)

def rounded(d, box, r, fill, alpha=1.0):
    d.rounded_rectangle(box, radius=r, fill=fill + (int(255 * clamp(alpha)),))

# ── Scenes: each returns an RGBA canvas, or None outside its window ───────────
def scene_title(t):
    a = scene_alpha(t, 0.0, 4.2)
    if a is None:
        return None
    img = Image.new("RGBA", SIZE, CANVAS + (255,))
    d = ImageDraw.Draw(img)
    head, body = F("bold", HEAD_PX), F("regular", BODY_PX)
    body_lines = wrap(body, SUBHEAD, W - 2 * MARGIN)
    if not fits(head, HEADLINE, W - 2 * MARGIN):
        raise ValueError("headline overflows the column: shorten or re-break")
    block = len(HEADLINE) * int(HEAD_PX * 1.1) + 40 + len(body_lines) * int(BODY_PX * 1.4)
    band = H - SAFE_TOP - SAFE_BOT
    y = SAFE_TOP + (band - block) // 2 - 60          # centred in the safe band
    text(d, (MARGIN, y - 80), EYEBROW, F("bold", 28), MUTED, a)
    for line in HEADLINE:
        text(d, (MARGIN, y), line, head, INK, a)
        y += int(HEAD_PX * 1.1)
    y += 40
    for line in body_lines:
        text(d, (MARGIN, y), line, body, MUTED, a)
        y += int(BODY_PX * 1.4)
    return img

def scene_cards(t):
    a = scene_alpha(t, 3.8, 9.4)
    if a is None:
        return None
    img = Image.new("RGBA", SIZE, CANVAS + (255,))
    d = ImageDraw.Draw(img)
    h, gap = 210, 32
    total = len(CARDS) * h + (len(CARDS) - 1) * gap
    band = H - SAFE_TOP - SAFE_BOT
    top = SAFE_TOP + (band - total) // 2              # centred in the safe band
    text(d, (MARGIN, top - 80), "02 — HOW IT WORKS", F("bold", 28), MUTED, a)
    for i, (title, sub) in enumerate(CARDS):
        p = ease_out(local(t, 3.8 + i * 0.35, 4.6 + i * 0.35))   # staggered, monotonic
        y = top + i * (h + gap) + int(28 * (1 - p))
        layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        rounded(dl, (MARGIN, y, W - MARGIN, y + h), RADIUS, SURFACE, a * p)
        text(dl, (MARGIN + 40, y + 44), title, F("bold", 56), INK, a * p)
        text(dl, (MARGIN + 40, y + 124), sub, F("regular", 34), MUTED, a * p)
        img.alpha_composite(layer)                                # fade = scaled alpha
    return img

def scene_cta(t):
    a = scene_alpha(t, 9.0, DUR + 0.5)
    if a is None:
        return None
    img = Image.new("RGBA", SIZE, DARK + (255,))
    d = ImageDraw.Draw(img)
    btn = F("bold", 64)
    bw, bh = btn.getlength(CTA) + 160, 156
    x0 = (W - bw) / 2
    y0 = H / 2 - SAFE_BOT / 2 - bh / 2
    rounded(d, (x0, y0, x0 + bw, y0 + bh), bh / 2, ACCENT, a)
    text(d, (W / 2, y0 + bh / 2), CTA, btn, ON_ACCENT, a, anchor="mm")
    text(d, (W / 2, y0 - 90), "Closing line, max six words.", F("regular", 40),
         (245, 245, 245), a, anchor="mm")
    return img

SCENES = [scene_title, scene_cards, scene_cta]   # order = time order, must not overlap

def frame(t):
    for sc in SCENES:
        img = sc(t)
        if img is not None:
            return img
    raise ValueError("no scene covers t=%.2fs — check the windows" % t)

# ── Render ───────────────────────────────────────────────────────────────────
def main():
    os.makedirs(FRAMES, exist_ok=True)
    for f in glob.glob(os.path.join(FRAMES, "*")):
        os.unlink(f)                                   # never leave stale frames behind
    n = int(FPS * DUR)
    for i in range(n):
        frame(i / FPS).convert("RGB").save(
            os.path.join(FRAMES, "f%05d.png" % i), optimize=True)
    print("%d frames %dx%d -> %s" % (n, W, H, FRAMES))
    print("ffmpeg -y -framerate %d -i %s/f%%05d.png -f lavfi -i "
          "anullsrc=channel_layout=stereo:sample_rate=44100 -shortest -c:v libx264 "
          "-profile:v high -pix_fmt yuv420p -crf 20 -preset medium -movflags +faststart "
          "-c:a aac -b:a 96k out.mp4" % (FPS, FRAMES))

if __name__ == "__main__":
    main()
```

For a **feed card** instead of a video, set `SIZE = (1080, 1350)` and save a single still:
`frame(DUR - 0.5).convert("RGB").save("card.png")` — same scenes, same tokens, no new template.

## Assembly
The script prints the exact command; `-shortest` stops at the images, a silent AAC track keeps the
container normal (a video-only stream can confuse players and upload checks), `+faststart` keeps the
moov atom up front.

## Pitfalls

- **Auto-wrap orphans the last word.** A 92-96 px headline wrapped automatically can leave a single
  short word on its own line, which reads as a typo. Break headlines by hand and assert with
  `fits()`; use `wrap()` only for body copy.
- **Check the real output, not the code.** Pick 3-4 timestamps, `resize` each frame and `paste` them
  side by side into one contact sheet, then look at it once — clipping, orphan words and off-centre
  cards all show up in one pass.
- **Clear the frames dir at the start.** One directory per reel plus unlinking leftovers keeps
  ffmpeg from ingesting frames of the previous reel (a longer old reel silently extends the new one).
- **Fonts must cover the language.** Diacritics such as `ı ş ğ ç ö ü` are missing from many system
  faces; check the path exists before building (`fc-list | grep -i <family>`), because
  `ImageFont.truetype` fails mid-render otherwise. Ship the ttf in `./fonts/` if unsure.
- **Text alpha needs an RGBA fill tuple** (`fill=(r, g, b, int(255 * p))`) — passing RGB silently
  ignores the fade.
- **Scene windows must be non-overlapping and monotonic** in time; `frame()` returns the first match,
  so a scene starting before the previous one ends simply never renders.
- **Stay inside the safe area.** On 1080x1920 the platform covers the top 180 px and the bottom
  300 px; anchor cards between `SAFE_TOP` and `H - SAFE_BOT`, never to the canvas edge.
- **A missing font is not a retry case.** A mid-render `OSError` means a bad path — fix the path.
