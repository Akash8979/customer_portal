import time
import jwt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.constant import USER, ROLES, TENANT

SECRET_KEY = 'customer-portal-secret-key'
ACCESS_TOKEN_EXPIRY = 60 * 60 * 24         # 14 hours
REFRESH_TOKEN_EXPIRY = 60 * 60 * 24 * 365  # 1 year


def generate_tokens(email, user_data):
    now = int(time.time())

    tenant_id = user_data.get('tenant_id')

    access_payload = {
        'user_id': user_data['user_id'],
        'user_name': user_data['user_name'],
        'email': email,
        'tenant_id': tenant_id,
        'token_type': 'access',
        'iat': now,
        'exp': now + ACCESS_TOKEN_EXPIRY,
    }

    refresh_payload = {
        'user_id': user_data['user_id'],
        'email': email,
        'tenant_id': tenant_id,
        'token_type': 'refresh',
        'iat': now,
        'exp': now + REFRESH_TOKEN_EXPIRY,
    }

    return {
        'access': jwt.encode(access_payload, SECRET_KEY, algorithm='HS256'),
        'refresh': jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256'),
    }


class LoginView(APIView):
    """
    POST /api/accounts/login/
    Body: { "email": "...", "password": "..." }
    Validates against the USER constant — no DB required.
    Returns access token (contains user_id & user_name) and refresh token.
    """

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Both email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if email exists
        user_data = USER.get(email)
        if user_data is None:
            return Response(
                {'error': 'Email does not exist.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check password
        if user_data['password'] != password:
            return Response(
                {'error': 'Incorrect password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Login success
        tokens = generate_tokens(email, user_data)
        role = user_data.get('role')
        permissions = ROLES.get(role, [])
        tenant_id = user_data.get('tenant_id')
        tenant_data = TENANT.get(tenant_id, {})
        response  =  Response({
            'message': 'Login successful.',
            'tokens': tokens,
            'user': {
                'user_id': user_data['user_id'],
                'email': email,
                'user_name': user_data['user_name'],
                'role': role,
                'permissions': permissions,
                'tenant_id': tenant_id,
                'tenant_name': tenant_data.get('tenant_name'),
            },
        }, status=status.HTTP_200_OK)
        # Set JWT in cookie
        response.set_cookie(
            key="token",
            value=tokens['access'],
            httponly=True,
            secure=True,        # True in production (HTTPS)
            samesite="none",     # or 'Strict' / 'None'
        )
        return response


class RefreshTokenView(APIView):
    """
    POST /api/accounts/token/refresh/
    Body: { "refresh": "<refresh_token>" }
    Validates the refresh token and returns a new access token.
    """

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Refresh token has expired.'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        if payload.get('token_type') != 'refresh':
            return Response({'error': 'Invalid token type.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Look up user from constant
        email = payload.get('email')
        user_data = USER.get(email)
        if user_data is None:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Generate new access token
        now = int(time.time())
        access_payload = {
            'user_id': user_data['user_id'],
            'user_name': user_data['user_name'],
            'email': email,
            'token_type': 'access',
            'iat': now,
            'exp': now + ACCESS_TOKEN_EXPIRY,
        }

        return Response({
            'access': jwt.encode(access_payload, SECRET_KEY, algorithm='HS256'),
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/accounts/logout/
    Since there's no DB/session, just acknowledges logout.
    """

    def post(self, request):
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    GET /api/accounts/me/?tenant_id=<tenant_id>
    Returns the logged-in user's details from the JWT token.
    """

    def get(self, request):
        email = request.email
        user_data = USER.get(email)
        if user_data is None:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        role = user_data.get('role')
        tenant_id = user_data.get('tenant_id')
        tenant_data = TENANT.get(tenant_id, {})

        return Response({
            'data': {
                'user_id': request.user_id,
                'user_name': request.user_name,
                'email': email,
                'role': role,
                'permissions': ROLES.get(role, []),
                'tenant_id': tenant_id,
                'tenant_name': tenant_data.get('tenant_name'),
            }
        }, status=status.HTTP_200_OK)
