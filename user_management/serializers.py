from rest_framework import serializers
from accounts.constant import ROLES
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user_name', 'email', 'role', 'tenant_id', 'tenant_name',
            'is_active', 'custom_permissions', 'permissions',
            'last_login', 'invited_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'last_login', 'created_at', 'updated_at', 'permissions']

    def get_permissions(self, obj):
        base = ROLES.get(obj.role, [])
        extras = obj.custom_permissions or []
        return sorted(set(base + extras))


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = UserProfile
        fields = [
            'user_name', 'email', 'password', 'role',
            'tenant_id', 'tenant_name', 'custom_permissions',
        ]

    def validate_email(self, value):
        if UserProfile.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        raw_password = validated_data.pop('password')
        user = UserProfile(**validated_data)
        user.set_password(raw_password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user_name', 'role', 'tenant_id', 'tenant_name', 'is_active', 'custom_permissions']


class RolePermissionMapSerializer(serializers.Serializer):
    """Returns the full permission set for every role — used by the UI to render the permission matrix."""
    roles = serializers.SerializerMethodField()

    def get_roles(self, _):
        return {role: sorted(perms) for role, perms in ROLES.items()}
