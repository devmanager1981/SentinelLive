# 🛡️ Sentinel Live - AI Security Operations Commander

> **Gemini Live Agent Challenge Submission** | Category: Live Agents

An autonomous AI security analyst powered by Gemini Live API that monitors threats in real-time and responds to voice commands. Built for the Gemini Live Agent Challenge (#GeminiLiveAgentChallenge).

## 🎯 The Problem

Security Operations Centers (SOCs) are overwhelmed with alerts. Analysts spend hours monitoring dashboards, manually investigating threats, and executing remediation actions. Traditional chatbots require constant user input and can't proactively alert teams.

## 💡 The Solution

Sentinel is a voice-first AI security analyst that:
- **Monitors autonomously**: Watches for security incidents in real-time
- **Alerts proactively**: Interrupts with urgent voice notifications when threats are detected
- **Responds naturally**: Accepts voice commands like "neutralize it" to execute actions
- **Handles interruptions**: Supports barge-in during conversations

## 🎥 Demo Video

[Link to YouTube/Vimeo demo - max 4 minutes]

## 🏗️ Architecture

```
┌─────────────────┐
│  Streamlit UI   │ ← User Interface (Dashboard + Audio Bridge)
└────────┬────────┘
         │ WebSocket
         ↓
┌─────────────────┐
│  FastAPI Server │ ← Backend Proxy + Incident Monitor
│  (Cloud Run)    │
└────┬───────┬────┘
     │       │
     │       └──────→ ┌──────────────┐
     │                │  Firestore   │ ← Real-time Data Store
     │                └──────────────┘
     ↓
┌─────────────────┐
│ Gemini Live API │ ← Audio I/O + Tool Calling
│ (2.5 Flash)     │
└─────────────────┘
```

### Key Components

1. **Streamlit Frontend** (`web/app.py`)
   - Real-time security dashboard
   - WebSocket audio bridge to Gemini
   - Incident visualization

2. **FastAPI Backend** (`server/main.py`)
   - WebSocket proxy for Gemini Live API
   - Autonomous incident monitoring
   - Tool execution (IP blocking simulation)

3. **Gemini Live Integration**
   - Real-time audio streaming (24kHz PCM)
    - Function calling for actions

4. **Google Cloud Firestore**
   - Stores security logs and incidents
   - Real-time queries for threat detection

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Project with Firestore enabled
- Google AI Studio API Key
- Node.js (for Streamlit components)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/sentinel-live.git
cd sentinel-live
```

### 2. Set Up Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file:

```env
GOOGLE_AISTUDIO_KEY=your_api_key_here
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_FIRESTORE_DB=your_firestore_db_name
BACKEND_URL=http://localhost:8000
```

### 4. Start Backend Server

```bash
cd server
uvicorn main:app --reload --port 8000
```

### 5. Start Frontend

```bash
cd web
streamlit run app.py --server.port 8501
```

### 6. Run Attack Simulation

```bash
python streamer.py
```

## 🎮 How to Use

1. **Open Dashboard**: Navigate to `http://localhost:8501`
2. **Connect to Gemini**: Click "Establish Neural Link" button
3. **Start Attack Simulation**: Run `streamer.py` and press 'a' for attack mode
4. **Listen for Alert**: Gemini will interrupt with voice alert when threat detected
5. **Respond with Voice**: Say "neutralize it" or click the Neutralize button
6. **Watch Resolution**: Incident status updates to "Neutralized"

## 🔧 Technologies Used

### Required (Hackathon Compliance)
- ✅ **Gemini Live API**: `gemini-2.5-flash-native-audio-latest`
- ✅ **Google GenAI SDK**: Python SDK for Live API integration
- ✅ **Google Cloud Firestore**: Real-time NoSQL database
- ✅ **Hosted on Google Cloud**: Deployable to Cloud Run

### Additional Stack
- **FastAPI**: High-performance async backend
- **Streamlit**: Interactive web dashboard
- **WebSockets**: Real-time bidirectional communication
- **Python 3.11**: Core language

## 📊 Key Features

### 1. Multimodal Interaction
- **Audio Input**: Natural voice commands via microphone
- **Audio Output**: Gemini speaks alerts and responses (24kHz PCM)
- **Visual Dashboard**: Real-time threat visualization

### 2. Autonomous Monitoring
- Polls Firestore every 2 seconds for new incidents
- Detects brute force attacks (5+ failed logins in 10s)
- Proactively alerts without user polling


### 3. Tool Calling
- `get_incident_report`: Fetches active threats
- `block_ip`: Neutralizes threats (simulated firewall action)

### 4. Error Handling
- WebSocket keepalive (prevents timeout)
- Incident deduplication (prevents duplicate alerts)
- Graceful reconnection

## 🏆 Hackathon Judging Criteria

### Innovation & Multimodal UX (40%)
- ✅ Breaks "text box" paradigm with voice-first interaction
- ✅ Seamless audio experience (no turn-based delays)
- ✅ Handles interruptions naturally
- ✅ Distinct persona: "Sentinel" AI Security Analyst
- ✅ Context-aware and proactive

### Technical Implementation (30%)
- ✅ Robust Google GenAI SDK integration
- ✅ Google Cloud native (Firestore + Cloud Run ready)
- ✅ Sound system design with error handling
- ✅ Tool calling for actions
- ✅ WebSocket architecture for real-time audio


## 📁 Project Structure

```
sentinel-live/
├── server/
│   ├── main.py              # FastAPI backend + WebSocket proxy
│   ├── database.py          # Firestore client
│   └── tools.py             # Tool definitions
├── web/
│   ├── app.py               # Streamlit dashboard
│   ├── gemini_live_bridge.py # WebSocket audio bridge
│   └── pulse_component/     # UI visualizations
├── streamer.py              # Attack simulation
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── README.md                # This file
```

## 🚢 Deployment to Google Cloud

### Option 1: Cloud Run (Recommended)

```bash
# Build and deploy backend
gcloud run deploy sentinel-backend \
  --source ./server \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Build and deploy frontend
gcloud run deploy sentinel-frontend \
  --source ./web \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Option 2: Manual Deployment

See `DEPLOYMENT.md` for detailed instructions.

## 🐛 Troubleshooting

### WebSocket Connection Issues
- Ensure backend is running on port 8000
- Check API key is valid and has no quotes
- Verify Firestore credentials are correct

### Audio Not Working
- Allow microphone permissions in browser
- Check audio output device is selected
- Verify sample rate is 24kHz

### Incidents Not Appearing
- Confirm Firestore database name matches `.env`
- Check streamer is running in attack mode
- Verify backend logs show incident creation

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built for the **Gemini Live Agent Challenge**
- Powered by **Google Gemini Live API**
- Hosted on **Google Cloud Platform**
- Created with ❤️ for the security community

## 📧 Contact

Sachin Gupta
- GitHub: https://github.com/devmanager1981/SentinelLive

---

**#GeminiLiveAgentChallenge** | **Category: Live Agents** | **Built with Gemini Live API**
