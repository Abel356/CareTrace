import json
import logging
from collections.abc import Callable
from time import perf_counter
from uuid import UUID

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from caretrace_api.errors import error_response

logger = logging.getLogger("uvicorn.error.caretrace")


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
