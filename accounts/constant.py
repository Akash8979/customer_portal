
TENANT = {
    "tenant_1": {
        "tenant_name": "Tenant One"
    },
    "tenant_2": {
        "tenant_name": "Tenant Two",
    }
}

USER = {
    "client_admin_test_1@gmail.com": {
        "user_id": 1,
        "user_name": "client Admin",
        "password": "test",
        "role": "client_admin",
        "tenant_id": "tenant_1"
    }
}

ROLES = {
    "client_admin": ["create", "edit", "delete"],
    "admin": ["create", "edit", "delete"],
    "agent": ["create", "edit", "delete"]
}