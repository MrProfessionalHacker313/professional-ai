# Professional AI - Backend Scripts Documentation

This directory contains all scripts for setting up and maintaining the "never expires" backend configuration.

## 📋 Scripts Overview

### 1. setup_ollama.sh
**Purpose**: Install and configure Ollama with all required AI models

**Usage**:
```bash
chmod +x setup_ollama.sh
./setup_ollama.sh
```

**What it does**:
- Installs Ollama on the server
- Starts and enables the Ollama service
- Pulls all required models (llama3.1:70b, qwen2.5:72b, deepseek-r1:70b, mistral, phi3, gemma2)
- Creates custom Modelfiles for optimized performance
- Configures models for different use cases (chat, code, reasoning)

**Time required**: 10-30 minutes (depending on internet speed)

---

### 2. setup_secrets.py
**Purpose**: Store all API keys and sensitive configuration in Google Secret Manager

**Usage**:
```bash
chmod +x setup_secrets.py
python3 setup_secrets.py
```

**What it does**:
- Checks for gcloud CLI installation
- Authenticates with Google Cloud
- Enables Secret Manager API
- Creates service account for secret access
- Interactively prompts for sensitive values
- Stores all secrets encrypted in Google Secret Manager
- Grants appropriate IAM permissions

**Security**: Never stores keys in code or .env files in production

---

### 3. health_check.py
**Purpose**: Monitor all services and auto-restart failed ones

**Usage**:
```bash
# Run manually
python3 health_check.py

# Run as systemd service (recommended)
sudo systemctl start pro-ai-healthcheck
sudo systemctl enable pro-ai-healthcheck
```

**What it monitors**:
- Ollama (LLM models)
- ComfyUI (image generation)
- Whisper (voice input)
- Piper TTS (voice output)
- SearXNG (search)
- PostgreSQL (database)
- Redis (cache)
- Backend API
- Frontend

**Features**:
- Checks every 60 seconds
- Marks unhealthy after 3 consecutive failures
- Auto-restarts failed services
- Prevents restart loops (max 5 restarts/hour)
- 10-minute cooldown between restarts
- Detailed health reporting

---

## 🚀 Quick Start

### Step 1: Initial Server Setup
```bash
# Follow the guide in ../docs/DEPLOYMENT_GUIDE.md
# Provision Google Cloud VM with GPU
# Install Docker, NVIDIA Toolkit, gcloud CLI
```

### Step 2: Configure Secrets
```bash
cd backend/scripts
python3 setup_secrets.py
# Follow the interactive prompts
```

### Step 3: Install Ollama
```bash
# Option A: On host (recommended for performance)
./setup_ollama.sh

# Option B: In Docker (already configured in docker-compose.yml)
# Just start docker-compose
```

### Step 4: Start Services
```bash
cd ../..
cp backend/.env.example backend/.env
# Edit backend/.env with your values

docker-compose up -d
```

### Step 5: Start Health Monitoring
```bash
cd backend/scripts
nohup python3 health_check.py > logs/health_check.log 2>&1 &

# Or as systemd service (see DEPLOYMENT_GUIDE.md)
```

---

## 🔧 Configuration

### Environment Variables

All configuration is done through the `.env` file (see `.env.example` for all options):

**Critical settings**:
```env
# Database
DB_PASSWORD=your-secure-password
REDIS_PASSWORD=your-redis-password

# Security
SECRET_KEY=your-generated-secret-key
JWT_SECRET=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key

# Model URLs (self-hosted)
OLLAMA_BASE_URL=http://localhost:11434
COMFYUI_URL=http://localhost:8188
WHISPER_API_URL=http://localhost:8001
TTS_API_URL=http://localhost:8002
SEARXNG_URL=http://localhost:8888

# Optional: Cloud API keys (for "Fastest/Pro" tier)
GEMINI_API_KEY=
OPENAI_API_KEY=
GROQ_API_KEY=
```

---

## 📊 Monitoring

### Health Check Reports

The health check script generates detailed reports:

```bash
# View real-time logs
tail -f logs/health_check.log

# Check service status
python3 -c "from health_check import HealthCheckService; import json; h = HealthCheckService(); print(json.dumps(h.get_health_report(), indent=2))"
```

### Grafana Dashboards

Access monitoring at `http://localhost:3001`:
- Docker container metrics
- GPU utilization
- Ollama performance
- Application metrics
- Health check status

---

## 🛠️ Troubleshooting

### Ollama Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
docker restart pro-ai-ollama

# Check logs
docker logs pro-ai-ollama
```

### Health Check Not Working

```bash
# Test manually
python3 health_check.py

# Check permissions
ls -la health_check.py
chmod +x health_check.py

# Check systemd service
sudo systemctl status pro-ai-healthcheck
journalctl -u pro-ai-healthcheck -f
```

### GPU Issues

```bash
# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Check Ollama GPU usage
docker logs pro-ai-ollama | grep -i gpu
```

---

## 🔐 Security Best Practices

1. **Never commit secrets**: Always use Google Secret Manager in production
2. **Rotate regularly**: Rotate API keys every 90 days
3. **Least privilege**: Service accounts should have minimal permissions
4. **Audit logging**: Enable Secret Manager audit logs
5. **Firewall rules**: Only expose ports 80/443 to the internet
6. **SSL/TLS**: Use Let's Encrypt for HTTPS
7. **Rate limiting**: Enable rate limiting on all endpoints
8. **Backup encryption**: Encrypt backups at rest

---

## 📈 Performance Tuning

### Ollama Optimization

```env
# In .env file
OLLAMA_NUM_PARALLEL=6          # Concurrent requests
OLLAMA_MAX_LOADED_MODELS=3     # Models in memory
CUDA_VISIBLE_DEVICES=all       # Use all GPUs
```

### Database Optimization

```sql
-- Add indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_usage_user_id ON usage(user_id, created_at);
ANALYZE;
```

### Redis Caching

```env
# In docker-compose.yml
command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 2gb --maxmemory-policy allkeys-lru
```

---

## 🔄 Maintenance

### Daily
- Monitor health check logs: `tail -f logs/health_check.log`
- Check disk space: `df -h`
- Review error logs: `docker-compose logs --tail=100`

### Weekly
- Review Grafana dashboards
- Check GPU utilization
- Verify backups completed

### Monthly
- Update Docker images: `docker-compose pull && docker-compose up -d`
- Rotate logs
- Review security updates

### Quarterly
- Rotate API keys and secrets
- Performance review
- Cost analysis
- Disaster recovery test

---

## 📚 Additional Resources

- **Deployment Guide**: `../docs/DEPLOYMENT_GUIDE.md`
- **API Documentation**: `../docs/API.md`
- **Main README**: `../README.md`
- **Configuration**: `.env.example`

---

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs in `../logs/`
3. Check Grafana dashboards for metrics
4. Verify all services are running: `docker-compose ps`
5. Test individual services with curl commands in DEPLOYMENT_GUIDE.md

---

## ✅ Checklist

Before going live, ensure:

- [ ] All secrets configured in Google Secret Manager
- [ ] .env file has all required values
- [ ] All Docker services are running
- [ ] Health check service is active
- [ ] Grafana dashboards are accessible
- [ ] SSL/TLS is configured
- [ ] Firewall rules are set
- [ ] Backups are configured
- [ ] Monitoring alerts are set up
- [ ] Team has access to documentation

---

**Last Updated**: 2026-07-31
**Version**: 1.0.0
**Maintainer**: Professional AI Team