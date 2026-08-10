"""Valori ammessi e condivisi dal dominio dei ticket."""

from enum import StrEnum


class Role(StrEnum):
    """Ruoli disponibili per gli account dimostrativi."""

    EMPLOYEE = "employee"
    TECHNICIAN = "technician"
    ADMIN = "admin"


class TicketCategory(StrEnum):
    """Categorie iniziali usate per classificare i ticket."""

    ACCOUNT_AND_ACCESS = "account_and_access"
    DEVICES_AND_HARDWARE = "devices_and_hardware"
    SOFTWARE_AND_APPLICATIONS = "software_and_applications"
    NETWORK_AND_CONNECTIVITY = "network_and_connectivity"
    PRINTERS_AND_LABELING = "printers_and_labeling"
    TELEPHONY = "telephony"
    RETAIL_SYSTEMS = "retail_systems"
    PRODUCTION_SYSTEMS = "production_systems"
    INFORMATION_SECURITY = "information_security"
    OTHER_REQUESTS = "other_requests"


class TicketStatus(StrEnum):
    """Stati possibili di un ticket già creato."""

    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_REQUESTER = "waiting_for_requester"
    WAITING_FOR_VENDOR = "waiting_for_vendor"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Impact(StrEnum):
    """Ampiezza delle conseguenze operative di un problema."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Urgency(StrEnum):
    """Rapidità con cui è necessario intervenire."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Priority(StrEnum):
    """Ordine di intervento calcolato dal backend."""

    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    P4 = "p4"
