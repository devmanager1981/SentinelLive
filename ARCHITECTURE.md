# 🏗️ Sentinel Live - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                         │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              Streamlit Dashboard (Port 8501)                │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │    │
│  │  │   Security   │  │   Incident   │  │   Control    │    │    │
│  │  │  Telemetry   │  │    Queue     │  │   Panel      │    │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │    │
│  │                                                             │    │
│  │  ┌─────────────────────────────────────────────────────┐  │    │
│  │  │      Gemini Live Audio Bridge (JavaScript)          │  │    │
│  │  │  • Microphone capture (16kHz PCM)                   │  │    │
│  │  │  • Audio playback (24kHz PCM)                       │  │    │
│  │  │  • WebSocket client                                 │  │    │
│  │  └─────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ WebSocket (ws://localhost:8000/ws/gemini-live)
                                │ HTTP REST (http://localhost:8000/*)
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                               │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │           FastAPI Backend (Port 8000)                       │    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │         WebSocket Proxy (/ws/gemini-live)            │  │    │
│  │  │  • Accepts client WebSocket connection               │  │    │
│  │  │  • Forwards audio to Gemini Live API                 │  │    │
│  │  │  • Streams audio responses back to client            │  │    │
│  │  │  • Keepalive ping every 15s                          │  │    │
│  │  └──────────────────────────────────────────────────────┘  │    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │         Incident Monitor (Background Task)           │  │    │
│  │  │  • Polls Firestore every 2s for new incidents        │  │    │
│  │  │  • Sends alerts to Gemini via session.send()         │  │    │
│  │  │  • Tracks alerted incidents (deduplication)          │  │    │
│  │  └──────────────────────────────────────────────────────┘  │    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │         REST API Endpoints                           │  │    │
│  │  │  • POST /stream - Ingest security logs               │  │    │
│  │  │  • GET /system_state - Get active incidents          │  │    │
│  │  │  • POST /neutralize/{id} - Neutralize threat         │  │    │
│  │  │  • POST /reset - Clear all data                      │  │    │
│  │  │  • GET /health - Health check                        │  │    │
│  │  └──────────────────────────────────────────────────────┘  │    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────────────┐  │    │
│  │  │      Anomaly Detection Engine                        │  │    │
│  │  │  • Brute Force: 5+ 401s in 10s from same IP         │  │    │
│  │  │  • Impossible Travel: Location change < 30 min      │  │    │
│  │  │  • Data Exfiltration: > 1GB transfer                │  │    │
│  │  └──────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────┘    │
└───────────────┬───────────────────────────┬─────────────────────────┘
                │                           │
                │                           │
                ↓                           ↓
┌─────────────────────────────┐  ┌─────────────────────────────┐
│      AI LAYER               │  │      DATA LAYER             │
│                             │  │                             │
│  ┌───────────────────────┐ │  │  ┌───────────────────────┐ │
│  │  Gemini Live API      │ │  │  │  Google Firestore     │ │
│  │  (2.5 Flash Native)   │ │  │  │  (NoSQL Database)     │ │
│  │                       │ │  │  │                       │ │
│  │  • Audio I/O (24kHz)  │ │  │  │  Collections:         │ │
│  │  • Barge-in support   │ │  │  │  • logs/              │ │
│  │  • Tool calling       │ │  │  │  • incidents/         │ │
│  │  • System instruction │ │  │  │  • system_state/      │ │
│  │                       │ │  │  │                       │ │
│  │  Tools:               │ │  │  │  Queries:             │ │
│  │  • get_incident_report│ │  │  │  • Active incidents   │ │
│  │  • block_ip           │ │  │  │  • Recent logs        │ │
│  └───────────────────────┘ │  │  │  • Brute force check  │ │
└─────────────────────────────┘  │  └───────────────────────┘ │
                                 └─────────────────────────────┘
```

## Data Flow Diagrams

### 1. Attack Detection Flow

```
┌──────────┐
│ Streamer │ (Simulates attacks)
└────┬─────┘
     │ POST /stream
     │ {ip, status_code, timestamp, ...}
     ↓
┌────────────────────────────────────────┐
│  FastAPI: process_log_and_detect_      │
│           anomalies()                   │
│                                         │
│  1. Store log in Firestore             │
│  2. Check for brute force:             │
│     - Query logs from last 10s         │
│     - Count 401s from same IP          │
│     - If >= 5, create incident         │
│  3. Check for impossible travel        │
│  4. Check for data exfiltration        │
└────┬───────────────────────────────────┘
     │
     │ If risk > 70%
     ↓
┌────────────────────────────────────────┐
│  Firestore: incidents/                 │
│  {                                      │
│    type: "Brute Force",                │
│    status: "Active",                   │
│    risk_score: 95,                     │
│    metadata: {ip, city, path},         │
│    timestamp: now                      │
│  }                                      │
└────────────────────────────────────────┘
```

### 2. Autonomous Alert Flow

```
┌────────────────────────────────────────┐
│  FastAPI: monitor_incidents()          │
│  (Background task, runs every 2s)      │
│                                         │
│  1. Query Firestore for Active         │
│     incidents newer than last_check    │
│  2. For each new incident:             │
│     - Skip if already alerted          │
│     - Build alert message              │
│     - Send to Gemini via session.send()│
│     - Mark as alerted                  │
└────┬───────────────────────────────────┘
     │
     │ session.send(input=alert_text)
     ↓
┌────────────────────────────────────────┐
│  Gemini Live API                       │
│  Receives text alert, generates audio  │
│  response with security briefing       │
└────┬───────────────────────────────────┘
     │
     │ Audio PCM data (24kHz)
     ↓
┌────────────────────────────────────────┐
│  WebSocket Proxy                       │
│  Forwards audio to client              │
└────┬───────────────────────────────────┘
     │
     │ WebSocket message
     ↓
┌────────────────────────────────────────┐
│  Browser: Audio playback               │
│  User hears: "Warning: I've detected   │
│  a Brute Force attack..."              │
└────────────────────────────────────────┘
```

### 3. Voice Command Flow

```
┌────────────────────────────────────────┐
│  User speaks: "neutralize it"          │
└────┬───────────────────────────────────┘
     │
     │ Microphone → 16kHz PCM
     ↓
┌────────────────────────────────────────┐
│  Browser: Audio capture                │
│  Converts to base64, sends via WS      │
└────┬───────────────────────────────────┘
     │
     │ WebSocket: realtime_input
     ↓
┌────────────────────────────────────────┐
│  WebSocket Proxy                       │
│  Forwards to Gemini Live API           │
└────┬───────────────────────────────────┘
     │
     │ session.send_realtime_input()
     ↓
┌────────────────────────────────────────┐
│  Gemini Live API                       │
│  1. Transcribes audio                  │
│  2. Understands intent: neutralize     │
│  3. Calls tool: block_ip(incident_id)  │
└────┬───────────────────────────────────┘
     │
     │ Tool call request
     ↓
┌────────────────────────────────────────┐
│  WebSocket Proxy: Tool execution       │
│  1. Receives tool call                 │
│  2. Updates Firestore:                 │
│     incidents/{id}.status = "Neutralized"│
│  3. Returns result to Gemini           │
└────┬───────────────────────────────────┘
     │
     │ Tool response
     ↓
┌────────────────────────────────────────┐
│  Gemini Live API                       │
│  Generates confirmation audio:         │
│  "Threat neutralized successfully"     │
└────┬───────────────────────────────────┘
     │
     │ Audio response
     ↓
┌────────────────────────────────────────┐
│  Browser: Audio playback               │
│  UI refreshes, incident removed        │
└────────────────────────────────────────┘
```

## Component Details

### Frontend (Streamlit)

**File**: `web/app.py`

**Responsibilities**:
- Render security dashboard
- Display real-time telemetry logs
- Show active incidents
- Embed Gemini Live audio bridge
- Manual neutralize button
- Emergency reset button

**Key Features**:
- No auto-refresh (prevents WebSocket disruption)
- Manual refresh button
- Toast notifications for new threats
- Balloons animation on neutralization

### Audio Bridge (JavaScript)

**File**: `web/gemini_live_bridge.py` (embedded JS)

**Responsibilities**:
- Establish WebSocket connection to backend
- Capture microphone audio (16kHz PCM)
- Send audio chunks to backend
- Receive audio from backend
- Play audio responses (24kHz PCM with 2x gain)
- Handle keepalive messages
- Execute tool calls from Gemini

**Key Features**:
- Barge-in support (can interrupt Gemini)
- Audio queueing for smooth playback
- Error handling and reconnection
- Tool call execution (neutralize endpoint)

### Backend (FastAPI)

**File**: `server/main.py`

**Responsibilities**:
- WebSocket proxy for Gemini Live API
- REST API for log ingestion and control
- Anomaly detection engine
- Autonomous incident monitoring
- Tool execution

**Key Features**:
- Async/await for concurrent operations
- Background tasks for monitoring
- WebSocket keepalive (15s interval)
- Incident deduplication
- Comprehensive logging

### Database (Firestore)

**Collections**:

1. **logs/**
   - Document ID: UUID
   - Fields: user_id, ip, status_code, path, method, severity, city, bytes_transferred, timestamp

2. **incidents/**
   - Document ID: UUID
   - Fields: type, user_id, status, severity, risk_score, reasoning_chain, metadata, timestamp, resolved_at

3. **system_state/**
   - Document ID: "current"
   - Fields: mode

**Indexes**:
- logs: timestamp (descending)
- incidents: status + timestamp (composite)

## Security Considerations

1. **API Key Protection**
   - Stored in environment variables
   - Never committed to repository
   - Sanitized (strip quotes/whitespace)

2. **Input Validation**
   - Pydantic models for request validation
   - Type checking on all endpoints

3. **Rate Limiting**
   - Firestore query limits (50 logs, 1 incident)
   - Background task intervals (2s minimum)

4. **Error Handling**
   - Try-catch blocks on all async operations
   - Graceful degradation on failures
   - Detailed logging for debugging

## Performance Optimizations

1. **Background Processing**
   - Log processing in background tasks
   - Non-blocking incident detection

2. **Query Optimization**
   - Limited result sets (50 logs max)
   - Indexed queries on Firestore
   - Python-side filtering to avoid composite indexes

3. **WebSocket Efficiency**
   - Keepalive prevents reconnection overhead
   - Audio streaming (no buffering delays)
   - Incident deduplication (no duplicate alerts)

4. **Memory Management**
   - Alerted incidents tracked in set (O(1) lookup)
   - Limited log retention (1 hour window)

## Scalability Considerations

### Current Architecture (Single Instance)
- Handles 1 concurrent user
- WebSocket connection per user
- In-memory state (alerted_incidents)

### Future Scaling (Multi-Instance)
- Use Redis for shared state (alerted_incidents)
- WebSocket sticky sessions
- Firestore handles concurrent writes
- Cloud Run auto-scaling

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Frontend | Streamlit | 1.31+ | Web dashboard |
| Backend | FastAPI | 0.109+ | REST + WebSocket API |
| AI | Gemini Live API | 2.5 Flash | Audio I/O + Tool calling |
| Database | Firestore | Latest | Real-time NoSQL |
| Language | Python | 3.11 | Core language |
| Deployment | Cloud Run | Latest | Serverless containers |

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                     │
│                                                               │
│  ┌────────────────────┐         ┌────────────────────┐     │
│  │   Cloud Run        │         │   Cloud Run        │     │
│  │   (Backend)        │         │   (Frontend)       │     │
│  │                    │         │                    │     │
│  │  • Auto-scaling    │         │  • Auto-scaling    │     │
│  │  • HTTPS endpoint  │         │  • HTTPS endpoint  │     │
│  │  • WebSocket       │◄────────┤  • Streamlit       │     │
│  │  • Environment vars│         │  • Static assets   │     │
│  └────────┬───────────┘         └────────────────────┘     │
│           │                                                  │
│           │                                                  │
│           ↓                                                  │
│  ┌────────────────────┐                                     │
│  │   Firestore        │                                     │
│  │   (Database)       │                                     │
│  │                    │                                     │
│  │  • Multi-region    │                                     │
│  │  • Auto-backup     │                                     │
│  │  • Real-time sync  │                                     │
│  └────────────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

1. **Logging**
   - Console logs (stdout)
   - File logs (server.log with rotation)
   - Cloud Logging (when deployed)

2. **Metrics**
   - WebSocket connection count
   - Incident detection rate
   - Tool execution success rate
   - API latency

3. **Health Checks**
   - `/health` endpoint
   - Firestore connectivity check
   - Gemini API availability

## Future Enhancements

1. **Multi-User Support**
   - User authentication
   - Per-user incident queues
   - Role-based access control

2. **Advanced Detection**
   - ML-based anomaly detection
   - Threat intelligence integration
   - Behavioral analysis

3. **Enhanced Actions**
   - Real firewall integration
   - Automated playbooks
   - Incident response workflows

4. **Visualization**
   - Real-time attack maps
   - Threat trend analysis
   - Performance dashboards
