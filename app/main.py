"""Punto di ingresso dell'applicazione web ServicePilot AI."""

from fastapi import FastAPI


app = FastAPI(
    title="ServicePilot AI",
    description="Portale dimostrativo per la gestione intelligente dei ticket IT.",
    version="0.1.0",
)


@app.get(
    "/health",
    tags=["sistema"],
    summary="Verifica che il servizio sia disponibile",
)
def health_check() -> dict[str, str]:
    """Restituisce uno stato minimo senza consultare servizi esterni."""

    return {"status": "ok"}
