from functools import wraps
from django.http import JsonResponse
from accounts.constant import ROLES


def require_permission(permission):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self_or_request, *args, **kwargs):
            request = self_or_request if hasattr(self_or_request, 'method') else (args[0] if args else None)

            role = getattr(request, 'role', None)
            if not role:
                return JsonResponse({'error': 'Unauthorized.'}, status=401)

            permissions = ROLES.get(role, [])
            if permission not in permissions:
                return JsonResponse({'error': f'Access denied. Required permission: "{permission}".'}, status=403)

            return view_func(self_or_request, *args, **kwargs)
        return wrapper
    return decorator
