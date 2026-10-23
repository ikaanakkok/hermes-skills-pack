---
name: social-media-asset-production
description: "Use when producing social post images or short Reels video assets."
version: 1.0.0
author: hermes-skills-pack contributors
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [social-media, design, images, video, reels, pillow, html-to-image]
    related_skills: [instagram-posting, linkedin-company-page-posting, baoyu-infographic]
---

# Social media asset production (HTML render + ffmpeg + Pillow)

Produce post images and short vertical video fully locally: one HTML/CSS template rendered in a
headless browser at exact pixel dimensions, or a pure-Pillow scene timeline; frames assembled with
ffmpeg. No stock imagery, no API cost.

Roles: copy and content decisions arrive as a brief; the agent produces every visual; a human
approves each asset before anything is published.

## 1. Output sizes — fix these before designing
| Slot | Pixels | Use |
|---|---|---|
| feed 4:5 | 1080x1350 | default feed image, safest reach |
| feed 1:1 | 1080x1080 | only when the grid needs squares |
| story / reel | 1080x1920 | 9:16, full bleed, 6-16 s |
| LinkedIn card | 1200x627 | 1.91:1 link or feed card |
| LinkedIn square | 1200x1200 | carousel slide |

Never upscale a 1080-wide render to 1350, or reuse a 1080x1920 story frame as a feed image: that is a
different layout, not a crop. One template per slot.

## 2. Brand kit first — never invent colors or fonts
Fill `references/brand-kit-template.md` once per brand, then pull real tokens from the live site:
```bash
curl -sL https://site.example -o /tmp/page.html
grep -oE '\-\-[a-z0-9-]+:[^;"]{1,60}' /tmp/page.html    # CSS variables
grep -oE 'fonts\.googleapis[^"]*' /tmp/page.html        # font stack
```
Icon-only logos with no wordmark need the brand name typeset beside them (700-800 weight, -0.02em).

## 3. Template rules (HTML path)
- `html,body{width:1080px;height:1350px;margin:0;overflow:hidden}` — exact px, nothing scrollable.
- Content margin: 96 px on feed, 120 px on 1080x1920. Body text 34-44 px, headline 92-140 px.
- Google Fonts via `<link>` load from `file://`; reference local images by relative path.
- Text limits per card: headline ≤ 8 words / 3 lines, body ≤ 25 words, one CTA ≤ 4 words.
  Caption limits: feed caption 2200 chars (first 125 shown), LinkedIn post 3000 (first 210 shown),
  alt text 125 chars.
- Any mockup (chat, dashboard, receipt) is labelled as an example and uses invented names.

## 4. Render a still and verify the pixel size
```python
new_tab("file:///abs/path/assets/post.html"); wait_for_load()
cdp('Emulation.setDeviceMetricsOverride', width=1080, height=1350,
    deviceScaleFactor=1, mobile=False)
# poll js("document.fonts.status") until "loaded" — 1 s apart, 10 tries
cdp('Page.bringToFront')
capture_screenshot(path="assets/post.png")          # helper allows 60 s
```
Browser-free equivalent: `chromium --headless --hide-scrollbars --force-device-scale-factor=1
--window-size=1080,1350 --screenshot=assets/post.png file:///abs/path/post.html`.

Always verify what landed on disk — a wrong viewport silently yields 800x600:
`python3 -c "from PIL import Image;print(Image.open('assets/post.png').size)"`.

## 5. QC every render, then iterate
`vision_analyze` the PNG: fonts applied, nothing clipped, alignment, mockup details. Use
`region=[x1,y1,x2,y2]` crops instead of re-rendering; 1-2 rounds is normal. Vision is advisory —
resolve convention disputes against the reference product, not against the model.

## 6. Video
**HTML route** — drive all animation from one pure JS function `setT(t)`; no CSS transitions,
no keyframes. Preview 3 timestamps, then capture the full set at 30 fps:
```python
FPS, DUR = 30, 16.0
for i in range(int(FPS * DUR)):
    js("setT(%.3f)" % (i / FPS))
    r = cdp('Page.captureScreenshot', format='jpeg', quality=92,
            captureBeyondViewport=False, _response_timeout=60)
    open("frames/f%05d.jpg" % i, "wb").write(base64.b64decode(r['data']))
```
**Pillow route** — when the video is typography, flat cards and shapes, skip the browser:
`references/pil-reel-generator.md` (1080x1920 or 1080x1350, ~0.13 s/frame).
```bash
ffmpeg -y -framerate 30 -i frames/f%05d.jpg -c:v libx264 -pix_fmt yuv420p -crf 18 \
  -preset medium -movflags +faststart out.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate \
  -of csv=p=0 out.mp4                                    # 1080,1920,30/1
ffmpeg -y -ss 7.8 -i out.mp4 -frames:v 1 check.png        # vision-check the real output
```
Reel safe area on 1080x1920: readable content between y=180 and y=1620 (top 180 px = status and
progress, bottom 300 px = caption and actions, right 140 px = action rail); ≥ 1.2 s of text at 30 fps.

## 7. Naming and caption pairing
```
assets/2026-05-01_ig_feed-4x5_slide-01-of-04_spring-launch_1080x1350.png
assets/2026-05-01_ig_feed-4x5_slide-01-of-04_spring-launch_1080x1350.caption.txt
assets/2026-05-01_ig_feed-4x5_slide-01-of-04_spring-launch_1080x1350.alt.txt
manifest.json
```
Pattern `YYYY-MM-DD_platform_slot_slide-NN-of-MM_slug_WxH`; sidecars carry the copy so a caption edit
never touches the image. `manifest.json` (`{file, platform, slot, order, w, h, caption, alt,
status:"draft"|"approved"}`) is the only input a publish step reads, and it must skip drafts. Keep
template + output pairs together so a copy edit is one re-render away (still: seconds, 480 frames: ~40 s).

## Pitfalls
- **Raw `cdp()` calls time out after 5 s** — big captures fail with "timed out waiting for the
  daemon". Use the `capture_screenshot()` helper or pass `_response_timeout=60`.
- **Wait for fonts** (`document.fonts.status == "loaded"`) or the headline silently renders in a
  serif fallback and the whole asset looks subtly wrong.
- **Avoid emoji glyphs.** A long-running browser caches its font list at startup, so a newly
  installed color-emoji font still renders badly; build glyphs in CSS (inline-flex circle + check mark).
- **Clipped text** comes from fixed heights and `overflow:hidden`. Give text blocks `max-width`
  (888 px on 1080x1350) and no fixed height; assert `scrollHeight <= clientHeight` per block in JS.
- **Orphan words**: auto-wrap at 90-140 px headlines leaves one short word on the last line. Measure
  with `font.getlength()` (PIL) or `getBoundingClientRect()` (JS) and break lines by hand.
- **Mid-animation frames look broken by design** (half-faded chips) — also inspect the final frame.
- **Renders are not feed-ready by default**: story frames are 1080x1920, feed needs 1080x1350.
  Measure every existing file before promising a calendar
  (`ffprobe -v error -show_entries stream=width,height -of csv=p=0:s=x f`) and report ready vs
  to-be-produced separately.
- **Review many renders in one look**: contact sheet via ffmpeg
  `scale=W:H:force_original_aspect_ratio=decrease,pad=W:H:(ow-iw)/2:(oh-ih)/2` then `hstack`
  (the pad step is mandatory or mixed heights fail).
- **Deliver as `MEDIA:` paths** — PNG as image, MP4 as video — flagged draft pending approval.

## Related
- `references/brand-kit-template.md` (blank per-brand token sheet) and
  `references/pil-reel-generator.md` (runnable Pillow generator).
- Publishing is a separate, approval-gated browser flow; this skill stops at approved files.
