"""Tests for EDABridge — uses a mock WebSocket server to avoid needing real EDA client."""
from __future__ import annotations

import asyncio
import json
import pytest

from auto_eda.core.errors import EDAError
from auto_eda.servers.easyeda.bridge import EDABridge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _MockWS:
    """Minimal WebSocket double that echoes a preset response."""

    def __init__(self, response: dict) -> None:
        self._response = response
        self.sent: list[str] = []
        self.closed = False

    async def ping(self) -> None:
        pass

    async def send(self, data: str) -> None:
        self.sent.append(data)

    async def recv(self) -> str:
        req = json.loads(self.sent[-1])
        req_id = req["id"]
        # Mirror hyl64/jlcmcp bridge protocol response format
        return json.dumps({
            "type": "result",
            "payload": {
                "commandId": req_id,
                "success": self._response.get("success", True),
                "data": self._response.get("data", {}),
                "error": self._response.get("error"),
            },
        })

    async def close(self) -> None:
        self.closed = True


def _bridge_with_mock(response: dict) -> EDABridge:
    bridge = EDABridge(url="ws://127.0.0.1:18800/ws/bridge")
    bridge._ws = _MockWS(response)  # inject mock
    return bridge


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_command_success() -> None:
    bridge = _bridge_with_mock({"success": True, "data": {"ref": "U1"}})
    result = await bridge.send_command("sch.placeSymbol", {"lcsc": "C8734", "x": 0, "y": 0})
    assert result == {"ref": "U1"}


@pytest.mark.asyncio
async def test_send_command_rpc_error() -> None:
    bridge = _bridge_with_mock({"success": False, "error": "Symbol not found"})
    with pytest.raises(EDAError, match="Symbol not found"):
        await bridge.send_command("sch.placeSymbol", {"lcsc": "INVALID"})


@pytest.mark.asyncio
async def test_ping_success() -> None:
    bridge = _bridge_with_mock({"success": True, "data": {"pong": True}})
    assert await bridge.ping() is True


@pytest.mark.asyncio
async def test_ping_failure_on_connection_error() -> None:
    bridge = EDABridge(url="ws://127.0.0.1:19999/nonexistent")
    # No real server — should return False, not raise
    result = await bridge.ping()
    assert result is False


@pytest.mark.asyncio
async def test_disconnect_clears_ws() -> None:
    bridge = _bridge_with_mock({"success": True, "data": {}})
    assert bridge._ws is not None
    await bridge.disconnect()
    assert bridge._ws is None


@pytest.mark.asyncio
async def test_request_ids_increment() -> None:
    bridge = _bridge_with_mock({"success": True, "data": {}})
    await bridge.send_command("sys.ping", {})
    await bridge.send_command("sys.ping", {})
    ids = [json.loads(m)["id"] for m in bridge._ws.sent]  # type: ignore[union-attr]
    assert ids == ["1", "2"]
