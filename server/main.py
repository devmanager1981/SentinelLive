from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from .database import get_db
from datetime import datetime, timedelta
from google.cloud import firestore
import uuid
import math
import logging
from logging.handlers import RotatingFileHandler

# Setup file logging with UTF-8 encoding to handle emojis
log_handler = RotatingFileHandler('server.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

# Get root logger and add handler
logger = logging.getLogger()
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

app = FastAPI(title="Sentinel Live API")
db = get_db()

class LogEntry(BaseModel):
    user_id: str = "user-123"
    ip: str
    status_code: int = 200
    path: str
    method: str = "GET"
    severity: str = "INFO"
    city: str = ""
    bytes_transferred: int = 0

@app.get("/")
async def root():
    return {"status": "Sentinel Live Production Backend Running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Sentinel Live API"
    }

def calculate_distance(city1, city2):
    # Mock distance calculation for demo
    if not city1 or not city2 or city1 == city2:
        return 0
    return 1000 # Assume cities are 1000km apart for demo

async def process_log_and_detect_anomalies(entry_dict: dict, now: datetime, doc_id: str):
    try:
        # 1. Log to Firestore
        print(f"📝 Processing log: {entry_dict.get('status_code')} from {entry_dict.get('ip')}")
        db.collection("logs").document(doc_id).set(entry_dict)
        
        entry = LogEntry(**entry_dict)
        risk_score = 0
        reasoning = []
        anomaly_type = None

        # 1. Check for Brute Force (High Frequency 401s)
        if entry.status_code == 401:
            print(f"🔍 Checking for brute force from IP {entry.ip}")
            five_secs_ago = now - timedelta(seconds=10) # 10s for better brute force detection
            recent_logs = db.collection("logs").where(filter=firestore.FieldFilter("timestamp", ">", five_secs_ago)).stream()
            count = 0
            for log in recent_logs:
                d = log.to_dict()
                if d.get("ip") == entry.ip and d.get("status_code") == 401:
                    count += 1
            
            print(f"🔢 Found {count} 401s from {entry.ip} in last 10 seconds")
            
            if count >= 5:  # Trigger on 5th attempt (was >= 6)
                risk_score = 95
                anomaly_type = "Brute Force"
                reasoning.append(f"Detected {count} authentication failures from IP {entry.ip} recently.")
                print(f"🚨 BRUTE FORCE DETECTED! Risk: {risk_score}%")

        # 2. Check for Impossible Travel
        if not anomaly_type:
            user_logs_query = db.collection("logs").where(filter=firestore.FieldFilter("user_id", "==", entry.user_id)).limit(10).stream()
            logs = [l.to_dict() for l in user_logs_query]
            logs.sort(key=lambda x: x.get("timestamp"), reverse=True)

            if len(logs) >= 2:
                prev_log = logs[1]
                if prev_log.get("city") and entry.city and prev_log.get("city") != entry.city:
                    time_diff = (now - prev_log["timestamp"].replace(tzinfo=None)).total_seconds() / 60
                    if time_diff < 30:
                        # Placeholder for Gemini model setup, as per instruction
                        # setup: { model: "models/gemini-2.0-flash-exp" }
                        reasoning.append(f"User {entry.user_id} @ {entry.city}, but was in {prev_log.get('city')} {int(time_diff)} mins ago.")

        # 3. Check for Data Exfiltration
        if not anomaly_type and entry.bytes_transferred > 1000000000:
            risk_score = 90
            anomaly_type = "Data Exfiltration"
            reasoning.append(f"Exfiltration: {entry.bytes_transferred / (1024**3):.2f} GB in one session.")

        # Trigger Incident if Risk is High
        if risk_score > 70:
            # Check if there's already an active incident for this IP to prevent duplicates
            existing_incidents = list(db.collection("incidents").where(
                filter=firestore.FieldFilter("status", "==", "Active")
            ).stream())
            
            # Check if any existing incident has the same IP
            has_active = False
            for existing in existing_incidents:
                existing_data = existing.to_dict()
                if existing_data.get("metadata", {}).get("ip") == entry.ip:
                    has_active = True
                    print(f"⚠️ Active incident already exists for IP {entry.ip}, skipping duplicate")
                    break
            
            if not has_active:
                incident_id = str(uuid.uuid4())
                print(f"🚨 Creating incident: {anomaly_type} (Risk: {risk_score}%)")
                db.collection("incidents").document(incident_id).set({
                    "type": anomaly_type,
                    "user_id": entry.user_id,
                    "status": "Active",
                    "severity": "CRITICAL" if risk_score >= 90 else "HIGH",
                    "risk_score": risk_score,
                    "reasoning_chain": reasoning,
                    "metadata": {"ip": entry.ip, "city": entry.city, "path": entry.path},
                    "timestamp": now
                })
                print(f"✅ Incident {incident_id} created in Firestore")
    except Exception as e:
        print(f"❌ Error in process_log_and_detect_anomalies: {e}")
        import traceback
        traceback.print_exc()

@app.post("/stream")
async def ingest_log(entry: LogEntry, background_tasks: BackgroundTasks):
    doc_id = str(uuid.uuid4())
    now = datetime.utcnow()
    log_data = entry.dict()
    log_data["timestamp"] = now
    
    logger.info(f"Received log: {entry.status_code} from {entry.ip}")
    
    # Process everything in background to avoid any response latency
    background_tasks.add_task(process_log_and_detect_anomalies, log_data, now, doc_id)

    return {"status": "accepted"}

@app.get("/system_state")
async def get_system_state():
    # Fetch most recent active incident for Gemini report
    inc_query = db.collection("incidents").where(filter=firestore.FieldFilter("status", "==", "Active")).limit(1).stream()
    inc_list = [i.to_dict() for i in inc_query]
    
    if inc_list:
        return {"active_incident": inc_list[0]}
    return {"status": "Nominal", "active_incident": None}

@app.post("/reset")
async def reset_demo(background_tasks: BackgroundTasks):
    """Reset demo by deleting all incidents and logs"""
    
    async def do_reset():
        try:
            print("🧹 Starting reset...")
            
            # Delete incidents in batches
            batch = db.batch()
            incidents = db.collection("incidents").limit(500).stream()
            count = 0
            for doc in incidents:
                batch.delete(doc.reference)
                count += 1
                if count % 100 == 0:
                    batch.commit()
                    batch = db.batch()
            if count % 100 != 0:
                batch.commit()
            print(f"✅ Deleted {count} incidents")
            
            # Delete logs in batches
            batch = db.batch()
            logs = db.collection("logs").limit(500).stream()
            count = 0
            for doc in logs:
                batch.delete(doc.reference)
                count += 1
                if count % 100 == 0:
                    batch.commit()
                    batch = db.batch()
            if count % 100 != 0:
                batch.commit()
            print(f"✅ Deleted {count} logs")
            
            # Reset system state
            db.collection("system_state").document("current").set({"mode": "normal"})
            print("✅ Reset complete")
            
        except Exception as e:
            print(f"❌ Error during reset: {e}")
            import traceback
            traceback.print_exc()
    
    # Run reset in background
    background_tasks.add_task(do_reset)
    
    return {"status": "Reset initiated"}


@app.post("/neutralize/{incident_id}")
async def neutralize_incident(incident_id: str):
    """Neutralize a specific incident by ID"""
    try:
        logger.info(f"Neutralizing incident: {incident_id}")
        print(f"[NEUTRALIZE] Incident: {incident_id}")
        
        # Check if incident exists
        incident_ref = db.collection("incidents").document(incident_id)
        incident = incident_ref.get()
        
        if not incident.exists:
            logger.error(f"Incident {incident_id} not found")
            print(f"[ERROR] Incident {incident_id} not found")
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Update status to Neutralized
        incident_ref.update({
            "status": "Neutralized",
            "resolved_at": datetime.utcnow()
        })
        
        logger.info(f"Incident {incident_id} neutralized via UI button")
        print(f"[SUCCESS] Incident {incident_id} neutralized via UI button")
        return {"status": "success", "incident_id": incident_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error neutralizing incident {incident_id}: {e}")
        print(f"[ERROR] Neutralizing incident {incident_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket proxy for Gemini Live API using Google Gen AI SDK
from fastapi import WebSocket, WebSocketDisconnect
from google import genai
import json
import os
import asyncio

@app.websocket("/ws/gemini-live")
async def gemini_live_proxy(websocket: WebSocket):
    """
    WebSocket proxy for Gemini Live API using the Google Gen AI SDK.
    The SDK handles authentication and WebSocket connection internally.
    """
    await websocket.accept()
    print("✅ Client connected to proxy")

    api_key = os.getenv("GOOGLE_AISTUDIO_KEY", "").strip().strip('\'"')
    if not api_key:
        print("❌ API key not configured")
        await websocket.send_text(json.dumps({"error": "API key not configured"}))
        await websocket.close()
        return

    print(f"🔑 Using API key (length: {len(api_key)})")
    
    try:
        # Initialize Gemini client with API key
        client = genai.Client(api_key=api_key)
        print("🔌 Connecting to Gemini Live API via SDK...")
        
        # Configure the Live API session using LiveConnectConfig
        from google.genai import types
        
        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            system_instruction="""You are Sentinel, an AI security analyst monitoring a live security operations center. 
                    
Your role:
- Monitor for security incidents by checking the incident report regularly
- Alert the user immediately when you detect critical threats
- Provide clear, concise security briefings
- Execute remediation actions when instructed

When you detect an active incident:
1. Announce it clearly: "Warning: I've detected a [threat type] attack"
2. Describe the threat details (IP, location, risk score)
3. Wait for user instruction to neutralize

Be proactive but wait for user confirmation before taking action.""",
            tools=[
                {
                    "function_declarations": [
                        {
                            "name": "get_incident_report",
                            "description": "Queries Firestore for the latest active security breach."
                        },
                        {
                            "name": "block_ip",
                            "description": "Sets incident status to 'Neutralized' and updates firewall/blocklist.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "incident_id": {"type": "string"}
                                },
                                "required": ["incident_id"]
                            }
                        }
                    ]
                }
            ]
        )
        
        print(f"📋 Config created: response_modalities={config.response_modalities}")
        
        # Connect to Gemini Live API
        async with client.aio.live.connect(
            model="models/gemini-2.5-flash-native-audio-latest",
            config=config
        ) as session:
            print("✅ Connected to Gemini Live API")
            print("🎧 Session object created successfully")
            
            # Send connection success to client
            await websocket.send_text(json.dumps({"status": "connected"}))
            print("📤 Sent connection success to client")
            
            # Forward messages from client to Gemini
            async def forward_to_gemini():
                try:
                    while True:
                        data = await websocket.receive_text()
                        message = json.loads(data)
                        print(f"📤 Client → Gemini: {list(message.keys())}")
                        
                        # Handle different message types
                        if "setup" in message:
                            # Setup is handled by the SDK config, skip
                            pass
                        elif "realtime_input" in message:
                            # Send audio chunks using send_realtime_input
                            for chunk in message["realtime_input"].get("media_chunks", []):
                                from google.genai import types
                                import base64
                                
                                # Decode base64 audio data
                                audio_data = base64.b64decode(chunk["data"])
                                
                                # Send using send_realtime_input with Blob
                                await session.send_realtime_input(
                                    audio=types.Blob(
                                        mime_type="audio/pcm",
                                        data=audio_data
                                    )
                                )
                        elif "client_content" in message:
                            # Send text messages
                            await session.send_client_content(
                                turns=message["client_content"],
                                turn_complete=True
                            )
                            
                except WebSocketDisconnect:
                    print("⚠️ Client disconnected")
                except Exception as e:
                    print(f"❌ Error forwarding to Gemini: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Monitor Firestore for new incidents and alert Gemini
            async def monitor_incidents():
                try:
                    print("Starting incident monitor...")
                    from datetime import timezone
                    last_check = datetime.now(timezone.utc)
                    alerted_incidents = set()
                    
                    while True:
                        await asyncio.sleep(2)
                        
                        active_incidents = db.collection("incidents").where(
                            filter=firestore.FieldFilter("status", "==", "Active")
                        ).stream()
                        
                        for inc_doc in active_incidents:
                            inc_data = inc_doc.to_dict()
                            incident_id = inc_doc.id
                            
                            if incident_id in alerted_incidents:
                                continue
                            
                            inc_timestamp = inc_data.get("timestamp")
                            
                            if not inc_timestamp or inc_timestamp <= last_check:
                                continue
                            
                            incident_type = inc_data.get("type", "Unknown")
                            risk_score = inc_data.get("risk_score", 0)
                            ip = inc_data.get("metadata", {}).get("ip", "Unknown")
                            city = inc_data.get("metadata", {}).get("city", "Unknown")
                            
                            # Don't include incident_id in the spoken alert - Gemini reads it out loud and it wastes time
                            # The backend will handle mapping internally
                            alert_text = (
                                f"CRITICAL SECURITY ALERT: A {incident_type} attack has been detected. "
                                f"Source IP address: {ip}. Location: {city}. Risk level: {risk_score} percent. "
                                f"Brief the operator immediately. Keep it short and urgent. "
                                f"If the operator says neutralize, use the block_ip tool with incident_id value: {incident_id}. "
                                f"Do NOT read the incident ID out loud."
                            )
                            
                            print(f"[ALERT] Pushing incident to Gemini: {incident_type} from {ip}")
                            
                            await session.send(input=alert_text, end_of_turn=True)
                            
                            alerted_incidents.add(incident_id)
                        
                        last_check = datetime.now(timezone.utc)
                        
                except Exception as e:
                    print(f"[ERROR] Incident monitor: {e}")
                    import traceback
                    traceback.print_exc()
            
            # WebSocket keepalive to prevent timeout
            async def keepalive():
                try:
                    while True:
                        await asyncio.sleep(15)  # Send keepalive every 15 seconds
                        # Send a minimal message to keep connection alive
                        await websocket.send_text(json.dumps({"keepalive": True}))
                        print("💓 Keepalive ping sent")
                except Exception as e:
                    print(f"❌ Error in keepalive: {e}")
            
            # Forward responses from Gemini to client
            async def forward_to_client():
                try:
                    print("🎧 Starting to listen for Gemini responses...")
                    async for response in session.receive():
                        print(f"📥 Gemini → Client: Response received, type={type(response)}")
                        
                        # Handle tool calls from Gemini
                        if hasattr(response, 'tool_call') and response.tool_call:
                            print(f"🔧 Tool call received: {response.tool_call}")
                            tool_responses = []
                            
                            for func_call in response.tool_call.function_calls:
                                tool_name = func_call.name
                                tool_args = func_call.args if hasattr(func_call, 'args') else {}
                                
                                print(f"🔧 Executing tool: {tool_name} with args: {tool_args}")
                                
                                # Execute the tool
                                if tool_name == "get_incident_report":
                                    result = await get_system_state()
                                    print(f"✅ Tool result: {result}")
                                elif tool_name == "block_ip":
                                    incident_id = tool_args.get("incident_id", "")
                                    print(f"🚫 Blocking IP for incident: {incident_id}")
                                    
                                    if not incident_id:
                                        result = {"error": "No incident_id provided"}
                                        print(f"❌ Error: No incident_id provided")
                                    else:
                                        try:
                                            # Update Firestore to neutralize
                                            db.collection("incidents").document(incident_id).update({
                                                "status": "Neutralized",
                                                "resolved_at": datetime.utcnow()
                                            })
                                            result = {"status": "success", "action": "Threat Neutralized", "incident_id": incident_id}
                                            print(f"✅ Incident {incident_id} neutralized via Gemini tool call")
                                        except Exception as e:
                                            result = {"error": str(e)}
                                            print(f"❌ Error neutralizing incident: {e}")
                                            import traceback
                                            traceback.print_exc()
                                else:
                                    result = {"error": "Unknown tool"}
                                    print(f"❌ Unknown tool: {tool_name}")
                                
                                tool_responses.append({
                                    "name": tool_name,
                                    "response": result
                                })
                            
                            # Send tool response back to Gemini
                            from google.genai import types
                            await session.send(
                                types.LiveClientToolResponse(
                                    function_responses=tool_responses
                                )
                            )
                            
                            # Also forward to client for UI update
                            response_data = {
                                "toolCall": {
                                    "functionCalls": [{"name": tc.name, "args": tc.args if hasattr(tc, 'args') else {}} for tc in response.tool_call.function_calls]
                                }
                            }
                            await websocket.send_text(json.dumps(response_data))
                            continue
                        
                        # Handle regular responses
                        response_data = {
                            "serverContent": {
                                "modelTurn": {
                                    "parts": []
                                }
                            }
                        }
                        
                        # Handle audio responses
                        if hasattr(response, 'server_content') and response.server_content:
                            if hasattr(response.server_content, 'model_turn') and response.server_content.model_turn:
                                for part in response.server_content.model_turn.parts:
                                    if hasattr(part, 'inline_data') and part.inline_data:
                                        import base64
                                        audio_bytes = part.inline_data.data
                                        
                                        # If data is already bytes, encode to base64
                                        if isinstance(audio_bytes, bytes):
                                            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                                        else:
                                            audio_b64 = audio_bytes
                                        
                                        print(f"🔊 Audio data received, length={len(audio_bytes) if isinstance(audio_bytes, bytes) else len(audio_b64)}")
                                        response_data["serverContent"]["modelTurn"]["parts"].append({
                                            "inlineData": {
                                                "mimeType": "audio/pcm",
                                                "data": audio_b64
                                            }
                                        })
                        
                        if response_data["serverContent"]["modelTurn"]["parts"]:
                            await websocket.send_text(json.dumps(response_data))
                            print("✅ Sent audio response to client")
                        
                except Exception as e:
                    print(f"❌ Error in forward_to_client: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Run all four tasks concurrently
            await asyncio.gather(
                forward_to_gemini(),
                forward_to_client(),
                monitor_incidents(),
                keepalive(),
                return_exceptions=True
            )

    except Exception as e:
        error_msg = f"Gemini connection failed: {str(e)}"
        print(f"❌ {error_msg}")
        await websocket.send_text(json.dumps({"error": error_msg}))
    finally:
        print("🔌 Closing proxy connection")
        await websocket.close()

