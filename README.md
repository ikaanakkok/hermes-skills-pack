# Hermes Skills Pack

A small pack of [Hermes Agent](https://hermes-agent.nousresearch.com/docs) skills for work that happens
in a **real, already-logged-in browser**: publishing and reading social accounts over the Chrome DevTools
Protocol, producing the images/video those posts need, school citation tooling, and taking a self-hosted
app live through a Cloudflare Tunnel.

Every skill here was written from debugging actual flows — the pitfalls are failure modes that were hit,
diagnosed, and then fixed, not guesses from documentation.

## What's inside

| Skill | Use it when |
|---|---|
| [`facebook-group-outreach`](skills/facebook-group-outreach/) | Posting to Facebook groups from a personal account, low-volume and rules-aware |
| [`instagram-posting`](skills/instagram-posting/) | Publishing feed posts, carousels, Reels, stories, comments and DMs on Instagram web |
| [`instagram-web-reading`](skills/instagram-web-reading/) | Reading an account's live state (counts, engagement, DM replies) and verifying a publish landed |
| [`linkedin-company-page-posting`](skills/linkedin-company-page-posting/) | Posting to a LinkedIn company page as an admin, without posting to the personal profile by accident |
| [`social-media-asset-production`](skills/social-media-asset-production/) | Producing post images and short Reels assets (HTML→PNG, Pillow) at exact platform sizes |
| [`noodletools-citations`](skills/noodletools-citations/) | Adding, fixing, and exporting NoodleTools citations and a works-cited list |
| [`cloudflare-tunnel-deploy`](skills/cloudflare-tunnel-deploy/) | Exposing a self-hosted app on a hostname through `cloudflared` + systemd |
| [`cloudflare-tunnel-domain-golive`](skills/cloudflare-tunnel-domain-golive/) | Taking a brand-new domain to public HTTPS on top of that tunnel |

Each skill is a folder with a `SKILL.md` (trigger, procedure, verification, pitfalls) plus optional
`references/` and `scripts/`.

## Requirements

- Hermes Agent, or any harness that exposes the browser helpers these skills call: `new_tab`, `goto_url`,
  `wait_for_load`, `js`, `cdp`, `page_info`, `fill_input`, `click_at_xy`.
- A Chromium instance started with `--remote-debugging-port=9222` (override with `CDP_URL`) whose profile is
  **already logged in** to the account you are operating. These skills never ask for, store, or type a password.
- Python 3.10+ and, for asset production, Pillow.
- `cloudflared` and a Cloudflare account for the two tunnel skills.

## Install

Skills are just directories. Copy or symlink them into your Hermes skills directory:

```bash
git clone https://github.com/<you>/hermes-skills-pack.git
cd hermes-skills-pack

# copy
mkdir -p ~/.hermes/skills
cp -r skills/* ~/.hermes/skills/

# or link, so `git pull` keeps them current
for d in skills/*/; do ln -sfn "$(pwd)/$d" ~/.hermes/skills/"$(basename "$d")"; done
```

Restart the session (or reload skills) and Hermes will pick up the new triggers.

## Configuration

Scripts never contain credentials. They read their target from the environment, so the same script works for
any account:

- `CDP_URL` — CDP endpoint (default `http://127.0.0.1:9222`)
- Instagram: `IG_HANDLE`, `IG_IMAGES`, `IG_TEXT_FILE`, `IG_COMMIT=1` to publish (dry run otherwise),
  `IG_API_CAPTION=0` to disable the caption API fallback
- LinkedIn: `LINKEDIN_ORG_URL`, `LINKEDIN_ORG_NAME`, `LINKEDIN_IMAGES`, `LINKEDIN_TEXT_FILE`,
  `LINKEDIN_COMMIT=1` to publish

Brand colours, fonts, and logos are **not** included: `social-media-asset-production/references/brand-kit-template.md`
is an empty template you fill in per brand.

## Ground rules baked into these skills

Automating a real account is not a growth hack. The skills enforce:

- **Approval before publish** — exact caption, image order, and target shown to the human first.
- **Verification after publish** — a clicked Share button is not a post; a permalink is.
- **Deliberate volume limits** — small batches, spaced out, varied wording. No scraping, no member-list
  harvesting, no mass identical posting, no CAPTCHA solving.
- **Hard stop on challenge** — an account warning, action block, or security challenge stops the whole queue.
- **Rules are read, not assumed** — if a group or platform forbids promotion, the answer is no post.

You are responsible for the accounts you drive and for each platform's terms. Use these on accounts you own
or are authorised to operate.

## Contributing

Issues and PRs welcome, especially new **verified** pitfalls: state the symptom, why it happens, and the fix
that worked. Keep account-specific data (handles, tokens, paths, customer data) out of PRs.

## License

MIT — see [LICENSE](LICENSE).
