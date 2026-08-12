"""API essenziali per creare, leggere e gestire i ticket."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.ai import TicketClassificationPersistenceError, classify_confirmed_ticket
from app.ai.dependencies import AIModelDependency
from app.api.dependencies import CurrentUser, TechnicalUser
from app.db.models import Ticket
from app.db.session import get_session
from app.domain.ticket_contracts import TicketCreate, TicketRead, TicketUpdate
from app.tickets.creation import (
    TicketPersistenceError,
    TicketSiteNotFoundError,
    create_confirmed_ticket,
)
from app.tickets.management import (
    ClassificationReviewRequiredError,
    InvalidStatusTransitionError,
    ManagedSiteNotFoundError,
    ManagedTechnicianNotFoundError,
    ManagedTechnicianUnavailableError,
    ManagedTicketNotFoundError,
    ResolutionRequiredError,
    TicketUpdatePersistenceError,
    update_managed_ticket,
)
from app.tickets.queries import get_visible_ticket, list_visible_tickets

router = APIRouter(prefix="/tickets", tags=["ticket"])
DatabaseSession = Annotated[Session, Depends(get_session)]
TicketId = Annotated[int, Path(gt=0, description="Identificativo positivo del ticket")]


@router.post(
    "",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un ticket confermato",
)
def create_ticket(
    payload: TicketCreate,
    session: DatabaseSession,
    current_user: CurrentUser,
    ai_model: AIModelDependency,
) -> Ticket:
    """Salva una richiesta confermata per l'utente autenticato."""

    try:
        ticket = create_confirmed_ticket(session, payload, current_user)
    except TicketSiteNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sede {payload.site_id} non trovata",
        ) from error
    except TicketPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Il ticket non può essere salvato con i riferimenti forniti",
        ) from error

    try:
        return classify_confirmed_ticket(session, ticket, ai_model=ai_model)
    except TicketClassificationPersistenceError:
        return ticket


@router.get(
    "",
    response_model=list[TicketRead],
    summary="Elenca i ticket",
)
def list_tickets(
    session: DatabaseSession,
    current_user: CurrentUser,
) -> list[Ticket]:
    """Restituisce tutti i ticket, dal più recente."""

    return list_visible_tickets(session, current_user)


@router.get(
    "/{ticket_id}",
    response_model=TicketRead,
    summary="Legge un ticket",
)
def get_ticket(
    ticket_id: TicketId,
    session: DatabaseSession,
    current_user: CurrentUser,
) -> Ticket:
    """Restituisce il ticket richiesto o un errore chiaro."""

    ticket = get_visible_ticket(session, current_user, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} non trovato",
        )
    return ticket


@router.patch(
    "/{ticket_id}",
    response_model=TicketRead,
    summary="Aggiorna la gestione tecnica di un ticket",
)
def update_ticket(
    ticket_id: TicketId,
    payload: TicketUpdate,
    session: DatabaseSession,
    technical_user: TechnicalUser,
) -> Ticket:
    """Modifica soltanto i campi tecnici validati e salva tutto insieme."""

    try:
        return update_managed_ticket(
            session,
            ticket_id,
            payload,
            updated_by=technical_user,
        )
    except ManagedTicketNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} non trovato",
        )
    except ManagedSiteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sede {payload.site_id} non trovata",
        )
    except ManagedTechnicianNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tecnico {payload.assigned_technician_id} non trovato",
        )
    except ManagedTechnicianUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Il ticket può essere assegnato soltanto a un tecnico attivo",
        )
    except InvalidStatusTransitionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(f"Transizione da {error.current.value} a {error.target.value} non consentita"),
        )
    except ResolutionRequiredError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Per risolvere o chiudere il ticket è necessaria una soluzione",
        )
    except ClassificationReviewRequiredError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Completa la classificazione prima di confermare la revisione",
        )
    except TicketUpdatePersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Il ticket non può essere aggiornato con i riferimenti forniti",
        ) from error
