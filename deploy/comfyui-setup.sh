#!/bin/bash
# =============================================================================
# MEDIA VAULT — GPU Server Setup: ComfyUI + AnimateDiff
# Runs on owner's NVIDIA T4/A100 GPU server (Linux).
# After this script: ComfyUI serves at http://localhost:8188
# AnimateDiff Lightning model installed. Zero per-use cost.
# =============================================================================
set -euo pipefail

echo "============================================================"
echo " MEDIA VAULT — GPU Server Setup (ComfyUI + AnimateDiff)"
echo "============================================================"

# 1. Verify NVIDIA GPU
if ! command -v nvidia-smi &>/dev/null; then
    echo "ERROR: nvidia-smi not found. Install NVIDIA drivers first."
    exit 1
fi
nvidia-smi -L

# 2. Install system dependencies
echo "[1/6] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq git python3 python3-venv python3-pip libgl1 libglib2.0-0

# 3. Clone ComfyUI (if not already present)
COMFYUI_DIR="${COMFYUI_DIR:-$HOME/comfyui}"
if [ ! -d "$COMFYUI_DIR" ]; then
    echo "[2/6] Cloning ComfyUI..."
    git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFYUI_DIR"
else
    echo "[2/6] ComfyUI already exists at $COMFYUI_DIR — pulling latest..."
    cd "$COMFYUI_DIR" && git pull
fi

# 4. Create Python venv
echo "[3/6] Creating Python virtual environment..."
cd "$COMFYUI_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q

# 5. Install ComfyUI requirements
echo "[4/6] Installing ComfyUI requirements..."
pip install -r requirements.txt -q

# 6. Install AnimateDiff custom node + Lightning model
echo "[5/6] Installing AnimateDiff Lightning..."
CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"
mkdir -p "$CUSTOM_NODES_DIR"

# Install ComfyUI-AnimateDiff-Evolved
if [ ! -d "$CUSTOM_NODES_DIR/ComfyUI-AnimateDiff-Evolved" ]; then
    git clone https://github.com/ArtVentureX/comfyui-animatediff.git "$CUSTOM_NODES_DIR/ComfyUI-AnimateDiff-Evolved"
fi

cd "$CUSTOM_NODES_DIR/ComfyUI-AnimateDiff-Evolved"
pip install -r requirements.txt -q

# Download AnimateDiff Lightning model (~2GB)
MODELS_DIR="$COMFYUI_DIR/models/checkpoints"
mkdir -p "$MODELS_DIR"
LIGHTNING_MODEL="$MODELS_DIR/animatediff_lightning.safetensors"

if [ ! -f "$LIGHTNING_MODEL" ]; then
    echo "Downloading AnimateDiff Lightning model (~2GB, this takes a few minutes)..."
    wget -q --show-progress \
        "https://huggingface.co/guoyww/animatediff/resolve/main/animatediff_lightning_4step.safetensors" \
        -O "$LIGHTNING_MODEL"
else
    echo "AnimateDiff Lightning model already present."
fi

# 7. Install Real-ESRGAN upscaler (optional, for 8K upscaling)
echo "[6/6] Installing Real-ESRGAN upscaler..."
REALESRGAN_DIR="$COMFYUI_DIR/custom_nodes/ComfyUI-Upscaler"
if [ ! -d "$REALESRGAN_DIR" ]; then
    git clone https://github.com/ssitu/ComfyUI-Upscaler "$REALESRGAN_DIR" 2>/dev/null || true
fi

# 8. Create startup script
cat > "$COMFYUI_DIR/start-comfyui.sh" << 'SCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py --listen 0.0.0.0 --port 8188
SCRIPT
chmod +x "$COMFYUI_DIR/start-comfyui.sh"

# 9. Create systemd service (optional)
sudo tee /etc/systemd/system/comfyui.service > /dev/null << EOF
[Unit]
Description=ComfyUI Media Server
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${COMFYUI_DIR}
ExecStart=${COMFYUI_DIR}/venv/bin/python main.py --listen 0.0.0.0 --port 8188
Restart=always
RestartSec=10
Environment="CUDA_VISIBLE_DEVICES=0"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable comfyui
sudo systemctl start comfyui

echo ""
echo "============================================================"
echo " ✅ COMFYUI + ANIMATEDIFF SETUP COMPLETE"
echo "============================================================"
echo " ComfyUI URL:  http://localhost:8188"
echo " Models dir:   $COMFYUI_DIR/models/checkpoints"
echo " AnimateDiff:  animatediff_lightning.safetensors"
echo ""
echo " Start manually: cd $COMFYUI_DIR && ./start-comfyui.sh"
echo " Start as service: sudo systemctl start comfyui"
echo ""
echo " Set COMFYUI_URL=http://your-server-ip:8188 in .env"
echo "============================================================"
