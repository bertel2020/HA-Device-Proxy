"""Notifications in Home Assistant through its Core API (via the Supervisor).

Each problem has a fixed id per connection (ser2net_<id>_<problem>), so a repeat updates the
one notification instead of adding more, and it is dismissed when the problem is gone.
Optionally a notify service (e.g. mobile_app_phone) gets a message when a problem starts and,
if set, when it is over. A problem is reported only after it lasted the grace time, and not
at all in the first minute after the app started (devices appear one after the other then).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

_LOGGER = logging.getLogger(__name__)

CORE = "http://supervisor/core/api"
QUIET_AFTER_START = 60  # seconds


def _call(path: str, data: dict[str, Any] | None = None) -> Any:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        raise OSError("no Supervisor token (not running as a Home Assistant app)")
    request = urllib.request.Request(
        f"{CORE}/{path}",
        data=None if data is None else json.dumps(data).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read()
    return json.loads(body) if body else None


def notify_services() -> list[str]:
    """The notify services Home Assistant offers (e.g. mobile_app_phone)."""
    try:
        domains = _call("services")
    except (OSError, ValueError) as err:
        _LOGGER.debug("Notify services not read: %s", err)
        return []
    for domain in domains or []:
        if domain.get("domain") == "notify":
            return sorted(
                name for name in domain.get("services", {}) if name != "persistent_notification"
            )
    return []


@dataclass
class Problem:
    key: str  # notification id
    title: str
    message: str
    since: float
    shown: bool = False


class Notifier:
    def __init__(self, *, clock: Any = time.time) -> None:
        self.clock = clock
        self.started = clock()
        self.problems: dict[str, Problem] = {}
        self.available = bool(os.environ.get("SUPERVISOR_TOKEN"))

    async def update(
        self,
        current: dict[str, tuple[str, str]],
        *,
        grace: float,
        dismiss: bool,
        service: str = "",
        resolved_message: bool = False,
    ) -> None:
        """current: notification id → (title, message) of every problem there is right now."""
        now = self.clock()
        for key, (title, message) in current.items():
            problem = self.problems.get(key)
            if problem is None:
                problem = self.problems[key] = Problem(key, title, message, now)
            problem.title, problem.message = title, message
            due = now - problem.since >= grace and now - self.started >= QUIET_AFTER_START
            if due and not problem.shown:
                problem.shown = True
                await self._show(problem, service)
        for key in list(self.problems):
            if key in current:
                continue
            problem = self.problems.pop(key)
            if problem.shown and dismiss:
                await self._send(
                    "services/persistent_notification/dismiss", {"notification_id": key}
                )
            if problem.shown and service and resolved_message:
                await self._send(
                    f"services/notify/{service}",
                    {"title": f"✓ {problem.title}", "message": "Wieder in Ordnung / OK again"},
                )

    async def _show(self, problem: Problem, service: str) -> None:
        await self._send(
            "services/persistent_notification/create",
            {"notification_id": problem.key, "title": problem.title, "message": problem.message},
        )
        if service:
            await self._send(
                f"services/notify/{service}", {"title": problem.title, "message": problem.message}
            )

    async def _send(self, path: str, data: dict[str, Any]) -> None:
        if not self.available:
            _LOGGER.info("Notification (no Home Assistant here): %s", data)
            return
        try:
            await asyncio.to_thread(_call, path, data)
        except (OSError, ValueError) as err:
            _LOGGER.warning("Notification not sent (%s): %s", path, err)
