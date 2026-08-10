"""Test del ciclo di vita deterministico dei ticket."""

import pytest

from app.domain import TicketStatus, can_transition_status


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (TicketStatus.NEW, TicketStatus.IN_PROGRESS),
        (TicketStatus.IN_PROGRESS, TicketStatus.WAITING_FOR_REQUESTER),
        (TicketStatus.IN_PROGRESS, TicketStatus.WAITING_FOR_VENDOR),
        (TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED),
        (TicketStatus.WAITING_FOR_REQUESTER, TicketStatus.IN_PROGRESS),
        (TicketStatus.WAITING_FOR_REQUESTER, TicketStatus.RESOLVED),
        (TicketStatus.WAITING_FOR_VENDOR, TicketStatus.IN_PROGRESS),
        (TicketStatus.WAITING_FOR_VENDOR, TicketStatus.RESOLVED),
        (TicketStatus.RESOLVED, TicketStatus.IN_PROGRESS),
        (TicketStatus.RESOLVED, TicketStatus.CLOSED),
    ],
)
def test_allowed_status_transitions(current: TicketStatus, target: TicketStatus) -> None:
    assert can_transition_status(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (TicketStatus.NEW, TicketStatus.RESOLVED),
        (TicketStatus.WAITING_FOR_REQUESTER, TicketStatus.CLOSED),
        (TicketStatus.RESOLVED, TicketStatus.WAITING_FOR_VENDOR),
        (TicketStatus.CLOSED, TicketStatus.IN_PROGRESS),
    ],
)
def test_forbidden_status_transitions(current: TicketStatus, target: TicketStatus) -> None:
    assert not can_transition_status(current, target)


def test_same_status_is_accepted_as_no_transition() -> None:
    assert can_transition_status(TicketStatus.IN_PROGRESS, TicketStatus.IN_PROGRESS)


@pytest.mark.parametrize("invalid_value", ["new", None])
def test_status_transition_rejects_unvalidated_values(invalid_value: object) -> None:
    with pytest.raises(TypeError):
        can_transition_status(invalid_value, TicketStatus.IN_PROGRESS)  # type: ignore[arg-type]
