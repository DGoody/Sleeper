"""Local config: which league and which team is 'you'."""
import json
import os

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".config", "sleeper-dynasty", "config.json")


def load():
    if not os.path.exists(CONFIG_PATH):
        return None
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save(cfg: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def require():
    cfg = load()
    if not cfg:
        raise SystemExit(
            "No config found. Run `python -m sleeper_dynasty setup <league_id> <your_sleeper_username>` first."
        )
    return cfg
