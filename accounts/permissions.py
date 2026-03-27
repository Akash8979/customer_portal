from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allows access only to users with ADMIN role."""

    message = 'Admin role required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, 'profile')
            and request.user.profile.role is not None
            and request.user.profile.role.name == 'ADMIN'
        )


class HasRolePermission(BasePermission):
    """
    Checks that the authenticated user's role includes the permission
    declared on the view as `required_permission`.

    Example on a ViewSet:
        required_permission = 'customer:write'

    ADMIN role bypasses all permission checks.
    """

    message = 'You do not have permission to perform this action.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'profile'):
            return False
        required = getattr(view, 'required_permission', None)
        if required is None:
            return True
        return request.user.profile.has_permission(required)
