"""Tests for EDABridge — mock-based, no real EDA client needed."""
from __future__ import annotations

import asyncio
import json
import pytest

from auto_eda.core.errors import EDAError
from auto_eda.servers.easyeda.bridge import EDABridge


# ---------------------------------------------------------------------------
# Mock ServerConnection — simulates the EDA extension side
# ---------------------------------------------------------------------------

class _MockConn:
    """Simulates a websockets ServerConnection that auto-responds to requests."""

    def __init__(self, bridge: EDABridge, response_data: dict | None = None,
                 error: dict | None = None) -> None:
        self._bridge = bridge
        self._response_data = response_data or {}
        self._error = error
        self.sent: list[str] = []
        self.closed = False
        self.remote_address = ("127.0.0.1", 12345)

    async def send(self, data: str) -> None:
        self.sent.append(data)
        req = json.loads(data)
        req_id = req["id"]
        # Simulate EDA extension responding asynchronously
        if self._error is not None:
            response = json.dumps({"type": "response", "id": req_id,
                                   "error": self._error})
        else:
            response = json.dumps({"type": "response", "id": req_id,
                                   "result": self._response_data})
        # Feed response back into bridge message handler
        asyncio.get_event_loop().call_soon(
            asyncio.ensure_future,
            self._bridge._handle_message(response),
        )

    async def close(self) -> None:
        self.closed = True


def _bridge_with_mock(response: dict | None = None,
                      error: dict | None = None) -> EDABridge:
    """Create an EDABridge with a mock connection injected."""
    bridge = EDABridge()
    mock = _MockConn(bridge, response_data=response, error=error)
    bridge._conn = mock  # type: ignore[assignment]
    bridge._connected.set()
    return bridge


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_command_success() -> None:
    bridge = _bridge_with_mock({"ref": "U1"})
    result = await bridge.send_command("eda.invoke", {"path": "test", "args": []})
    assert result == {"ref": "U1"}


@pytest.mark.asyncio
async def test_send_command_rpc_error() -> None:
    bridge = _bridge_with_mock(error={"message": "Symbol not found"})
    with pytest.raises(EDAError, match="EDA error"):
        await bridge.send_command("eda.invoke", {"path": "test", "args": []})


@pytest.mark.asyncio
async def test_ping_success() -> None:
    bridge = _bridge_with_mock({"pong": True})
    assert await bridge.ping() is True


@pytest.mark.asyncio
async def test_ping_failure_when_not_connected() -> None:
    bridge = EDABridge()
    # No connection — should return False, not raise
    result = await bridge.ping()
    assert result is False


@pytest.mark.asyncio
async def test_disconnect_clears_conn() -> None:
    bridge = _bridge_with_mock({})
    assert bridge._conn is not None
    await bridge.disconnect()
    assert bridge._conn is None


@pytest.mark.asyncio
async def test_request_ids_increment() -> None:
    bridge = _bridge_with_mock({})
    await bridge.send_command("ping", {})
    await bridge.send_command("ping", {})
    ids = [json.loads(m)["id"] for m in bridge._conn.sent]  # type: ignore[union-attr]
    assert ids == ["1", "2"]
