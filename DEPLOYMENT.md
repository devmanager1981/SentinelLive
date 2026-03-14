# 🚀 Sentinel Live - Deployment Guide

This guide covers deploying Sentinel Live to Google Cloud Run for the hackathon submission.

---

## 📋 Prerequisites

### 1. Google Cloud Account
- Active Google Cloud account with billing enabled
- Project created (or use existing project)
- Owner or Editor role on the project

### 2. Local Tools
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed
- Docker installed (for local testing)
- Python 3.11+ installed
- Git installed

### 3. API Keys & Credentials
- Google AI Studio API key ([Get here](https://aistudio.google.com/app/apikey))
- Google Cloud project with Firestore enabled

---

## 🔧 Pre-Deployment Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/sentinel-live.git
cd sentinel-live
```

### Step 2: Configure Environment Variables

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
GOOGLE_AISTUDIO_KEY=AIzaSy...your_key_here
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_FIRESTORE_DB=glive-fire-db
BACKEND_URL=http://localhost:8000
GOOGLE_CLOUD_REGION=us-central1
```

### Step 3: Enable Firestore

1. Go to [Firestore Console](https://console.cloud.google.com/firestore)
2. Click "Create Database"
3. Choose "Native Mode"
4. Select region (e.g., `us-east1`)
5. Name your database (e.g., `glive-fire-db`)

### Step 4: Test Locally (Optional but Recommended)

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start backend
uvicorn server.main:app --reload --port 8000

# In another terminal, start frontend
streamlit run web/app.py --server.port 8501

# Test at http://localhost:8501
```

---

## ☁️ Cloud Run Deployment

### Option 1: Automated Deployment (Recommended)

Use the provided deployment script:

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
1. Authenticate with Google Cloud
2. Enable required APIs
3. Build and deploy backend service
4. Build and deploy frontend service
5. Output service URLs

### Option 2: Manual Deployment

#### Step 1: Authenticate

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### Step 2: Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com
```

#### Step 3: Deploy Backend

```bash
gcloud run deploy sentinel-backend \
  --source . \
  --dockerfile Dockerfile.backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_AISTUDIO_KEY=${GOOGLE_AISTUDIO_KEY},GOOGLE_PROJECT_ID=${GOOGLE_PROJECT_ID},GOOGLE_FIRESTORE_DB=${GOOGLE_FIRESTORE_DB}" \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --port 8080
```

Get backend URL:

```bash
BACKEND_URL=$(gcloud run services describe sentinel-backend --region us-central1 --format 'value(status.url)')
echo "Backend URL: $BACKEND_URL"
```

#### Step 4: Deploy Frontend

```bash
gcloud run deploy sentinel-frontend \
  --source . \
  --dockerfile Dockerfile.frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_AISTUDIO_KEY=${GOOGLE_AISTUDIO_KEY},GOOGLE_PROJECT_ID=${GOOGLE_PROJECT_ID},GOOGLE_FIRESTORE_DB=${GOOGLE_FIRESTORE_DB},BACKEND_URL=${BACKEND_URL}" \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --port 8501
```

Get frontend URL:

```bash
FRONTEND_URL=$(gcloud run services describe sentinel-frontend --region us-central1 --format 'value(status.url)')
echo "Frontend URL: $FRONTEND_URL"
```

---

## ✅ Post-Deployment Verification

### 1. Check Backend Health

```bash
curl https://sentinel-backend-xxxxx-uc.a.run.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-14T12:34:56.789Z",
  "service": "Sentinel Live API"
}
```

### 2. Test Frontend

1. Open frontend URL in browser
2. Click "Establish Neural Link"
3. Allow microphone permissions
4. Status should change to "Uplink Active"

### 3. Test End-to-End

The `streamer.py` attack simulator runs **locally** and sends logs to your Cloud Run backend.

**Option A: Update .env file (Recommended)**
```bash
# Edit .env file
BACKEND_URL=https://sentinel-backend-xxxxx-uc.a.run.app

# Run streamer
python streamer.py
```

**Option B: Use environment variable**
```bash
# Run with Cloud Run backend URL
BACKEND_URL=https://sentinel-backend-xxxxx-uc.a.run.app python streamer.py
```

**Test Steps**:
1. Run `python streamer.py`
2. Press 'a' for attack mode
3. Open Cloud Run frontend URL in browser
4. Click "Establish Neural Link"
5. Gemini should alert with voice notification
6. Say "neutralize it" to resolve incident

---

## 📊 Monitoring & Logs

### View Logs

```bash
# Backend logs
gcloud run logs read sentinel-backend --region us-central1 --limit 50

# Frontend logs
gcloud run logs read sentinel-frontend --region us-central1 --limit 50

# Follow logs in real-time
gcloud run logs tail sentinel-backend --region us-central1
```

### View Metrics

```bash
# Open Cloud Console
gcloud run services describe sentinel-backend --region us-central1

# Or visit:
# https://console.cloud.google.com/run
```

### Check Firestore Data

```bash
# Open Firestore Console
gcloud firestore databases describe glive-fire-db

# Or visit:
# https://console.cloud.google.com/firestore
```

---

## 🔒 Security Considerations

### 1. API Key Protection

- API keys are stored as environment variables (not in code)
- Never commit `.env` file to Git
- Use Secret Manager for production:

```bash
# Store API key in Secret Manager
echo -n "YOUR_API_KEY" | gcloud secrets create gemini-api-key --data-file=-

# Update Cloud Run to use secret
gcloud run services update sentinel-backend \
  --update-secrets=GOOGLE_AISTUDIO_KEY=gemini-api-key:latest \
  --region us-central1
```

### 2. Authentication (Optional)

For production, enable authentication:

```bash
# Remove --allow-unauthenticated flag
gcloud run services update sentinel-backend \
  --no-allow-unauthenticated \
  --region us-central1

# Add IAM binding for specific users
gcloud run services add-iam-policy-binding sentinel-backend \
  --member="user:your-email@example.com" \
  --role="roles/run.invoker" \
  --region us-central1
```

### 3. CORS Configuration

If deploying frontend separately, update CORS in `server/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sentinel-frontend-xxxxx-uc.a.run.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 💰 Cost Optimization

### Cloud Run Pricing

- **Free tier**: 2 million requests/month, 360,000 GB-seconds
- **Estimated cost**: $0-5/month for demo usage
- **Optimization tips**:
  - Set `--min-instances 0` (scale to zero when idle)
  - Use `--memory 1Gi` (sufficient for demo)
  - Set `--max-instances 10` (prevent runaway costs)

### Firestore Pricing

- **Free tier**: 1 GB storage, 50K reads/day, 20K writes/day
- **Estimated cost**: Free for demo usage
- **Optimization tips**:
  - Delete old logs regularly
  - Use TTL policies for automatic cleanup

---

## 🎯 Attack Simulator (streamer.py)

### Overview

The `streamer.py` script simulates security events and runs **locally on your machine**. It sends HTTP requests to your backend (local or Cloud Run) to generate logs and trigger incidents.

### How It Works

```
┌─────────────────┐
│  Your Computer  │
│                 │
│  streamer.py    │ ──HTTP POST──> Backend (Cloud Run)
│  (Local)        │                     │
└─────────────────┘                     ↓
                                   Firestore
                                        │
                                        ↓
                                   Gemini Alert
```

### Configuration

The streamer uses the `BACKEND_URL` environment variable from your `.env` file:

```env
# For local testing
BACKEND_URL=http://localhost:8000

# For Cloud Run testing
BACKEND_URL=https://sentinel-backend-xxxxx-uc.a.run.app
```

### Usage

**Start the streamer**:
```bash
python streamer.py
```

**Commands**:
- `n` - Normal mode (benign traffic)
- `a` - Attack mode (brute force)
- `i` - Impossible travel mode
- `e` - Data exfiltration mode
- `q` - Quit

### Testing with Cloud Run

**Method 1: Update .env file**
```bash
# Edit .env
BACKEND_URL=https://sentinel-backend-xxxxx-uc.a.run.app

# Run streamer
python streamer.py
```

**Method 2: Environment variable override**
```bash
BACKEND_URL=https://sentinel-backend-xxxxx-uc.a.run.app python streamer.py
```

**Method 3: Temporary .env**
```bash
# Create temporary .env for Cloud Run testing
cp .env .env.local
echo "BACKEND_URL=https://sentinel-backend-xxxxx-uc.a.run.app" >> .env

# Run streamer
python streamer.py

# Restore local .env
mv .env.local .env
```

### Demo Workflow

1. **Deploy to Cloud Run**: `./deploy.sh`
2. **Get backend URL**: Copy from deployment output
3. **Update .env**: Set `BACKEND_URL` to Cloud Run URL
4. **Open frontend**: Visit Cloud Run frontend URL
5. **Connect Gemini**: Click "Establish Neural Link"
6. **Run streamer**: `python streamer.py`
7. **Trigger attack**: Press 'a'
8. **Wait for alert**: Gemini will interrupt with voice alert
9. **Neutralize**: Say "neutralize it"

### Troubleshooting

**Issue: Connection refused**
```bash
# Check backend is running
curl https://sentinel-backend-xxxxx-uc.a.run.app/health

# Expected response:
# {"status":"healthy","timestamp":"...","service":"Sentinel Live API"}
```

**Issue: Logs not appearing**
- Check `BACKEND_URL` is correct in `.env`
- Verify backend is deployed and healthy
- Check Firestore database name matches
- Look for errors in streamer output

**Issue: No incidents created**
- Press 'a' for attack mode (not 'n')
- Wait for 5+ failed login attempts (10 seconds)
- Check backend logs: `gcloud run logs read sentinel-backend --region us-central1`

### Advanced: Deploy Streamer to Cloud Run (Optional)

If you want the streamer to run in the cloud (not recommended for demo):

```dockerfile
# Dockerfile.streamer
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY streamer.py .
CMD ["python", "streamer.py"]
```

```bash
gcloud run deploy sentinel-streamer \
  --source . \
  --dockerfile Dockerfile.streamer \
  --region us-central1 \
  --set-env-vars "BACKEND_URL=${BACKEND_URL}"
```

**Note**: For the demo, running locally is better because you can control it interactively.

---

## 🎬 Demo Recording Setup

### Issue: Backend deployment fails

**Solution**: Check build logs

```bash
gcloud builds list --limit 5
gcloud builds log BUILD_ID
```

Common issues:
- Missing dependencies in `requirements.txt`
- Incorrect Dockerfile syntax
- Port mismatch (must be 8080 for Cloud Run)

### Issue: WebSocket connection fails

**Solution**: Check CORS and WebSocket support

- Cloud Run supports WebSockets (no special config needed)
- Ensure `BACKEND_URL` environment variable is set correctly
- Check browser console for errors

### Issue: Firestore permission denied

**Solution**: Enable Firestore API and check IAM

```bash
# Enable API
gcloud services enable firestore.googleapis.com

# Grant Cloud Run service account Firestore access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/datastore.user"
```

### Issue: Gemini API authentication fails

**Solution**: Verify API key

- Check API key is valid at [AI Studio](https://aistudio.google.com/app/apikey)
- Ensure no quotes or whitespace in `.env` file
- Verify environment variable is set in Cloud Run:

```bash
gcloud run services describe sentinel-backend \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

---

## 🔄 Updating Deployment

### Update Backend

```bash
gcloud run deploy sentinel-backend \
  --source . \
  --dockerfile Dockerfile.backend \
  --region us-central1
```

### Update Frontend

```bash
gcloud run deploy sentinel-frontend \
  --source . \
  --dockerfile Dockerfile.frontend \
  --region us-central1
```

### Update Environment Variables

```bash
gcloud run services update sentinel-backend \
  --update-env-vars "NEW_VAR=value" \
  --region us-central1
```

---

## 🗑️ Cleanup

### Delete Services

```bash
# Delete backend
gcloud run services delete sentinel-backend --region us-central1

# Delete frontend
gcloud run services delete sentinel-frontend --region us-central1
```

### Delete Firestore Data

```bash
# Use clear_firestore.py script
python clear_firestore.py

# Or delete database entirely
gcloud firestore databases delete glive-fire-db
```

### Delete Secrets

```bash
gcloud secrets delete gemini-api-key
```

---

## 📸 Screenshots for Hackathon Submission

### Required Screenshots

1. **Cloud Run Services**
   - Navigate to: https://console.cloud.google.com/run
   - Screenshot showing both services deployed

2. **Firestore Database**
   - Navigate to: https://console.cloud.google.com/firestore
   - Screenshot showing collections (logs, incidents)

3. **Live Demo**
   - Screenshot of frontend URL in browser
   - Screenshot of Gemini connection active
   - Screenshot of incident detection

### How to Capture

```bash
# Get service URLs
gcloud run services list --platform managed

# Get Firestore info
gcloud firestore databases describe glive-fire-db
```

---

## 🎯 Hackathon Submission Checklist

- [ ] Backend deployed to Cloud Run
- [ ] Frontend deployed to Cloud Run
- [ ] Firestore database created and populated
- [ ] Demo video recorded (max 4 minutes)
- [ ] Architecture diagram included
- [ ] README.md updated with Cloud Run URLs
- [ ] Screenshots of GCP deployment
- [ ] GitHub repository public
- [ ] Devpost submission completed

---

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Gemini Live API Documentation](https://ai.google.dev/api/multimodal-live)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Streamlit Cloud Deployment](https://docs.streamlit.io/streamlit-community-cloud)

---

## 🆘 Support

If you encounter issues:

1. Check logs: `gcloud run logs read sentinel-backend --region us-central1`
2. Review troubleshooting section above
3. Check GitHub Issues
4. Contact: your.email@example.com

---

**Good luck with your deployment! 🚀**
