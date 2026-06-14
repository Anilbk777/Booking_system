import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.utils.logging import LoggerFactory
from app.utils.exceptions import AppBaseException

logger = LoggerFactory.get_logger(__name__)

app = FastAPI()


# ── 1. Your custom exceptions ─────────────────────────────────
@app.exception_handler(AppBaseException)
async def handle_app_exception(request: Request, exc: AppBaseException):
    logger.error(
        "[%s] %s | path=%s\n%s",
        exc.__class__.__name__,
        exc.internal_detail,
        request.url.path,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.user_message},
    )


# ── 2. Request validation error (bad incoming JSON / query params) ──
async def handle_request_validation_error(
    request: Request, exc: RequestValidationError
):
    logger.warning(
        "[RequestValidationError] path=%s | errors=%s",
        request.url.path,
        exc.errors(),
    )

    first_error = exc.errors()[0]

    field = " → ".join(str(loc) for loc in first_error["loc"][1:])
    message = first_error["msg"].replace("Value error, ", "")

    return JSONResponse(
        status_code=422,
        content={"error": f"{field}: {message}"},
    )


# ── 3. Pydantic ValidationError (raised inside your code, not from request) ──
@app.exception_handler(ValidationError)
async def handle_pydantic_validation_error(request: Request, exc: ValidationError):
    # This fires when you manually call a Pydantic model inside a service
    # and it fails — it's an internal issue, so treat it like a 500
    logger.error(
        "[PydanticValidationError] path=%s | errors=%s\n%s",
        request.url.path,
        exc.errors(),
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"error": "An internal data error occurred."},
    )


# ── 4. FastAPI's own HTTPException ────────────────────────────────
@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    # Log 5xx but not 4xx — 4xx are expected client errors
    if exc.status_code >= 500:
        logger.error(
            "[HTTPException] status=%s detail=%s | path=%s",
            exc.status_code,
            exc.detail,
            request.url.path,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


# ── 5. Catch-all safety net ───────────────────────────────────────
@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception):
    logger.critical(
        "[UnhandledException] %s | path=%s\n%s",
        str(exc),
        request.url.path,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred. Please contact support."},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppBaseException, handle_app_exception)
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
    app.add_exception_handler(ValidationError, handle_pydantic_validation_error)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_unexpected_exception)
