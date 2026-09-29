"""Trade evaluator: sum dynasty trade values on each side and call it fair/lopsided."""


def evaluate(give: list, get: list) -> dict:
    give_total = sum(a.value for a in give)
    get_total = sum(a.value for a in get)
    delta = get_total - give_total
    denom = max(give_total, get_total, 1)
    pct = round(100 * delta / denom, 1)

    if abs(pct) <= 7:
        verdict = "Fair trade"
    elif delta > 0:
        verdict = "Favors you" if pct <= 20 else "Strongly favors you"
    else:
        verdict = "Favors them" if pct >= -20 else "Strongly favors them"

    return {
        "give_total": give_total,
        "get_total": get_total,
        "delta": delta,
        "pct": pct,
        "verdict": verdict,
    }


def roster_impact(ctx, current_ids: list, give: list, get: list) -> dict:
    """Positional depth on your roster before vs. after the trade."""
    give_ids = {a.id for a in give if a.kind == "player"}
    get_players = [a for a in get if a.kind == "player"]

    after_ids = [pid for pid in current_ids if pid not in give_ids]
    after_ids += [a.id for a in get_players]

    before = ctx.roster_by_position(current_ids)
    after = ctx.roster_by_position(after_ids)
    return {"before": before, "after": after}
