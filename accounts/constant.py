
TENANT_IDS= ["1","2"]

TENANT = {
    "1": {
        "tenant_name": "Tenant One"
    },
    "2": {
        "tenant_name": "Tenant Two",
    }
}

USER = {
    "client_admin_test_1@gmail.com": {
        "user_id": 1,
        "user_name": "client Admin",
        "password": "test",
        "role": "CLIENT_ADMIN",
        "tenant_id": ""
    },
    "internal_agent_test_1@gmail.com": {
        "user_id": 2,
        "user_name": "Internal Admin",
        "password": "test",
        "role": "AGENT",
        "tenant_id": ""
    }
}

ROLES = {
    "CLIENT_ADMIN": ["CREATE", "EDIT", "DELETE"],
    "ADMIN": ["CREATE", "EDIT", "DELETE"],
    "AGENT": ["CREATE", "EDIT", "DELETE"]
}