#!/bin/bash
# VPS first-time setup for Syzygy Intelligence
# Usage: bash scripts/vps-startup.sh [--domain example.com]
set -euo pipefail

DOMAIN="${1:-localhost}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "========================================"
echo " Syzygy Intelligence - VPS Setup"
echo "========================================"

# --- Prerequisites ---
echo ""
echo "[1/5] Checking prerequisites..."

command -v docker &>/dev/null || { echo "FATAL: Docker not found. Install Docker first: https://docs.docker.com/engine/install/"; exit 1; }
echo "  ✓ Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"

if docker info 2>/dev/null | grep -q nvidia; then
    echo "  ✓ NVIDIA Docker runtime detected"
    HAS_GPU=true
else
    echo "  ⚠ NVIDIA Docker runtime not found. GPU models will fall back to CPU."
    echo "    Install: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
    HAS_GPU=false
fi

# --- Environment File ---
echo ""
echo "[2/5] Configuring environment..."
if [ ! -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    echo "  ✓ Created .env from .env.example"
    echo "  → Edit .env to set passwords, domain, and secrets before deploying"
else
    echo "  ✓ .env already exists (skipped)"
fi

# --- Pull Ollama Models ---
echo ""
echo "[3/5] Pulling Ollama models..."
MODELS=("qwen3:8b-gpu" "dolphin-llama3:8b-gpu" "llava:13b-gpu" "nomic-embed-text")
for model in "${MODELS[@]}"; do
    if curl -s http://localhost:11434/api/tags | grep -q "\"$model\"" 2>/dev/null; then
        echo "  ✓ $model already pulled"
    else
        echo "  → Pulling $model (this may take a while)..."
        if [ "$HAS_GPU" = true ]; then
            docker compose -f "$REPO_DIR/docker-compose.yml" exec -T ollama ollama pull "$model" 2>/dev/null \
            || docker run --rm --gpus all -v ~/.ollama:/root/.ollama ollama/ollama pull "$model"
        else
            docker run --rm -v ~/.ollama:/root/.ollama ollama/ollama pull "$model"
        fi
        echo "  ✓ $model pulled"
    fi
done

# --- Docker Compose Build & Start ---
echo ""
echo "[4/5] Building and starting services..."
cd "$REPO_DIR"
docker compose build --parallel
echo "  ✓ Build complete"

if [ "$HAS_GPU" = true ]; then
    docker compose up -d
else
    # Disable GPU reservations if no NVIDIA runtime
    sed -i '/nvidia/d; /driver:/d; /capabilities:/d; /devices:/d; /count:/d; /reservations:/d; /resources:/d; /deploy:/d' docker-compose.yml
    docker compose up -d
    echo "  ⚠ GPU sections stripped from docker-compose.yml"
fi

echo "  ✓ Services started"

# --- Status ---
echo ""
echo "[5/5] Health check..."
sleep 5
docker compose ps --status running
echo ""
echo "========================================"
echo " Syzygy Intelligence is running!"
echo " Frontend: http://$DOMAIN:3000"
echo " Backend:  http://$DOMAIN:8000"
echo " Ollama:   http://$DOMAIN:11434"
echo ""
echo " Next steps:"
echo "  - Set up a reverse proxy (nginx/Caddy) for HTTPS"
echo "  - Run: bash scripts/setup-prod-env.sh"
echo "  - Review and edit .env with secure passwords"
echo "  - Use the Knowledge page (/rag) to ingest documents"
echo "========================================"
