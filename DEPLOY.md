# 🚀 Deployment Guide - IT Problem Helper

This guide shows how to deploy the Operations Assistant to various platforms.

---

## Quick Deploy Options

| Platform | Difficulty | Free Tier | Link |
|----------|------------|-----------|------|
| **Railway** | Easy | Yes (500 hrs/mo) | railway.app |
| **Render** | Easy | Yes (limited) | render.com |
| **Azure Container Apps** | Medium | Yes ($50 credit) | azure.com |
| **AWS App Runner** | Medium | Yes (free tier) | aws.amazon.com |
| **Docker (Self-hosted)** | Easy | N/A | Your server |

---

## Option 1: Deploy to Railway (Easiest)

### Step 1: Push to GitHub
```bash
# Create repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/ops-assistant.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `ops-assistant` repo
4. Railway auto-detects Dockerfile
5. Add environment variable:
   - `LLM_BASE_URL` = `http://wiphack30qx5aw.cloudloka.com:8000/v1`
6. Click Deploy!

Your app will be live at: `https://ops-assistant-xxx.railway.app`

---

## Option 2: Deploy to Render

### Step 1: Push to GitHub (same as above)

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com)
2. New → Web Service
3. Connect your GitHub repo
4. Settings:
   - Environment: Docker
   - Instance Type: Free
5. Add environment variables (same as Railway)
6. Deploy!

---

## Option 3: Deploy with Docker (Self-hosted)

### On Any Server with Docker:

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/ops-assistant.git
cd ops-assistant

# Create .env file
cp .env.example .env
# Edit .env with your LLM endpoint

# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f

# Access at http://your-server-ip:8000
```

### Using Docker directly:
```bash
# Build
docker build -t ops-assistant .

# Run
docker run -d \
  -p 8000:8000 \
  -e LLM_BASE_URL=http://your-llm-endpoint:8000/v1 \
  -v ops-data:/app/chroma_db \
  --name ops-assistant \
  ops-assistant
```

---

## Option 4: Deploy to Azure Container Apps

```bash
# Login to Azure
az login

# Create resource group
az group create --name ops-assistant-rg --location eastus

# Create container app environment
az containerapp env create \
  --name ops-assistant-env \
  --resource-group ops-assistant-rg \
  --location eastus

# Deploy from GitHub (after pushing code)
az containerapp up \
  --name ops-assistant \
  --resource-group ops-assistant-rg \
  --environment ops-assistant-env \
  --source . \
  --ingress external \
  --target-port 8000
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_BASE_URL` | Yes | (none) | Your LLM API endpoint |
| `LLM_MODEL` | No | `Qwen/Qwen3-8B` | Model name |
| `LLM_TIMEOUT` | No | `120` | Request timeout (seconds) |
| `PORT` | No | `8000` | Server port |

---

## After Deployment

### Access Your App:
- **UI**: `https://your-app-url/`
- **API Docs**: `https://your-app-url/docs`
- **Health Check**: `https://your-app-url/health`

### Test It:
```bash
curl https://your-app-url/health
```

### Update the UI:
Change the `API_URL` in `ui_combined.html` to your deployed URL:
```javascript
const API_URL = 'https://your-app-url';
```

---

## Troubleshooting

### "LLM not available" error
- Check if your LLM endpoint is accessible from the deployed server
- Verify `LLM_BASE_URL` environment variable is set correctly

### Slow first request
- Normal! The embedding model (~90MB) downloads on first request
- Subsequent requests are fast

### Container keeps restarting
- Check logs: `docker logs ops-assistant`
- Ensure enough memory (minimum 2GB recommended)

---

## Need Help?

1. Check container logs
2. Verify environment variables
3. Test health endpoint: `/health`
4. Open an issue on GitHub

---

Happy Deploying! 🎉
