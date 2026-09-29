"""Start/sit optimizer: best legal lineup for a given week by projected points."""

FLEX_ELIGIBLE = {
    "FLEX": {"RB", "WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
    "WRRB_FLEX": {"RB", "WR"},
    "REC_FLEX": {"WR", "TE"},
}


def _points_key(scoring_settings: dict) -> str:
    rec = scoring_settings.get("rec", 0)
    if rec >= 1:
        return "pts_ppr"
    if rec > 0:
        return "pts_half_ppr"
    return "pts_std"


def projected_points(ctx, player_id: str, week: int) -> float:
    proj = ctx.projections(week)
    stats = proj.get(player_id) or {}
    key = _points_key(ctx.league["scoring_settings"])
    val = stats.get(key)
    if val is None:
        val = stats.get("pts_std", 0.0)
    return round(val or 0.0, 2)


def best_lineup(ctx, roster_player_ids: list, week: int) -> dict:
    """Returns {'slots': [(slot_label, player_id_or_None, points)], 'total': float, 'bench': [...]}."""
    roster_positions = ctx.league["roster_positions"]
    pure_slots = [p for p in roster_positions if p not in ("BN",) and p not in FLEX_ELIGIBLE]
    flex_slots = [p for p in roster_positions if p in FLEX_ELIGIBLE]

    candidates = []
    for pid in roster_player_ids:
        pos = ctx.player_position(pid)
        pts = projected_points(ctx, pid, week)
        candidates.append({"id": pid, "pos": pos, "pts": pts})

    used = set()
    result_slots = []

    for slot in pure_slots:
        pool = sorted(
            (c for c in candidates if c["pos"] == slot and c["id"] not in used),
            key=lambda c: c["pts"],
            reverse=True,
        )
        if pool:
            pick = pool[0]
            used.add(pick["id"])
            result_slots.append((slot, pick["id"], pick["pts"]))
        else:
            result_slots.append((slot, None, 0.0))

    for slot in flex_slots:
        eligible_positions = FLEX_ELIGIBLE[slot]
        pool = sorted(
            (c for c in candidates if c["pos"] in eligible_positions and c["id"] not in used),
            key=lambda c: c["pts"],
            reverse=True,
        )
        if pool:
            pick = pool[0]
            used.add(pick["id"])
            result_slots.append((slot, pick["id"], pick["pts"]))
        else:
            result_slots.append((slot, None, 0.0))

    total = sum(pts for _, pid, pts in result_slots if pid)
    bench = sorted(
        (c for c in candidates if c["id"] not in used),
        key=lambda c: c["pts"],
        reverse=True,
    )
    return {"slots": result_slots, "total": round(total, 2), "bench": bench}
