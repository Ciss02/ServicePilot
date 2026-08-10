"""Test della matrice deterministica usata per calcolare la priorità."""

import pytest

from app.domain import Impact, Priority, Urgency, calculate_priority


@pytest.mark.parametrize(
    ("impact", "urgency", "expected_priority"),
    [
        pytest.param(Impact.LOW, Urgency.LOW, Priority.P4, id="low-low-p4"),
        pytest.param(Impact.LOW, Urgency.MEDIUM, Priority.P4, id="low-medium-p4"),
        pytest.param(Impact.LOW, Urgency.HIGH, Priority.P3, id="low-high-p3"),
        pytest.param(Impact.MEDIUM, Urgency.LOW, Priority.P4, id="medium-low-p4"),
        pytest.param(Impact.MEDIUM, Urgency.MEDIUM, Priority.P3, id="medium-medium-p3"),
        pytest.param(Impact.MEDIUM, Urgency.HIGH, Priority.P2, id="medium-high-p2"),
        pytest.param(Impact.HIGH, Urgency.LOW, Priority.P3, id="high-low-p3"),
        pytest.param(Impact.HIGH, Urgency.MEDIUM, Priority.P2, id="high-medium-p2"),
        pytest.param(Impact.HIGH, Urgency.HIGH, Priority.P1, id="high-high-p1"),
    ],
)
def test_calculate_priority_uses_complete_matrix(
    impact: Impact, urgency: Urgency, expected_priority: Priority
) -> None:
    assert calculate_priority(impact, urgency) is expected_priority


def test_calculate_priority_rejects_unvalidated_impact() -> None:
    with pytest.raises(TypeError, match="impact"):
        calculate_priority("high", Urgency.HIGH)  # type: ignore[arg-type]


def test_calculate_priority_rejects_unvalidated_urgency() -> None:
    with pytest.raises(TypeError, match="urgency"):
        calculate_priority(Impact.HIGH, "high")  # type: ignore[arg-type]
