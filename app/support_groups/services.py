"""Regole condivise per catalogo e appartenenze dei gruppi di supporto."""

from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import SupportGroup, SupportGroupMembership, User
from app.domain.vocabulary import Role


class SupportGroupError(RuntimeError):
    """Errore atteso nella gestione dei gruppi."""


class SupportGroupNotFoundError(SupportGroupError):
    """Il gruppo richiesto non esiste."""


class DuplicateSupportGroupError(SupportGroupError):
    """Il nome normalizzato appartiene già a un altro gruppo."""


class InvalidSupportGroupDataError(SupportGroupError):
    """Nome o descrizione non rispettano il contratto."""


class InvalidSupportGroupMemberError(SupportGroupError):
    """Una persona selezionata non può appartenere al supporto tecnico."""


class SupportGroupPersistenceError(SupportGroupError):
    """Il database non ha salvato l'operazione richiesta."""


def normalize_support_group_name(value: str) -> tuple[str, str]:
    """Restituisce nome leggibile e chiave stabile per l'unicità."""

    name = " ".join(value.split())
    if not 2 <= len(name) <= 100:
        raise InvalidSupportGroupDataError("Il nome deve contenere da 2 a 100 caratteri.")
    return name, name.casefold()


def normalize_support_group_description(value: str) -> str:
    """Controlla la descrizione mostrata agli amministratori."""

    description = " ".join(value.split())
    if not 2 <= len(description) <= 500:
        raise InvalidSupportGroupDataError("La descrizione deve contenere da 2 a 500 caratteri.")
    return description


def list_support_groups(session: Session) -> list[SupportGroup]:
    return list(session.scalars(select(SupportGroup).order_by(SupportGroup.name)).all())


def list_active_support_groups(session: Session) -> list[SupportGroup]:
    return list(
        session.scalars(
            select(SupportGroup).where(SupportGroup.is_active.is_(True)).order_by(SupportGroup.name)
        ).all()
    )


def active_support_group_names(session: Session) -> list[str]:
    return [group.name for group in list_active_support_groups(session)]


def list_eligible_group_members(session: Session) -> list[User]:
    return list(
        session.scalars(
            select(User)
            .where(
                User.role.in_((Role.TECHNICIAN, Role.ADMIN)),
                User.is_active.is_(True),
            )
            .order_by(User.display_name)
        ).all()
    )


def support_group_members_by_group(session: Session) -> dict[int, list[User]]:
    rows = session.execute(
        select(SupportGroupMembership.support_group_id, User)
        .join(User, User.id == SupportGroupMembership.user_id)
        .order_by(User.display_name)
    ).all()
    members: dict[int, list[User]] = {}
    for group_id, user in rows:
        members.setdefault(group_id, []).append(user)
    return members


def _save(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise SupportGroupPersistenceError from error


def create_support_group(session: Session, *, name: str, description: str) -> SupportGroup:
    clean_name, name_key = normalize_support_group_name(name)
    clean_description = normalize_support_group_description(description)
    if session.scalar(select(SupportGroup.id).where(SupportGroup.name_key == name_key)):
        raise DuplicateSupportGroupError
    group = SupportGroup(
        name=clean_name,
        name_key=name_key,
        description=clean_description,
    )
    session.add(group)
    _save(session)
    session.refresh(group)
    return group


def update_support_group(
    session: Session,
    group_id: int,
    *,
    name: str,
    description: str,
) -> SupportGroup:
    group = session.get(SupportGroup, group_id)
    if group is None:
        raise SupportGroupNotFoundError
    clean_name, name_key = normalize_support_group_name(name)
    clean_description = normalize_support_group_description(description)
    duplicate_id = session.scalar(
        select(SupportGroup.id).where(
            SupportGroup.name_key == name_key,
            SupportGroup.id != group.id,
        )
    )
    if duplicate_id is not None:
        raise DuplicateSupportGroupError
    group.name = clean_name
    group.name_key = name_key
    group.description = clean_description
    _save(session)
    session.refresh(group)
    return group


def set_support_group_active(
    session: Session,
    group_id: int,
    *,
    is_active: bool,
) -> SupportGroup:
    group = session.get(SupportGroup, group_id)
    if group is None:
        raise SupportGroupNotFoundError
    group.is_active = is_active
    _save(session)
    session.refresh(group)
    return group


def replace_support_group_members(
    session: Session,
    group_id: int,
    member_ids: Iterable[int],
) -> SupportGroup:
    group = session.get(SupportGroup, group_id)
    if group is None:
        raise SupportGroupNotFoundError
    unique_ids = set(member_ids)
    users = (
        list(session.scalars(select(User).where(User.id.in_(unique_ids))).all())
        if unique_ids
        else []
    )
    if len(users) != len(unique_ids) or any(
        user.role not in {Role.TECHNICIAN, Role.ADMIN} or not user.is_active for user in users
    ):
        raise InvalidSupportGroupMemberError
    session.execute(
        delete(SupportGroupMembership).where(SupportGroupMembership.support_group_id == group.id)
    )
    session.add_all(
        [
            SupportGroupMembership(support_group_id=group.id, user_id=user_id)
            for user_id in sorted(unique_ids)
        ]
    )
    _save(session)
    session.refresh(group)
    return group


def add_support_group_member(
    session: Session,
    group_id: int,
    user_id: int,
) -> SupportGroup:
    """Aggiunge una sola appartenenza senza riscrivere gli altri membri."""

    group = session.get(SupportGroup, group_id)
    if group is None:
        raise SupportGroupNotFoundError
    user = session.get(User, user_id)
    if user is None or user.role not in {Role.TECHNICIAN, Role.ADMIN} or not user.is_active:
        raise InvalidSupportGroupMemberError
    if session.get(SupportGroupMembership, (group_id, user_id)) is None:
        session.add(SupportGroupMembership(support_group_id=group_id, user_id=user_id))
        _save(session)
        session.refresh(group)
    return group


def remove_support_group_member(
    session: Session,
    group_id: int,
    user_id: int,
) -> SupportGroup:
    """Rimuove una singola appartenenza mantenendo gruppo e account."""

    group = session.get(SupportGroup, group_id)
    if group is None:
        raise SupportGroupNotFoundError
    membership = session.get(SupportGroupMembership, (group_id, user_id))
    if membership is not None:
        session.delete(membership)
        _save(session)
        session.refresh(group)
    return group
