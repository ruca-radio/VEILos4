#!/bin/bash
# ─── VEILos Deployment Script ───────────────────────────
# Builds and launches VEILos in Docker with optional
# Cloudflare tunnel for remote access.
#
# Usage:
#   ./deploy.sh                    # Local only
#   ./deploy.sh --tunnel DOMAIN    # With Cloudflare tunnel
# ─────────────────────────────────────────────────────────

set -e

DOMAIN="${2:-}"

echo "╔═══════════════════════════════════════╗"
echo "║         VEILos Deployment             ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Build and start
echo "[1/3] Building containers..."
docker compose build

echo "[2/3] Starting VEILos..."
docker compose up -d

echo "[3/3] Waiting for health check..."
sleep 5

if curl -sf http://127.0.0.1:8000/api/stats > /dev/null 2>&1; then
    echo ""
    echo "✓ VEILos is running on http://localhost:8000"
else
    echo "✗ Health check failed. Check logs: docker compose logs"
    exit 1
fi

# Cloudflare tunnel
if [ -n "$DOMAIN" ]; then
    echo ""
    echo "Setting up Cloudflare tunnel to $DOMAIN..."

    # Check if cloudflared is installed
    if ! command -v cloudflared &> /dev/null; then
        echo "Installing cloudflared..."
        curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        sudo dpkg -i cloudflared.deb
        rm cloudflared.deb
    fi

    echo "Starting tunnel: $DOMAIN -> localhost:8000"
    cloudflared tunnel --url http://localhost:8000 --hostname "$DOMAIN" &

    echo ""
    echo "✓ VEILos accessible at https://$DOMAIN"
    echo "  Models can POST to https://$DOMAIN/api/chat"
    echo "  Patrick can open https://$DOMAIN in browser"
fi

echo ""
echo "─── Status ───"
docker compose ps
echo ""
echo "─── Commands ───"
echo "  Logs:    docker compose logs -f"
echo "  Stop:    docker compose down"
echo "  Restart: docker compose restart"
echo ""
echo "VEILos is live. The VEIL is open."
