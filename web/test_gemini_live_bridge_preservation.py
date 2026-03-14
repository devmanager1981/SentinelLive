"""
Preservation Property Tests for Gemini Live WebSocket Connection

**Property 2: Preservation** - WebSocket Communication Behavior

**IMPORTANT**: These tests follow observation-first methodology.
They observe behavior on UNFIXED code for WebSocket operations AFTER successful connection.

**EXPECTED OUTCOME ON UNFIXED CODE**: Tests PASS (confirms baseline behavior to preserve)
**EXPECTED OUTCOME ON FIXED CODE**: Tests PASS (confirms no regressions)

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
"""

import pytest
from hypothesis import given, strategies as st, settings, Phase
from unittest.mock import patch, MagicMock, call
import re
import json
from web.gemini_live_bridge import gemini_live_audio


def extract_js_function(js_code: str, function_name: str) -> str:
    """
    Extracts a JavaScript function definition from the generated code.
    """
    # Match function definition: function name() { ... }
    pattern = rf'function {function_name}\([^)]*\)\s*{{[^}}]*}}'
    match = re.search(pattern, js_code, re.DOTALL)
    if match:
        return match.group(0)
    
    # Match async function: async function name() { ... }
    pattern = rf'async function {function_name}\([^)]*\)\s*{{[^}}]*}}'
    match = re.search(pattern, js_code, re.DOTALL)
    if match:
        return match.group(0)
    
    return ""


def extract_setup_message(js_code: str) -> dict:
    """
    Extracts the setup message structure from the sendSetup function.
    """
    # Find the setup object in the sendSetup function
    match = re.search(r'const setup = ({.*?});', js_code, re.DOTALL)
    if match:
        setup_str = match.group(1)
        # This is a simplified extraction - in real code we'd parse the JS object
        # For testing purposes, we verify the structure exists
        return {"found": True, "content": setup_str}
    return {"found": False}


def extract_audio_processing_function(js_code: str) -> str:
    """
    Extracts the floatTo16BitPCM function that converts audio to 16-bit PCM.
    """
    return extract_js_function(js_code, "floatTo16BitPCM")


def extract_tool_call_handler(js_code: str) -> str:
    """
    Extracts the handleToolCall function that processes tool calls.
    """
    return extract_js_function(js_code, "handleToolCall")


def extract_disconnect_logic(js_code: str) -> str:
    """
    Extracts the stop function that handles disconnection.
    """
    return extract_js_function(js_code, "stop")


# Test 3.1: Setup message with model configuration and tool declarations
@pytest.mark.parametrize("api_key", [
    "AQ.TestKey123",  # Clean API key without quotes or whitespace
    "AQ.ValidKey456789",
    "AB.CleanKey000111",
])
def test_preservation_setup_message_structure(api_key):
    """
    **Property 2: Preservation** - Setup Message Structure
    
    **Validates: Requirement 3.1**
    
    Verifies that the setup message with model configuration and tool declarations
    is sent correctly. This behavior should remain unchanged after the fix.
    
    Test observes:
    - Setup message contains model specification
    - Setup message contains generation_config with response_modalities
    - Setup message contains tools with function_declarations
    - Function declarations include get_incident_report and block_ip
    """
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio(api_key)
        
        js_code = mock_html.call_args[0][0]
        
        # Verify sendSetup function exists
        assert 'function sendSetup()' in js_code, "sendSetup function should exist"
        
        # Verify setup message structure
        setup_info = extract_setup_message(js_code)
        assert setup_info["found"], "Setup message should be defined"
        
        setup_content = setup_info["content"]
        
        # Verify model configuration
        assert 'model: "models/gemini-2.5-flash-native-audio-latest"' in setup_content, \
            "Setup should specify the Gemini model"
        
        # Verify response modalities
        assert 'response_modalities: ["AUDIO"]' in setup_content, \
            "Setup should specify AUDIO response modality"
        
        # Verify tools are declared
        assert 'function_declarations' in setup_content, \
            "Setup should include function declarations"
        
        # Verify specific tool functions
        assert 'get_incident_report' in setup_content, \
            "Setup should include get_incident_report tool"
        assert 'block_ip' in setup_content, \
            "Setup should include block_ip tool"
        
        # Verify setup is sent via WebSocket
        assert 'ws.send(JSON.stringify(setup))' in js_code, \
            "Setup message should be sent via WebSocket"


# Test 3.2: Audio data conversion to 16-bit PCM format
@pytest.mark.parametrize("api_key", [
    "AQ.TestKey123",
    "AB.ValidKey789",
])
def test_preservation_audio_pcm_conversion(api_key):
    """
    **Property 2: Preservation** - Audio PCM Conversion
    
    **Validates: Requirement 3.2**
    
    Verifies that audio data is converted to 16-bit PCM format and transmitted
    via WebSocket. This behavior should remain unchanged after the fix.
    
    Test observes:
    - floatTo16BitPCM function exists and converts float audio to 16-bit PCM
    - Audio processor sends data via WebSocket when connection is open
    - Audio data is base64 encoded before transmission
    - MIME type is set to "audio/pcm;rate=16000"
    """
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio(api_key)
        
        js_code = mock_html.call_args[0][0]
        
        # Verify floatTo16BitPCM function exists
        pcm_function = extract_audio_processing_function(js_code)
        assert pcm_function, "floatTo16BitPCM function should exist"
        
        # Verify the function converts to Int16Array
        assert 'Int16Array' in pcm_function, \
            "Audio conversion should use Int16Array for 16-bit PCM"
        
        # Verify clamping logic (max/min to prevent overflow)
        assert 'Math.max' in pcm_function and 'Math.min' in pcm_function, \
            "Audio conversion should clamp values to prevent overflow"
        
        # Verify audio processor setup
        assert 'audioContext.createScriptProcessor(4096, 1, 1)' in js_code, \
            "Audio processor should be created with correct buffer size"
        
        # Verify audio data is sent via WebSocket
        assert 'realtime_input' in js_code, \
            "Audio data should be sent as realtime_input"
        assert 'media_chunks' in js_code, \
            "Audio data should be sent as media_chunks"
        assert 'audio/pcm;rate=16000' in js_code, \
            "Audio MIME type should be audio/pcm with 16kHz sample rate"
        
        # Verify base64 encoding
        assert 'btoa(String.fromCharCode(...new Uint8Array(pcmData.buffer)))' in js_code, \
            "Audio data should be base64 encoded before transmission"


# Test 3.3: Audio playback from Gemini API responses
@pytest.mark.parametrize("api_key", [
    "AQ.TestKey123",
    "AB.ValidKey789",
])
def test_preservation_audio_playback(api_key):
    """
    **Property 2: Preservation** - Audio Playback
    
    **Validates: Requirement 3.3**
    
    Verifies that audio playback from Gemini API responses works correctly.
    This behavior should remain unchanged after the fix.
    
    Test observes:
    - playAudio function exists and decodes base64 audio data
    - Audio is converted from Int16Array back to Float32Array
    - Audio buffer is created with correct sample rate (16kHz)
    - Audio is played through the audio context
    """
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio(api_key)
        
        js_code = mock_html.call_args[0][0]
        
        # Verify playAudio function exists
        assert 'function playAudio(base64Data)' in js_code, \
            "playAudio function should exist"
        
        # Verify base64 decoding
        assert 'atob(base64Data)' in js_code, \
            "Audio data should be base64 decoded"
        
        # Verify conversion from Int16Array to Float32Array
        assert 'new Int16Array(bytes.buffer)' in js_code, \
            "Audio should be converted to Int16Array"
        assert 'new Float32Array(pcmData.length)' in js_code, \
            "Audio should be converted to Float32Array for playback"
        
        # Verify audio buffer creation
        assert 'audioContext.createBuffer(1, floatData.length, 16000)' in js_code, \
            "Audio buffer should be created with 16kHz sample rate"
        
        # Verify audio playback
        assert 'audioContext.createBufferSource()' in js_code, \
            "Audio buffer source should be created"
        assert 'source.connect(audioContext.destination)' in js_code, \
            "Audio source should be connected to destination"
        assert 'source.start()' in js_code, \
            "Audio playback should be started"
        
        # Verify WebSocket message handler calls playAudio
        assert 'playAudio(response.serverContent.modelTurn.parts[0].inlineData.data)' in js_code, \
            "WebSocket message handler should call playAudio for audio responses"


# Test 3.4: Tool call execution against FastAPI backend
@pytest.mark.parametrize("api_key", [
    "AQ.TestKey123",
    "AB.ValidKey789",
])
def test_preservation_tool_call_execution(api_key):
    """
    **Property 2: Preservation** - Tool Call Execution
    
    **Validates: Requirement 3.4**
    
    Verifies that tool calls are executed against the FastAPI backend correctly.
    This behavior should remain unchanged after the fix.
    
    Test observes:
    - handleToolCall function exists and processes tool calls
    - get_incident_report calls the /system_state endpoint
    - block_ip calls the /toggle_attack endpoint
    - Tool responses are sent back via WebSocket
    """
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio(api_key)
        
        js_code = mock_html.call_args[0][0]
        
        # Verify handleToolCall function exists
        tool_handler = extract_tool_call_handler(js_code)
        assert tool_handler or 'async function handleToolCall(toolCall)' in js_code, \
            "handleToolCall function should exist"
        
        # Verify get_incident_report tool
        assert 'get_incident_report' in js_code, \
            "get_incident_report tool should be handled"
        assert 'http://localhost:8000/system_state' in js_code, \
            "get_incident_report should call /system_state endpoint"
        
        # Verify block_ip tool
        assert 'block_ip' in js_code, \
            "block_ip tool should be handled"
        assert 'http://localhost:8000/toggle_attack?mode=normal' in js_code, \
            "block_ip should call /toggle_attack endpoint"
        
        # Verify tool response is sent back via WebSocket
        assert 'tool_response' in js_code, \
            "Tool response should be sent back via WebSocket"
        assert 'function_responses' in js_code, \
            "Tool response should include function_responses"
        
        # Verify WebSocket message handler calls handleToolCall
        assert 'handleToolCall(response.toolCall)' in js_code, \
            "WebSocket message handler should call handleToolCall for tool calls"


# Test 3.5: Disconnect button closes WebSocket and releases resources
@pytest.mark.parametrize("api_key", [
    "AQ.TestKey123",
    "AB.ValidKey789",
])
def test_preservation_disconnect_cleanup(api_key):
    """
    **Property 2: Preservation** - Disconnect and Resource Cleanup
    
    **Validates: Requirement 3.5**
    
    Verifies that the disconnect button properly closes the WebSocket connection
    and releases microphone resources. This behavior should remain unchanged after the fix.
    
    Test observes:
    - stop function exists and closes WebSocket
    - Microphone stream tracks are stopped
    - Audio context is closed
    - WebSocket reference is cleared
    """
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio(api_key)
        
        js_code = mock_html.call_args[0][0]
        
        # Verify stop function exists
        stop_function = extract_disconnect_logic(js_code)
        assert stop_function or 'function stop()' in js_code, \
            "stop function should exist"
        
        # Verify WebSocket is closed
        assert 'if (ws) ws.close()' in js_code, \
            "stop function should close WebSocket connection"
        
        # Verify microphone stream is stopped
        assert 'if (stream) stream.getTracks().forEach(t => t.stop())' in js_code, \
            "stop function should stop all microphone tracks"
        
        # Verify audio context is closed
        assert 'if (audioContext) audioContext.close()' in js_code, \
            "stop function should close audio context"
        
        # Verify WebSocket reference is cleared
        assert 'ws = null' in js_code, \
            "stop function should clear WebSocket reference"
        
        # Verify button click handler calls stop
        assert 'stop()' in js_code, \
            "Button click handler should call stop function"


# Test 3.6: UI status indicator updates
@pytest.mark.parametrize("api_key", [
    "AQ.TestKey123",
    "AB.ValidKey789",
])
def test_preservation_ui_status_updates(api_key):
    """
    **Property 2: Preservation** - UI Status Indicator Updates
    
    **Validates: Requirement 3.6**
    
    Verifies that the UI status indicator and button text update appropriately
    when connection status changes. This behavior should remain unchanged after the fix.
    
    Test observes:
    - Status shows "Offline" initially
    - Status shows "Initializing..." when connecting
    - Status shows "Uplink Active" when connected
    - Button text changes between "Establish Neural Link" and "Terminate Link"
    - Button color changes based on connection state
    """
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio(api_key)
        
        js_code = mock_html.call_args[0][0]
        
        # Verify initial offline status
        assert 'Status: <span style="color: #ff4b4b;">Offline</span>' in js_code, \
            "Initial status should be Offline"
        
        # Verify initializing status
        assert 'Status: <span style="color: #fbbf24;">Initializing...</span>' in js_code, \
            "Status should show Initializing when connecting"
        
        # Verify connected status
        assert 'Status: <span style="color: #22c55e;">Uplink Active</span>' in js_code, \
            "Status should show Uplink Active when connected"
        
        # Verify button text changes
        assert 'Establish Neural Link' in js_code, \
            "Button should show 'Establish Neural Link' when disconnected"
        assert 'Terminate Link' in js_code, \
            "Button should show 'Terminate Link' when connected"
        
        # Verify button color changes
        assert '#00c0f2' in js_code, \
            "Button should be blue when disconnected"
        assert '#ff4b4b' in js_code, \
            "Button should be red when connected"
        
        # Verify status updates in WebSocket handlers
        assert 'ws.onopen' in js_code, \
            "WebSocket onopen handler should exist"
        assert 'ws.onclose' in js_code, \
            "WebSocket onclose handler should exist"
        assert 'ws.onerror' in js_code, \
            "WebSocket onerror handler should exist"


# Property-based test: Preservation across many valid API keys
@given(
    api_key=st.from_regex(r'[A-Z]{2}\.[A-Za-z0-9_-]{10,50}', fullmatch=True)
)
@settings(phases=[Phase.generate, Phase.target])
def test_property_preservation_all_websocket_operations(api_key):
    """
    **Property 2: Preservation** - All WebSocket Operations (Property-Based)
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
    
    Property-based test that generates many valid API keys (without quotes/whitespace).
    
    For ANY valid API key, all WebSocket operations after successful connection
    (setup messages, audio streaming, tool calls, disconnection) SHALL produce
    exactly the same behavior as the original code.
    
    **EXPECTED OUTCOME**: This test PASSES on both unfixed and fixed code,
    confirming that non-API-key-processing behavior is preserved.
    """
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio(api_key)
        
        js_code = mock_html.call_args[0][0]
        
        # Verify all critical functions exist (preservation of structure)
        assert 'function sendSetup()' in js_code, \
            "sendSetup function should be preserved"
        assert 'function floatTo16BitPCM' in js_code, \
            "floatTo16BitPCM function should be preserved"
        assert 'function playAudio' in js_code, \
            "playAudio function should be preserved"
        assert 'async function handleToolCall' in js_code, \
            "handleToolCall function should be preserved"
        assert 'function stop()' in js_code, \
            "stop function should be preserved"
        
        # Verify WebSocket event handlers exist
        assert 'ws.onopen' in js_code, \
            "WebSocket onopen handler should be preserved"
        assert 'ws.onmessage' in js_code, \
            "WebSocket onmessage handler should be preserved"
        assert 'ws.onclose' in js_code, \
            "WebSocket onclose handler should be preserved"
        assert 'ws.onerror' in js_code, \
            "WebSocket onerror handler should be preserved"
        
        # Verify audio processing pipeline
        assert 'audioContext.createScriptProcessor' in js_code, \
            "Audio processor creation should be preserved"
        assert 'processor.onaudioprocess' in js_code, \
            "Audio processing callback should be preserved"
        
        # Verify tool endpoints
        assert 'http://localhost:8000/system_state' in js_code, \
            "get_incident_report endpoint should be preserved"
        assert 'http://localhost:8000/toggle_attack' in js_code, \
            "block_ip endpoint should be preserved"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
