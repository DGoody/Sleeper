"""Waiver-wire targets: free agents ranked by add-trend and dynasty value, with a
note on whether they'd address a real need on your roster."""
from . import sleeper_api as sapi
from . import lineup as lineup_mod

RELEVANT_POSITIONS = {"QB", "RB", "WR", "TE", "K", "DEF"}
STARTER_SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}  # + FLEX pool handled separately


def free_agents(ctx) -> set:
    rostered = set()
    for r in ctx.rosters:
        rostered.update(r.get("players") or [])
    return {pid for pid in ctx.all_players if pid not in rostered}


def your_needs(ctx) -> dict:
    """Rough need score per position: how thin your roster is relative to starter slots."""
    by_pos = ctx.roster_by_position(ctx.my_roster.get("players") or [])
    needs = {}
    for pos, min_starters in STARTER_SLOTS.items():
        have = by_pos.get(pos, [])
        quality_depth = sum(1 for _, _, v in have if v > 0)
        needs[pos] = max(0, min_starters + 1 - quality_depth)  # +1 buffer for bye/flex
    return needs


def top_targets(ctx, limit: int = 20) -> list:
    fa_ids = free_agents(ctx)
    trending = sapi.get_trending("add", lookback_hours=24, limit=200)
    trend_count = {t["player_id"]: t["count"] for t in trending}

    needs = your_needs(ctx)
    rows = []
    for pid in fa_ids:
        p = ctx.all_players.get(pid) or {}
        pos = p.get("position")
        if pos not in RELEVANT_POSITIONS:
            continue
        if p.get("status") not in (None, "Active", "Inactive") and pos != "DEF":
            continue
        count = trend_count.get(pid)
        value = ctx.dynasty_value(pid)
        if count is None and value == 0:
            continue
        rows.append(
            {
                "id": pid,
                "name": ctx.player_name(pid),
                "pos": pos,
                "team": p.get("team") or "FA",
                "trend": count or 0,
                "value": value,
                "need": needs.get(pos, 0) > 0,
            }
        )

    rows.sort(key=lambda r: (r["trend"], r["value"]), reverse=True)
    return rows[:limit]
