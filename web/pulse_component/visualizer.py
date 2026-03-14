import streamlit as st
import streamlit.components.v1 as components

def neural_pulse(risk_score: float):
    # risk_score: 0.0 to 1.0
    # Color mapping: 0.0 (Green) -> 1.0 (Red)
    
    color = "rgb(34, 197, 94)" # Green
    if risk_score > 0.3:
        color = "rgb(234, 179, 8)" # Yellow
    if risk_score > 0.7:
        color = "rgb(239, 68, 68)" # Red
        
    duration = max(0.2, 2.0 - (risk_score * 1.8)) # Pulse faster as risk increases
    
    html_code = f"""
    <div style="display: flex; justify-content: center; align-items: center; height: 180px; background: #0e1117;">
        <svg width="150" height="150" viewBox="0 0 100 100">
            <!-- Central Shield/Neural Node -->
            <circle cx="50" cy="50" r="15" fill="{color}" opacity="0.8">
                <animate attributeName="r" values="14;16;14" dur="{duration}s" repeatCount="indefinite" />
            </circle>
            
            <!-- Concentric Rings -->
            <circle cx="50" cy="50" r="25" fill="none" stroke="{color}" stroke-width="0.5" opacity="0.5">
                <animate attributeName="r" values="20;35" dur="{duration}s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.5;0" dur="{duration}s" repeatCount="indefinite" />
            </circle>
            
            <circle cx="50" cy="50" r="35" fill="none" stroke="{color}" stroke-width="0.3" opacity="0.3">
                <animate attributeName="r" values="30;50" dur="{duration*1.5}s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.3;0" dur="{duration*1.5}s" repeatCount="indefinite" />
            </circle>
            
            <circle cx="50" cy="50" r="45" fill="none" stroke="{color}" stroke-width="0.1" opacity="0.1">
                <animate attributeName="r" values="40;60" dur="{duration*2}s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.1;0" dur="{duration*2}s" repeatCount="indefinite" />
            </circle>
        </svg>
    </div>
    """
    components.html(html_code, height=180)
