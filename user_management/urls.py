from django.urls import path
from .views import (
    RolePermissionMapView,
    UserListView, UserCreateView, UserDetailView,
    UserDeactivateView, UserMentionListView,
)

urlpatterns = [
    path('role-permissions', RolePermissionMapView.as_view(), name='role-permissions'),
    path('',                 UserListView.as_view(),           name='user-list'),
    path('create',           UserCreateView.as_view(),         name='user-create'),
    path('mentions',         UserMentionListView.as_view(),    name='user-mentions'),
    path('<int:pk>',         UserDetailView.as_view(),         name='user-detail'),
    path('<int:pk>/<str:action>', UserDeactivateView.as_view(), name='user-toggle'),
]
