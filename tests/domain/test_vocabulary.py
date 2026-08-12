"""Verifica che il vocabolario contenga soltanto i valori approvati."""

from enum import StrEnum

import pytest

from app.domain import (
    ActionStatus,
    ActionType,
    Impact,
    Priority,
    Role,
    TicketCategory,
    TicketStatus,
    Urgency,
)

DOMAIN_VALUES = [
    (
        ActionType,
        {"assign_ticket", "notify_requester", "escalate_vendor"},
    ),
    (
        ActionStatus,
        {
            "pending_approval",
            "approved",
            "rejected",
            "executing",
            "succeeded",
            "failed",
        },
    ),
    (Role, {"employee", "technician", "admin"}),
    (
        TicketCategory,
        {
            "account_and_access",
            "devices_and_hardware",
            "software_and_applications",
            "network_and_connectivity",
            "printers_and_labeling",
            "telephony",
            "retail_systems",
            "production_systems",
            "information_security",
            "other_requests",
        },
    ),
    (
        TicketStatus,
        {
            "new",
            "in_progress",
            "waiting_for_requester",
            "waiting_for_vendor",
            "resolved",
            "closed",
        },
    ),
    (Impact, {"low", "medium", "high"}),
    (Urgency, {"low", "medium", "high"}),
    (Priority, {"p1", "p2", "p3", "p4"}),
]


@pytest.mark.parametrize(("enum_type", "expected_values"), DOMAIN_VALUES)
def test_domain_values_are_complete_and_unique(
    enum_type: type[StrEnum], expected_values: set[str]
) -> None:
    actual_values = [member.value for member in enum_type]

    assert set(actual_values) == expected_values
    assert len(actual_values) == len(set(actual_values))


@pytest.mark.parametrize(("enum_type", "_"), DOMAIN_VALUES)
def test_domain_values_can_be_used_as_strings(enum_type: type[StrEnum], _: set[str]) -> None:
    assert all(str(member) == member.value for member in enum_type)
