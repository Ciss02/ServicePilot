"""Verifiche della struttura iniziale del database."""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import Site, Ticket, User, build_engine, create_database
from app.domain.vocabulary import Role, TicketStatus


@pytest.fixture
def database_engine(tmp_path):
    """Usa un file SQLite temporaneo, isolato dai dati locali."""

    engine = build_engine(f"sqlite:///{tmp_path / 'servicepilot-test.db'}")
    yield engine
    engine.dispose()


def test_database_creation_is_repeatable(database_engine) -> None:
    create_database(database_engine)
    create_database(database_engine)

    assert set(inspect(database_engine).get_table_names()) == {
        "sites",
        "tickets",
        "users",
    }


def test_initial_records_can_be_saved(database_engine) -> None:
    create_database(database_engine)

    with Session(database_engine) as session:
        requester = User(
            email="dipendente@example.test",
            display_name="Dipendente Demo",
            role=Role.EMPLOYEE,
        )
        site = Site(code="HQ", name="Sede centrale demo")
        session.add_all([requester, site])
        session.flush()

        ticket = Ticket(
            title="Accesso VPN non disponibile",
            description="Il collegamento VPN demo non completa la connessione.",
            requester_id=requester.id,
            site_id=site.id,
            service="VPN",
            affected_users=1,
        )
        session.add(ticket)
        session.commit()
        session.refresh(ticket)

        assert ticket.id is not None
        assert ticket.status is TicketStatus.NEW
        assert ticket.category is None

    with database_engine.connect() as connection:
        stored_codes = connection.execute(
            text(
                "SELECT users.role, tickets.status "
                "FROM tickets JOIN users ON users.id = tickets.requester_id"
            )
        ).one()

    assert stored_codes == ("employee", "new")


def test_ticket_rejects_unknown_requester(database_engine) -> None:
    create_database(database_engine)

    with Session(database_engine) as session:
        site = Site(code="STORE-01", name="Punto vendita demo")
        session.add(site)
        session.flush()
        session.add(
            Ticket(
                title="Stampante etichette non disponibile",
                description="La stampante demo non risponde al comando di stampa.",
                requester_id=999,
                site_id=site.id,
                service="Stampa etichette",
                affected_users=2,
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()

