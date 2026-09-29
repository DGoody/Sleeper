"""Loads and cross-references everything a command needs about one league."""
from . import sleeper_api as sapi
from . import values_api as vapi


class LeagueContext:
    def __init__(self, league_id: str, username: str):
        self.league_id = league_id
        self.username = username

        self.league = sapi.get_league(league_id)
        self.users = sapi.get_users(league_id)
        self.rosters = sapi.get_rosters(league_id)
        self.state = sapi.get_nfl_state()

        self.user_by_id = {u["user_id"]: u for u in self.users}
        self.roster_by_id = {r["roster_id"]: r for r in self.rosters}

        me = next(
            (u for u in self.users if u["display_name"].lower() == username.lower()),
            None,
        )
        if me is None:
            raise SystemExit(f"'{username}' is not a member of this league.")
        self.me = me
        self.my_roster = next(r for r in self.rosters if r["owner_id"] == me["user_id"])

        self._all_players = None
        self._values = None
        self._values_by_sid = None
        self._picks_by_name = None
        self._projections = {}

    # -- lazily-loaded, expensive lookups --

    @property
    def all_players(self) -> dict:
        if self._all_players is None:
            self._all_players = sapi.get_all_players()
        return self._all_players

    @property
    def values_by_sid(self) -> dict:
        if self._values_by_sid is None:
            self._load_values()
        return self._values_by_sid

    @property
    def picks_by_name(self) -> dict:
        if self._picks_by_name is None:
            self._load_values()
        return self._picks_by_name

    def _load_values(self):
        settings = self.league["settings"]
        scoring = self.league["scoring_settings"]
        ppr = scoring.get("rec", 0)
        roster_positions = self.league["roster_positions"]
        num_qbs = 2 if roster_positions.count("QB") + roster_positions.count("SUPER_FLEX") > 1 else 1
        values = vapi.get_values(
            num_teams=settings["num_teams"],
            ppr=ppr,
            num_qbs=num_qbs,
            is_dynasty=True,
        )
        self._values_by_sid = vapi.index_by_sleeper_id(values)
        self._picks_by_name = vapi.index_picks_by_name(values)

    def projections(self, week: int) -> dict:
        """player_id -> stats dict for the given week, cached per-context."""
        if week not in self._projections:
            season = self.league["season"]
            raw = sapi.get_projections(season, week)
            self._projections[week] = {p["player_id"]: p.get("stats") or {} for p in raw}
        return self._projections[week]

    # -- helpers --

    def player_name(self, player_id: str) -> str:
        if player_id in self.all_players:
            p = self.all_players[player_id]
            if p.get("position") == "DEF":
                return p.get("full_name") or player_id
            return p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or player_id
        return player_id

    def player_position(self, player_id: str) -> str:
        p = self.all_players.get(player_id) or {}
        return p.get("position") or "?"

    def owner_name(self, roster_id: int) -> str:
        roster = self.roster_by_id.get(roster_id)
        if not roster:
            return "Unknown"
        user = self.user_by_id.get(roster["owner_id"])
        return user["display_name"] if user else "Unknown"

    def dynasty_value(self, player_id: str) -> int:
        entry = self.values_by_sid.get(str(player_id))
        return entry["value"] if entry else 0

    def is_rostered(self, player_id: str) -> bool:
        for r in self.rosters:
            if player_id in (r.get("players") or []):
                return True
        return False

    def roster_by_position(self, player_ids: list) -> dict:
        """position -> list of (player_id, name, dynasty_value), sorted best first."""
        out = {}
        for pid in player_ids:
            pos = self.player_position(pid)
            out.setdefault(pos, []).append((pid, self.player_name(pid), self.dynasty_value(pid)))
        for pos in out:
            out[pos].sort(key=lambda t: t[2], reverse=True)
        return out
