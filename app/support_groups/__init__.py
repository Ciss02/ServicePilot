"""Catalogo e appartenenze dei gruppi di supporto."""

from app.support_groups.services import (
    DuplicateSupportGroupError,
    InvalidSupportGroupDataError,
    InvalidSupportGroupMemberError,
    SupportGroupNotFoundError,
    SupportGroupPersistenceError,
    active_support_group_names,
    create_support_group,
    list_active_support_groups,
    list_eligible_group_members,
    list_support_groups,
    replace_support_group_members,
    set_support_group_active,
    support_group_members_by_group,
    update_support_group,
)

__all__ = [
    "DuplicateSupportGroupError",
    "InvalidSupportGroupDataError",
    "InvalidSupportGroupMemberError",
    "SupportGroupNotFoundError",
    "SupportGroupPersistenceError",
    "active_support_group_names",
    "create_support_group",
    "list_active_support_groups",
    "list_eligible_group_members",
    "list_support_groups",
    "replace_support_group_members",
    "set_support_group_active",
    "support_group_members_by_group",
    "update_support_group",
]
