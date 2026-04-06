from functools import wraps

from django.http import JsonResponse

from accounts.constant import USER, ROLES


def require_permission(permission):
    """
    Decorator to check if the authenticated user has the required permission.

    Usage:
        @require_permission('create')
        def post(self, request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self_or_request, *args, **kwargs):
            # Handle both APIView methods (self, request) and plain functions (request)
            if hasattr(self_or_request, 'method'):
                request = self_or_request
            else:
                request = args[0] if args else None

            email = getattr(request, 'email', None)
            if not email:
                return JsonResponse({'error': 'Unauthorized. No user context found.'}, status=401)

            user_data = USER.get(email)
            if not user_data:
                return JsonResponse({'error': 'User not found.'}, status=403)

            role = user_data.get('role')
            permissions = ROLES.get(role, [])

            if permission not in permissions:
                return JsonResponse(
                    {'error': f'Access denied. Required permission: "{permission}".'},
                    status=403
                )

            return view_func(self_or_request, *args, **kwargs)
        return wrapper
    return decorator
