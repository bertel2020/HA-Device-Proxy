import asyncio
import logging
from pathlib import Path

import pytest

from ser2net_app import process
from ser2net_app.process import Ser2Net


async def test_forwards_the_log_and_starts_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    script = tmp_path / "ser2net"
    script.write_text("#!/bin/sh\necho started with $*\n")
    script.chmod(0o755)
    monkeypatch.setattr(process, "RESTART_DELAYS", (0,))
    ser2net = Ser2Net(tmp_path / "ser2net.yaml", binary=str(script))
    stop = asyncio.Event()
    caplog.set_level(logging.INFO)
    task = asyncio.create_task(ser2net.run(stop))
    while ser2net.restarts < 2:
        await asyncio.sleep(0.01)
    stop.set()
    await task
    assert f"ser2net: started with -d -c {tmp_path / 'ser2net.yaml'}" in caplog.text
