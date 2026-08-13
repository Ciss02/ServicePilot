"""Verifiche delle regole di catalogo e appartenenza."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import (
    Site,
    SupportGroupMembership,
    Ticket,
    User,
    build_engine,
    create_database,
)
from app.domain.ticket_contracts import TicketUpdate
from app.domain.vocabulary import Role
from app.support_groups import (
    DuplicateSupportGroupError,
    InvalidSupportGroupMemberError,
    active_support_group_names,
    create_support_group,
    replace_support_group_members,
    set_support_group_active,
    support_group_members_by_group,
    update_support_group,
)
from app.tickets.management import (
    ManagedSupportGroupUnavailableError,
    update_managed_ticket,
)


@pytest.fixture
def group_database(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'support-groups.db'}")
    create_database(engine)
    yield engine
    engine.dispose()


def _users(session: Session) -> tuple[User, User, User]:
    technician = User(
        email="tecnico.gruppi@servicepilot.example",
        display_name="Tecnico Gruppi Demo",
        role=Role.TECHNICIAN,
    )
    admin = User(
        email="admin.gruppi@servicepilot.example",
        display_name="Admin Gruppi Demo",
        role=Role.ADMIN,
    )
    employee = User(
        email="dipendente.gruppi@servicepilot.example",
        display_name="Dipendente Gruppi Demo",
        role=Role.EMPLOYEE,
    )
    session.add_all([technician, admin, employee])
    session.flush()
    return technician, admin, employee


def test_technical_user_can_belong_to_multiple_groups(group_database) -> None:
    with Session(group_database) as session:
        technician, admin, _ = _users(session)
        network = create_support_group(
            session,
            name="Supporto rete",
            description="Connettività della demo.",
        )
        workplace = create_support_group(
            session,
            name="Supporto workplace",
            description="Postazioni della demo.",
        )

        replace_support_group_members(session, network.id, [technician.id, admin.id])
        replace_support_group_members(session, workplace.id, [technician.id])

        members = support_group_members_by_group(session)
        assert {user.id for user in members[network.id]} == {technician.id, admin.id}
        assert {user.id for user in members[workplace.id]} == {technician.id}
        assert session.scalar(select(func.count()).select_from(SupportGroupMembership)) == 3


def test_group_name_is_unique_ignoring_case_and_spacing(group_database) -> None:
    with Session(group_database) as session:
        create_support_group(
            session,
            name="Supporto rete",
            description="Connettività della demo.",
        )

        with pytest.raises(DuplicateSupportGroupError):
            create_support_group(
                session,
                name="  SUPPORTO   RETE ",
                description="Altro gruppo fittizio.",
            )


def test_employee_cannot_become_group_member(group_database) -> None:
    with Session(group_database) as session:
        _, _, employee = _users(session)
        group = create_support_group(
            session,
            name="Service desk",
            description="Primo contatto della demo.",
        )

        with pytest.raises(InvalidSupportGroupMemberError):
            replace_support_group_members(session, group.id, [employee.id])

        assert session.scalar(select(func.count()).select_from(SupportGroupMembership)) == 0


def test_inactive_group_keeps_ticket_history_but_cannot_be_new_assignment(
    group_database,
) -> None:
    with Session(group_database) as session:
        technician, admin, employee = _users(session)
        site = Site(code="GROUP-DEMO", name="Sede gruppi demo")
        session.add(site)
        group = create_support_group(
            session,
            name="Supporto storico",
            description="Gruppo usato per verificare lo storico.",
        )
        session.add(
            Ticket(
                title="Ticket con gruppo storico",
                description="Ticket fittizio per verificare la disattivazione del gruppo.",
                requester_id=employee.id,
                site_id=site.id,
                service="Servizio demo",
                affected_users=1,
                assigned_group=group.name,
            )
        )
        session.commit()
        ticket = session.scalar(select(Ticket))

        set_support_group_active(session, group.id, is_active=False)
        update_support_group(
            session,
            group.id,
            name="Supporto rinominato",
            description="Gruppo storico rinominato nella demo.",
        )

        assert ticket.assigned_group == "Supporto storico"
        assert "Supporto rinominato" not in active_support_group_names(session)
        with pytest.raises(ManagedSupportGroupUnavailableError):
            update_managed_ticket(
                session,
                ticket.id,
                TicketUpdate(assigned_group="Supporto rinominato"),
                updated_by=technician,
            )

        unchanged = update_managed_ticket(
            session,
            ticket.id,
            TicketUpdate(assigned_group="Supporto storico"),
            updated_by=admin,
        )
        assert unchanged.assigned_group == "Supporto storico"
