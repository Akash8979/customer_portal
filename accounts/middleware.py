import jwt
from django.http import JsonResponse

from accounts.constant import TENANT,ROLES

SECRET_KEY = 'customer-portal-secret-key'

EXEMPT_PATHS = [
    '/portal/user/login',
    '/portal/user/token/refresh/',
    '/portal/user/logout/',
    '/admin/'
]


class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(path) for path in EXEMPT_PATHS):
            return self.get_response(request)

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        cookies_ = request.COOKIES
        if not auth_header.startswith('Bearer ') and not cookies_:
            return JsonResponse({'error': 'Authorization header missing or invalid.'}, status=401)

        token = auth_header.split(' ', 1)[1] if auth_header else cookies_['token']

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Access token has expired.'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid access token.'}, status=401)

        if payload.get('token_type') != 'access':
            return JsonResponse({'error': 'Invalid token type. Expected access token.'}, status=401)

        tenant_id = request.GET.get('tenant_id')
        if not tenant_id and ['CLIENT_ADMIN','CLIENT_USER']:
            return JsonResponse({'error': 'tenant_id is required as a query parameter.'}, status=400)

        if tenant_id not in TENANT:
            return JsonResponse({'error': f'Tenant "{tenant_id}" does not exist.'}, status=400)

        request.user_id = payload.get('user_id')
        request.user_name = payload.get('user_name')
        request.email = payload.get('email')
        # request.tenant_id = tenant_id
        request.created_by = payload.get('user_id')
        request.updated_at = payload.get('updated_at')

        return self.get_response(request)
