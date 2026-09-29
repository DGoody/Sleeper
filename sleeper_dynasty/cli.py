import argparse
import sys

from . import config as cfgmod
from . import sleeper_api as sapi
from . import lineup as lineup_mod
from . import trade as trade_mod
from . import waivers as waivers_mod
from . import outlook as outlook_mod
from . import resolve as resolve_mod
from .context import LeagueContext
from .format import table


def cmd_setup(args):
    user = sapi.get_user(args.username)
    if not user:
        raise SystemExit(f"Sleeper user '{args.username}' not found.")
    league = sapi.get_league(args.league_id)
    if not league:
        raise SystemExit(f"League '{args.league_id}' not found.")
    cfgmod.save({"league_id": args.league_id, "username": args.username})
    print(f"Saved config: league '{league['name']}', user '{args.username}'.")
    print(f"Config file: {cfgmod.CONFIG_PATH}")


def _ctx(args) -> LeagueContext:
    cfg = cfgmod.require()
    league_id = getattr(args, "league_id_override", None) or cfg["league_id"]
    username = getattr(args, "username_override", None) or cfg["username"]
    return LeagueContext(league_id, username)


def cmd_roster(args):
    ctx = _ctx(args)
    ids = ctx.my_roster.get("players") or []
    rows = []
    for pid in sorted(ids, key=lambda p: ctx.dynasty_value(p), reverse=True):
        entry = ctx.values_by_sid.get(str(pid))
        age = entry["player"].get("maybeAge") if entry else None
        rows.append(
            [
                ctx.player_name(pid),
                ctx.player_position(pid),
                age,
                ctx.dynasty_value(pid),
                "TAXI" if pid in (ctx.my_roster.get("taxi") or []) else
                ("IR" if pid in (ctx.my_roster.get("reserve") or []) else ""),
            ]
        )
    print(f"Roster for {ctx.username} in '{ctx.league['name']}'\n")
    table(["Player", "Pos", "Age", "Dynasty Value", "Status"], rows)


def cmd_lineup(args):
    ctx = _ctx(args)
    week = args.week or ctx.state["week"]
    ids = ctx.my_roster.get("players") or []
    result = lineup_mod.best_lineup(ctx, ids, week)

    print(f"Optimal lineup for week {week} ({ctx.username})\n")
    rows = [
        [slot, ctx.player_name(pid) if pid else "-- empty --", pts]
        for slot, pid, pts in result["slots"]
    ]
    table(["Slot", "Player", "Proj Pts"], rows)
    print(f"\nProjected total: {result['total']}")

    print("\nBench (best remaining):")
    bench_rows = [[c["pos"], ctx.player_name(c["id"]), c["pts"]] for c in result["bench"][:10]]
    table(["Pos", "Player", "Proj Pts"], bench_rows)


def cmd_trade(args):
    ctx = _ctx(args)
    give_texts = [t.strip() for t in args.give.split(",")]
    get_texts = [t.strip() for t in args.get.split(",")]
    give = resolve_mod.resolve_many(ctx, give_texts)
    get = resolve_mod.resolve_many(ctx, get_texts)

    result = trade_mod.evaluate(give, get)

    print("You give:")
    table(["Asset", "Pos", "Value"], [[a.name, a.position, a.value] for a in give])
    print(f"  Total: {result['give_total']}\n")

    print("You get:")
    table(["Asset", "Pos", "Value"], [[a.name, a.position, a.value] for a in get])
    print(f"  Total: {result['get_total']}\n")

    print(f"Value delta: {result['delta']:+d} ({result['pct']:+.1f}%)")
    print(f"Verdict: {result['verdict']}")

    if any(a.kind == "player" for a in give + get):
        impact = trade_mod.roster_impact(ctx, ctx.my_roster.get("players") or [], give, get)
        print("\nRoster fit after trade (your depth by position):")
        positions = sorted(set(impact["before"]) | set(impact["after"]))
        rows = []
        for pos in positions:
            before_n = len(impact["before"].get(pos, []))
            after_n = len(impact["after"].get(pos, []))
            rows.append([pos, before_n, after_n, after_n - before_n])
        table(["Pos", "Before", "After", "Change"], rows)


def cmd_waivers(args):
    ctx = _ctx(args)
    needs = waivers_mod.your_needs(ctx)
    needed_positions = [p for p, n in needs.items() if n > 0]
    if needed_positions:
        print(f"Your thin spots: {', '.join(needed_positions)}\n")

    rows = waivers_mod.top_targets(ctx, limit=args.limit)
    table(
        ["Player", "Pos", "Team", "Trend Adds (24h)", "Dynasty Value", "Fills Need"],
        [[r["name"], r["pos"], r["team"], r["trend"], r["value"], "yes" if r["need"] else ""] for r in rows],
    )


def cmd_outlook(args):
    ctx = _ctx(args)
    standings = outlook_mod.league_standings_by_value(ctx)
    me = next(r for r in standings if r["is_me"])
    num_teams = len(standings)

    print(f"League: {ctx.league['name']} ({num_teams} teams)\n")
    print(
        f"Your roster dynasty value rank: {me['value_rank']}/{num_teams}  "
        f"({me['value']} pts)"
    )
    print(f"Your record rank: {me['record_rank']}/{num_teams}  ({me['wins']}-{me['losses']})\n")

    print(outlook_mod.verdict(me["value_rank"], me["record_rank"], num_teams))

    candidates = outlook_mod.buy_sell_candidates(ctx, ctx.my_roster.get("players") or [], top_n=args.top)
    print("\nSell-high candidates (redraft value currently exceeds dynasty value):")
    table(
        ["Player", "Pos", "Age", "Value", "Redraft-Dynasty Gap"],
        [[r["name"], r["pos"], r["age"], r["value"], r["gap"]] for r in candidates["sell"]],
    )
    print("\nBuy-low / long-term holds (dynasty value exceeds redraft value):")
    table(
        ["Player", "Pos", "Age", "Value", "Redraft-Dynasty Gap"],
        [[r["name"], r["pos"], r["age"], r["value"], r["gap"]] for r in candidates["buy"]],
    )

    print("\nLeague standings by roster value:")
    table(
        ["Rank", "Owner", "Value", "Record", "You"],
        [
            [r["value_rank"], r["owner"], r["value"], f"{r['wins']}-{r['losses']}", "<-- you" if r["is_me"] else ""]
            for r in standings
        ],
    )


def build_parser():
    p = argparse.ArgumentParser(prog="sleeper-dynasty", description="Dynasty fantasy football decision helper for Sleeper leagues.")
    p.add_argument("--league-id", dest="league_id_override", default=None, help="Override the configured league ID.")
    p.add_argument("--username", dest="username_override", default=None, help="Override the configured Sleeper username.")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("setup", help="Save your league ID and Sleeper username.")
    s.add_argument("league_id")
    s.add_argument("username")
    s.set_defaults(func=cmd_setup)

    s = sub.add_parser("roster", help="Show your current roster with dynasty values.")
    s.set_defaults(func=cmd_roster)

    s = sub.add_parser("lineup", help="Optimal starting lineup for a given week.")
    s.add_argument("--week", type=int, default=None)
    s.set_defaults(func=cmd_lineup)

    s = sub.add_parser("trade", help="Evaluate a proposed trade by dynasty value.")
    s.add_argument("--give", required=True, help="Comma-separated players/picks you send, e.g. 'Bijan Robinson,2027 1st'")
    s.add_argument("--get", required=True, help="Comma-separated players/picks you receive.")
    s.set_defaults(func=cmd_trade)

    s = sub.add_parser("waivers", help="Best available free agents right now.")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_waivers)

    s = sub.add_parser("outlook", help="Contend vs. rebuild analysis, plus buy/sell candidates.")
    s.add_argument("--top", type=int, default=5)
    s.set_defaults(func=cmd_outlook)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "setup":
        return cmd_setup(args)
    try:
        return args.func(args)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
