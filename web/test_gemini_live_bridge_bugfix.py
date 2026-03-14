"""
Bug Condition Exploration Test for Gemini Live WebSocket Connection

**CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists.
**DO NOT attempt to fix the test or the code when it fails.**

This test encodes the expected behavior - it will validate the fix when it passes after implementation.

**Validates: Requirements 2.1, 2.2, 2.4**
"""

import pytest
from hypothesis import given, strategies as st, example
from unittest.mock import Mock, patch, MagicMock
import re
from web.gemini_live_bridge import gemini_live_audio


def is_bug_condition(api_key: str) -> bool:
    """
    Determines if an API key matches the bug condition.
    
    Bug condition: API key contains surrounding quotes (single or double) 
    or leading/trailing whitespace.
    """
    if not api_key:
        return False
    
    has_quotes = (
        api_key.startswith('"') or api_key.startswith("'") or
        api_key.endswith('"') or api_key.endswith("'")
    )
    has_whitespace = api_key != api_key.strip()
    
    return has_quotes or has_whitespace


def extract_api_key_from_js(js_code: str) -> str:
    """
    Extracts the API key value from the generated JavaScript code.
    
    The JavaScript code contains: const API_KEY = "{api_key}";
    This function extracts the value between the quotes.
    """
    match = re.search(r'const API_KEY = "([^"]*)";', js_code)
    if match:
        return match.group(1)
    return ""


def extract_websocket_url_from_js(js_code: str) -> str:
    """
    Extracts the WebSocket URL construction from the generated JavaScript code.
    
    The JavaScript code contains: const URL = "wss://...?key=" + encodeURIComponent(API_KEY);
    This function extracts the URL pattern to verify how the API key is used.
    """
    match = re.search(r'const URL = "([^"]+)" \+ encodeURIComponent\(API_KEY\);', js_code)
    if match:
        return match.group(1)
    return ""


# Property 1: Bug Condition - Sanitized API Key Establishes Connection
@pytest.mark.parametrize("api_key", [
    '"AQ.TestKey123"',  # Double-quoted API key
    "'AQ.TestKey123'",  # Single-quoted API key
    ' AQ.TestKey123 ',  # API key with leading/trailing whitespace
    '"AQ.TestKey123',   # API key with leading double quote only
    'AQ.TestKey123"',   # API key with trailing double quote only
    ' "AQ.TestKey123" ',  # API key with quotes AND whitespace
])
def test_bug_condition_api_keys_fail_on_unfixed_code(api_key):
    """
    **Property 1: Bug Condition** - Sanitized API Key Establishes Connection
    
    **Validates: Requirements 2.1, 2.2, 2.4**
    
    Test that API keys matching isBugCondition (contains quotes or whitespace) 
    fail to establish WebSocket connection on unfixed code.
    
    **EXPECTED OUTCOME ON UNFIXED CODE**: This test FAILS because:
    - The API key is passed unsanitized to JavaScript
    - Quotes and whitespace are included in the WebSocket URL
    - The encoded URL contains %22 (double quotes), %27 (single quotes), or %20 (spaces)
    - The WebSocket connection would fail with error 1006
    
    **EXPECTED OUTCOME ON FIXED CODE**: This test PASSES because:
    - The API key is sanitized before being passed to JavaScript
    - Quotes and whitespace are removed
    - The WebSocket URL contains only the clean API key
    - The WebSocket connection establishes successfully
    """
    # Verify this is a bug condition
    assert is_bug_condition(api_key), f"API key '{api_key}' should match bug condition"
    
    # Mock Streamlit components to capture the generated JavaScript
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        # Call the function with the buggy API key
        gemini_live_audio(api_key)
        
        # Verify the function was called
        assert mock_html.called, "components.html should have been called"
        
        # Extract the generated JavaScript code
        js_code = mock_html.call_args[0][0]
        
        # Extract the API key from the JavaScript code
        embedded_api_key = extract_api_key_from_js(js_code)
        
        # **CRITICAL ASSERTION**: On unfixed code, this will FAIL
        # The embedded API key should be sanitized (no quotes, no whitespace)
        # On unfixed code, the API key is passed as-is with quotes/whitespace
        
        # Check for quotes in the embedded API key
        has_quotes = (
            embedded_api_key.startswith('"') or embedded_api_key.startswith("'") or
            embedded_api_key.endswith('"') or embedded_api_key.endswith("'")
        )
        
        # Check for whitespace in the embedded API key
        has_whitespace = embedded_api_key != embedded_api_key.strip()
        
        # On UNFIXED code: embedded_api_key will contain quotes/whitespace -> test FAILS
        # On FIXED code: embedded_api_key will be sanitized -> test PASSES
        assert not has_quotes, (
            f"API key in JavaScript should not contain quotes. "
            f"Input: '{api_key}' -> Embedded: '{embedded_api_key}'. "
            f"This indicates the API key was not sanitized before being passed to JavaScript."
        )
        
        assert not has_whitespace, (
            f"API key in JavaScript should not contain leading/trailing whitespace. "
            f"Input: '{api_key}' -> Embedded: '{embedded_api_key}'. "
            f"This indicates the API key was not sanitized before being passed to JavaScript."
        )
        
        # Additional verification: The embedded API key should be the sanitized version
        expected_sanitized = api_key.strip().strip('\'"')
        assert embedded_api_key == expected_sanitized, (
            f"API key should be sanitized. "
            f"Input: '{api_key}' -> Expected: '{expected_sanitized}' -> Got: '{embedded_api_key}'"
        )


@given(
    api_key=st.one_of(
        # Generate API keys with double quotes
        st.from_regex(r'"[A-Z]{2}\.[A-Za-z0-9_-]{10,50}"', fullmatch=True),
        # Generate API keys with single quotes
        st.from_regex(r"'[A-Z]{2}\.[A-Za-z0-9_-]{10,50}'", fullmatch=True),
        # Generate API keys with leading whitespace
        st.from_regex(r' +[A-Z]{2}\.[A-Za-z0-9_-]{10,50}', fullmatch=True),
        # Generate API keys with trailing whitespace
        st.from_regex(r'[A-Z]{2}\.[A-Za-z0-9_-]{10,50} +', fullmatch=True),
        # Generate API keys with both leading and trailing whitespace
        st.from_regex(r' +[A-Z]{2}\.[A-Za-z0-9_-]{10,50} +', fullmatch=True),
    )
)
def test_property_bug_condition_all_quoted_keys_sanitized(api_key):
    """
    **Property 1: Bug Condition** - Sanitized API Key Establishes Connection (Property-Based)
    
    **Validates: Requirements 2.1, 2.2, 2.4**
    
    Property-based test that generates many API keys with quotes and whitespace.
    
    For ANY API key that matches the bug condition (contains quotes or whitespace),
    the fixed gemini_live_audio function SHALL sanitize the key before passing it to JavaScript.
    
    **EXPECTED OUTCOME ON UNFIXED CODE**: This test FAILS with counterexamples showing
    that API keys with quotes/whitespace are passed unsanitized to JavaScript.
    
    **EXPECTED OUTCOME ON FIXED CODE**: This test PASSES, confirming that all API keys
    matching the bug condition are properly sanitized.
    """
    # Verify this is a bug condition
    if not is_bug_condition(api_key):
        return  # Skip non-buggy inputs
    
    # Mock Streamlit components to capture the generated JavaScript
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        # Call the function with the buggy API key
        gemini_live_audio(api_key)
        
        # Extract the generated JavaScript code
        js_code = mock_html.call_args[0][0]
        
        # Extract the API key from the JavaScript code
        embedded_api_key = extract_api_key_from_js(js_code)
        
        # The embedded API key should be sanitized
        expected_sanitized = api_key.strip().strip('\'"')
        
        # **CRITICAL ASSERTION**: On unfixed code, this will FAIL with counterexamples
        assert embedded_api_key == expected_sanitized, (
            f"API key should be sanitized. "
            f"Input: '{api_key}' -> Expected: '{expected_sanitized}' -> Got: '{embedded_api_key}'"
        )
        
        # Verify no quotes remain
        assert not (embedded_api_key.startswith('"') or embedded_api_key.startswith("'")), (
            f"Sanitized API key should not start with quotes: '{embedded_api_key}'"
        )
        assert not (embedded_api_key.endswith('"') or embedded_api_key.endswith("'")), (
            f"Sanitized API key should not end with quotes: '{embedded_api_key}'"
        )
        
        # Verify no leading/trailing whitespace remains
        assert embedded_api_key == embedded_api_key.strip(), (
            f"Sanitized API key should not have leading/trailing whitespace: '{embedded_api_key}'"
        )


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
