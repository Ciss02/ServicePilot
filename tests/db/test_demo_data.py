"""Verifiche del dataset dimostrativo ripetibile."""

import secrets

import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.db import (
    AuditEvent,
    ProposedAction,
    Site,
    Ticket,
    User,
    build_engine,
    create_database,
    load_demo_data,
)
from app.domain.priority import calculate_priority
from app.domain.vocabulary import (
    ActionStatus,
    ActionType,
    ClassificationReviewStatus,
    Priority,
    Role,
)
from app.security.demo_credentials import (
    DEMO_PASSWORD_ENV_BY_ROLE,
    DemoCredentialsError,
)
from app.security.passwords import verify_password


@pytest.fixture
def database_engine(tmp_path):
    """Crea un database temporaneo per ogni verifica."""

    engine = build_engine(f"sqlite:///{tmp_path / 'demo-data-test.db'}")
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def demo_passwords(monkeypatch) -> dict[Role, str]:
    """Configura credenziali casuali che non vengono salvate nel repository."""

    passwords = {role: secrets.token_urlsafe(24) for role in DEMO_PASSWORD_ENV_BY_ROLE}
    for role, variable_name in DEMO_PASSWORD_ENV_BY_ROLE.items():
        monkeypatch.setenv(variable_name, passwords[role])
    return passwords


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
        assert session.scalar(select(func.count()).select_from(ProposedAction)) == 3
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 9
        event_keys = list(session.scalars(select(AuditEvent.event_key)).all())
        assert len(event_keys) == len(set(event_keys))


def test_missing_credentials_stop_before_database_changes(
    database_engine,
    monkeypatch,
) -> None:
    for variable_name in DEMO_PASSWORD_ENV_BY_ROLE.values():
        monkeypatch.delenv(variable_name, raising=False)

    with pytest.raises(DemoCredentialsError):
        load_demo_data(database_engine)

    assert inspect(database_engine).get_table_names() == []


def test_demo_users_store_only_verifiable_hashes(
    database_engine,
    demo_passwords: dict[Role, str],
) -> None:
    load_demo_data(database_engine)

    with Session(database_engine) as session:
        users = session.scalars(select(User)).all()
        hashes = [user.password_hash for user in users]

    assert len(users) == 5
    assert all(encoded_hash is not None for encoded_hash in hashes)
    assert all(verify_password(demo_passwords[user.role], user.password_hash) for user in users)
    assert all(
        password not in encoded_hash
        for password in demo_passwords.values()
        for encoded_hash in hashes
        if encoded_hash is not None
    )


def test_reload_keeps_valid_password_hashes(database_engine) -> None:
    load_demo_data(database_engine)
    with Session(database_engine) as session:
        first_hashes = {user.email: user.password_hash for user in session.scalars(select(User))}

    load_demo_data(database_engine)
    with Session(database_engine) as session:
        second_hashes = {user.email: user.password_hash for user in session.scalars(select(User))}

    assert second_hashes == first_hashes


def test_reload_restores_expected_demo_values(database_engine) -> None:
    load_demo_data(database_engine)

    with Session(database_engine) as session:
        site = session.scalar(select(Site).where(Site.code == "HQ-DEMO"))
        ticket = session.scalar(
            select(Ticket).where(Ticket.title == "[DEMO] Linea produttiva non raggiungibile")
        )
        assert site is not None
        assert ticket is not None
        site.name = "Valore modificato"
        ticket.priority = Priority.P4
        action = session.scalar(select(ProposedAction).limit(1))
        action.status = ActionStatus.REJECTED
        session.commit()

    load_demo_data(database_engine)

    with Session(database_engine) as session:
        site = session.scalar(select(Site).where(Site.code == "HQ-DEMO"))
        ticket = session.scalar(
            select(Ticket).where(Ticket.title == "[DEMO] Linea produttiva non raggiungibile")
        )
        assert site is not None
        assert ticket is not None
        assert site.name == "Sede centrale Polaris Demo"
        assert ticket.priority is Priority.P1
        action = session.scalar(select(ProposedAction).limit(1))
        assert action.status is ActionStatus.PENDING_APPROVAL
        assert action.reviewed_by_user_id is None


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
        tickets = session.scalars(select(Ticket).where(Ticket.title.startswith("[DEMO]"))).all()

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
        assert all(
            ticket.classification_review_status is ClassificationReviewStatus.HUMAN_REVIEWED
            for ticket in tickets
        )
        actions = session.scalars(select(ProposedAction)).all()
        assert len(actions) == 3
        assert {action.action_type for action in actions} == set(ActionType)
        assert all(action.status is ActionStatus.PENDING_APPROVAL for action in actions)
