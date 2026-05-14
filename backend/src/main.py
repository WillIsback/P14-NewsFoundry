from contextlib import asynccontextmanager
import os
import traceback

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
import sentry_sdk

from api.models import (
    ApiResponse,
    MessageData,
    error_response,
    success_response,
)
from core.config import (
    APP_ENV,
    CORS_ORIGINS,
    DEBUG_MODE,
    ENVIRONMENT,
    validate_runtime_config,
)
from core.middleware import register_middlewares

import uvicorn

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", ""),
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    # Enable sending logs to Sentry
    enable_logs=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profile_session_sample_rate to 1.0 to profile 100%
    # of profile sessions.
    profile_session_sample_rate=1.0,
    # Set profile_lifecycle to "trace" to automatically
    # run the profiler on when there is an active transaction
    profile_lifecycle="trace",
)


def generate_operation_id(route: APIRoute) -> str:
    """Generate stable, concise OpenAPI operation IDs for codegen.

    Format:
    - `<tag>_<handler_name>` for tagged routers
    - `<handler_name>` for untagged routes
    """
    tag = (str(route.tags[0]) if route.tags else "").strip().lower()
    tag = tag.replace(" ", "_").replace("-", "_")
    name = route.name.strip().lower().replace(" ", "_").replace("-", "_")
    return f"{tag}_{name}" if tag else name


def create_app() -> FastAPI:
    missing_vars = validate_runtime_config()
    if missing_vars:
        missing_list = ", ".join(sorted(set(missing_vars)))
        raise RuntimeError(
            "Missing required environment variables: "
            f"{missing_list}. Configure your environment before starting the API."
        )

    # Import only after config validation, to avoid early crashes from transitive imports.
    from api.router import setup_routers
    from database.database import Database

    db = Database()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # En dev local uniquement: applique les migrations + seed au démarrage.
        # En production (Railway), les migrations sont gérées par le release command:
        #   uv run src/bootstrap.py
        if APP_ENV != "production":
            db.init_db()
        yield

    app = FastAPI(
        lifespan=lifespan,
        title="NewsFoundry backend API",
        description="Backend API for NewsFoundry application",
        version="1.0.0",
        generate_unique_id_function=generate_operation_id,
        docs_url=None if ENVIRONMENT == "production" else "/api/docs",
        redoc_url=None if ENVIRONMENT == "production" else "/api/redoc",
        openapi_url=None if ENVIRONMENT == "production" else "/api/openapi.json",
    )

    # --- CONFIGURATION CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_middlewares(app)
    setup_routers(app, db)
    return app


app = create_app()


@app.get("/")
async def hello() -> ApiResponse[MessageData]:
    """Handle the root endpoint of the API.

    Returns:
        dict: A greeting message with a wave emoji.

    Example:
        Response: {"message": "👋"}
    """
    return success_response(
        status=status.HTTP_200_OK,
        message="API reachable",
        data=MessageData(message="👋"),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    payload = error_response(
        status=exc.status_code,
        code="HTTP_EXCEPTION",
        message=detail,
        details=exc.detail,
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    payload = error_response(
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details=exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload.model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    details = (
        {"type": type(exc).__name__, "trace": traceback.format_exc()}
        if DEBUG_MODE
        else {"type": type(exc).__name__}
    )
    payload = error_response(
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details=details,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload.model_dump(),
    )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        log_level="debug" if DEBUG_MODE else "info",
        access_log=True,
    )
