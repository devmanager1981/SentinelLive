import os
import time
import random
import requests
import threading
import sys
try:
    import msvcrt
except ImportError:
    msvcrt = None # Fallback for non-windows if needed

from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "glive-build")
DATABASE_ID = os.getenv("GOOGLE_FIRESTORE_DB", "(default)")
BACKEND_URL = os.getenv("BACKEND_URL", "https://sentinel-backend-6beoejihxa-uc.a.run.app")

# Initialize Firestore
db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

MODE = "normal"

def input_loop():
    global MODE
    print("\n" + "="*50)
    print("🛰️  SENTINEL COMMAND CONSOLE")
    print("="*50)
    print(" [N] - Normal Mode")
    print(" [A] - Trigger Brute Force")
    print(" [I] - Trigger Impossible Travel")
    print(" [E] - Trigger Data Exfiltration")
    print(" [Q] - QUIT STREAMER")
    print("="*50 + "\n")

    while True:
        try:
            if msvcrt:
                char = msvcrt.getch()
                if char == b'\x03': # Ctrl+C
                    print("\n🛑 Shutting down...")
                    os._exit(0)
                cmd = char.decode('utf-8').lower()
            else:
                cmd = sys.stdin.read(1).lower()
        except Exception:
            continue
            
        if cmd == 'q':
            print("\n🛑 Exiting Sentinel Streamer...")
            os._exit(0)
        
        new_mode = None
        if cmd == 'n': new_mode = "normal"
        elif cmd == 'a': new_mode = "attack"
        elif cmd == 'i': new_mode = "impossible_travel"
        elif cmd == 'e': new_mode = "exfiltration"
        
        if new_mode:
            MODE = new_mode
            db.collection("system_state").document("current").set({"mode": MODE})
            print(f"\n🚀 MODE SWITCHED TO: {MODE.upper()}")
            print("="*30)

def generate_log(mode):
    # Common fields
    log = {
        "user_id": "user-42",
        "ip": f"192.168.1.{random.randint(100, 255)}" if mode == "normal" else "192.168.1.100",  # Same IP in attack mode
        "path": "/api/v1/resource",
        "method": "GET",
        "status_code": 200,
        "city": "San Francisco",
        "bytes_transferred": random.randint(100, 5000),
        "severity": "INFO"
    }

    if mode == "attack":
        log.update({"status_code": 401, "path": "/api/auth/login", "method": "POST", "severity": "CRITICAL"})
    elif mode == "impossible_travel":
        log.update({"city": random.choice(["London", "Tokyo", "Berlin", "Dubai"]), "path": "/api/account/billing", "severity": "HIGH"})
    elif mode == "exfiltration":
        log.update({"path": "/api/sensitive/customer-records-export", "bytes_transferred": 1200000000, "severity": "CRITICAL"})
    
    return log

def main():
    global MODE
    print(f"🚀 Sentinel Chaos Engine v3 started.")
    
    # Reset on start
    db.collection("system_state").document("current").set({"mode": "normal"})
    
    # Start input listener thread
    threading.Thread(target=input_loop, daemon=True).start()
    
    while True:
        try:
            log_data = generate_log(MODE)
            response = requests.post(f"{BACKEND_URL}/stream", json=log_data, timeout=5)
            
            if response.status_code == 200:
                res_json = response.json()
                risk = res_json.get("risk_score", 0)
                anomaly = res_json.get("anomaly")
                
                status_text = f"[{MODE.upper()}]"
                if risk > 0: print(f"{status_text} 🔥 ALERT: {anomaly} (RISK: {risk}%) | {log_data['user_id']} @ {log_data['city']}")
                else: print(f"{status_text} ✅ Heartbeat OK")
            
            time.sleep(0.1 if MODE == "attack" else 3)
                
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
