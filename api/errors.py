"""Unified error handling module."""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from utils.logger_handler import app_logger, error_logger


def register_error_handlers(app):
    """Register unified error handlers on the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        error_logger.error(f"Unhandled exception | {request.method} {request.url.path} | {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                }
            },
        )
