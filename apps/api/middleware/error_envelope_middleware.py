"""
Error envelope middleware.

Starlette's `ServerErrorMiddleware` answers unexpected exceptions outside `CORSMiddleware`, so browsers would see
a 500 without CORS headers. This pure ASGI middleware sits inside CORS and turns any exception that escapes the
app into the standard 500 envelope through `ErrorHandlers`.
"""

from typing import Optional

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from errors.error_handlers import ErrorHandlers, error_handlers


class ErrorEnvelopeMiddleware:
    """Packages unexpected exceptions as error responses inside the CORS middleware."""

    def __init__(self, app: ASGIApp, handlers: Optional[ErrorHandlers] = None):
        """
        Wrap an ASGI app.

        Args:
            app: Wrapped ASGI application
            handlers: Error handlers that package the exception; default to the shared instance
        """
        self._app = app
        self._handlers = handlers or error_handlers

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle one ASGI call; an exception after the response started is re-raised (it cannot be replaced).

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        started = False

        async def send_tracking(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self._app(scope, receive, send_tracking)
        except Exception as error:
            if started:
                raise
            response = await self._handlers.handle(Request(scope), error)
            await response(scope, receive, send)
