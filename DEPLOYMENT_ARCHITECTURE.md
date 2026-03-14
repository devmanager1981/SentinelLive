# 🏗️ Deployment Architecture Overview

## Local Development Setup

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR COMPUTER                             │
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  streamer.py │    │   Backend    │    │   Frontend   │  │
│  │  (Port N/A)  │───▶│  (Port 8000) │◀───│ (Port 8501)  │  │
│  │              │    │              │    │              │  │
│  │  Simulates   │    │  FastAPI +   │    │  Streamlit   │  │
│  │  attacks     │    │  WebSocket   │    │  Dashboard   │  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘  │
│                              │                               │
└──────────────────────────────┼───────────────────────────────┘
                               │
                               ↓
                    ┌──────────────────┐
                    │  Google Cloud    │
                    │                  │
                    │  • Firestore     │
                    │  • Gemini Live   │
                    └──────────────────┘
```

**URLs**:
- Frontend: `http://localhost:8501`
- Backend: `http://localhost:8000`
- Streamer: Runs in terminal (no web interface)

**Environment Variables**:
```env
BACKEND_URL=http://localhost:8000
```

---

## Cloud Run Deployment (Recommended for Demo)

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR COMPUTER                             │
│                                                               │
│  ┌──────────────┐                                            │
│  │  streamer.py │                                            │
│  │              │                                            │
│  │  Simulates   │                                            │
│  │  attacks     │                                            │
│  └──────┬───────┘                                            │
│         │                                                     │
└─────────┼─────────────────────────────────────────────────────┘
          │
          │ HTTPS POST /stream
          │
          ↓
┌─────────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD RUN                          │
│                                                               │
│  ┌──────────────────────┐         ┌──────────────────────┐  │
│  │   Backend Service    │         │  Frontend Service    │  │
│  │   sentinel-backend   │◀────────│  sentinel-frontend   │  │
│  │                      │         │                      │  │
│  │  • FastAPI           │         │  • Streamlit         │  │
│  │  • WebSocket Proxy   │         │  • Audio Bridge      │  │
│  │  • Incident Monitor  │         │  • Dashboard         │  │
│  │  • Tool Execution    │         │                      │  │
│  └──────────┬───────────┘         └──────────────────────┘  │
│             │                                                 │
└─────────────┼─────────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD SERVICES                     │
│                                                               │
│  ┌──────────────────┐              ┌──────────────────┐     │
│  │   Firestore      │              │  Gemini Live API │     │
│  │                  │              │                  │     │
│  │  • logs/         │              │  • Audio I/O     │     │
│  │  • incidents/    │              │  • Tool Calling  │     │
│  │  • system_state/ │              │  • Barge-in      │     │
│  └──────────────────┘              └──────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

**URLs**:
- Frontend: `https://sentinel-frontend-xxxxx-uc.a.run.app`
- Backend: `https://sentinel-backend-xxxxx-uc.a.run.app`
- Streamer: Runs locally on your computer

**Environment Variables**:
```env
BACKEND_URL=https://sentinel-backend-xxxxx-uc.a.run.app
```

---

## Hybrid Setup (Demo Recording)

For the best demo experience, use this hybrid approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR COMPUTER                             │
│                                                               │
│  ┌──────────────┐         ┌──────────────────────────────┐  │
│  │  streamer.py │         │  Browser                     │  │
│  │              │         │                              │  │
│  │  Terminal    │         │  Open Cloud Run Frontend URL │  │
│  │  Press 'a'   │         │  https://...run.app          │  │
│  └──────┬───────┘         └──────────────────────────────┘  │
│         │                                                     │
└─────────┼─────────────────────────────────────────────────────┘
          │
          │ HTTPS POST
          │
          ↓
┌─────────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD RUN                          │
│                                                               │
│  Backend ◀──── Frontend ◀──── User (Browser)                 │
│     │              │                                          │
│     ↓              ↓                                          │
│  Firestore    Gemini Live                                    │
└─────────────────────────────────────────────────────────────┘
```

**Why This Works Best**:
1. ✅ Shows Cloud Run deployment (URLs visible)
2. ✅ Easy to control attack timing (local terminal)
3. ✅ No need to deploy streamer to cloud
4. ✅ Can see streamer output in terminal
5. ✅ Proves end-to-end cloud integration

---

## Component Responsibilities

### Streamer (Local)
**What it does**:
- Generates simulated security logs
- Sends HTTP POST requests to backend `/stream` endpoint
- Runs in interactive mode (press keys to change mode)

**What it does NOT do**:
- Does NOT need to be deployed
- Does NOT have a web interface
- Does NOT connect directly to Firestore (goes through backend)

**Configuration**:
- Uses `BACKEND_URL` from `.env` file
- Can point to local or Cloud Run backend
- Always runs on your local machine

---

### Backend (Cloud Run)
**What it does**:
- Receives logs from streamer
- Detects anomalies (brute force, impossible travel, etc.)
- Creates incidents in Firestore
- Monitors Firestore for new incidents
- Sends alerts to Gemini Live API
- Executes tool calls (neutralize threats)
- Proxies WebSocket connection to Gemini

**Endpoints**:
- `POST /stream` - Ingest logs from streamer
- `GET /system_state` - Get active incidents
- `POST /neutralize/{id}` - Neutralize threat
- `POST /reset` - Clear all data
- `GET /health` - Health check
- `WS /ws/gemini-live` - WebSocket proxy

---

### Frontend (Cloud Run)
**What it does**:
- Displays security dashboard
- Shows real-time telemetry logs
- Shows active incidents
- Embeds Gemini Live audio bridge
- Connects to backend via WebSocket
- Sends audio to backend
- Receives audio from backend
- Displays incident queue

**User Actions**:
- Click "Establish Neural Link" to connect
- Speak voice commands to Gemini
- Click "Neutralize" button manually
- Click "Refresh" to update dashboard

---

## Data Flow: Attack Detection

```
1. Streamer (Local)
   │
   │ HTTP POST /stream
   │ {"ip": "192.168.1.100", "status_code": 401, ...}
   │
   ↓
2. Backend (Cloud Run)
   │
   │ Store in Firestore
   │ Check for anomalies
   │ Create incident if risk > 70%
   │
   ↓
3. Firestore (Cloud)
   │
   │ incidents/abc123 created
   │ status: "Active"
   │
   ↓
4. Backend Monitor (Cloud Run)
   │
   │ Polls Firestore every 2s
   │ Detects new incident
   │ Sends alert to Gemini
   │
   ↓
5. Gemini Live API (Cloud)
   │
   │ Receives text alert
   │ Generates audio response
   │ Sends audio to backend
   │
   ↓
6. Backend WebSocket (Cloud Run)
   │
   │ Forwards audio to frontend
   │
   ↓
7. Frontend Browser (User)
   │
   │ Plays audio alert
   │ User hears: "Warning! Brute Force attack detected..."
```

---

## Data Flow: Voice Command

```
1. User speaks: "neutralize it"
   │
   │ Microphone → 16kHz PCM
   │
   ↓
2. Frontend JavaScript (Browser)
   │
   │ Capture audio
   │ Convert to base64
   │ Send via WebSocket
   │
   ↓
3. Backend WebSocket (Cloud Run)
   │
   │ Forward to Gemini Live API
   │
   ↓
4. Gemini Live API (Cloud)
   │
   │ Transcribe audio
   │ Understand intent: neutralize
   │ Call tool: block_ip(incident_id)
   │
   ↓
5. Backend Tool Handler (Cloud Run)
   │
   │ Execute tool
   │ Update Firestore: status = "Neutralized"
   │ Return result to Gemini
   │
   ↓
6. Gemini Live API (Cloud)
   │
   │ Generate confirmation audio
   │ "Threat neutralized successfully"
   │
   ↓
7. Frontend Browser (User)
   │
   │ Play confirmation audio
   │ Refresh UI (incident removed)
```

---

## Environment Variables Summary

### Local Development
```env
GOOGLE_AISTUDIO_KEY=AIzaSy...
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_FIRESTORE_DB=glive-fire-db
BACKEND_URL=http://localhost:8000
```

### Cloud Run Testing
```env
GOOGLE_AISTUDIO_KEY=AIzaSy...
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_FIRESTORE_DB=glive-fire-db
BACKEND_URL=https://sentinel-backend-xxxxx-uc.a.run.app
```

### Cloud Run Services (Set via gcloud)
```bash
# Backend environment variables
GOOGLE_AISTUDIO_KEY=AIzaSy...
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_FIRESTORE_DB=glive-fire-db

# Frontend environment variables
GOOGLE_AISTUDIO_KEY=AIzaSy...
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_FIRESTORE_DB=glive-fire-db
BACKEND_URL=https://sentinel-backend-xxxxx-uc.a.run.app
```

---

## Quick Reference

| Component | Location | URL | Purpose |
|-----------|----------|-----|---------|
| Streamer | Local | N/A (terminal) | Generate attacks |
| Backend | Cloud Run | https://...run.app | Process logs, detect threats |
| Frontend | Cloud Run | https://...run.app | Display dashboard, audio bridge |
| Firestore | Cloud | N/A (database) | Store logs and incidents |
| Gemini | Cloud | N/A (API) | Voice AI analyst |

---

## Demo Day Checklist

- [ ] Deploy backend to Cloud Run
- [ ] Deploy frontend to Cloud Run
- [ ] Update `.env` with Cloud Run backend URL
- [ ] Test streamer → Cloud Run backend
- [ ] Open Cloud Run frontend in browser
- [ ] Connect to Gemini
- [ ] Run streamer locally
- [ ] Press 'a' for attack
- [ ] Verify Gemini alerts
- [ ] Say "neutralize it"
- [ ] Record entire flow

---

**Key Takeaway**: The streamer always runs locally. It's just a log generator that sends HTTP requests to your backend (local or cloud). This gives you full control during the demo!
