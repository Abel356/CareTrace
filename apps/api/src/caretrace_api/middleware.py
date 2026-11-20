import json
import logging
from collections.abc import Callable
from time import perf_counter
from uuid import UUID

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from caretrace_api.errors import error_response
from caretrace_api.settings import Settings

logger = logging.getLogger("uvicorn.error.caretrace")


class RequestBoundaryMiddleware:
    def __init__(self, app: ASGIApp, *, settings: Settings) -> None:
        self.app = app
        self.allowed_hosts = frozenset(settings.allowed_hosts)
        self.max_request_bytes = settings.max_request_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        request_id = scope["state"]["request_id"]
        hosts = headers.getlist("host")
        if len(hosts) != 1 or not self._allows_host(hosts[0]):
            response = error_response(
                400, "invalid_host", "Host is not allowed", request_id
            )
            await response(scope, receive, send)
            return

        lengths = headers.getlist("content-length")
        if lengths:
            try:
                (length,) = lengths
                if not length.isascii() or not length.isdecimal():
                    raise ValueError("Content length must be an ASCII integer")
                declared_size = int(length)
            except ValueError:
                response = error_response(
                    400, "invalid_length", "Invalid content length", request_id
                )
                await response(scope, receive, send)
                return
            if declared_size > self.max_request_bytes:
                await self._reject_body(scope, receive, send, request_id)
                return

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.max_request_bytes:
                await self._reject_body(scope, receive, send, request_id)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        buffered = True

        async def receive_body() -> Message:
            nonlocal buffered
            if buffered:
                buffered = False
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, receive_body, send)

    def _allows_host(self, authority: str) -> bool:
        hostname, separator, port = authority.partition(":")
        if hostname.lower() not in self.allowed_hosts:
            return False
        return not separator or (
            0 < len(port) <= 5
            and port.isascii()
            and port.isdecimal()
            and 0 < int(port) <= 65_535
        )

    async def _reject_body(
        self, scope: Scope, receive: Receive, send: Send, request_id: str
    ) -> None:
        response = error_response(
            413, "request_too_large", "Request body is too large", request_id
        )
        await response(scope, receive, send)


class RequestContextMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        id_factory: Callable[[], UUID],
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        self.app = app
        self.id_factory = id_factory
        self.clock = clock

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(self.id_factory())
        scope.setdefault("state", {})["request_id"] = request_id
        started = self.clock()
        status: int | None = None
        failed = False

        async def send_with_context(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Cache-Control"] = "no-store"
            await send(message)

        try:
            await self.app(scope, receive, send_with_context)
        except Exception:
            failed = True
            if status is not None:
                # The server must close a response that failed after starting.
                raise RuntimeError("Request failed after response started") from None
            response = error_response(
                500, "internal_error", "Internal server error", request_id
            )
            await response(scope, receive, send_with_context)
        finally:
            if status is not None:
                event = {
                    "event": "http_request",
                    "request_id": request_id,
                    "status_code": status,
                    "duration_ms": round((self.clock() - started) * 1000, 2),
                }
                logger.log(
                    logging.ERROR if failed or status >= 500 else logging.INFO,
                    json.dumps(event),
                )
