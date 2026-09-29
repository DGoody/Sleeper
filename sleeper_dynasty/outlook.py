"""Dynasty team outlook: are you set up to contend now or should you be rebuilding?"""


def team_value(ctx, player_ids: list) -> int:
    return sum(ctx.dynasty_value(pid) for pid in player_ids)


def league_standings_by_value(ctx) -> list:
    rows = []
    for r in ctx.rosters:
        pids = r.get("players") or []
        rows.append(
            {
                "roster_id": r["roster_id"],
                "owner": ctx.owner_name(r["roster_id"]),
                "value": team_value(ctx, pids),
                "wins": r["settings"].get("wins", 0),
                "losses": r["settings"].get("losses", 0),
                "is_me": r["roster_id"] == ctx.my_roster["roster_id"],
            }
        )
    rows.sort(key=lambda x: x["value"], reverse=True)
    for i, row in enumerate(rows, 1):
        row["value_rank"] = i
    rows.sort(key=lambda x: (x["wins"], -x["losses"]), reverse=True)
    for i, row in enumerate(rows, 1):
        row["record_rank"] = i
    rows.sort(key=lambda x: x["value_rank"])
    return rows


def buy_sell_candidates(ctx, player_ids: list, top_n: int = 5) -> dict:
    """Uses FantasyCalc's redraft-vs-dynasty value gap as a buy-low / sell-high signal."""
    sell = []  # redraft value well above dynasty value -> aging, cash out now
    buy = []  # dynasty value well above redraft value -> ascending, long-term hold
    for pid in player_ids:
        entry = ctx.values_by_sid.get(str(pid))
        if not entry or entry["value"] < 300:
            continue
        name = ctx.player_name(pid)
        pos = ctx.player_position(pid)
        gap = entry.get("redraftDynastyValueDifference", 0)
        age = entry["player"].get("maybeAge")
        row = {"name": name, "pos": pos, "value": entry["value"], "age": age, "gap": gap}
        if gap > 0:
            sell.append(row)
        elif gap < 0:
            buy.append(row)
    sell.sort(key=lambda r: r["gap"], reverse=True)
    buy.sort(key=lambda r: r["gap"])
    return {"sell": sell[:top_n], "buy": buy[:top_n]}


def verdict(value_rank: int, record_rank: int, num_teams: int) -> str:
    top_third = max(1, round(num_teams / 3))
    bottom_third = num_teams - top_third + 1

    strong_value = value_rank <= top_third
    weak_value = value_rank >= bottom_third
    winning_now = record_rank <= top_third
    losing_now = record_rank >= bottom_third

    if strong_value and winning_now:
        return "CONTEND — strong roster value and a good record. Push chips in on rentals; avoid trading future picks for marginal upgrades."
    if strong_value and losing_now:
        return "RETOOL — your roster is more talented than your record. Bad luck or bad lineup calls are likelier culprits than a bad team; don't panic-sell."
    if weak_value and losing_now:
        return "REBUILD — low roster value and a losing record. Sell aging vets for picks/youth now while their redraft value is still high."
    if weak_value and winning_now:
        return "SELL WHILE WINNING — you're winning games on a thin roster. Consider cashing in veterans at peak value before the record catches down to the roster."
    return "HOLD — roster value and record are both middle-of-the-pack. Make targeted upgrades rather than a wholesale rebuild or all-in push."
