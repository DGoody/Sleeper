"""Dynasty trade-value data from FantasyCalc (free, no key required)."""
from . import http

BASE = "https://api.fantasycalc.com/values/current"


def get_values(num_teams: int, ppr: float, num_qbs: int = 1, is_dynasty: bool = True) -> list:
    ppr_str = "0" if ppr == 0 else ("1" if ppr == 1 else "0.5")
    url = (
        f"{BASE}?isDynasty={'true' if is_dynasty else 'false'}"
        f"&numQbs={num_qbs}&numTeams={num_teams}&ppr={ppr_str}"
    )
    key = f"fc_values_{num_teams}_{ppr_str}_{num_qbs}_{is_dynasty}"
    return http.get_json(url, cache_key=key, ttl_seconds=6 * 3600)


def index_by_sleeper_id(values: list) -> dict:
    out = {}
    for entry in values:
        sid = entry["player"].get("sleeperId")
        if sid:
            out[str(sid)] = entry
    return out


def index_picks_by_name(values: list) -> dict:
    """Pick entries have no sleeperId; key them by their display name, e.g. '2027 1st'."""
    out = {}
    for entry in values:
        if entry["player"]["position"] == "PICK":
            out[entry["player"]["name"].lower()] = entry
    return out
