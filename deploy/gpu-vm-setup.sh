#!/bin/bash
# =============================================================================
# MEDIA VAULT — Google Cloud GPU VM Setup
# Provisions a GCP VM with NVIDIA T4/A100 GPU for ComfyUI + AnimateDiff.
# Cost estimate: ~$1-3/hour for T4, ~$3-8/hour for A100.
# =============================================================================
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
ZONE="${GOOGLE_CLOUD_ZONE:-us-central1-a}"
INSTANCE_NAME="media-vault-gpu"
MACHINE_TYPE="n1-standard-4"  # 4 vCPUs, 15GB RAM
GPU_TYPE="nvidia-t4"          # Options: nvidia-t4, nvidia-l4, nvidia-a100
GPU_COUNT=1
BOOT_DISK_SIZE=200
IMAGE_FAMILY="debian-12"
IMAGE_PROJECT="debian-cloud"

echo "============================================================"
echo " MEDIA VAULT — Google Cloud GPU VM Setup"
echo "============================================================"
echo " Project:    $PROJECT_ID"
echo " Zone:       $ZONE"
echo " GPU:        $GPU_COUNT x $GPU_TYPE"
echo " Machine:    $MACHINE_TYPE"
echo ""

# 1. Enable required APIs
echo "[1/5] Enabling GCP APIs..."
gcloud services enable compute.googleapis.com --project="$PROJECT_ID" --quiet

# 2. Create firewall rules
echo "[2/5] Setting up firewall rules..."
gcloud compute firewall-rules create allow-comfyui \
    --project="$PROJECT_ID" \
    --allow=tcp:8188 \
    --source-ranges=0.0.0.0/0 \
    --description="ComfyUI media server" \
    --quiet 2>/dev/null || true

gcloud compute firewall-rules create allow-ssh \
    --project="$PROJECT_ID" \
    --allow=tcp:22 \
    --source-ranges=0.0.0.0/0 \
    --description="SSH access" \
    --quiet 2>/dev/null || true

# 3. Create GPU VM
echo "[3/5] Creating GPU VM (this takes 3-5 minutes)..."
gcloud compute instances create "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --accelerator="type=$GPU_TYPE,count=$GPU_COUNT" \
    --image-family="$IMAGE_FAMILY" \
    --image-project="$IMAGE_PROJECT" \
    --boot-disk-size="${BOOT_DISK_SIZE}GB" \
    --boot-disk-type=pd-ssd \
    --maintenance-policy=TERMINATE \
    --restart-on-failure \
    --metadata="install-nvidia-driver=True" \
    --tags="media-vault" \
    --quiet

VM_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" --zone="$ZONE" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "[4/5] VM created. IP: $VM_IP"
echo "Waiting for NVIDIA driver installation (2-3 minutes)..."
sleep 180

# 4. Copy setup scripts and run
echo "[5/5] Running GPU server setup..."
gcloud compute scp \
    --project="$PROJECT_ID" --zone="$ZONE" \
    --quiet \
    deploy/comfyui-setup.sh "ubuntu@$VM_IP:~/comfyui-setup.sh"

gcloud compute ssh "ubuntu@$VM_IP" \
    --project="$PROJECT_ID" --zone="$ZONE" \
    --quiet \
    --command="chmod +x ~/comfyui-setup.sh && ~/comfyui-setup.sh"

echo ""
echo "============================================================"
echo " ✅ GPU VM READY"
echo "============================================================"
echo " ComfyUI:   http://$VM_IP:8188"
echo " SSH:       gcloud compute ssh ubuntu@$VM_IP --zone=$ZONE"
echo ""
echo " Set in .env:"
echo "   COMFYUI_URL=http://$VM_IP:8188"
echo "============================================================"
echo ""
echo " Monthly cost estimate:"
echo "   T4:    ~\$1.50/hr = ~\$1,080/mo (on-demand)"
echo "   A100:  ~\$4.50/hr = ~\$3,240/mo (on-demand)"
echo "   Use committed use discounts for 30-50% savings."
echo "   Stop VM when not in use: gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE"
