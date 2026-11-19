"""
Upload limit middleware.

FastAPI reads the whole multipart body before the import route runs. This pure ASGI middleware rejects a workbook
upload whose `Content-Length` already exceeds the limit (`WorkbookImportFeature.check_content_length`) with the same
413 error, before any of the body is received.
"""

from typing import Optional

from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from constants.import_constants import IMPORT_SETTINGS
from errors.app_error import AppError
from errors.error_handlers import ErrorHandlers, error_handlers
from features.workbook_import_feature import WorkbookImportFeature, workbook_import_feature


class UploadLimitMiddleware:
    """Rejects oversize workbook uploads from their declared size."""

    def __init__(
        self,
        app: ASGIApp,
        feature: Optional[WorkbookImportFeature] = None,
        handlers: Optional[ErrorHandlers] = None,
        path: str = IMPORT_SETTINGS["UPLOAD_PATH"],
    ):
        """
        Wrap an ASGI app.

        Args:
            app: Wrapped ASGI application
            feature: Import feature holding the limit; defaults to the shared instance
            handlers: Error handlers that package the 413; default to the shared instance
            path: Upload route path
        """
        self._app = app
        self._feature = feature or workbook_import_feature
        self._handlers = handlers or error_handlers
        self._path = path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle one ASGI call.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] == "http" and scope["path"] == self._path:
            try:
                self._feature.check_content_length(Headers(scope=scope).get("content-length"))
            except AppError as error:
                response = await self._handlers.handle(Request(scope), error)
                await response(scope, receive, send)
                return
        await self._app(scope, receive, send)
