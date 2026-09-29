# sleeper-dynasty

A command-line assistant for dynasty fantasy football decisions in a [Sleeper](https://sleeper.com)
league. Pulls your live roster/league data from Sleeper's public API and dynasty
trade values from [FantasyCalc](https://fantasycalc.com) (both free, no API keys needed)
and turns them into concrete recommendations.

Pure Python standard library — no `pip install` required.

## Setup

```
python3 -m sleeper_dynasty setup <league_id> <your_sleeper_username>
```

Your league ID is the number in the league's Sleeper URL, e.g.
`sleeper.com/leagues/1388918312167026688/...` → `1388918312167026688`.

This saves your league and username to `~/.config/sleeper-dynasty/config.json` so you
don't have to pass them on every command. Override per-command with `--league-id` /
`--username`.

## Commands

### `roster`
Your current roster with dynasty trade value, age, and taxi/IR status, sorted by value.

```
python3 -m sleeper_dynasty roster
```

### `lineup`
The projected-points-optimal starting lineup for a given week (defaults to the
current NFL week), respecting your league's exact roster slots (FLEX, SUPER_FLEX,
etc.), plus your best bench options.

```
python3 -m sleeper_dynasty lineup --week 5
```

### `trade`
Evaluates a proposed trade by summing FantasyCalc dynasty values on each side, and
shows how it changes your positional depth. Accepts player names and draft picks
(e.g. `2027 1st`, `2026 2nd (Early)`), comma-separated, with fuzzy name matching.

```
python3 -m sleeper_dynasty trade --give "Josh Allen" --get "Jayden Daniels,2027 1st"
```

### `waivers`
Best available free agents, ranked by how fast they're being added across Sleeper
right now and by dynasty value, flagged against your roster's thin spots.

```
python3 -m sleeper_dynasty waivers --limit 20
```

### `outlook`
Contend-vs-rebuild read on your team: your roster-value rank and record rank among
the league, a verdict (contend / retool / rebuild / sell-while-winning / hold), and
buy-low / sell-high candidates on your own roster based on the gap between a
player's dynasty value and their current-year (redraft) value.

```
python3 -m sleeper_dynasty outlook
```

## How it decides things

- **Dynasty values** come from FantasyCalc's crowd-sourced trade database, pulled
  live and matched to your league's actual settings (team count, PPR, 1QB/superflex).
- **Lineup optimization** pulls Sleeper's own weekly projections and fills strict
  position slots with the best player at that position, then flex slots with the
  best remaining eligible player — this is optimal because a player's projected
  points don't depend on which slot they're placed in.
- **Buy-low/sell-high** uses FantasyCalc's redraft-value-minus-dynasty-value gap:
  a big positive gap means a player's win-now value currently exceeds their
  long-term value (aging/peaking — a sell-high candidate); a big negative gap means
  the reverse (ascending — a buy-low/long-term hold).
- **Contend/rebuild verdict** cross-references your roster-value rank against your
  record rank in the league. Strong value + good record = contend. Good record on a
  weak roster = sell while winning. Weak value + bad record = rebuild.

Data is cached locally (`~/.cache/sleeper-dynasty/`) for a few hours to a day
depending on how often it changes, so repeated commands are fast.
