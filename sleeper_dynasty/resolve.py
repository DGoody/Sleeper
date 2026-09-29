"""Fuzzy-match free-text asset names ('Bijan Robinson', '2027 1st') to Sleeper players
or FantasyCalc draft-pick entries."""
import difflib

FANTASY_POSITIONS = {"QB", "RB", "WR", "TE", "K", "DEF"}


def _player_name_index(ctx) -> dict:
    idx = {}
    for pid, p in ctx.all_players.items():
        if p.get("position") not in FANTASY_POSITIONS:
            continue
        name = p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        if not name:
            continue
        idx.setdefault(name.lower(), []).append(pid)
    return idx


class Asset:
    def __init__(self, kind, id_, name, position, value, extra=None):
        self.kind = kind  # 'player' or 'pick'
        self.id = id_
        self.name = name
        self.position = position
        self.value = value
        self.extra = extra or {}

    def __repr__(self):
        return f"<Asset {self.kind} {self.name} v={self.value}>"


def resolve_one(ctx, text: str, player_name_idx: dict) -> Asset:
    text_l = text.strip().lower()

    # Exact / fuzzy pick match first (e.g. "2027 1st", "2026 2nd (Early)")
    picks = ctx.picks_by_name
    if text_l in picks:
        entry = picks[text_l]
        return Asset("pick", None, entry["player"]["name"], "PICK", entry["value"])
    pick_match = difflib.get_close_matches(text_l, picks.keys(), n=1, cutoff=0.6)
    if pick_match:
        entry = picks[pick_match[0]]
        return Asset("pick", None, entry["player"]["name"], "PICK", entry["value"])

    # Exact / fuzzy player match
    if text_l in player_name_idx:
        pids = player_name_idx[text_l]
    else:
        name_match = difflib.get_close_matches(text_l, player_name_idx.keys(), n=1, cutoff=0.6)
        pids = player_name_idx[name_match[0]] if name_match else []

    if not pids:
        raise SystemExit(f"Could not match '{text}' to a player or draft pick.")

    if len(pids) > 1:
        pids = sorted(pids, key=lambda pid: ctx.dynasty_value(pid), reverse=True)
    pid = pids[0]
    p = ctx.all_players[pid]
    name = p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
    return Asset("player", pid, name, p.get("position"), ctx.dynasty_value(pid), extra=p)


def resolve_many(ctx, texts: list) -> list:
    idx = _player_name_index(ctx)
    return [resolve_one(ctx, t, idx) for t in texts if t.strip()]
