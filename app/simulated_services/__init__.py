"""Servizi REST locali usati per simulare gli effetti delle azioni approvate."""

from app.simulated_services.main import app, create_simulated_services_app

__all__ = ["app", "create_simulated_services_app"]
