# Professional AI - Deployment Guide
## "Never Expires" Backend Configuration

This guide covers complete deployment of the Professional AI backend with all self-hosted models on Google Cloud.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Server Setup](#initial-server-setup)
3. [Google Cloud Setup](#google-cloud-setup)
4. [Secret Manager Configuration](#secret-manager-configuration)
5. [Docker & Ollama Setup](#docker--ollama-setup)
6. [Application Deployment](#application-deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements
- **GPU**: NVIDIA GPU with 24GB+ VRAM (A10G, A100, L4, or better)
- **CPU**: 8+ cores
- **RAM**: 32GB+ (64GB recommended for 70b models)
- **Storage**: 500GB+ SSD (1TB+ recommended for models)
- **OS**: Ubuntu 22.04 LTS or similar

### Software Requirements
- Docker Engine 24.0+
- Docker Compose 2.20+
- NVIDIA Container Toolkit
- gcloud CLI
- Git

### Google Cloud Requirements
- Google Cloud Project with billing enabled
- Compute Engine API enabled
- Secret Manager API enabled
- Service Account with appropriate permissions

---

## Initial Server Setup

### 1. Provision Google Cloud VM

```bash
# Create VM with GPU (example: a2-highgpu-1g with A10G)
gcloud compute instances create pro-ai-server \
  --project=YOUR_PROJECT_ID \
  --zone=us-central1-a \
  --machine-type=a2-highgpu-1g \
  --accelerator=type=nvidia-tesla-a10g,count=1 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=200GB \
  --boot-disk-type=pd-ssd \
  --maintenance-policy=TERMINATE \
  --restart-on-failure \
  --metadata=install-nvidia-driver=True
```

### 2. Connect to Server

```bash
gcloud compute ssh pro-ai-server --zone=us-central1-a
```

### 3. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

---

## Google Cloud Setup

### 1. Enable Required APIs

```bash
gcloud services enable \
  compute.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com
```

### 2. Create Service Account

```bash
# Create service account for the application
gcloud iam service-accounts create pro-ai-backend \
  --display-name="Professional AI Backend" \
  --description="Service account for Professional AI backend services"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:pro-ai-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:pro-ai-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/monitoring.metricWriter"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:pro-ai-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# Create and download key
gcloud iam service-accounts keys create service-account.json \
  --iam-account=pro-ai-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Move key to backend directory
mv service-account.json professional-ai/backend/
```

---

## Secret Manager Configuration

### 1. Run Setup Script

```bash
cd professional-ai/backend
python3 scripts/setup_secrets.py
```

This interactive script will:
- Enable Secret Manager API
- Create service account
- Prompt for all sensitive values
- Store them encrypted in Google Secret Manager
- Grant appropriate access permissions

### 2. Alternative: Manual Secret Creation

```bash
# Generate secure keys
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -hex 32)
REDIS_PASSWORD=$(openssl rand -hex 32)

# Create secrets
echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=-
echo -n "$REDIS_PASSWORD" | gcloud secrets create redis-password --data-file=-
echo -n "$SECRET_KEY" | gcloud secrets create secret-key --data-file=-
echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret --data-file=-
echo -n "$ENCRYPTION_KEY" | gcloud secrets create encryption-key --data-file=-

# Add API keys (if available)
echo -n "YOUR_GEMINI_KEY" | gcloud secrets create gemini-api-key --data-file=-
echo -n "YOUR_OPENAI_KEY" | gcloud secrets create openai-api-key --data-file=-
echo -n "YOUR_GROQ_KEY" | gcloud secrets create groq-api-key --data-file=-
```

---

## Docker & Ollama Setup

### 1. Install Ollama on Host (Optional but Recommended)

Running Ollama on the host (not in Docker) provides better performance:

```bash
curl -fsSL https://ollama.com/install.sh | sh

# Start and enable service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull all required models (this takes 10-30 minutes)
ollama pull llama3.1:70b
ollama pull qwen2.5:72b
ollama pull deepseek-r1:70b
ollama pull mistral
ollama pull phi3
ollama pull gemma2

# Verify installation
ollama list
```

**Note**: If using Docker Ollama (as in docker-compose.yml), skip this step.

### 2. Configure Docker Compose

```bash
cd professional-ai

# Create .env file from example
cp backend/.env.example backend/.env

# Edit .env with your values
nano backend/.env
```

**Critical values to set:**
```env
DB_PASSWORD=your-secure-password
REDIS_PASSWORD=your-redis-password
SECRET_KEY=your-generated-secret-key
JWT_SECRET=your-generated-jwt-secret
ENCRYPTION_KEY=your-generated-encryption-key
GOOGLE_CLOUD_PROJECT=your-project-id
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Monitor startup
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Verify Services

```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check backend health
curl http://localhost:8000/api/health

# Check frontend
curl http://localhost:3000

# Check all services
docker-compose ps
```

---

## Application Deployment

### Option 1: Docker Compose (Recommended for Single Server)

```bash
# Already done in previous section
# Services run on:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - Grafana: http://localhost:3001
# - Prometheus: http://localhost:9090
```

### Option 2: Google Cloud Run (Scalable)

```bash
# Build and push backend image
cd professional-ai/backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/pro-ai-backend

# Deploy to Cloud Run
gcloud run deploy pro-ai-backend \
  --image gcr.io/YOUR_PROJECT_ID/pro-ai-backend \
  --region us-central1 \
  --allow-unauthenticated \
  --cpu 4 \
  --memory 16Gi \
  --timeout 300 \
  --max-instances 10 \
  --set-secrets="DB_PASSWORD=db-password:latest,REDIS_PASSWORD=redis-password:latest,SECRET_KEY=secret-key:latest,JWT_SECRET=jwt-secret:latest,ENCRYPTION_KEY=encryption-key:latest"
```

**Note**: Cloud Run requires external Ollama instance (use Compute Engine or GKE for Ollama).

### Option 3: Google Kubernetes Engine (GKE)

```bash
# Create GKE cluster with GPU
gcloud container clusters create pro-ai-cluster \
  --zone=us-central1-a \
  --machine-type=a2-highgpu-1g \
  --accelerator=type=nvidia-tesla-a10g,count=1 \
  --num-nodes=1 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5

# Get credentials
gcloud container clusters get-credentials pro-ai-cluster --zone=us-central1-a

# Deploy using Helm or kubectl
kubectl apply -f k8s/
```

---

## Monitoring & Maintenance

### 1. Start Health Check Service

```bash
# Run health check script in background
cd professional-ai/backend
nohup python3 scripts/health_check.py > logs/health_check.log 2>&1 &

# Or as systemd service (recommended)
sudo nano /etc/systemd/system/pro-ai-healthcheck.service
```

```ini
[Unit]
Description=Professional AI Health Check Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/professional-ai/backend
ExecStart=/usr/bin/python3 scripts/health_check.py
Restart=always
RestartSec=10
Environment="PATH=/usr/bin:/usr/local/bin"

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable pro-ai-healthcheck
sudo systemctl start pro-ai-healthcheck
sudo systemctl status pro-ai-healthcheck
```

### 2. Configure Monitoring

```bash
# Access Grafana
open http://localhost:3001
# Default login: admin / admin (change in .env)

# Import dashboards
# - Docker Container Monitoring
# - NVIDIA GPU Metrics
# - Ollama Performance
# - Application Metrics
```

### 3. Setup Logging

```bash
# View application logs
docker-compose logs -f backend
docker-compose logs -f ollama

# View health check logs
tail -f logs/health_check.log

# Setup log rotation
sudo nano /etc/logrotate.d/pro-ai
```

```
/home/YOUR_USER/professional-ai/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 YOUR_USER YOUR_USER
}
```

### 4. Backup Strategy

```bash
# Backup PostgreSQL
docker exec pro-ai-postgres pg_dump -U postgres professional_ai > backups/db_backup_$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v pro-ai-postgres_data:/data -v $(pwd)/backups:/backup alpine tar cvf /backup/postgres_backup.tar.gz /data
docker run --rm -v ollama_data:/data -v $(pwd)/backups:/backup alpine tar cvf /backup/ollama_backup.tar.gz /data

# Automated backup script
nano scripts/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/YOUR_USER/professional-ai/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker exec pro-ai-postgres pg_dump -U postgres professional_ai | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Volume backups
docker run --rm -v pro-ai-postgres_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/postgres_$DATE.tar.gz /data
docker run --rm -v ollama_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/ollama_$DATE.tar.gz /data

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x scripts/backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /home/YOUR_USER/professional-ai/scripts/backup.sh
```

---

## Troubleshooting

### Common Issues

#### 1. GPU Not Detected

```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# If not working, reinstall NVIDIA Container Toolkit
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

#### 2. Ollama Out of Memory

```bash
# Reduce loaded models
# Edit docker-compose.yml entrypoint to load fewer models

# Or increase swap
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. Services Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs postgres

# Restart specific service
docker-compose restart backend

# Rebuild if code changed
docker-compose up -d --build
```

#### 4. Health Check Not Working

```bash
# Test health check script
python3 scripts/health_check.py

# Check permissions
ls -la scripts/health_check.py
chmod +x scripts/health_check.py

# Check logs
journalctl -u pro-ai-healthcheck -f
```

### Performance Optimization

#### 1. Ollama Performance

```bash
# Set environment variables in .env
OLLAMA_NUM_PARALLEL=6
OLLAMA_MAX_LOADED_MODELS=3
CUDA_VISIBLE_DEVICES=all

# Use smaller context windows for faster responses
# Edit Modelfiles in setup_ollama.sh
```

#### 2. Database Performance

```sql
-- Connect to PostgreSQL
docker exec -it pro-ai-postgres psql -U postgres professional_ai

-- Add indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_usage_user_id ON usage(user_id, created_at);
```

#### 3. Redis Caching

```python
# Already configured in docker-compose.yml
# Adjust maxmemory in redis.conf if needed
```

---

## Security Checklist

- [ ] All secrets stored in Google Secret Manager (not in .env)
- [ ] .env file added to .gitignore
- [ ] Service account keys stored securely
- [ ] Firewall rules configured (only ports 80, 443 open)
- [ ] SSL/TLS certificates configured (use Let's Encrypt)
- [ ] Regular security updates enabled
- [ ] Monitoring and alerting configured
- [ ] Backup strategy implemented
- [ ] Rate limiting enabled
- [ ] CORS properly configured

---

## Maintenance Schedule

### Daily
- Monitor health check logs
- Check disk space: `df -h`
- Review error logs

### Weekly
- Review Grafana dashboards
- Check GPU utilization
- Verify backup completion

### Monthly
- Update Docker images: `docker-compose pull && docker-compose up -d`
- Rotate logs
- Review security updates
- Check Secret Manager access logs

### Quarterly
- Rotate API keys and secrets
- Performance review and optimization
- Cost analysis
- Disaster recovery test

---

## Cost Estimation

### Google Cloud Costs (Monthly)

| Resource | Specification | Cost/Month |
|----------|--------------|------------|
| Compute Engine | a2-highgpu-1g (A10G) | ~$1,500 |
| SSD Storage | 1TB | ~$170 |
| Egress | 1TB | ~$80 |
| Secret Manager | <1GB | ~$3 |
| Cloud Monitoring | Basic | ~$0 |
| **Total** | | **~$1,753** |

**Note**: Self-hosted models have NO per-request costs. Only infrastructure costs apply.

### Cost Optimization Tips
1. Use committed use discounts (30-50% savings)
2. Use spot instances for non-critical workloads
3. Implement auto-scaling
4. Optimize model loading (don't load all models at once)
5. Use smaller models when possible

---

## Support & Documentation

- **Project Docs**: `/docs/`
- **API Documentation**: http://localhost:8000/docs
- **Health Status**: http://localhost:8000/api/health
- **Grafana Dashboards**: http://localhost:3001
- **Prometheus Metrics**: http://localhost:9090

---

## Next Steps

1. ✅ Complete initial setup
2. ✅ Configure secrets
3. ✅ Deploy services
4. ✅ Test all endpoints
5. ✅ Setup monitoring
6. ✅ Configure backups
7. ✅ Setup SSL/TLS
8. ✅ Configure domain name
9. ✅ Enable auto-scaling (if needed)
10. ✅ Setup alerting

---

**Congratulations!** Your Professional AI backend is now running 24/7 with:
- ✅ Self-hosted models (no expiry, no per-request costs)
- ✅ Automatic failover to cloud APIs
- ✅ Health monitoring with auto-restart
- ✅ Secure secret management
- ✅ Complete observability