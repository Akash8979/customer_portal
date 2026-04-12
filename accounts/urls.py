from django.urls import path
from .views import LoginView, LogoutView, RefreshTokenView, MeView

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('token/refresh', RefreshTokenView.as_view(), name='token-refresh'),
    path('auth/session', MeView.as_view(), name='session'),
]
