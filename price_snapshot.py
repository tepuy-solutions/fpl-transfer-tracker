# price_snapshot.py
import requests, json, os
from datetime import datetime

DATA_DIR = "data"
OUT_FILE = "fpl_price_log.json"
URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, OUT_FILE)

    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    bs = r.json()

    total_players = bs.get("total_players")
    elements = bs.get("elements", [])
    prev = load_json(path)
    prev_players = prev[-1]["players"] if prev else []
    prev_idx = {p["id"]: p for p in prev_players}

    players = []
    for p in elements:
        pid = p["id"]
        tin, tout = int(p["transfers_in"]), int(p["transfers_out"])
        prev_p = prev_idx.get(pid)
        d_in = tin - int(prev_p["transfers_in"]) if prev_p else None
        d_out = tout - int(prev_p["transfers_out"]) if prev_p else None

        players.append({
            "id": pid,
            "name": f"{p['first_name']} {p['second_name']}",
            "team": p["team"],
            "position": p["element_type"],
            "cost": p["now_cost"] / 10.0,
            "transfers_in": tin,
            "transfers_out": tout,
            "ownership_percent": p["selected_by_percent"],
            "delta_transfers_in": d_in,
            "delta_transfers_out": d_out,
            "delta_nti": (d_in or 0) - (d_out or 0) if prev_p else None
        })

    snapshot = {
        "timestamp_utc": datetime.utcnow().isoformat(),
        "note": "Pre-price-change daily snapshot (~30 min before).",
        "total_players": total_players,
        "players": players
    }

    prev.append(snapshot)
    with open(path, "w") as f:
        json.dump(prev, f, indent=2)

if __name__ == "__main__":
    main()
