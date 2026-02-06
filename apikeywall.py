import asyncio
import json
import logging
from pathlib import Path
from typing import TypedDict
from mitmproxy import ctx, http

log = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / ".mitmproxy" / "apikeywall.json"
TMP_SUFFIX = ".loading"
TCP_TIMEOUT = 7200

class Rule(TypedDict):
    tokenout: str
    endpoints: list[str]

class ApiKeyWall:
    def load(self, loader):
        """Called when addon is loaded, set tcp_timeout here."""
        self.RULES: dict[str, Rule] = {}
        self._loaded_generation = 0
        self._last_check = 0.0
        self._all_endpoints = set()  # Store all unique endpoints
        # Initial load on startup
        self._reload_if_present(True)
        ctx.options.tcp_timeout = TCP_TIMEOUT
        log.info(f"Set tcp_timeout to {TCP_TIMEOUT} seconds")
        asyncio.ensure_future(self._maybe_reload())

    def _load_and_delete(self, path: Path) -> object | None:
        """Atomically load config and delete it immediately after."""
        tmp = path.with_suffix(path.suffix + TMP_SUFFIX)
        try:
            path.rename(tmp)
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

    def _validate(self, raw: object) -> tuple[list[str], dict[str, Rule]]:
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

    def _update_allow_hosts(self):
        """Update ctx.options.allow_hosts with all endpoints from RULES."""
        # Collect all unique endpoints
        new_endpoints = set()
        for rule in self.RULES.values():
            new_endpoints.update(rule["endpoints"])
        # Update if the set has changed
        if new_endpoints != self._all_endpoints:
            self._all_endpoints = new_endpoints
            # Convert set to sorted list for consistent option setting
            allow_list = sorted(self._all_endpoints)
            ctx.options.allow_hosts = allow_list
            log.info(
                "Updated allow_hosts with %d endpoints (generation %d)",
                len(allow_list),
                self._loaded_generation,
            )

    def _reload_if_present(self, init: bool = False) -> None:
        raw = self._load_and_delete(CONFIG_PATH)
        if raw is None:
            if init:
                log.error("%s: config file missing", CONFIG_PATH)
                ctx.master.should_exit.set()
            return
        errors, rules = self._validate(raw)
        if errors:
            for e in errors:
                log.error("%s: %s", CONFIG_PATH, e)
            return
        self.RULES = rules
        self._loaded_generation += 1
        # Update the allow_hosts option whenever rules are reloaded
        self._update_allow_hosts()
        log.info(
            "%s: loaded %d rules (generation %d)",
            CONFIG_PATH,
            len(self.RULES),
            self._loaded_generation,
        )

    async def _maybe_reload(self) -> None:
        while True:
            if ctx.master.should_exit.is_set():
                return
            if CONFIG_PATH.exists():
                self._reload_if_present()
            await asyncio.sleep(1)

    def requestheaders(self, flow: http.HTTPFlow) -> None:
        if not self.RULES:
            return
        auth = flow.request.headers.get("authorization")
        if not auth or not auth.lower().startswith("bearer "):
            return
        token = auth[7:]
        rule = self.RULES.get(token)
        if not rule:
            return
        if flow.request.pretty_host in rule["endpoints"]: # double check (allow_hosts already filtered out other hosts)
            flow.request.headers["authorization"] = f"Bearer {rule['tokenout']}"
            log.info(f"Replaced placeholder '{token}' ({flow.request.pretty_host})")

# Make the addon instance available to mitmproxy
addons = [ApiKeyWall()]
