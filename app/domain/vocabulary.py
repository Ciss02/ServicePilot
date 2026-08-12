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


class AssignmentGroup(StrEnum):
    """Gruppi fittizi ai quali l'AI può indirizzare un ticket."""

    SERVICE_DESK = "Service desk"
    WORKPLACE_SUPPORT = "Supporto workplace"
    NETWORK_SUPPORT = "Supporto rete"
    RETAIL_SUPPORT = "Supporto sistemi retail"
    PRODUCTION_SUPPORT = "Supporto sistemi produttivi"
    WAREHOUSE_SUPPORT = "Supporto magazzino"
    IT_SECURITY = "Sicurezza IT"


class ClassificationReviewStatus(StrEnum):
    """Stato sicuro della proposta AI e della successiva verifica umana."""

    PENDING = "pending"
    AI_SUGGESTED = "ai_suggested"
    HUMAN_REVIEWED = "human_reviewed"
    AI_UNAVAILABLE = "ai_unavailable"
    AI_INVALID_RESPONSE = "ai_invalid_response"


class ActionType(StrEnum):
    """Azioni che l'agente può proporre senza eseguirle."""

    ASSIGN_TICKET = "assign_ticket"
    NOTIFY_REQUESTER = "notify_requester"
    ESCALATE_VENDOR = "escalate_vendor"


class ActionStatus(StrEnum):
    """Stato controllato della proposta e della futura esecuzione."""

    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ActionDecision(StrEnum):
    """Decisioni esplicite disponibili a tecnico e amministratore."""

    APPROVE = "approve"
    REJECT = "reject"


class AuditActorType(StrEnum):
    """Origine riconoscibile di un evento del registro."""

    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"


class AuditEventType(StrEnum):
    """Passaggi rilevanti che permettono di ricostruire un ticket."""

    TICKET_CREATED = "ticket_created"
    TICKET_UPDATED = "ticket_updated"
    TICKET_STATUS_CHANGED = "ticket_status_changed"
    TICKET_ASSIGNMENT_CHANGED = "ticket_assignment_changed"
    AI_CLASSIFICATION_SUGGESTED = "ai_classification_suggested"
    AI_CLASSIFICATION_UNAVAILABLE = "ai_classification_unavailable"
    AI_CLASSIFICATION_INVALID = "ai_classification_invalid"
    CLASSIFICATION_REVIEWED = "classification_reviewed"
    AI_SOLUTION_GENERATED = "ai_solution_generated"
    AI_SOLUTION_UNAVAILABLE = "ai_solution_unavailable"
    AI_SOLUTION_INVALID = "ai_solution_invalid"
    ACTION_PROPOSED = "action_proposed"
    ACTION_APPROVED = "action_approved"
    ACTION_REJECTED = "action_rejected"
    ACTION_EXECUTION_STARTED = "action_execution_started"
    ACTION_EXECUTION_SUCCEEDED = "action_execution_succeeded"
    ACTION_EXECUTION_FAILED = "action_execution_failed"


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
