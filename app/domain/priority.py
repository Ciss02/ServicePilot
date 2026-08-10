"""Calcolo deterministico della priorità dei ticket."""

from app.domain.vocabulary import Impact, Priority, Urgency


_PRIORITY_MATRIX: dict[tuple[Impact, Urgency], Priority] = {
    (Impact.LOW, Urgency.LOW): Priority.P4,
    (Impact.LOW, Urgency.MEDIUM): Priority.P4,
    (Impact.LOW, Urgency.HIGH): Priority.P3,
    (Impact.MEDIUM, Urgency.LOW): Priority.P4,
    (Impact.MEDIUM, Urgency.MEDIUM): Priority.P3,
    (Impact.MEDIUM, Urgency.HIGH): Priority.P2,
    (Impact.HIGH, Urgency.LOW): Priority.P3,
    (Impact.HIGH, Urgency.MEDIUM): Priority.P2,
    (Impact.HIGH, Urgency.HIGH): Priority.P1,
}


def calculate_priority(impact: Impact, urgency: Urgency) -> Priority:
    """Restituisce la priorità prevista per impatto e urgenza già validati."""

    if not isinstance(impact, Impact):
        raise TypeError("impact deve essere un valore Impact")
    if not isinstance(urgency, Urgency):
        raise TypeError("urgency deve essere un valore Urgency")

    return _PRIORITY_MATRIX[(impact, urgency)]
