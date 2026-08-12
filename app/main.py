"""Punto di ingresso dell'applicazione web ServicePilot AI."""

from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.auth import router as auth_router
from app.api.tickets import router as tickets_router
from app.db.session import create_database
from app.security.configuration import load_security_settings
from app.security.middleware import BrowserSecurityMiddleware
from app.web.routes import router as web_router

STATIC_DIRECTORY = Path(__file__).resolve().parent / "static"


def create_app(database_initializer: Callable[[], None] = create_database) -> FastAPI:
    """Costruisce l'app e permette ai test di usare un database isolato."""

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        database_initializer()
        yield

    security_settings = load_security_settings()
    application = FastAPI(
        title="ServicePilot AI",
        description="Portale dimostrativo per la gestione intelligente dei ticket IT.",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        BrowserSecurityMiddleware,
        enable_hsts=security_settings.secure_cookies,
        login_attempts_per_minute=security_settings.login_attempts_per_minute,
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(security_settings.allowed_hosts),
        www_redirect=False,
    )
    application.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="static")
    application.include_router(web_router)
    application.include_router(auth_router)
    application.include_router(tickets_router)

    @application.get(
        "/health",
        tags=["sistema"],
        summary="Verifica che il servizio sia disponibile",
    )
    def health_check() -> dict[str, str]:
        """Restituisce uno stato minimo senza consultare servizi esterni."""

        return {"status": "ok"}

    return application


app = create_app()
