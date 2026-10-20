"""Runs ser2net in the foreground, forwards its log and starts it again when it ends."""

from __future__ import annotations

import asyncio
import logging
import signal
from collections.abc import Callable
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

RESTART_DELAYS = (1, 2, 5, 10, 30)  # seconds; the last one repeats
STABLE_AFTER = 60  # a run this long resets the delay


class Ser2Net:
    def __init__(
        self,
        config: Path,
        binary: str = "ser2net",
        on_exit: Callable[[int | None, float], None] | None = None,
    ) -> None:
        self.config = config
        self.binary = binary
        self.on_exit = on_exit  # (exit code, seconds until the next start)
        self.restarts = 0
        self._proc: asyncio.subprocess.Process | None = None

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    async def run(self, stop: asyncio.Event) -> None:
        failures = 0
        while not stop.is_set():
            loop = asyncio.get_running_loop()
            started = loop.time()
            code = await self._run_once(stop)
            if stop.is_set():
                return
            if loop.time() - started >= STABLE_AFTER:
                failures = 0
            delay = RESTART_DELAYS[min(failures, len(RESTART_DELAYS) - 1)]
            failures += 1
            self.restarts += 1
            if self.on_exit is not None:
                self.on_exit(code, delay)
            else:
                _LOGGER.warning("ser2net ended (exit code %s), starting again in %s s", code, delay)
            try:
                await asyncio.wait_for(stop.wait(), delay)
            except TimeoutError:
                pass

    async def _run_once(self, stop: asyncio.Event) -> int | None:
        # -d: stay in the foreground and write the log to stdout instead of syslog
        try:
            self._proc = await asyncio.create_subprocess_exec(
                self.binary,
                "-d",
                "-c",
                str(self.config),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except OSError as err:
            _LOGGER.error("ser2net cannot be started: %s", err)
            return None
        _LOGGER.info("ser2net started (pid %s)", self._proc.pid)
        logs = asyncio.create_task(self._forward_log())
        stopping = asyncio.create_task(stop.wait())
        await asyncio.wait([logs, stopping], return_when=asyncio.FIRST_COMPLETED)
        if stop.is_set():
            await self.terminate()
        stopping.cancel()
        await logs
        return await self._proc.wait()

    async def _forward_log(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        async for raw in self._proc.stdout:
            line = raw.decode(errors="replace").rstrip()
            if line:
                _LOGGER.info("ser2net: %s", line)

    def reload(self) -> bool:
        """Reread the configuration; only changed connections are rebuilt."""
        if not self.running:
            return False
        assert self._proc is not None
        self._proc.send_signal(signal.SIGHUP)
        _LOGGER.info("ser2net: configuration reloaded")
        return True

    async def terminate(self, timeout: float = 5) -> None:
        if not self.running:
            return
        assert self._proc is not None
        self._proc.terminate()
        try:
            await asyncio.wait_for(self._proc.wait(), timeout)
        except TimeoutError:
            _LOGGER.warning("ser2net did not stop within %s s, killing it", timeout)
            self._proc.kill()
            await self._proc.wait()
