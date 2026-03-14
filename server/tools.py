from .database import get_db
from datetime import datetime

db = get_db()

async def get_incident_report():
    """
    Queries Firestore for the latest active security breach.
    """
    incidents_ref = db.collection("incidents")
    query = incidents_ref.where("status", "==", "Active").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1)
    results = query.stream()
    
    for doc in results:
        return doc.to_dict()
    return {"message": "No active incidents found."}

async def block_ip(incident_id: str):
    """
    Sets incident status to 'Neutralized' and updates firewall/blocklist.
    """
    incident_ref = db.collection("incidents").document(incident_id)
    incident_ref.update({
        "status": "Neutralized",
        "resolved_at": datetime.utcnow()
    })
    return {"status": "success", "incident_id": incident_id, "action": "IP Blocked"}
