# Customer Portal

A Django REST Framework-based customer support portal with ticket management, threaded comments, and attachment handling.

## Tech Stack

- **Python** / **Django 5.x**
- **Django REST Framework**
- **PostgreSQL**
- **PyJWT** — stateless authentication (no DB sessions)

## Project Structure

```
customer_portal/
├── accounts/               # Authentication & authorization
│   ├── constant.py         # Users, roles, tenants (no DB)
│   ├── views.py            # Login, logout, token refresh
│   └── urls.py
├── portal/                 # Core ticketing app
│   ├── models/
│   │   ├── ticket.py
│   │   ├── attachment.py
│   │   ├── ticket_attachment.py
│   │   └── comment.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
└── manage.py
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configure your PostgreSQL database in `customer_portal/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'customer_portal',
        'USER': '<your_db_user>',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Run migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

---

## Authentication

All auth endpoints are under `/portal/user/`.

Authentication is stateless — users and roles are defined in `accounts/constant.py`. No database is used for auth.

### Login

`POST /portal/user/login`

```json
{
  "email": "client_admin_test_1@gmail.com",
  "password": "test"
}
```

**Response:**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "user_id": 1,
  "user_name": "client Admin",
  "role": "client_admin",
  "permissions": ["create", "edit", "delete"],
  "tenant_id": "tenant_1"
}
```

Access token expires in **14 hours**. Refresh token expires in **1 year**.

### Refresh Token

`POST /portal/user/token/refresh/`

```json
{ "refresh_token": "<jwt>" }
```

### Logout

`POST /portal/user/logout/`

---

## Ticket APIs

Base path: `/portal/tickets/`

### Create Ticket

`POST /portal/tickets/`

```json
{
  "title": "Login page broken",
  "description": "500 error on login",
  "category": "BUG",
  "priority": "HIGH",
  "created_by": "user@example.com",
  "due_date": "2026-04-01T00:00:00Z",
  "attachment_ids": [1, 2]
}
```

**Category options:** `BUG`, `FEATURE_REQUEST`, `SUPPORT`, `BILLING`, `OTHER`

**Priority options:** `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

### Get Ticket

`GET /portal/tickets/<id>/`

Returns ticket details with linked attachments.

### Update Ticket

`PATCH /portal/tickets/<id>/update/`

```json
{
  "status": "IN_PROGRESS",
  "assigned_to": "agent@example.com",
  "attachment_ids": [3]
}
```

`attachment_ids` appends new attachments — does not replace existing ones.

**Status options:** `OPEN`, `ACKNOWLEDGED`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`, `REOPENED`

---

## Attachment API

### Upload Attachment (metadata only)

`POST /portal/attachments/`

```json
{
  "file_name": "screenshot.png",
  "file_type": "image/png",
  "file_path": "/uploads/screenshot.png",
  "metadata": {}
}
```

Returns an attachment `id` which can then be passed in `attachment_ids` when creating/updating tickets or comments.

---

## Comment API

### Create Comment

`POST /portal/comments/`

```json
{
  "ticket_id": 1,
  "user_id": 1,
  "message": "Looking into this now.",
  "parent_id": null,
  "attachment_ids": [4, 5]
}
```

- `parent_id` — optional. Set to an existing comment `id` to create a threaded reply.
- `attachment_ids` — optional list of existing attachment IDs to link to the comment.

Attachments are linked via the `portal_ticket_attachment` table using `reference_id = comment.id`.

---

## Data Models

### Ticket (`portal_ticket`)

| Field | Type | Notes |
|---|---|---|
| id | AutoField | Primary key |
| title | CharField | |
| description | TextField | |
| category | CharField | BUG / FEATURE_REQUEST / SUPPORT / BILLING / OTHER |
| status | CharField | OPEN / ACKNOWLEDGED / IN_PROGRESS / RESOLVED / CLOSED / REOPENED |
| priority | CharField | LOW / MEDIUM / HIGH / CRITICAL |
| created_by | CharField | |
| assigned_to | CharField | Nullable |
| due_date | DateTimeField | Nullable |
| resolved_at | DateTimeField | Nullable |
| closed_at | DateTimeField | Nullable |
| created_at | DateTimeField | Auto |
| updated_at | DateTimeField | Auto |

### Attachment (`portal_attachment`)

| Field | Type | Notes |
|---|---|---|
| id | AutoField | Primary key |
| file_name | CharField | |
| file_type | CharField | |
| file_path | CharField | |
| metadata | JSONField | |
| created_at | DateTimeField | Auto |

### TicketAttachment (`portal_ticket_attachment`)

Generic join table linking attachments to either tickets or comments.

| Field | Type | Notes |
|---|---|---|
| id | AutoField | Primary key |
| reference_id | IntegerField | ticket.id or comment.id |
| attachment_id | IntegerField | attachment.id |
| created_at | DateTimeField | Auto |

### Comment (`portal_comment`)

| Field | Type | Notes |
|---|---|---|
| id | AutoField | Primary key |
| ticket_id | IntegerField | |
| user_id | IntegerField | |
| parent_id | IntegerField | Nullable — for threaded replies |
| message | TextField | |
| is_deleted | BooleanField | Soft delete |
| created_at | DateTimeField | Auto |
| updated_at | DateTimeField | Auto |

---

## Roles & Permissions

Defined in `accounts/constant.py`:

| Role | Permissions |
|---|---|
| client_admin | create, edit, delete |
| admin | create, edit, delete |
| agent | create, edit, delete |

Tenant-to-user mapping is also maintained in `constant.py`.
