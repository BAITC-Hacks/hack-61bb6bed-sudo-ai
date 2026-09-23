import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException

from app.api.auth import router as auth_router
from app.api.routes import router
from app.api.teams import router as teams_router
from app.application.service import ChallengeService
from app.core.config import Settings
from app.core.logging import configure_logging
from app.domain.entities import DomainError
from app.infrastructure.accounts import Accounts
from app.infrastructure.ai import OpenAIAnalyzer
from app.infrastructure.db.session import PostgresUnitOfWork, create_database
from app.infrastructure.teams import TeamManagement

logger = logging.getLogger(__name__)


def error_response(code: str, message: str, status: int, **extra):
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message, **extra}}
    )


def create_app(settings: Settings | None = None, analyzer=None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging()
        engine, factory = create_database(settings.database_url)
        key = settings.openai_api_key.get_secret_value()
        client = (
            AsyncOpenAI(api_key=key, timeout=settings.ai_timeout_seconds, max_retries=1)
            if key
            else None
        )
        app.state.settings = settings
        app.state.engine = engine
        app.state.accounts = Accounts(factory, settings.session_days)
        app.state.teams = TeamManagement(factory, settings.frontend_url)
        app.state.uow = lambda: PostgresUnitOfWork(factory)
        app.state.service = ChallengeService(
            app.state.uow,
            analyzer or OpenAIAnalyzer(client, settings.openai_model, settings.ai_timeout_seconds),
        )
        try:
            yield
        finally:
            if client:
                await client.close()
            await engine.dispose()

    app = FastAPI(title="SanaChallenge AI", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-Demo-User", "X-CSRF-Token"],
    )

    @app.middleware("http")
    async def browser_security(request: Request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            allowed = {settings.frontend_url.rstrip("/"), str(request.base_url).rstrip("/")}
            if (origin and origin not in allowed) or request.headers.get(
                "sec-fetch-site"
            ) == "cross-site":
                return error_response("origin_forbidden", "Источник запроса не разрешён.", 403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        response = error_response(exc.code, exc.message, exc.status)
        if exc.code == "session_expired":
            response.delete_cookie("sana_session", path="/")
            response.delete_cookie("sana_csrf", path="/")
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        details = [{"location": list(item["loc"]), "message": item["msg"]} for item in exc.errors()]
        return error_response(
            "validation_error", "Проверьте параметры запроса.", 422, details=details
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return error_response("http_error", str(exc.detail), exc.status_code)

    @app.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc: IntegrityError):
        logger.warning("database_conflict", extra={"error_type": type(exc).__name__})
        return error_response("conflict", "Операция конфликтует с существующими данными.", 409)

    @app.exception_handler(OSError)
    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError | OSError):
        logger.error("database_error", extra={"error_type": type(exc).__name__})
        return error_response("database_unavailable", "База данных временно недоступна.", 503)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error("request_failed", extra={"error_type": type(exc).__name__})
        return error_response("internal_error", "Внутренняя ошибка сервера.", 500)

    app.include_router(router)
    app.include_router(auth_router)
    app.include_router(teams_router)
    return app


app = create_app()
