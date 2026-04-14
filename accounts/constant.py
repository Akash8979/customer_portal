"""
static_data.py
==============
Static user store — kept in-memory, no database needed.

Structure matches the original exactly.
Permissions are simple strings checked via has_permission().

Roles
------
Client side (scoped to tenant_id):
  CLIENT_ADMIN    – manages own org, sees all org tickets
  CLIENT_USER     – raises own tickets only

Internal 3SC side (no tenant_id — cross-tenant access):
  AGENT      – works assigned tickets
  LEAD       – agent + assign/routing/SLA
  ADMIN      – lead + manage all customer orgs

All passwords are "test" for development.
"""

# ─────────────────────────────────────────────────────────────────────────────
# TENANTS
# ─────────────────────────────────────────────────────────────────────────────

TENANT_IDS = ["1", "2"]

TENANT = {
    "1": {
        "tenant_name": "Acme Corp",
    },
    "2": {
        "tenant_name": "Beta Industries",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# ROLES AND PERMISSIONS
# Each role maps to a list of permission strings.
# Use has_permission(email, "TICKET_CREATE") to check in your views.
# ─────────────────────────────────────────────────────────────────────────────

ROLES = {

    # ── Client side ───────────────────────────────────────────────────────────

    "CLIENT_ADMIN": [
        # Tickets — sees all tickets in own org
        "TICKET_CREATE",
        "TICKET_VIEW_ORG",      # all tickets in their org
        "TICKET_EDIT",
        "TICKET_STATUS_CHANGE",
        "TICKET_REOPEN",
        # Comments
        "COMMENT_CREATE",
        # Attachments
        "ATTACHMENT_UPLOAD",
        "ATTACHMENT_DELETE",
        # Org members
        "MEMBER_INVITE",
        "MEMBER_MANAGE",
        "MEMBER_VIEW",
        # Reports — own org only
        "REPORT_VIEW",
        "REPORT_EXPORT",
        # Other
        "KB_VIEW",
        "SLA_VIEW",
        "WORKSPACE_CONFIGURE",
    ],

    "CLIENT_USER": [
        # Tickets — own tickets only
        "TICKET_CREATE",
        "TICKET_VIEW_OWN",      # only their own tickets
        "TICKET_REOPEN",
        # Comments
        "COMMENT_CREATE",
        # Attachments
        "ATTACHMENT_UPLOAD",
        # Other
        "MEMBER_VIEW",
        "KB_VIEW",
        "SLA_VIEW",
    ],

    # ── Internal 3SC side ─────────────────────────────────────────────────────

    "AGENT": [
        # Tickets — can work any assigned ticket across all tenants
        "TICKET_VIEW_ALL",
        "TICKET_EDIT",
        "TICKET_STATUS_CHANGE",
        # Comments — can write internal notes
        "COMMENT_CREATE",
        "COMMENT_INTERNAL",
        # Attachments
        "ATTACHMENT_UPLOAD",
        # AI assist panel
        "AI_SUGGEST",
        "AI_FEEDBACK",
        # Other
        "KB_VIEW",
        "SLA_VIEW",
        "MEMBER_VIEW",
    ],

    "LEAD": [
        # Everything AGENT has, plus assignment + routing + SLA config
        "TICKET_VIEW_ALL",
        "TICKET_EDIT",
        "TICKET_STATUS_CHANGE",
        "TICKET_ASSIGN",        # assign/reassign to any agent
        "TICKET_DELETE",
        "COMMENT_CREATE",
        "COMMENT_INTERNAL",
        "COMMENT_DELETE",
        "ATTACHMENT_UPLOAD",
        "ATTACHMENT_DELETE",
        # SLA
        "SLA_VIEW",
        "SLA_CONFIGURE",
        "ESCALATION_CONFIGURE",
        # Reports — all tenants
        "REPORT_VIEW",
        "REPORT_EXPORT",
        # AI assist
        "AI_SUGGEST",
        "AI_FEEDBACK",
        # Other
        "KB_VIEW",
        "MEMBER_VIEW",
    ],

    "ADMIN": [
        # Everything LEAD has, plus org management + audit
        "TICKET_VIEW_ALL",
        "TICKET_EDIT",
        "TICKET_STATUS_CHANGE",
        "TICKET_ASSIGN",
        "TICKET_DELETE",
        "TICKET_REOPEN",
        "COMMENT_CREATE",
        "COMMENT_INTERNAL",
        "COMMENT_DELETE",
        "ATTACHMENT_UPLOAD",
        "ATTACHMENT_DELETE",
        # SLA — full control
        "SLA_VIEW",
        "SLA_CONFIGURE",
        "ESCALATION_CONFIGURE",
        # Reports
        "REPORT_VIEW",
        "REPORT_EXPORT",
        # AI assist
        "AI_SUGGEST",
        "AI_FEEDBACK",
        # KB — full control
        "KB_VIEW",
        "KB_MANAGE",
        # Members — manage any org
        "MEMBER_INVITE",
        "MEMBER_MANAGE",
        "MEMBER_VIEW",
        # Audit trail
        "AUDIT_VIEW",
        # Workspace
        "WORKSPACE_CONFIGURE",
    ]
}


# ─────────────────────────────────────────────────────────────────────────────
# USERS
# Key   = email (used as login identifier)
# Notes:
#   - Client roles have tenant_id
#   - Internal roles (AGENT, LEAD, ADMIN, SUPERADMIN) have NO tenant_id
#   - All passwords are "test"
# ─────────────────────────────────────────────────────────────────────────────

USER = {

    # =========================================================================
    # TENANT 1 — Acme Corp
    # =========================================================================

    # CLIENT_ADMIN (3 users)
    "client_admin_test_1@gmail.com": {
        "user_id":   1,
        "user_name": "Alice Johnson",
        "password":  "test",
        "role":      "CLIENT_ADMIN",
        "tenant_id": "1",
    },
    "client_admin_test_2@gmail.com": {
        "user_id":   2,
        "user_name": "Bob Chen",
        "password":  "test",
        "role":      "CLIENT_ADMIN",
        "tenant_id": "1",
    },
    "client_admin_test_3@gmail.com": {
        "user_id":   3,
        "user_name": "Carol Davis",
        "password":  "test",
        "role":      "CLIENT_ADMIN",
        "tenant_id": "1",
    },

    # CLIENT_USER (3 users)
    "client_user_test_1@gmail.com": {
        "user_id":   4,
        "user_name": "Dave Patel",
        "password":  "test",
        "role":      "CLIENT_USER",
        "tenant_id": "1",
    },
    "client_user_test_2@gmail.com": {
        "user_id":   5,
        "user_name": "Eve Wilson",
        "password":  "test",
        "role":      "CLIENT_USER",
        "tenant_id": "1",
    },
    "client_user_test_3@gmail.com": {
        "user_id":   6,
        "user_name": "Frank Lee",
        "password":  "test",
        "role":      "CLIENT_USER",
        "tenant_id": "1",
    },

    # =========================================================================
    # TENANT 2 — Beta Industries
    # =========================================================================

    # CLIENT_ADMIN (3 users)
    "client_admin_test_4@gmail.com": {
        "user_id":   10,
        "user_name": "Jack Nguyen",
        "password":  "test",
        "role":      "CLIENT_ADMIN",
        "tenant_id": "2",
    },
    "client_admin_test_5@gmail.com": {
        "user_id":   11,
        "user_name": "Kate Svensson",
        "password":  "test",
        "role":      "CLIENT_ADMIN",
        "tenant_id": "2",
    },
    "client_admin_test_6@gmail.com": {
        "user_id":   12,
        "user_name": "Liam Okonkwo",
        "password":  "test",
        "role":      "CLIENT_ADMIN",
        "tenant_id": "2",
    },

    # CLIENT_USER (3 users)
    "client_user_test_4@gmail.com": {
        "user_id":   13,
        "user_name": "Maya Sharma",
        "password":  "test",
        "role":      "CLIENT_USER",
        "tenant_id": "2",
    },
    "client_user_test_5@gmail.com": {
        "user_id":   14,
        "user_name": "Noah Fernandez",
        "password":  "test",
        "role":      "CLIENT_USER",
        "tenant_id": "2",
    },
    "client_user_test_6@gmail.com": {
        "user_id":   15,
        "user_name": "Olivia Braun",
        "password":  "test",
        "role":      "CLIENT_USER",
        "tenant_id": "2",
    },

    # =========================================================================
    # INTERNAL — 3SC Staff (no tenant_id — cross-tenant access)
    # =========================================================================

    # AGENT (3 users)
    "internal_agent_test_1@gmail.com": {
        "user_id":   19,
        "user_name": "Sam Torres",
        "password":  "test",
        "role":      "AGENT",
    },
    "internal_agent_test_2@gmail.com": {
        "user_id":   20,
        "user_name": "Tina Rahman",
        "password":  "test",
        "role":      "AGENT",
    },
    "internal_agent_test_3@gmail.com": {
        "user_id":   21,
        "user_name": "Umar Hassan",
        "password":  "test",
        "role":      "AGENT",
    },

    # LEAD (3 users)
    "internal_lead_test_1@gmail.com": {
        "user_id":   22,
        "user_name": "Vera Morozova",
        "password":  "test",
        "role":      "LEAD",
    },
    "internal_lead_test_2@gmail.com": {
        "user_id":   23,
        "user_name": "Will Andersen",
        "password":  "test",
        "role":      "LEAD",
    },
    "internal_lead_test_3@gmail.com": {
        "user_id":   24,
        "user_name": "Xena Balogun",
        "password":  "test",
        "role":      "LEAD",
    },

    # ADMIN (3 users)
    "internal_admin_test_1@gmail.com": {
        "user_id":   25,
        "user_name": "Yusuf Al-Rashid",
        "password":  "test",
        "role":      "ADMIN",
    },
    "internal_admin_test_2@gmail.com": {
        "user_id":   26,
        "user_name": "Zara Mbeki",
        "password":  "test",
        "role":      "ADMIN",
    },
    "internal_admin_test_3@gmail.com": {
        "user_id":   27,
        "user_name": "Alex Park",
        "password":  "test",
        "role":      "ADMIN",
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_user(email: str) -> dict | None:
    """Return user dict for an email, or None if not found."""
    return USER.get(email)


def get_user_permissions(email: str) -> list[str]:
    """Return the full permission list for a user's role."""
    user = get_user(email)
    if not user:
        return []
    return ROLES.get(user["role"], [])


def has_permission(email: str, permission: str) -> bool:
    """
    Check whether a user has a specific permission.

    Usage:
        if not has_permission(current_user_email, "TICKET_ASSIGN"):
            return jsonify({"error": "Insufficient permissions"}), 403
    """
    return permission in get_user_permissions(email)


def get_users_by_role(role: str) -> list[dict]:
    """Return all users with a given role."""
    return [u for u in USER.values() if u["role"] == role]


def get_tenant_users(tenant_id: str) -> list[dict]:
    """Return all users belonging to a specific tenant."""
    return [u for u in USER.values() if u.get("tenant_id") == tenant_id]


def is_client_role(role: str) -> bool:
    return role in ("CLIENT_ADMIN", "CLIENT_USER", "CLIENT_READONLY")


def is_internal_role(role: str) -> bool:
    return role in ("AGENT", "LEAD", "ADMIN", "SUPERADMIN")