# price_logger.py
import requests, json, datetime as dt, os
from collections import defaultdict

DATA_DIR = "data"
FILENAME = "fpl_price_log.json"
URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

def load_logs(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def index_prev(players_prev):
    """Map player id -> prev summary for quick delta calc."""
    idx = {}
    for p in players_prev:
        idx[p["id"]] = p
    return idx

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, FILENAME)

    # fetch fresh data
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    bs = r.json()

    total_players = bs.get("total_players")
    elements = bs.get("elements", [])

    # load previous snapshot (if any)
    logs = load_logs(path)
    prev_players = logs[-1]["players"] if logs else []
    prev_idx = index_prev(prev_players)

    players_out = []
    for p in elements:
        pid = p["id"]
        cost = p["now_cost"] / 10.0
        tin = int(p["transfers_in"])
        tout = int(p["transfers_out"])
        own = p["selected_by_percent"]  # string like "15.6"
        # deltas vs previous snapshot
        dp_in = dp_out = d_nti = None
        prev = prev_idx.get(pid)
        if prev:
            dp_in = tin - int(prev["transfers_in"])
            dp_out = tout - int(prev["transfers_out"])
            d_nti = (dp_in if dp_in is not None else 0) - (dp_out if dp_out is not None else 0)

        players_out.append({
            "id": pid,
            "name": f"{p['first_name']} {p['second_name']}",
            "team": p["team"],            # numeric team id
            "position": p["element_type"],# 1=GK,2=DEF,3=MID,4=FWD
            "cost": cost,
            "transfers_in": tin,
            "transfers_out": tout,
            "ownership_percent": own,     # keep as string to match API
            "delta_transfers_in": dp_in,  # last-snapshot deltas (can be null for first run)
            "delta_transfers_out": dp_out,
            "delta_nti": d_nti
        })

    snapshot = {
        "timestamp_utc": dt.datetime.utcnow().isoformat(),
        "note": "Snapshot taken ~30 min before daily FPL price change.",
        "total_players": total_players,
        "players": players_out
    }

    logs.append(snapshot)
    with open(path, "w") as f:
        json.dump(logs, f, indent=2)

if __name__ == "__main__":
    main()
