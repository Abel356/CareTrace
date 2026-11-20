from collections.abc import Mapping
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
    request_id: str


def error_response(
    status: int,
    code: str,
    message: str,
    request_id: str,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorEnvelope(
        error=ErrorDetail(code=code, message=message), request_id=request_id
    )
    return JSONResponse(body.model_dump(), status_code=status, headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exception: HTTPException) -> JSONResponse:
        status_code = exception.status_code
        try:
            message = HTTPStatus(status_code).phrase
        except ValueError:
            message = "Request failed"
        return error_response(
            status_code,
            f"http_{status_code}",
            message,
            request.state.request_id,
            exception.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(
        request: Request, exception: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            422,
            "invalid_request",
            "Request validation failed",
            request.state.request_id,
        )
