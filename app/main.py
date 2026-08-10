"""Punto di ingresso dell'applicazione web ServicePilot AI."""

from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.tickets import router as tickets_router
from app.db.session import create_database


def create_app(database_initializer: Callable[[], None] = create_database) -> FastAPI:
    """Costruisce l'app e permette ai test di usare un database isolato."""

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        database_initializer()
        yield

    application = FastAPI(
        title="ServicePilot AI",
        description="Portale dimostrativo per la gestione intelligente dei ticket IT.",
        version="0.1.0",
        lifespan=lifespan,
    )
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
