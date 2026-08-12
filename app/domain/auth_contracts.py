"""Contratti validati per l'accesso e l'identita autenticata."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.vocabulary import Role

Email = Annotated[str, Field(min_length=3, max_length=254)]
Password = Annotated[str, Field(min_length=1, max_length=1_024, repr=False)]
Identifier = Annotated[int, Field(strict=True, gt=0)]
DisplayName = Annotated[str, Field(min_length=1, max_length=120)]


class _AuthContract(BaseModel):
    """Impostazioni comuni ai dati di autenticazione."""

    model_config = ConfigDict(extra="forbid")


class LoginRequest(_AuthContract):
    """Credenziali ricevute dal modulo di accesso."""

    email: Email
    password: Password

    @field_validator("email")
    @classmethod
    def normalize_email(cls, email: str) -> str:
        """Normalizza il confronto senza introdurre una registrazione pubblica."""

        local_part, separator, domain = email.strip().casefold().partition("@")
        if not separator or not local_part or not domain or "." not in domain:
            raise ValueError("email non valida")
        return f"{local_part}@{domain}"


class AuthenticatedUser(_AuthContract):
    """Identita sicura restituita al browser, senza dati riservati."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    id: Identifier
    email: Email
    display_name: DisplayName
    role: Role
