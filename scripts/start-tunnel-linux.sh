#!/bin/bash
# Start Cloudflare Tunnel and display the URL
# Run: ./scripts/start-tunnel-linux.sh
#
# To run as a background service that auto-starts on boot:
#   sudo cp scripts/cma-tunnel.service /etc/systemd/system/
#   sudo systemctl enable cma-tunnel
#   sudo systemctl start cma-tunnel

echo "Starting Cloudflare Tunnel..."
echo "The tunnel URL will appear below. Update Vercel NEXT_PUBLIC_API_URL with it."
echo "Press Ctrl+C to stop."
echo ""

cloudflared tunnel --url http://localhost:8000
