---
name: cloudflare-tunnel-domain-golive
description: "Use when taking a new domain live to a local origin via Cloudflare."
version: 1.0.0
author: hermes-skills-pack contributors
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [cloudflare, dns, domain, https, tunnel, launch, self-hosting]
    related_skills: [cloudflare-tunnel-deploy]
---

# Domain → Cloudflare → Tunnel → live HTTPS

Continuation of `cloudflare-tunnel-deploy`. That skill gets a tunnel running and the origin answering; this one takes a
**brand-new, registrar-registered domain** to public HTTPS. Both are prerequisites for a public launch — deploy proves
the origin, this proves the domain reaches it. Examples: `example.com` (apex), `app.example.com` (host).

## 1 — Point the domain at Cloudflare

- Dashboard → *Add a site* → **enter DNS records manually**. Importing the registrar's parked records pollutes the zone
  with dead entries that later shadow the tunnel CNAME. The free plan is enough.
- Copy the two assigned nameservers, switch the domain to Custom DNS at the registrar with exactly those two, then
  trigger the dashboard re-check.
- Order is registrar → TLD registry → resolvers. Poll, don't guess: `dig +short NS example.com` on two different public
  resolvers, plus `curl -s https://<tld-rdap-host>/rdap/domain/example.com` for the registry's own view.
- Resolver lag is not propagation failure: read the ANSWER TTL from `dig NS example.com` and wait it out. The registry
  updates minutes after the registrar save; public resolvers can trail for hours.
- Registrar email forwarding dies with the NS swap — rebuild it as Cloudflare Email Routing (destination address
  verifies, MX/SPF/DKIM auto-created) or accept the loss before switching.

**Exit:** `dig +short NS example.com` returns exactly the two assigned nameservers from both resolvers and the zone reads
Active.

## 2 — Create the hostname with the tunnel, never by hand

- `cloudflared tunnel route dns <tunnel> app.example.com` writes the proxied CNAME to `<tunnel-uuid>.cfargotunnel.com` —
  the only form that carries tunnel traffic. A hand-made A/CNAME to a server IP looks fine and serves nothing.
- Confirm **proxied** (orange cloud). DNS-only (grey) bypasses the edge, so Cloudflare never terminates TLS and the
  tunnel is never reached.
- The apex is a separate decision: a tunnel hostname does not cover it. Route `example.com` and `www.example.com`
  explicitly, or redirect them at the edge (phase 4).

**Exit:** `dig +short app.example.com` returns Cloudflare anycast addresses (104.x / 172.67.x), not the origin IP and not
a parking IP.

## 3 — SSL/TLS mode and the certificate wait

- Set SSL mode explicitly; never inherit the plan default. `GET /api/v4/zones/<zone_id>/settings/ssl`, then `PATCH` it
  with `{"value":"full"}`. Token needs Zone:Read + Zone Settings:Edit; zone id from `GET /api/v4/zones?name=example.com`.
- **Full (strict)** when the origin has a publicly trusted or Cloudflare Origin CA cert; **Full** for a self-signed
  origin; **Flexible** only for a plain-HTTP origin.
- Flexible is the classic footgun: the edge speaks HTTP to the origin, so an origin redirecting HTTP→HTTPS loops forever
  (ERR_TOO_MANY_REDIRECTS) and a TLS-only origin is unreachable. Fix the origin certificate and use Full.
- Universal SSL is issued **after** the zone goes Active — minutes to ~24h. Check the edge cert, not the badge:
  `openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null | openssl x509 -noout -issuer -dates`.
- 525 = edge→origin handshake failed (nothing TLS listening, wrong port/service). 526 = origin cert not trusted under
  Full (strict). Both are origin faults; Flexible "fixing" a 526 only hides an expired cert.

**Exit:** the edge cert covers the host and `curl -sI https://app.example.com` returns the origin's real status, no CF error page.

## 4 — Enforce HTTPS

- Zone setting `always_use_https=on` (settings API, `/settings/always_use_https`) redirects at the edge before traffic
  reaches the origin.
- Canonicalize `www` ↔ apex with a Redirect Rule at the edge, not in the app, so it survives origin deploys.
- Keep HSTS **off** until every subdomain is known-good; `includeSubDomains` locks browsers out of hosts you have not
  finished, and the max-age window is a one-way door.

**Exit:** `curl -sI http://app.example.com` returns 301 to the `https://` URL and the canonical host returns 200 without
a second hop.

## 5 — Verify from outside

Run from a machine that is neither the origin nor on its LAN:

- `dig +short app.example.com` → Cloudflare anycast IPs.
- `curl -sI https://app.example.com` → 200 with `server: cloudflare`; `curl -sv … 2>&1 | grep -i issuer` → the edge cert.
- `curl -sI --resolve app.example.com:443:<edge-ip> https://app.example.com` pins the edge, separating DNS from origin
  faults.
- A protected path still returns 401/403: origin auth survives the tunnel.

**Exit:** every check above passes externally. A dashboard "Active" banner is not evidence.

## 6 — Caching, after every deploy

- Edge-cached assets outlive deployments. Purge as part of the deploy: `POST /api/v4/zones/<zone_id>/purge_cache` with
  `{"files":[...]}` or `{"purge_everything":true}`.
- Read `cf-cache-status`: `HIT` right after a deploy means the purge did not land; `DYNAMIC` or `BYPASS` on HTML is
  healthy. Never cache HTML per host without a Cache Rule — the usual "stale for some visitors". Dev mode (3h) bypasses cache.

**Exit:** a changed asset serves new content and a fresh `cf-cache-status` from two networks.

## 7 — Rollback

Least destructive first:

1. **Take Cloudflare out of the path**: set the record DNS-only. On a tunnel CNAME this fails, which confirms the tunnel
   was serving it.
2. **Remove the DNS record**: `tunnel route dns` has no delete. Drop the CNAME in the dashboard or
   `DELETE /api/v4/zones/<zone_id>/dns_records/<record_id>` — before touching the tunnel, or the zone keeps advertising
   a dead hostname.
3. **Stop the tunnel**: `sudo systemctl disable --now cloudflared`, then `cloudflared tunnel cleanup <tunnel>`.
4. **Full retreat**: revert registrar nameservers to their previous values; the zone config survives a re-add.

**Exit:** `dig +short app.example.com` no longer returns Cloudflare addresses and `curl -sI https://app.example.com`
fails to connect.

## Pitfalls

- **Zone setting pages can render blank** while DNS and Cache pages work. Read/write through the dashboard's own session
  API from inside the page: `fetch('/api/v4/zones/<zone_id>/settings/ssl',{credentials:'include'})` — the session cookie
  is enough, no token header. Keep each evaluate to ~3 fetches (CDP calls time out near 5s); use `Promise.all`.
- **React/Base-UI forms drop programmatic input**: `fill_input` leaves the field empty. Use the native setter
  `Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set`, then dispatch `input` and `change`.
  A `button[role=combobox]` opens only on a real mouse click (`getBoundingClientRect()` + click at coordinates).
- **Email Address Obfuscation breaks behind a strict CSP.** A policy with no `script-src` (e.g. `default-src 'none'`)
  blocks the same-origin decode script, so `/cdn-cgi/l/email-protection#…` links dead-end on an error page. Append
  `script-src 'self'` and commit it to the config's repo copy, or the next reinstall reverts it.
- **Config owned by another repo**: host-side edits on a deploy target are temporary — report the exact lines to commit.
  If a setting "will not stick", look for a second writer (IaC, another operator) before re-saving.
