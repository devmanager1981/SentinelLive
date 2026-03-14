import streamlit as st
import streamlit.components.v1 as components
import os

def gemini_live_audio(api_key: str):
    """
    Injects a Javascript-based audio bridge into the Streamlit app.
    Connects directly to the Google AI Studio Multimodal Live API.
    """
    # Validate API key is not None before sanitization
    if api_key is None:
        api_key = ""
    
    # Sanitize API key: remove leading/trailing whitespace and surrounding quotes
    api_key = api_key.strip().strip('\'"')
    
    # Validate API key
    if not api_key or len(api_key) < 10:
        error_html = """
        <div style="border: 1px solid rgba(255,77,77,0.3); padding: 15px; border-radius: 12px; background: rgba(255,77,77,0.1); backdrop-filter: blur(10px);">
            <div style="color: #ff4b4b; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; font-weight: 600; margin-bottom: 8px;">
                ⚠️ API Key Error
            </div>
            <div style="color: #fbbf24; font-family: sans-serif; font-size: 0.85rem; line-height: 1.5;">
                Invalid or missing Google AI Studio API key. Please check your .env file and ensure GOOGLE_AISTUDIO_KEY is set correctly.
            </div>
        </div>
        """
        components.html(error_html, height=100)
        return
    
    # Get backend URL from environment variable (supports Cloud Run deployment)
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    # Convert HTTP URL to WebSocket URL
    ws_url = backend_url.replace("https://", "wss://").replace("http://", "ws://")
    ws_endpoint = f"{ws_url}/ws/gemini-live"
    
    js_code = f"""
    <div id="bridge-container" style="border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; background: rgba(255,255,255,0.03); backdrop-filter: blur(10px);">
        <div id="gemini-status" style="color: #9ca3af; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; margin-bottom: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em;">
            Status: <span style="color: #ff4b4b;">Offline</span>
        </div>
    <button id="connect-btn" style="width: 100%; height: 45px; background: #00c0f2; color: #000; border: none; border-radius: 8px; cursor: pointer; font-weight: 800; font-family: sans-serif; transition: all 0.2s; text-transform: uppercase; letter-spacing: 0.05em;">
        Establish Neural Link
    </button>
    <audio id="gemini-audio" autoplay></audio>

    <script>
        const BACKEND_URL = "{backend_url}";
        const URL = "{ws_endpoint}";
        
        let ws;
        let audioContext;
        let processor;
        let stream;
        let audioQueue = [];
        let isPlaying = false;
        let nextStartTime = 0;

        const connectBtn = document.getElementById('connect-btn');
        const statusDiv = document.getElementById('gemini-status');

        connectBtn.onclick = async () => {{
            if (ws) {{
                stop();
                return;
            }}
            start();
        }};

        async function start() {{
            statusDiv.innerHTML = 'Status: <span style="color: #fbbf24;">Initializing...</span>';
            console.log("Connecting to:", URL);
            ws = new WebSocket(URL);

            ws.onopen = () => {{
                console.log("WebSocket opened.");
                statusDiv.innerHTML = 'Status: <span style="color: #22c55e;">Uplink Active</span>';
                connectBtn.innerText = "Terminate Link";
                connectBtn.style.background = "#ff4b4b";
                sendSetup();
                startMicrophone();
            }};

            ws.onmessage = async (event) => {{
                const response = JSON.parse(event.data);
                
                // Ignore keepalive messages
                if (response.keepalive) {{
                    return;
                }}
                
                // console.log("Received:", response);
                if (response.serverContent?.modelTurn?.parts?.[0]?.inlineData) {{
                    playAudio(response.serverContent.modelTurn.parts[0].inlineData.data);
                }}
                if (response.toolCall) {{
                    handleToolCall(response.toolCall);
                }}
            }};

            ws.onclose = (e) => {{
                console.log("WebSocket closed:", e.code, e.reason);
                
                // Provide specific error messages based on close code
                if (e.code === 1006) {{
                    // Abnormal closure - likely authentication or connection issue
                    const maskedUrl = URL.replace(/key=[^&]+/, 'key=***MASKED***');
                    console.error("Connection failed (1006 - Abnormal Closure). URL:", maskedUrl);
                    console.error("API key length:", API_KEY.length, "characters");
                    statusDiv.innerHTML = 'Status: <span style="color: #ff4b4b;">ERR: Auth Failed - Check API Key</span>';
                }} else if (e.code === 1000) {{
                    // Normal closure
                    console.log("Connection closed normally");
                }} else {{
                    // Other error codes
                    console.error("Connection closed with code:", e.code, "reason:", e.reason);
                    statusDiv.innerHTML = 'Status: <span style="color: #ff4b4b;">ERR: Connection Closed (' + e.code + ')</span>';
                }}
                
                stop();
            }};
            
            ws.onerror = (e) => {{
                console.error("WebSocket Error:", e);
                const maskedUrl = URL.replace(/key=[^&]+/, 'key=***MASKED***');
                console.error("Failed to connect to:", maskedUrl);
                console.error("Troubleshooting tips:");
                console.error("  1. Verify GOOGLE_AISTUDIO_KEY in .env file");
                console.error("  2. Ensure API key has no quotes or extra spaces");
                console.error("  3. Check that the API key is valid and active");
                console.error("  4. Verify network connectivity to generativelanguage.googleapis.com");
                statusDiv.innerHTML = 'Status: <span style="color: #ff4b4b;">ERR: Connection Failed</span>';
            }};
        }}

        function stop() {{
            if (ws) ws.close();
            if (stream) stream.getTracks().forEach(t => t.stop());
            if (audioContext) audioContext.close();
            ws = null;
            statusDiv.innerHTML = 'Status: <span style="color: #ff4b4b;">Offline</span>';
            connectBtn.innerText = "Establish Neural Link";
            connectBtn.style.background = "#00c0f2";
        }}

        function sendSetup() {{
            const setup = {{
                setup: {{
                    model: "models/gemini-2.5-flash-native-audio-latest",
                    generation_config: {{
                        response_modalities: ["AUDIO"]
                    }},
                    tools: [{{
                        function_declarations: [
                            {{
                                name: "get_incident_report",
                                description: "Queries Firestore for the latest active security breach."
                            }},
                            {{
                                name: "block_ip",
                                description: "Sets incident status to 'Neutralized' and updates firewall/blocklist.",
                                parameters: {{
                                    type: "object",
                                    properties: {{
                                        incident_id: {{ type: "string" }}
                                    }},
                                    required: ["incident_id"]
                                }}
                            }}
                        ]
                    }}]
                }}
            }};
            console.log("Sending setup:", setup);
            ws.send(JSON.stringify(setup));
        }}

        async function startMicrophone() {{
            audioContext = new AudioContext({{ sampleRate: 16000 }});
            stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
            const source = audioContext.createMediaStreamSource(stream);
            processor = audioContext.createScriptProcessor(4096, 1, 1);
            
            source.connect(processor);
            processor.connect(audioContext.destination);

            processor.onaudioprocess = (e) => {{
                if (ws && ws.readyState === WebSocket.OPEN) {{
                    const inputData = e.inputBuffer.getChannelData(0);
                    const pcmData = floatTo16BitPCM(inputData);
                    const base64Data = btoa(String.fromCharCode(...new Uint8Array(pcmData.buffer)));
                    ws.send(JSON.stringify({{
                        realtime_input: {{
                            media_chunks: [{{
                                mime_type: "audio/pcm;rate=16000",
                                data: base64Data
                            }}]
                        }}
                    }}));
                }}
            }};
        }}

        function floatTo16BitPCM(input) {{
            const output = new Int16Array(input.length);
            for (let i = 0; i < input.length; i++) {{
                const s = Math.max(-1, Math.min(1, input[i]));
                output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }}
            return output;
        }}

        function playAudio(base64Data) {{
            try {{
                const binary = atob(base64Data);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                const pcmData = new Int16Array(bytes.buffer);
                const floatData = new Float32Array(pcmData.length);
                for (let i = 0; i < pcmData.length; i++) floatData[i] = pcmData[i] / 0x8000;
                
                // Gemini Live API outputs 24kHz PCM audio
                const sampleRate = 24000;
                const buffer = audioContext.createBuffer(1, floatData.length, sampleRate);
                buffer.getChannelData(0).set(floatData);
                
                // Queue audio for sequential playback
                const currentTime = audioContext.currentTime;
                const startTime = Math.max(currentTime, nextStartTime);
                
                const source = audioContext.createBufferSource();
                source.buffer = buffer;
                
                // Add gain node for volume control
                const gainNode = audioContext.createGain();
                gainNode.gain.value = 2.0; // Increase volume 2x
                
                source.connect(gainNode);
                gainNode.connect(audioContext.destination);
                source.start(startTime);
                
                // Update next start time
                nextStartTime = startTime + buffer.duration;
                
                console.log(`🔊 Playing audio chunk: ${{floatData.length}} samples at ${{sampleRate}}Hz, duration: ${{buffer.duration.toFixed(3)}}s`);
            }} catch (e) {{
                console.error("Error playing audio:", e);
            }}
        }}

        async function handleToolCall(toolCall) {{
            const call = toolCall.functionCalls[0];
            console.log("🔧 Tool call from Gemini:", call.name, call.args);
            statusDiv.innerHTML = 'Status: <span style="color: #fbbf24;">Executing: ' + call.name + '</span>';
            
            let result = {{ "status": "error", "message": "Unknown tool" }};
            
            try {{
                if (call.name === "get_incident_report") {{
                    const resp = await fetch(BACKEND_URL + "/system_state");
                    result = await resp.json();
                    console.log("✅ Incident report fetched:", result);
                }} else if (call.name === "block_ip") {{
                    const incident_id = call.args?.incident_id;
                    console.log("🚫 Neutralizing incident:", incident_id);
                    
                    if (!incident_id) {{
                        result = {{ "error": "No incident_id provided" }};
                        console.error("❌ No incident_id in tool call");
                    }} else {{
                        const resp = await fetch(BACKEND_URL + `/neutralize/${{incident_id}}`, {{ method: "POST" }});
                        if (resp.ok) {{
                            result = {{ "status": "success", "action": "Threat Neutralized", "incident_id": incident_id }};
                            console.log("✅ Incident neutralized:", incident_id);
                            statusDiv.innerHTML = 'Status: <span style="color: #22c55e;">THREAT NEUTRALIZED</span>';
                            
                            // Refresh UI after 2 seconds
                            setTimeout(() => {{ 
                                console.log("🔄 Refreshing UI...");
                                location.reload(); 
                            }}, 2000);
                        }} else {{
                            const error = await resp.text();
                            result = {{ "error": error }};
                            console.error("❌ Neutralization failed:", error);
                        }}
                    }}
                }}
            }} catch (e) {{
                console.error("Tool execution failed:", e);
                result = {{ "error": e.message }};
            }}
            
            // Send tool response back to Gemini (handled by backend)
            console.log("📤 Tool result:", result);
        }}

        function min(a,b) {{ return a < b ? a : b; }}
    </script>
    """
    components.html(js_code, height=150)
