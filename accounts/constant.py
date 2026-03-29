
TENANT_IDS= ["TENANT_1","TENANT_2"]

TENANT = {
    "TENANT_1": {
        "tenant_name": "Tenant One"
    },
    "TENANT_2": {
        "tenant_name": "Tenant Two",
    }
}

USER = {
    "client_admin_test_1@gmail.com": {
        "user_id": 1,
        "user_name": "client Admin",
        "password": "test",
        "role": "CLIENT_ADMIN",
        "tenant_id": "TENANT_1"
    }
}

ROLES = {
    "CLIENT_ADMIN": ["CREATE", "EDIT", "DELETE"],
    "ADMIN": ["CREATE", "EDIT", "DELETE"],
    "AGENT": ["CREATE", "EDIT", "DELETE"]
}