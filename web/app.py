import streamlit as st
import os
from datetime import datetime, timedelta
import time
import requests
from google.cloud import firestore
from dotenv import load_dotenv
from pulse_component.visualizer import neural_pulse
from gemini_live_bridge import gemini_live_audio

load_dotenv()

# Phase 3: Early Session Initialization
# Initialize session start time if not set, or if user wants to see all data
if "session_start" not in st.session_state:
    # Start from 1 hour ago to show recent activity
    st.session_state.session_start = datetime.utcnow() - timedelta(hours=1)

st.set_page_config(page_title="Sentinel Live | SOC", layout="wide", initial_sidebar_state="collapsed")
CSS_STYLES = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        --bg-color: #050510;
        --card-bg: rgba(255, 255, 255, 0.03);
        --glass-border: rgba(255, 255, 255, 0.1);
        --accent-blue: #00c0f2;
        --accent-red: #ff4b4b;
        --text-primary: #ffffff;
        --text-secondary: #9ca3af;
    }

    .main { 
        background-color: var(--bg-color); 
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }

    /* Unified Glass Header */
    .unified-header {
        background: rgba(15, 15, 35, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .header-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #fff, var(--accent-blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    /* Professional SOC Cards */
    .soc-card {
        background: var(--card-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .card-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 15px;
        border-left: 3px solid var(--accent-blue);
        padding-left: 10px;
    }

    /* Telemetry Log Styling */
    .log-container {
        background: #000;
        border-radius: 8px;
        padding: 15px;
        height: 400px;
        overflow-y: auto;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        border: 1px solid #1f2937;
    }

    .log-entry { 
        padding: 4px 0;
        border-bottom: 1px solid #111;
        display: flex;
        gap: 10px;
    }

    .log-ts { color: var(--text-secondary); width: 80px; }
    .severity-critical { color: var(--accent-red); font-weight: 700; }
    .severity-high { color: #fbbf24; font-weight: 700; }
    .severity-info { color: var(--accent-blue); }

    /* Buttons */
    .stButton>button {
        background: var(--accent-blue);
        color: black;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        transition: all 0.2s;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 192, 242, 0.3);
    }

    .stButton>button[secondary="true"] {
        background: rgba(255, 255, 255, 0.05);
        color: white;
        border: 1px solid var(--glass-border);
    }
    
    /* Health Bar */
    .health-bar-container {
        width: 100%;
        height: 40px;
        background: #111;
        border-radius: 20px;
        overflow: hidden;
        position: relative;
        border: 1px solid var(--glass-border);
    }
    .health-bar-fill {
        height: 100%;
        transition: width 0.5s ease-in-out, background 0.5s;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 800;
    }

    /* Hide standard streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    section[data-testid='stSidebar'] {display: none;}
"""
st.markdown(f"<style>{CSS_STYLES}</style>", unsafe_allow_html=True)

# Auth & Project Setup
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "glive-build")
DATABASE_ID = os.getenv("GOOGLE_FIRESTORE_DB", "glive-fire-db") # region - us-east1
db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

# Unified Professional Header
st.markdown(f"""
    <div class="unified-header">
        <div>
            <h1 class="header-title">🛡️ SENTINEL LIVE</h1>
            <p style="color: var(--text-secondary); margin: 0; font-size: 0.8rem; font-weight: 600;">MISSION CONTROL // AUTONOMOUS CYBER DEFENSE</p>
        </div>
        <div style="display: flex; gap: 20px; align-items: center;">
            <div style="text-align: right;">
                <p style="color: var(--text-secondary); margin: 0; font-size: 0.7rem; font-weight: bold; text-transform: uppercase;">Engine Status</p>
                <p style="color: #22c55e; margin: 0; font-size: 0.8rem; font-weight: 800;">● SYNCED</p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Inject Gemini Bridge directly into a floating or specific container if needed, 
# but for better integration, we'll place it in the next layout block.

main_col1, main_col2 = st.columns([1, 2])

with main_col1:
    # 1. Gemini SOC Commander Card
    st.markdown('<p class="card-title">Connect to Gemini SOC Commander</p>', unsafe_allow_html=True)
    api_key = os.getenv("GOOGLE_AISTUDIO_KEY")
    gemini_live_audio(api_key)
    st.markdown('<p style="font-family: \'JetBrains Mono\', monospace; font-size: 0.65rem; color: var(--text-secondary); margin-top: 10px; opacity: 0.5;">UPLINK V2.0 // MULTIMODAL LIVE PROTOCOL</p>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Combined System Status & Incident Queue Card
    st.markdown('<p class="card-title">System Status & Active Threats</p>', unsafe_allow_html=True)
    
    # Fetch active incidents with force refresh
    active_incidents = list(db.collection("incidents").where(filter=firestore.FieldFilter("status", "==", "Active")).stream())
    max_risk = 0
    if active_incidents:
        max_risk = max([inc.to_dict().get("risk_score", 0) for inc in active_incidents])
    
    status_color = "#22c55e" # Green
    status_text = "NOMINAL"
    if max_risk >= 90:
        status_color = "#ef4444" # Red
        status_text = "CRITICAL BREACH"
    elif max_risk > 0:
        status_color = "#f59e0b" # Yellow
        status_text = "ANOMALY DETECTED"
        
    st.markdown(f"""
        <div class="health-bar-container">
            <div class="health-bar-fill" style="width: {max_risk if max_risk > 5 else 100}%; background: {status_color};">
                {status_text} (THREAT LEVEL: {max_risk}%)
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Show active incidents
    active_incidents_list = [inc for inc in active_incidents]
    active_incidents_list.sort(key=lambda x: x.to_dict().get("timestamp", datetime.min), reverse=True)

    if not active_incidents_list:
        st.markdown('<p style="color: #444; font-size: 0.8rem; font-style: italic;">No active threats detected.</p>', unsafe_allow_html=True)
    else:
        for inc in active_incidents_list:
            data = inc.to_dict()
            with st.expander(f"🔴 {data.get('type')} Incident", expanded=True):
                st.markdown(f"**Risk Score:** {data.get('risk_score')}%")
                st.markdown(f"**IP Address:** {data.get('metadata', {}).get('ip')}")
                st.markdown(f"**Location:** {data.get('metadata', {}).get('city')}")
                st.markdown("**Sentinel Analysis:**")
                for step in data.get("reasoning_chain", []):
                    st.markdown(f"- {step}")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(f"🚫 Neutralize", key=f"neutralize_{inc.id}", use_container_width=True):
                        with st.spinner("Neutralizing threat..."):
                            try:
                                response = requests.post(
                                    f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/neutralize/{inc.id}",
                                    timeout=5
                                )
                                
                                if response.status_code == 200:
                                    st.success("✅ Threat neutralized!")
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed: {response.status_code}")
                            except requests.exceptions.Timeout:
                                st.error("⏱️ Request timed out")
                            except requests.exceptions.ConnectionError:
                                st.error("🔌 Cannot connect to backend")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                with col2:
                    st.markdown(f'<p style="color: #666; font-size: 0.75rem; text-align: center; margin-top: 8px;">ID: {inc.id[:8]}...</p>', unsafe_allow_html=True)

with main_col2:
    # 4. Telemetry Card
    st.markdown('<p class="card-title">Live Security Telemetry</p>', unsafe_allow_html=True)
    log_container = st.empty()
    
    def update_logs():
        # Fetching logs ONLY from this session
        logs_stream = db.collection("logs").where(filter=firestore.FieldFilter("timestamp", ">", st.session_state.session_start)).limit(50).stream()
        logs_list = [l.to_dict() for l in logs_stream]
        logs_list.sort(key=lambda x: x.get("timestamp"), reverse=True)
        
        log_html = f'<style>{CSS_STYLES}</style><div class="log-container">'
        for data in logs_list:
            sev = data.get("severity", "info").lower()
            ts = data.get("timestamp").strftime("%H:%M:%S")
            log_item = f'<div class="log-entry"><span class="log-ts">[{ts}]</span>'
            log_item += f'<span class="severity-{sev}">{data.get("severity").ljust(8)}</span>'
            log_item += f'<span style="color: #fff;">{data.get("user_id")} @ {data.get("city")}</span>'
            log_item += f'<span style="color: #444;">-</span>'
            log_item += f'<span style="color: var(--accent-blue);">{data.get("path")}</span></div>'
            log_html += log_item
        log_html += '</div>'
        log_container.markdown(log_html, unsafe_allow_html=True)

    update_logs()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 5. Control Card
    st.markdown('<p class="card-title">Tactical Control</p>', unsafe_allow_html=True)
    ctrl_col1, ctrl_col2 = st.columns(2)
    with ctrl_col1:
        if st.button("🔄 REFRESH TELEMETRY"):
            st.rerun()
    with ctrl_col2:
        if st.button("🧨 EMERGENCY RESET"):
            try:
                response = requests.post(f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/reset")
                if response.status_code == 200:
                    # Reset session start time to now
                    st.session_state.session_start = datetime.utcnow() - timedelta(hours=1)
                    st.toast("System Reset Complete. Refreshing...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Reset failed: {response.text}")
            except Exception as e:
                st.error(f"Reset failed: {e}")

# Autorefresh is handled by the user manual trigger or we could add st_autorefresh here.

# Note: In a real hackathon demo, we'd use st_autorefresh or a background thread
# For now, we manually refresh to ensure data is "fresh" and from this session.
