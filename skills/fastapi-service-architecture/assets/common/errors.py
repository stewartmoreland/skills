"""Domain errors and the handlers that turn them into HTTP responses.

Repositories and service modules raise these; only this module knows about status
codes. That keeps the data layer testable without a request context and stops
`HTTPException` from leaking into code that has nothing to do with HTTP.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

# Starlette renamed HTTP_422_UNPROCESSABLE_ENTITY to HTTP_422_UNPROCESSABLE_CONTENT
# and deprecated the old spelling. The literal works on every version.
HTTP_422 = 422


class AppError(Exception):
    """Base class for expected, client-visible failures."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "bad_request"

    def __init__(self, detail: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.context = context or {}


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class PermissionDeniedError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "permission_denied"


class UnprocessableError(AppError):
    status_code = HTTP_422
    code = "unprocessable"


def _payload(code: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {"error": {"code": code, "detail": detail, **extra}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.code, exc.detail, **exc.context),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_422,
            content=_payload(
                "validation_error",
                "Request validation failed.",
                errors=jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_error(_: Request, exc: IntegrityError) -> JSONResponse:
        # A unique/foreign-key violation is a client mistake, not a server fault.
        # The driver message can name internal columns, so log it and return a
        # generic body.
        logger.warning("integrity error", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_payload("conflict", "Request conflicts with existing data."),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled error", extra={"path": request.url.path, "method": request.method}
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_payload("internal_error", "An unexpected error occurred."),
        )
