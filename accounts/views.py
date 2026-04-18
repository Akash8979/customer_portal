import time
import jwt
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.constant import ROLES, TENANT
from user_management.models import UserProfile

SECRET_KEY = 'customer-portal-secret-key'
ACCESS_TOKEN_EXPIRY = 60 * 60 * 24         # 24 hours
REFRESH_TOKEN_EXPIRY = 60 * 60 * 24 * 365  # 1 year


def generate_tokens(user: UserProfile):
    now = int(time.time())
    base = {
        'user_id':   user.id,
        'user_name': user.user_name,
        'email':     user.email,
        'role':      user.role,
        'tenant_id': user.tenant_id,
        'iat':       now,
    }
    access_payload  = {**base, 'token_type': 'access',  'exp': now + ACCESS_TOKEN_EXPIRY}
    refresh_payload = {**base, 'token_type': 'refresh', 'exp': now + REFRESH_TOKEN_EXPIRY}
    return {
        'access':  jwt.encode(access_payload,  SECRET_KEY, algorithm='HS256'),
        'refresh': jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256'),
    }


class LoginView(APIView):
    def post(self, request):
        email    = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if not email or not password:
            return Response({'error': 'Both email and password are required.'}, status=400)

        user = UserProfile.objects.filter(email=email).first()
        if user is None:
            return Response({'error': 'Email does not exist.'}, status=404)

        if not user.is_active:
            return Response({'error': 'Account is deactivated. Contact your administrator.'}, status=403)

        if not user.check_password(password):
            return Response({'error': 'Incorrect password.'}, status=401)

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        tokens = generate_tokens(user)
        role = user.role
        permissions = ROLES.get(role, []) + (user.custom_permissions or [])
        tenant_data = TENANT.get(user.tenant_id, {})

        response = Response({
            'message': 'Login successful.',
            'tokens': tokens,
            'user': {
                'user_id':     user.id,
                'email':       user.email,
                'user_name':   user.user_name,
                'role':        role,
                'permissions': sorted(set(permissions)),
                'tenant_id':   user.tenant_id,
                'tenant_name': user.tenant_name or tenant_data.get('tenant_name'),
            },
        }, status=200)
        response.set_cookie(
            key='token', value=tokens['access'],
            httponly=True, secure=True, samesite='none',
        )
        return response


class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required.'}, status=400)

        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Refresh token has expired.'}, status=401)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid refresh token.'}, status=401)

        if payload.get('token_type') != 'refresh':
            return Response({'error': 'Invalid token type.'}, status=401)

        user = UserProfile.objects.filter(email=payload.get('email')).first()
        if not user:
            return Response({'error': 'User not found.'}, status=404)
        if not user.is_active:
            return Response({'error': 'Account deactivated.'}, status=403)

        now = int(time.time())
        access_payload = {
            'user_id':    user.id,
            'user_name':  user.user_name,
            'email':      user.email,
            'role':       user.role,
            'tenant_id':  user.tenant_id,
            'token_type': 'access',
            'iat':        now,
            'exp':        now + ACCESS_TOKEN_EXPIRY,
        }
        return Response({'access': jwt.encode(access_payload, SECRET_KEY, algorithm='HS256')})


class LogoutView(APIView):
    def post(self, request):
        return Response({'message': 'Logged out successfully.'})


class MeView(APIView):
    def get(self, request):
        user = UserProfile.objects.filter(email=request.email).first()
        if not user:
            return Response({'error': 'User not found.'}, status=404)

        role = user.role
        tenant_data = TENANT.get(user.tenant_id, {})
        permissions = ROLES.get(role, []) + (user.custom_permissions or [])

        return Response({
            'data': {
                'user_id':     user.id,
                'user_name':   user.user_name,
                'email':       user.email,
                'role':        role,
                'permissions': sorted(set(permissions)),
                'tenant_id':   user.tenant_id,
                'tenant_name': user.tenant_name or tenant_data.get('tenant_name'),
            }
        })
