#!/bin/bash
# CMA Automation — Oracle Cloud VM Setup Script
# Run this ONCE on a fresh Oracle Cloud Ubuntu VM:
#   curl -sSL https://raw.githubusercontent.com/ashutoshrathi0909-oss/cma-automation/master/scripts/setup-oracle-vm.sh | bash
#
# Prerequisites: Ubuntu 22.04+ VM with at least 2GB RAM

set -e

echo "=========================================="
echo "  CMA Automation — Server Setup"
echo "=========================================="

# 1. Install Docker
echo "[1/5] Installing Docker..."
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER

# 2. Install cloudflared
echo "[2/5] Installing Cloudflare Tunnel..."
curl -sSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb
sudo dpkg -i /tmp/cloudflared.deb
rm /tmp/cloudflared.deb

# 3. Clone the repo
echo "[3/5] Cloning CMA Automation..."
cd ~
if [ -d "cma-automation" ]; then
    cd cma-automation && git pull
else
    git clone https://github.com/ashutoshrathi0909-oss/cma-automation.git
    cd cma-automation
fi

# 4. Create .env from template
echo "[4/5] Setting up environment..."
if [ ! -f .env ]; then
    cp .env.production.example .env
    echo ""
    echo "================================================"
    echo "  IMPORTANT: Edit .env with your actual values!"
    echo "  Run: nano ~/cma-automation/.env"
    echo "================================================"
    echo ""
fi

# 5. Start services
echo "[5/5] Starting Docker services..."
sudo docker compose -f docker-compose.production.yml up -d --build

echo ""
echo "=========================================="
echo "  Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env if you haven't:  nano ~/cma-automation/.env"
echo "  2. Restart after editing:     sudo docker compose -f docker-compose.production.yml up -d"
echo "  3. Start tunnel:              ./scripts/start-tunnel-linux.sh"
echo "  4. Check health:              curl http://localhost:8000/health"
echo ""
