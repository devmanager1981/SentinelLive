"""
Test API key validation in gemini_live_bridge.py

This test verifies that the API key validation correctly:
- Rejects None or empty API keys
- Rejects API keys that are too short (< 10 characters)
- Displays appropriate error messages in the UI
"""

import pytest
from unittest.mock import patch
from web.gemini_live_bridge import gemini_live_audio


def test_empty_api_key_shows_error():
    """Test that an empty API key displays an error message."""
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio("")
        
        # Verify that html was called (error message displayed)
        assert mock_html.called
        
        # Get the HTML content
        error_html = mock_html.call_args[0][0]
        
        # Verify error message contains expected text
        assert "API Key Error" in error_html
        assert "Invalid or missing" in error_html
        assert "GOOGLE_AISTUDIO_KEY" in error_html


def test_none_api_key_shows_error():
    """Test that a None API key displays an error message."""
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio(None)
        
        # Verify that html was called (error message displayed)
        assert mock_html.called
        
        # Get the HTML content
        error_html = mock_html.call_args[0][0]
        
        # Verify error message contains expected text
        assert "API Key Error" in error_html


def test_short_api_key_shows_error():
    """Test that an API key shorter than 10 characters displays an error message."""
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio("short")
        
        # Verify that html was called (error message displayed)
        assert mock_html.called
        
        # Get the HTML content
        error_html = mock_html.call_args[0][0]
        
        # Verify error message contains expected text
        assert "API Key Error" in error_html


def test_whitespace_only_api_key_shows_error():
    """Test that an API key with only whitespace displays an error message."""
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio("   ")
        
        # Verify that html was called (error message displayed)
        assert mock_html.called
        
        # Get the HTML content
        error_html = mock_html.call_args[0][0]
        
        # Verify error message contains expected text
        assert "API Key Error" in error_html


def test_quoted_empty_api_key_shows_error():
    """Test that a quoted empty API key displays an error message."""
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio('""')
        
        # Verify that html was called (error message displayed)
        assert mock_html.called
        
        # Get the HTML content
        error_html = mock_html.call_args[0][0]
        
        # Verify error message contains expected text
        assert "API Key Error" in error_html


def test_valid_api_key_does_not_show_error():
    """Test that a valid API key does not display an error message."""
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio("AQ.ValidKey123456789")
        
        # Verify that html was called
        assert mock_html.called
        
        # Get the HTML content
        html_content = mock_html.call_args[0][0]
        
        # Verify it's NOT an error message (should contain WebSocket code)
        assert "API Key Error" not in html_content
        assert "bridge-container" in html_content
        assert "connect-btn" in html_content


@pytest.mark.parametrize("invalid_key", [
    "",
    "   ",
    '""',
    "''",
    "short",
    "123",
    None,
])
def test_invalid_api_keys_show_error(invalid_key):
    """Property test: All invalid API keys should display error messages."""
    with patch('web.gemini_live_bridge.components.html') as mock_html:
        gemini_live_audio(invalid_key)
        
        # Verify that html was called
        assert mock_html.called
        
        # Get the HTML content
        error_html = mock_html.call_args[0][0]
        
        # Verify error message is displayed
        assert "API Key Error" in error_html
