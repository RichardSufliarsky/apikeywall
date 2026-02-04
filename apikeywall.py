import json
import logging
import time

from pathlib import Path
from typing import TypedDict
from mitmproxy import http


log = logging.getLogger(__name__)

_last_check = 0.0
CHECK_INTERVAL = 10.0  # seconds

CONFIG_PATH = Path.home() / ".mitmproxy" / "apikeywall.json"
TMP_SUFFIX = ".loading"


class Rule(TypedDict):
    tokenout: str
    endpoints: list[str]


# Active rules (in-memory only)
RULES: dict[str, Rule] = {}

# Track last processed file
_loaded_generation = 0


def _load_and_delete(path: Path) -> object | None:
    """
    Atomically load config and delete it immediately after.
    """
    tmp = path.with_suffix(path.suffix + TMP_SUFFIX)

    try:
        path.rename(tmp)  # atomic on same filesystem
    except FileNotFoundError:
        return None
    except Exception as e:
        log.error("%s: cannot acquire config file: %s", path, e)
        return None

    try:
        with tmp.open() as f:
            data = json.load(f)
    except Exception as e:
        log.error("%s: invalid JSON: %s", path, e)
        return None
    finally:
        try:
            tmp.unlink()
        except Exception:
            log.warning("%s: failed to delete secret file", tmp)

    return data


def _validate(raw: object) -> tuple[list[str], dict[str, Rule]]:
    errors: list[str] = []
    rules: dict[str, Rule] = {}

    if not isinstance(raw, list):
        return ["JSON root must be an array"], rules

    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append(f"item {i}: must be an object")
            continue

        tokenin = item.get("tokenin")
        tokenout = item.get("tokenout")
        endpoints = item.get("endpoints")

        if not isinstance(tokenin, str) or not tokenin:
            errors.append(f"item {i}: invalid tokenin")
            continue
        if not isinstance(tokenout, str) or not tokenout:
            errors.append(f"item {i}: invalid tokenout")
            continue
        if not isinstance(endpoints, list) or any(
            not isinstance(e, str) or not e for e in endpoints
        ):
            errors.append(f"item {i}: invalid endpoints")
            continue

        rules[tokenin] = {
            "tokenout": tokenout,
            "endpoints": endpoints,
        }

    return errors, rules


def _reload_if_present() -> None:
    global RULES, _loaded_generation

    raw = _load_and_delete(CONFIG_PATH)
    if raw is None:
        return

    errors, rules = _validate(raw)
    if errors:
        for e in errors:
            log.error("%s: %s", CONFIG_PATH, e)
        return

    RULES = rules
    _loaded_generation += 1
    log.info(
        "%s: loaded %d rules (generation %d)",
        CONFIG_PATH,
        len(RULES),
        _loaded_generation,
    )

def _maybe_reload() -> None:
    global _last_check

    now = time.monotonic()
    if now - _last_check < CHECK_INTERVAL:
        return

    _last_check = now

    if CONFIG_PATH.exists():
        _reload_if_present()


_reload_if_present() # initial pickup at script import

def request(flow: http.HTTPFlow) -> None:
    _maybe_reload()

    if not RULES:
        return

    auth = flow.request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return

    token = auth[7:]
    rule = RULES.get(token)
    if not rule:
        return

    if flow.request.pretty_host in rule["endpoints"]:
        flow.request.headers["authorization"] = f"Bearer {rule['tokenout']}"
