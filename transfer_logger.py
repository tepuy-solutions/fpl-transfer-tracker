import json
import requests
from datetime import datetime
import os

API_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
LOG_FILE = "data/fpl_transfer_log.json"
MAX_ENTRIES = 10  # Keep only last 10 records per player

def fetch_fpl_data():
    res = requests.get(API_URL)
    res.raise_for_status()
    data = res.json()
    players = data["elements"]
    timestamp = datetime.utcnow().isoformat()

    snapshot = {}
    for p in players:
        player_id = f"id_{p['id']}"
        print(f"{p['web_name']} sel%: {p.get('selected_by_percent')}")
        snapshot[player_id] = {
            "timestamp": timestamp,
            "transfers_in": p["transfers_in"],
            "transfers_out": p["transfers_out"],
            "selected_by_percent": float(p.get("selected_by_percent", 0.0))  # ✅ ADD THIS
        }

    return snapshot


def load_existing_log():
    if not os.path.exists(LOG_FILE):
        return {}
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def update_log(new_snapshot, log):
    for player_id, entry in new_snapshot.items():
        if player_id not in log:
            log[player_id] = []
        log[player_id].append(entry)
        # Keep only last 10
        log[player_id] = log[player_id][-MAX_ENTRIES:]
    return log

if __name__ == "__main__":
    new_data = fetch_fpl_data()
    existing_log = load_existing_log()
    updated_log = update_log(new_data, existing_log)
    save_log(updated_log)
    print("Transfer log updated.")
 
