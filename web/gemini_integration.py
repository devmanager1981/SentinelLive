import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_AISTUDIO_KEY")

def get_gemini_config():
    """
    Returns the configuration needed for the Multimodal Live API.
    """
    return {
        "model": "models/gemini-2.0-flash-exp", # Using latest multimodal live model
        "api_key": GEMINI_API_KEY,
        "tools": [
            {
                "function_declarations": [
                    {
                        "name": "get_incident_report",
                        "description": "Queries Firestore for the latest active security breach.",
                    },
                    {
                        "name": "block_ip",
                        "description": "Sets incident status to 'Neutralized' and updates firewall/blocklist.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "incident_id": {
                                    "type": "string",
                                    "description": "The unique ID of the incident to neutralize/block."
                                }
                            },
                            "required": ["incident_id"]
                        }
                    }
                ]
            }
        ]
    }
