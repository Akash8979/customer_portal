import math
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.constant import ROLES, USER, TENANT
from accounts.decorators import require_permission
from .models import UserProfile
from .serializers import (
    UserProfileSerializer, UserCreateSerializer,
    UserUpdateSerializer, RolePermissionMapSerializer,
)


def paginate_qs(qs, request, serializer_class):
    total = qs.count()
    try:
        page = max(1, int(request.query_params.get('page', 1)))
        page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
    except ValueError:
        page, page_size = 1, 20
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    page = min(page, total_pages) if total_pages > 0 else 1
    offset = (page - 1) * page_size
    data = serializer_class(qs[offset:offset + page_size], many=True).data
    return Response({'data': data, 'total': total, 'page': page, 'page_size': page_size, 'total_pages': total_pages})


class RolePermissionMapView(APIView):
    """
    GET /portal/users/role-permissions
    Returns the full permission map for all roles — no auth needed for UI to build the matrix.
    """

    def get(self, request):
        data = {role: sorted(perms) for role, perms in ROLES.items()}
        return Response({'data': data})


class UserListView(APIView):
    """
    GET /portal/users
    - ADMIN: all users across all tenants
    - LEAD: all users (read-only perspective)
    - CLIENT_ADMIN: only users in their tenant
    """

    def get(self, request):
        caller = USER.get(request.email, {})
        role = caller.get('role', '')

        qs = UserProfile.objects.all()

        if role == 'CLIENT_ADMIN':
            qs = qs.filter(tenant_id=request.tenant_id)
        elif role == 'CLIENT_USER':
            return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        # Filters
        for field in ('role', 'tenant_id', 'is_active'):
            val = request.query_params.get(field)
            if val is not None:
                if field == 'is_active':
                    qs = qs.filter(is_active=val.lower() == 'true')
                else:
                    qs = qs.filter(**{field: val})

        search = request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(user_name__icontains=search) | Q(email__icontains=search))

        return paginate_qs(qs, request, UserProfileSerializer)


class UserCreateView(APIView):
    """
    POST /portal/users/create
    ADMIN can create any user.
    CLIENT_ADMIN can only create CLIENT_USER / CLIENT_ADMIN within their tenant.
    """

    def post(self, request):
        caller = USER.get(request.email, {})
        caller_role = caller.get('role', '')

        if caller_role not in ('ADMIN', 'CLIENT_ADMIN'):
            return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        data = dict(request.data)

        # CLIENT_ADMIN can only create client-side users in their own tenant
        if caller_role == 'CLIENT_ADMIN':
            if data.get('role') not in ('CLIENT_ADMIN', 'CLIENT_USER'):
                return Response(
                    {'error': 'You can only create CLIENT_ADMIN or CLIENT_USER roles.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            data['tenant_id'] = request.tenant_id
            tenant_info = TENANT.get(request.tenant_id, {})
            data['tenant_name'] = tenant_info.get('tenant_name', '')

        data['invited_by'] = request.email

        serializer = UserCreateSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'data': UserProfileSerializer(user).data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    """
    GET /portal/users/<pk>
    PATCH /portal/users/<pk>
    """

    def _get_user(self, pk, caller_role, caller_tenant):
        user = UserProfile.objects.filter(pk=pk).first()
        if not user:
            return None, Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if caller_role == 'CLIENT_ADMIN' and user.tenant_id != caller_tenant:
            return None, Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        return user, None

    def get(self, request, pk):
        caller = USER.get(request.email, {})
        caller_role = caller.get('role', '')
        if caller_role == 'CLIENT_USER':
            return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        user, err = self._get_user(pk, caller_role, request.tenant_id)
        if err:
            return err
        return Response({'data': UserProfileSerializer(user).data})

    def patch(self, request, pk):
        caller = USER.get(request.email, {})
        caller_role = caller.get('role', '')
        if caller_role not in ('ADMIN', 'CLIENT_ADMIN'):
            return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        user, err = self._get_user(pk, caller_role, request.tenant_id)
        if err:
            return err

        data = dict(request.data)
        # CLIENT_ADMIN cannot escalate roles beyond their scope
        if caller_role == 'CLIENT_ADMIN':
            allowed_roles = ('CLIENT_ADMIN', 'CLIENT_USER')
            if 'role' in data and data['role'] not in allowed_roles:
                return Response({'error': 'Cannot assign that role.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserUpdateSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': UserProfileSerializer(user).data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDeactivateView(APIView):
    """
    POST /portal/users/<pk>/deactivate
    POST /portal/users/<pk>/activate
    """

    def _toggle(self, request, pk, active: bool):
        caller = USER.get(request.email, {})
        caller_role = caller.get('role', '')
        if caller_role not in ('ADMIN', 'CLIENT_ADMIN'):
            return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        user = UserProfile.objects.filter(pk=pk).first()
        if not user:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if caller_role == 'CLIENT_ADMIN' and user.tenant_id != request.tenant_id:
            return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        user.is_active = active
        user.save(update_fields=['is_active', 'updated_at'])
        return Response({'data': UserProfileSerializer(user).data})

    def post(self, request, pk, action):
        if action == 'deactivate':
            return self._toggle(request, pk, False)
        elif action == 'activate':
            return self._toggle(request, pk, True)
        return Response({'error': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)


class StaticUserListView(APIView):
    """
    GET /portal/users/static — returns all users from constant.py (seed/dev reference)
    Internal only.
    """

    @require_permission('MEMBER_VIEW')
    def get(self, request):
        caller = USER.get(request.email, {})
        caller_role = caller.get('role', '')

        result = []
        for email, u in USER.items():
            if caller_role == 'CLIENT_ADMIN' and u.get('tenant_id') != request.tenant_id:
                continue
            result.append({
                'user_id': u['user_id'],
                'user_name': u['user_name'],
                'email': email,
                'role': u['role'],
                'tenant_id': u.get('tenant_id'),
            })
        return Response({'data': result})
