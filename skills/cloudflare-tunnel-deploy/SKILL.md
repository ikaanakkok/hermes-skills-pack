---
name: cloudflare-tunnel-deploy
description: "Use when exposing a self-hosted app through a Cloudflare Tunnel."
version: 1.0.0
author: hermes-skills-pack contributors
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [cloudflare, tunnel, cloudflared, dns, self-hosting, systemd, reverse-proxy]
    related_skills: [cloudflare-tunnel-domain-golive]
---

# Exposing a self-hosted app through a Cloudflare Tunnel

Install, authenticate, create the tunnel, write ingress, route DNS, run under systemd, verify from both
sides. Zone creation and nameserver cutover are `cloudflare-tunnel-domain-golive`'s job: the tunnel needs a zone already **Active**.

## Rules

- One hostname → one `service:` in `ingress`; use a reverse-proxy vhost if the app needs its own headers, TLS or auth.
- Never hand-create the hostname record: `cloudflared tunnel route dns` creates it and keeps it bound to the tunnel.
- The catch-all `- service: http_status:404` is the **last** rule; anything below it never matches.
- `cert.pem` is account-scoped and `<UUID>.json` is tunnel-scoped; both are secrets — no chat, no commit.

## 1. Install

```bash
# Debian/Ubuntu
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt-get update && sudo apt-get install -y cloudflared
# any Linux, static binary (macOS: brew install cloudflared)
sudo curl -fsSL -o /usr/local/bin/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && sudo chmod +x /usr/local/bin/cloudflared
```

Check the path the unit will run, not just `command -v`: `systemctl cat cloudflared | grep ExecStart`. A unit
expecting `/usr/local/bin/cloudflared` while the binary lives elsewhere is a symlink fix, not a reinstall; confirm with `cloudflared --version`.

## 2. Authenticate (browser-issued certificate)

```bash
cloudflared tunnel login
```

Prints a `https://dash.cloudflare.com/argotunnel?...` URL and serves a loopback callback: open it, pick the zone,
**Authorize** → "Cloudflared has installed a certificate" + `~/.cloudflared/cert.pem`. On a headless host forward
that port (`ssh -L <port>:localhost:<port> <host>`), or run `login` on a browser machine and copy `cert.pem` over.
A missing `cert.pem` later surfaces as an auth error, never as a config error.

## 3. Create the tunnel

```bash
cloudflared tunnel create <TUNNEL_NAME>     # -> "Created tunnel <TUNNEL_NAME> with id <UUID>"
sudo mkdir -p /etc/cloudflared && sudo mv ~/.cloudflared/<UUID>.json /etc/cloudflared/
sudo chmod 600 /etc/cloudflared/<UUID>.json
```

## 4. Ingress — `/etc/cloudflared/config.yml`

```yaml
tunnel: <UUID>
credentials-file: /etc/cloudflared/<UUID>.json
ingress:
  - hostname: app.<domain>
    service: http://127.0.0.1:8080
  - service: http_status:404
```

## 5. Route DNS (creates the record)

```bash
cloudflared tunnel ingress validate
cloudflared tunnel ingress rule https://app.<domain>/     # must echo the app rule, not the 404
cloudflared tunnel route dns <TUNNEL_NAME> app.<domain>  # -> INF Added CNAME app.<domain> ...
```

`route dns` fails while the zone is not Active — a prerequisite problem, not a CLI problem. The record must be
a **proxied (orange-cloud)** CNAME to `<UUID>.cfargotunnel.com`; a grey-cloud record or a manual A record to the
origin IP bypasses the tunnel and leaks the origin address.

## 6. systemd — `/etc/systemd/system/cloudflared.service`

```ini
[Unit]
Description=Cloudflare Tunnel
After=network-online.target

[Service]
Type=notify
ExecStart=/usr/local/bin/cloudflared --config /etc/cloudflared/config.yml tunnel run
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then `sudo systemctl daemon-reload && sudo systemctl enable --now cloudflared`; `Restart=always` keeps a tunnel alive across transient edge disconnects.

## Verification

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/   # -> 200 (origin answers)
curl -sS -o /dev/null -w '%{http_code}\n' https://app.<domain>/    # -> 200 (303/401 = app alive too)
curl -sSI http://app.<domain>/ | head -1                           # -> HTTP/1.1 301 Moved Permanently
dig +short app.<domain>                                            # -> Cloudflare edge IPs, not the origin
systemctl is-active cloudflared                                    # -> active
cloudflared tunnel info <TUNNEL_NAME>                              # -> CONNECTOR rows present
journalctl -u cloudflared --since "5 min ago" | grep -c "Registered tunnel connection"   # -> >= 1

# while resolver caches still hold old records, bypass DNS with an edge IP:
CF_IP=$(dig +short app.<domain> @8.8.8.8 | head -n1)
curl --resolve app.<domain>:443:$CF_IP -sS -o /dev/null -w '%{http_code}\n' https://app.<domain>/
```

A tunnel can be `active` with **no connector** and route nothing: `tunnel info` and the journal count are the real signals.

## Failure modes

| Symptom | Cause | Check / fix |
| --- | --- | --- |
| 502 Bad Gateway | Tunnel up, origin not answering | `curl http://127.0.0.1:<port>/`; start the app or fix `service:` |
| 521 / 522 / 523 / 1033 | Edge cannot reach the tunnel, or zero connectors | `systemctl is-active`; `cloudflared tunnel info` |
| CF 404 or misrouted traffic | Record missing, or grey-cloud CNAME / manual A record | `dig app.<domain>`; must be a proxied CNAME to `<UUID>.cfargotunnel.com` |
| Works on host, 502 from outside, containerized origin | App bound to `127.0.0.1` in its own netns | Bind app to `0.0.0.0`; use container name/bridge IP in `service:` |
| 403 / auth error at start | Credentials JSON missing, or UUID mismatch | `credentials-file:` and `tunnel:` carry the same UUID |

Logs: `journalctl -u cloudflared -f` live, `journalctl -u cloudflared --since "1 hour ago" | grep -Ei 'error|warn|Registered'` for history, `cloudflared --loglevel debug tunnel run` in the foreground when the unit keeps restarting. Add `--logfile /var/log/cloudflared.log` only without journald; config-parse errors appear in `systemctl restart` output, connection errors only in the journal.

## Rollback

1. `sudo systemctl disable --now cloudflared` — traffic stops, the app keeps serving locally.
2. Delete the hostname's record (dashboard, or `DELETE /api/v4/zones/<ZONE_ID>/dns_records/<RECORD_ID>`).
3. `cloudflared tunnel delete <TUNNEL_NAME>` — it refuses while connectors are live, so do step 1 first.
4. Remove `/etc/cloudflared/config.yml`, `/etc/cloudflared/<UUID>.json` and the unit, then `sudo systemctl daemon-reload`; keep `cert.pem` if other tunnels use it.
5. Point DNS back at the registrar or a temporary host, confirm `dig +short app.<domain>` stops returning Cloudflare edge IPs, and confirm the origin survived with `curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/`.

Report the tunnel UUID, the exact `credentials-file:` line, `systemctl is-enabled cloudflared` and the verification output verbatim. If the host config is deploy-managed, list the lines the source repo must change and let the owner commit them.
