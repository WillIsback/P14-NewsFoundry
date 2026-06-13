#!/bin/sh
set -e

# Dev/CI fallback: without an auth key, skip Tailscale and run the app directly.
if [ -z "$TS_AUTHKEY" ]; then
  echo "[entrypoint] TS_AUTHKEY not set — skipping Tailscale, starting app directly"
  exec python src/main.py
fi

TS_SOCKET=/app/.tailscale/tailscaled.sock
TS_STATEDIR=/app/.tailscale

echo "[entrypoint] starting tailscaled (userspace networking)…"
tailscaled \
  --tun=userspace-networking \
  --outbound-http-proxy-listen=localhost:1055 \
  --statedir="$TS_STATEDIR" \
  --socket="$TS_SOCKET" &

echo "[entrypoint] bringing tailscale up…"
# `tailscale up` blocks until the node is authenticated and Running; with
# `set -e`, an auth failure aborts the container (visible failed deploy).
tailscale --socket="$TS_SOCKET" up \
  --authkey="$TS_AUTHKEY" \
  --hostname="${TS_HOSTNAME:-newsfoundry-backend}"

echo "[entrypoint] tailnet up — starting app"
exec python src/main.py
