"""Verifiche del dataset dimostrativo ripetibile."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import Site, Ticket, User, build_engine, create_database, load_demo_data
from app.domain.priority import calculate_priority
from app.domain.vocabulary import Priority, Role


@pytest.fixture
def database_engine(tmp_path):
    """Crea un database temporaneo per ogni verifica."""

    engine = build_engine(f"sqlite:///{tmp_path / 'demo-data-test.db'}")
    yield engine
    engine.dispose()


def _count(session: Session, model: type[Site] | type[User] | type[Ticket]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_demo_data_load_is_repeatable(database_engine) -> None:
    first_summary = load_demo_data(database_engine)
    second_summary = load_demo_data(database_engine)

    assert first_summary == second_summary
    assert (second_summary.sites, second_summary.users, second_summary.tickets) == (
        6,
        5,
        6,
    )

    with Session(database_engine) as session:
        assert _count(session, Site) == 6
        assert _count(session, User) == 5
        assert _count(session, Ticket) == 6


def test_reload_restores_expected_demo_values(database_engine) -> None:
    load_demo_data(database_engine)

    with Session(database_engine) as session:
        site = session.scalar(select(Site).where(Site.code == "HQ-DEMO"))
        ticket = session.scalar(
            select(Ticket).where(
                Ticket.title == "[DEMO] Linea produttiva non raggiungibile"
            )
        )
        assert site is not None
        assert ticket is not None
        site.name = "Valore modificato"
        ticket.priority = Priority.P4
        session.commit()

    load_demo_data(database_engine)

    with Session(database_engine) as session:
        site = session.scalar(select(Site).where(Site.code == "HQ-DEMO"))
        ticket = session.scalar(
            select(Ticket).where(
                Ticket.title == "[DEMO] Linea produttiva non raggiungibile"
            )
        )
        assert site is not None
        assert ticket is not None
        assert site.name == "Sede centrale Polaris Demo"
        assert ticket.priority is Priority.P1


def test_load_preserves_records_outside_demo_dataset(database_engine) -> None:
    create_database(database_engine)
    with Session(database_engine) as session:
        session.add(Site(code="LOCAL", name="Sede locale non demo"))
        session.commit()

    load_demo_data(database_engine)
    load_demo_data(database_engine)

    with Session(database_engine) as session:
        local_site = session.scalar(select(Site).where(Site.code == "LOCAL"))
        assert local_site is not None
        assert local_site.name == "Sede locale non demo"
        assert _count(session, Site) == 7


def test_demo_records_are_synthetic_and_coherent(database_engine) -> None:
    load_demo_data(database_engine)

    with Session(database_engine) as session:
        sites = session.scalars(select(Site).where(Site.code.endswith("-DEMO"))).all()
        users = session.scalars(
            select(User).where(User.email.endswith("@servicepilot.example"))
        ).all()
        tickets = session.scalars(
            select(Ticket).where(Ticket.title.startswith("[DEMO]"))
        ).all()

        assert len(sites) == 6
        assert all(site.name.endswith("Demo") for site in sites)
        assert len(users) == 5
        assert {user.role for user in users} == {
            Role.EMPLOYEE,
            Role.TECHNICIAN,
            Role.ADMIN,
        }
        assert len(tickets) == 6
        assert all(ticket.impact is not None for ticket in tickets)
        assert all(ticket.urgency is not None for ticket in tickets)
        assert all(
            ticket.priority == calculate_priority(ticket.impact, ticket.urgency)
            for ticket in tickets
        )
