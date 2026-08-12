"""Dataset sintetico e caricamento ripetibile per la demo."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.db.models import AuditEvent, ProposedAction, Site, Ticket, User
from app.db.session import create_database, engine
from app.domain.priority import calculate_priority
from app.domain.vocabulary import (
    ActionStatus,
    ActionType,
    ClassificationReviewStatus,
    Impact,
    Role,
    TicketCategory,
    TicketStatus,
    Urgency,
)
from app.security.demo_credentials import load_demo_passwords, validate_demo_passwords
from app.security.passwords import hash_password, verify_password


@dataclass(frozen=True)
class SiteSeed:
    """Dati stabili di una sede dimostrativa."""

    code: str
    name: str


@dataclass(frozen=True)
class UserSeed:
    """Account dimostrativo collegato a una credenziale configurata per ruolo."""

    email: str
    display_name: str
    role: Role


@dataclass(frozen=True)
class TicketSeed:
    """Scenario dimostrativo collegato a sedi e profili fittizi."""

    title: str
    description: str
    requester_email: str
    site_code: str
    service: str
    affected_users: int
    category: TicketCategory
    subcategory: str
    impact: Impact
    urgency: Urgency
    assigned_group: str
    status: TicketStatus
    assigned_technician_email: str | None = None
    technician_note: str | None = None
    resolution: str | None = None


@dataclass(frozen=True)
class ActionSeed:
    """Proposta completamente fittizia collegata a uno scenario demo."""

    ticket_title: str
    action_type: ActionType
    rationale: str
    payload: dict[str, object]
    expected_effect: str


@dataclass(frozen=True)
class SeedSummary:
    """Numero di record previsti dal dataset demo."""

    sites: int
    users: int
    tickets: int


DEMO_SITES = (
    SiteSeed("HQ-DEMO", "Sede centrale Polaris Demo"),
    SiteSeed("PLANT-DEMO", "Stabilimento Vega Demo"),
    SiteSeed("WAREHOUSE-DEMO", "Magazzino Orione Demo"),
    SiteSeed("STORE-NORTH-DEMO", "Punto vendita Aurora Demo"),
    SiteSeed("STORE-CENTER-DEMO", "Punto vendita Zenith Demo"),
    SiteSeed("STORE-SOUTH-DEMO", "Punto vendita Nova Demo"),
)

DEMO_USERS = (
    UserSeed(
        "dipendente.hq@servicepilot.example",
        "Dipendente Sede Demo",
        Role.EMPLOYEE,
    ),
    UserSeed(
        "dipendente.plant@servicepilot.example",
        "Dipendente Stabilimento Demo",
        Role.EMPLOYEE,
    ),
    UserSeed(
        "dipendente.store@servicepilot.example",
        "Dipendente Negozio Demo",
        Role.EMPLOYEE,
    ),
    UserSeed(
        "tecnico@servicepilot.example",
        "Tecnico IT Demo",
        Role.TECHNICIAN,
    ),
    UserSeed(
        "admin@servicepilot.example",
        "Amministratore Demo",
        Role.ADMIN,
    ),
)

DEMO_TICKETS = (
    TicketSeed(
        title="[DEMO] Linea produttiva non raggiungibile",
        description=("Le postazioni demo della linea non comunicano con il sistema di controllo."),
        requester_email="dipendente.plant@servicepilot.example",
        site_code="PLANT-DEMO",
        service="Controllo produzione",
        affected_users=24,
        category=TicketCategory.PRODUCTION_SYSTEMS,
        subcategory="Connettività linea",
        impact=Impact.HIGH,
        urgency=Urgency.HIGH,
        assigned_group="Supporto sistemi produttivi",
        assigned_technician_email="tecnico@servicepilot.example",
        status=TicketStatus.IN_PROGRESS,
        technician_note="Scenario demo: analisi della connettività in corso.",
    ),
    TicketSeed(
        title="[DEMO] Connettività assente nel punto vendita",
        description=(
            "Le casse demo e le postazioni del negozio non raggiungono i servizi centrali."
        ),
        requester_email="dipendente.store@servicepilot.example",
        site_code="STORE-NORTH-DEMO",
        service="Rete punto vendita",
        affected_users=12,
        category=TicketCategory.NETWORK_AND_CONNECTIVITY,
        subcategory="Connettività sede",
        impact=Impact.HIGH,
        urgency=Urgency.MEDIUM,
        assigned_group="Supporto rete",
        status=TicketStatus.NEW,
    ),
    TicketSeed(
        title="[DEMO] Accesso VPN intermittente",
        description=("La connessione VPN demo si interrompe durante il lavoro da remoto."),
        requester_email="dipendente.hq@servicepilot.example",
        site_code="HQ-DEMO",
        service="Accesso remoto",
        affected_users=1,
        category=TicketCategory.NETWORK_AND_CONNECTIVITY,
        subcategory="VPN",
        impact=Impact.MEDIUM,
        urgency=Urgency.MEDIUM,
        assigned_group="Supporto workplace",
        assigned_technician_email="tecnico@servicepilot.example",
        status=TicketStatus.WAITING_FOR_REQUESTER,
        technician_note="Richiesto un orario demo in cui riprodurre il problema.",
    ),
    TicketSeed(
        title="[DEMO] Richiesta installazione software",
        description=("Serve installare uno strumento grafico fittizio sulla postazione demo."),
        requester_email="dipendente.hq@servicepilot.example",
        site_code="HQ-DEMO",
        service="Gestione software",
        affected_users=1,
        category=TicketCategory.SOFTWARE_AND_APPLICATIONS,
        subcategory="Installazione software",
        impact=Impact.LOW,
        urgency=Urgency.LOW,
        assigned_group="Supporto workplace",
        status=TicketStatus.NEW,
    ),
    TicketSeed(
        title="[DEMO] Stampante etichette bloccata",
        description=("La stampante Zebra dimostrativa del magazzino non completa le etichette."),
        requester_email="dipendente.plant@servicepilot.example",
        site_code="WAREHOUSE-DEMO",
        service="Stampa etichette",
        affected_users=6,
        category=TicketCategory.PRINTERS_AND_LABELING,
        subcategory="Stampante Zebra",
        impact=Impact.MEDIUM,
        urgency=Urgency.HIGH,
        assigned_group="Supporto magazzino",
        assigned_technician_email="tecnico@servicepilot.example",
        status=TicketStatus.RESOLVED,
        technician_note="Scenario demo: coda di stampa verificata.",
        resolution="Coda demo ripulita e servizio di stampa riavviato.",
    ),
    TicketSeed(
        title="[DEMO] Possibile messaggio di phishing",
        description=(
            "Un account demo ha ricevuto un messaggio sospetto con un collegamento esterno."
        ),
        requester_email="dipendente.store@servicepilot.example",
        site_code="STORE-SOUTH-DEMO",
        service="Sicurezza posta elettronica",
        affected_users=1,
        category=TicketCategory.INFORMATION_SECURITY,
        subcategory="Phishing",
        impact=Impact.LOW,
        urgency=Urgency.HIGH,
        assigned_group="Sicurezza IT",
        assigned_technician_email="admin@servicepilot.example",
        status=TicketStatus.IN_PROGRESS,
        technician_note="Scenario demo: messaggio isolato per l'analisi.",
    ),
)

DEMO_ACTIONS = (
    ActionSeed(
        ticket_title="[DEMO] Linea produttiva non raggiungibile",
        action_type=ActionType.ASSIGN_TICKET,
        rationale=("Il problema coinvolge la connettività dello scenario produttivo demo."),
        payload={
            "assigned_group": "Supporto sistemi produttivi",
            "assigned_technician_id": None,
        },
        expected_effect=(
            "Registrare l'assegnazione demo al gruppo specializzato nella produzione."
        ),
    ),
    ActionSeed(
        ticket_title="[DEMO] Linea produttiva non raggiungibile",
        action_type=ActionType.NOTIFY_REQUESTER,
        rationale=("Il richiedente deve sapere che la verifica tecnica demo è stata avviata."),
        payload={
            "message": (
                "Abbiamo avviato la verifica della connettività della linea demo. "
                "Ti aggiorneremo al termine dei controlli."
            )
        },
        expected_effect=("Registrare una comunicazione demo chiara e visibile al richiedente."),
    ),
    ActionSeed(
        ticket_title="[DEMO] Linea produttiva non raggiungibile",
        action_type=ActionType.ESCALATE_VENDOR,
        rationale=("La procedura demo prevede il coinvolgimento del partner della linea."),
        payload={
            "vendor_name": "Automazione Partner Demo",
            "summary": ("Verificare la connettività fittizia tra controllo linea e rete demo."),
        },
        expected_effect=("Aprire un riferimento demo presso il fornitore senza contatti reali."),
    ),
)


def _upsert_sites(session: Session) -> dict[str, Site]:
    sites_by_code: dict[str, Site] = {}

    for seed in DEMO_SITES:
        site = session.scalar(select(Site).where(Site.code == seed.code))
        if site is None:
            site = Site(code=seed.code, name=seed.name)
            session.add(site)
        else:
            site.name = seed.name
            site.is_active = True
        sites_by_code[seed.code] = site

    session.flush()
    return sites_by_code


def _upsert_users(
    session: Session,
    demo_passwords: Mapping[Role, str],
) -> dict[str, User]:
    users_by_email: dict[str, User] = {}

    for seed in DEMO_USERS:
        user = session.scalar(select(User).where(User.email == seed.email))
        if user is None:
            user = User(
                email=seed.email,
                display_name=seed.display_name,
                role=seed.role,
            )
            session.add(user)
        else:
            user.display_name = seed.display_name
            user.role = seed.role
            user.is_active = True
        password = demo_passwords[seed.role]
        if not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
        users_by_email[seed.email] = user

    session.flush()
    return users_by_email


def _upsert_tickets(
    session: Session,
    sites_by_code: dict[str, Site],
    users_by_email: dict[str, User],
) -> dict[str, Ticket]:
    tickets_by_title: dict[str, Ticket] = {}
    for seed in DEMO_TICKETS:
        ticket = session.scalar(select(Ticket).where(Ticket.title == seed.title))
        requester = users_by_email[seed.requester_email]
        site = sites_by_code[seed.site_code]
        assigned_technician = (
            users_by_email[seed.assigned_technician_email]
            if seed.assigned_technician_email
            else None
        )
        values = {
            "description": seed.description,
            "requester_id": requester.id,
            "site_id": site.id,
            "service": seed.service,
            "affected_users": seed.affected_users,
            "category": seed.category,
            "subcategory": seed.subcategory,
            "impact": seed.impact,
            "urgency": seed.urgency,
            "priority": calculate_priority(seed.impact, seed.urgency),
            "assigned_group": seed.assigned_group,
            "classification_review_status": ClassificationReviewStatus.HUMAN_REVIEWED,
            "assigned_technician_id": (assigned_technician.id if assigned_technician else None),
            "status": seed.status,
            "technician_note": seed.technician_note,
            "resolution": seed.resolution,
        }

        if ticket is None:
            ticket = Ticket(title=seed.title, **values)
            session.add(ticket)
        else:
            for field_name, value in values.items():
                setattr(ticket, field_name, value)
        tickets_by_title[seed.title] = ticket
    session.flush()
    return tickets_by_title


def _upsert_actions(
    session: Session,
    tickets_by_title: dict[str, Ticket],
) -> list[ProposedAction]:
    actions: list[ProposedAction] = []
    for seed in DEMO_ACTIONS:
        ticket = tickets_by_title[seed.ticket_title]
        action = session.scalar(
            select(ProposedAction).where(
                ProposedAction.ticket_id == ticket.id,
                ProposedAction.action_type == seed.action_type,
                ProposedAction.rationale == seed.rationale,
            )
        )
        values = {
            "ticket_id": ticket.id,
            "action_type": seed.action_type,
            "rationale": seed.rationale,
            "payload_json": json.dumps(
                seed.payload,
                ensure_ascii=False,
                sort_keys=True,
            ),
            "expected_effect": seed.expected_effect,
            "status": ActionStatus.PENDING_APPROVAL,
            "reviewed_by_user_id": None,
            "decided_at": None,
            "execution_reference": None,
            "execution_message": None,
            "execution_error_code": None,
        }
        if action is None:
            action = ProposedAction(**values)
            session.add(action)
        else:
            for field_name, value in values.items():
                setattr(action, field_name, value)
        actions.append(action)
    session.flush()
    return actions


def _seed_audit_events(
    session: Session,
    tickets_by_title: dict[str, Ticket],
    actions: list[ProposedAction],
    users_by_email: dict[str, User],
) -> None:
    """Aggiunge un punto di partenza demo senza duplicare eventi esistenti."""

    from app.audit.events import record_action_proposed, record_ticket_created

    existing_keys = set(
        session.scalars(select(AuditEvent.event_key).where(AuditEvent.event_key.is_not(None))).all()
    )
    requester_by_title = {seed.title: users_by_email[seed.requester_email] for seed in DEMO_TICKETS}
    for title, ticket in tickets_by_title.items():
        event_key = f"demo:ticket:{ticket.id}:created"
        if event_key not in existing_keys:
            record_ticket_created(
                session,
                ticket,
                requester_by_title[title],
                event_key=event_key,
                created_at=ticket.created_at,
            )
    tickets_by_id = {ticket.id: ticket for ticket in tickets_by_title.values()}
    for position, action in enumerate(actions, start=1):
        event_key = f"demo:action:{action.id}:proposed"
        if event_key not in existing_keys:
            record_action_proposed(
                session,
                action,
                event_key=event_key,
                created_at=(
                    tickets_by_id[action.ticket_id].created_at + timedelta(seconds=position)
                ),
            )


def seed_demo_data(
    session: Session,
    demo_passwords: Mapping[Role, str],
) -> SeedSummary:
    """Inserisce o riallinea i record demo senza eseguire il commit."""

    sites_by_code = _upsert_sites(session)
    users_by_email = _upsert_users(session, demo_passwords)
    tickets_by_title = _upsert_tickets(session, sites_by_code, users_by_email)
    actions = _upsert_actions(session, tickets_by_title)
    _seed_audit_events(session, tickets_by_title, actions, users_by_email)
    session.flush()

    return SeedSummary(
        sites=len(DEMO_SITES),
        users=len(DEMO_USERS),
        tickets=len(DEMO_TICKETS),
    )


def load_demo_data(
    target_engine: Engine = engine,
    demo_passwords: Mapping[Role, str] | None = None,
) -> SeedSummary:
    """Crea le tabelle e salva l'intero dataset in una singola transazione."""

    passwords = (
        load_demo_passwords() if demo_passwords is None else validate_demo_passwords(demo_passwords)
    )
    create_database(target_engine)
    with Session(target_engine) as session:
        try:
            summary = seed_demo_data(session, passwords)
            session.commit()
        except Exception:
            session.rollback()
            raise
    return summary
