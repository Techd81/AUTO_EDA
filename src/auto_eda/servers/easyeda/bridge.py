"""WebSocket bridge server — listens for EasyEDA Pro extension to connect.

Architecture (CORRECT):
  EDA Extension (WS client) ──connects to──▶ EDABridge (WS server, port 9050)
  EDABridge ──forwards──▶ MCP Server tools

The jlceda-mcp-bridge extension (v0.0.17) acts as WebSocket CLIENT.
It repeatedly tries to connect to ws://127.0.0.1:9050/.
We must run a WS SERVER and wait for it.

Protocol (XuF163/jlc-eda-mcp):
  Request  (us→eda): {"type":"request", "id":"<str>", "method":"<str>", "params":{...}}
  Response (eda→us): {"type":"response", "id":"<str>", "result":{...}}  or  "error":{...}
  Also receives: {"type":"hello", ...} on connect
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

try:
    import websockets
    from websockets.asyncio.server import ServerConnection, serve
except ImportError:
    websockets = None  # type: ignore[assignment]
    ServerConnection = None  # type: ignore[assignment]
    serve = None  # type: ignore[assignment]

from auto_eda.core.errors import EDAError, EDAErrorCode

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9050
_CMD_TIMEOUT  = 30.0


class EDABridge:
    """WebSocket SERVER that waits for EDA extension to connect.

    Usage:
        bridge = EDABridge()
        await bridge.start_server()   # starts listening, non-blocking
        # ... wait for EDA to connect ...
        result = await bridge.send_command("jlc.board.getInfo", {})
        await bridge.stop_server()
    """

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        self._host = host
        self._port = port
        self._conn: ServerConnection | None = None
        self._server = None
        self._lock = asyncio.Lock()
        self._req_id = 0
        self._pending: dict[str, asyncio.Future] = {}
        self._connected = asyncio.Event()

    # ------------------------------------------------------------------
    # Server lifecycle
    # ------------------------------------------------------------------

    async def start_server(self) -> None:
        """Start listening for EDA extension connection."""
        if websockets is None:
            raise EDAError(
                EDAErrorCode.DEPENDENCY_MISSING,
                "websockets package not installed. Run: pip install websockets",
            )
        self._server = await serve(
            self._handler, self._host, self._port,
            ping_interval=20, ping_timeout=10,
        )
        logger.info("EDA bridge server listening on ws://%s:%d/", self._host, self._port)

    async def stop_server(self) -> None:
        """Stop the WS server and close active connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        self._connected.clear()

    async def wait_for_connection(self, timeout: float = 30.0) -> bool:
        """Block until EDA extension connects (or timeout). Returns True if connected."""
        try:
            await asyncio.wait_for(self._connected.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    # ------------------------------------------------------------------
    # Connection handler (called by websockets for each new connection)
    # ------------------------------------------------------------------

    async def _handler(self, conn: ServerConnection) -> None:
        """Handle incoming EDA extension connection."""
        logger.info("EDA extension connected from %s", conn.remote_address)
        self._conn = conn
        self._connected.set()
        try:
            async for raw in conn:
                await self._handle_message(raw)
        except Exception as exc:
            logger.warning("EDA connection closed: %s", exc)
        finally:
            self._conn = None
            self._connected.clear()
            # Fail all pending requests
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(
                        EDAError(EDAErrorCode.UNKNOWN, "EDA connection lost")
                    )
            self._pending.clear()
            logger.info("EDA extension disconnected")

    async def _handle_message(self, raw: str | bytes) -> None:
        """Dispatch incoming message to waiting futures."""
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Received non-JSON message: %s", raw)
            return

        msg_type = msg.get("type", "")
        if msg_type == "hello":
            logger.info("EDA hello: %s", msg)
            return

        msg_id = msg.get("id")
        if msg_id and msg_id in self._pending:
            fut = self._pending.pop(msg_id)
            if not fut.done():
                if "error" in msg:
                    err = msg["error"]
                    fut.set_exception(EDAError(
                        EDAErrorCode.UNKNOWN,
                        f"EDA error in response: {err}",
                    ))
                else:
                    fut.set_result(msg.get("result", {}))

    # ------------------------------------------------------------------
    # Public command API
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """Return True if EDA extension is connected and responsive."""
        if not self._conn:
            return False
        try:
            result = await self.send_command("ping", {}, timeout=5.0)
            return True
        except Exception:
            return False

    async def eda_invoke(self, path: str, *args: Any, timeout: float = _CMD_TIMEOUT) -> Any:
        """Convenience wrapper for eda.invoke — call an EDA globalThis method.

        Args:
            path: Dot-separated path on eda object, e.g. "sch_PrimitiveComponent.create"
            *args: Positional arguments to pass to the method.
            timeout: Per-command timeout in seconds.

        Returns:
            The `result` field from the EDA response.
        """
        resp = await self.send_command(
            "eda.invoke",
            {"path": path, "args": list(args)},
            timeout=timeout,
        )
        return resp.get("result")

    async def eda_get(self, path: str, timeout: float = _CMD_TIMEOUT) -> Any:
        """Read a property value from eda globalThis object."""
        resp = await self.send_command("eda.get", {"path": path}, timeout=timeout)
        return resp.get("value")

    async def send_command(
        self,
        method: str,
        params: dict[str, Any],
        timeout: float = _CMD_TIMEOUT,
    ) -> dict[str, Any]:
        """Send a command to EDA and wait for response."""
        if not self._conn:
            raise EDAError(
                EDAErrorCode.UNKNOWN,
                "EDA extension not connected. Make sure EDA Pro is open with MCP Bridge extension enabled.",
            )
        async with self._lock:
            req_id = self._next_id()
            fut: asyncio.Future = asyncio.get_event_loop().create_future()
            self._pending[req_id] = fut
            payload = json.dumps({
                "type": "request",
                "id": req_id,
                "method": method,
                "params": params,
            })
            try:
                await self._conn.send(payload)
                return await asyncio.wait_for(asyncio.shield(fut), timeout=timeout)
            except asyncio.TimeoutError:
                self._pending.pop(req_id, None)
                raise EDAError(
                    EDAErrorCode.TIMEOUT,
                    f"Command '{method}' timed out after {timeout}s",
                )
            except EDAError:
                raise
            except Exception as exc:
                self._pending.pop(req_id, None)
                raise EDAError(
                    EDAErrorCode.UNKNOWN,
                    f"WebSocket error during '{method}': {exc}",
                )

    async def disconnect(self) -> None:
        """Close the active connection (server keeps listening)."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            self._connected.clear()

    def _next_id(self) -> str:
        self._req_id += 1
        return str(self._req_id)

    @property
    def is_connected(self) -> bool:
        return self._conn is not None


# ---------------------------------------------------------------------------
# Module-level singleton — shared across all tool calls in one server process
# ---------------------------------------------------------------------------
_bridge: EDABridge | None = None


def get_bridge() -> EDABridge:
    """Return the module-level EDABridge singleton."""
    global _bridge
    if _bridge is None:
        _bridge = EDABridge()
    return _bridge
