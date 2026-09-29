"""Thin wrappers over Sleeper's public read-only API (no auth needed)."""
from . import http

BASE = "https://api.sleeper.app/v1"

FANTASY_POSITIONS = {"QB", "RB", "WR", "TE", "K", "DEF"}


def get_user(username: str) -> dict:
    return http.get_json(f"{BASE}/user/{username}")


def get_league(league_id: str) -> dict:
    return http.get_json(f"{BASE}/league/{league_id}", cache_key=f"league_{league_id}", ttl_seconds=300)


def get_users(league_id: str) -> list:
    return http.get_json(f"{BASE}/league/{league_id}/users", cache_key=f"users_{league_id}", ttl_seconds=300)


def get_rosters(league_id: str) -> list:
    return http.get_json(f"{BASE}/league/{league_id}/rosters", cache_key=f"rosters_{league_id}", ttl_seconds=120)


def get_matchups(league_id: str, week: int) -> list:
    return http.get_json(f"{BASE}/league/{league_id}/matchups/{week}")


def get_transactions(league_id: str, week: int) -> list:
    return http.get_json(f"{BASE}/league/{league_id}/transactions/{week}")


def get_nfl_state() -> dict:
    return http.get_json(f"{BASE}/state/nfl", cache_key="nfl_state", ttl_seconds=1800)


def get_all_players() -> dict:
    # ~5MB payload; Sleeper asks this only be pulled a few times a day.
    return http.get_json(f"{BASE}/players/nfl", cache_key="all_players", ttl_seconds=86400)


def get_trending(add_or_drop: str = "add", lookback_hours: int = 24, limit: int = 100) -> list:
    url = f"{BASE}/players/nfl/trending/{add_or_drop}?lookback_hours={lookback_hours}&limit={limit}"
    return http.get_json(url, cache_key=f"trending_{add_or_drop}_{lookback_hours}_{limit}", ttl_seconds=1800)


def get_projections(season: str, week: int) -> list:
    # Undocumented but stable endpoint used by the Sleeper app itself.
    url = f"https://api.sleeper.app/projections/nfl/{season}/{week}?season_type=regular"
    return http.get_json(url, cache_key=f"proj_{season}_{week}", ttl_seconds=3600)
