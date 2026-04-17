from django.urls import path
from .views import (
    OnboardingProjectListView, OnboardingProjectCreateView, OnboardingProjectDetailView,
    OnboardingPhaseView, OnboardingPhaseDetailView,
    OnboardingTaskView, OnboardingTaskDetailView,
    FeatureListView, FeatureCreateView, FeatureDetailView, FeatureVoteView,
    FeatureRequestListView, FeatureRequestCreateView, FeatureRequestDetailView,
    ReleaseListView, ReleaseCreateView, ReleaseDetailView,
    BugListView, BugCreateView, BugDetailView, BugStatsView,
)

urlpatterns = [
    # Onboarding
    path('onboarding', OnboardingProjectListView.as_view(), name='onboarding-list'),
    path('onboarding/create', OnboardingProjectCreateView.as_view(), name='onboarding-create'),
    path('onboarding/<int:pk>', OnboardingProjectDetailView.as_view(), name='onboarding-detail'),
    path('onboarding/<int:project_pk>/phases', OnboardingPhaseView.as_view(), name='onboarding-phase-create'),
    path('phases/<int:pk>', OnboardingPhaseDetailView.as_view(), name='onboarding-phase-detail'),
    path('phases/<int:phase_pk>/tasks', OnboardingTaskView.as_view(), name='onboarding-task-create'),
    path('tasks/<int:pk>', OnboardingTaskDetailView.as_view(), name='onboarding-task-detail'),

    # Features / Roadmap
    path('features', FeatureListView.as_view(), name='feature-list'),
    path('features/create', FeatureCreateView.as_view(), name='feature-create'),
    path('features/<int:pk>', FeatureDetailView.as_view(), name='feature-detail'),
    path('features/<int:pk>/vote', FeatureVoteView.as_view(), name='feature-vote'),

    # Feature Requests
    path('feature-requests', FeatureRequestListView.as_view(), name='feature-request-list'),
    path('feature-requests/create', FeatureRequestCreateView.as_view(), name='feature-request-create'),
    path('feature-requests/<int:pk>', FeatureRequestDetailView.as_view(), name='feature-request-detail'),

    # Releases
    path('releases', ReleaseListView.as_view(), name='release-list'),
    path('releases/create', ReleaseCreateView.as_view(), name='release-create'),
    path('releases/<int:pk>', ReleaseDetailView.as_view(), name='release-detail'),

    # Bugs
    path('bugs', BugListView.as_view(), name='bug-list'),
    path('bugs/create', BugCreateView.as_view(), name='bug-create'),
    path('bugs/stats', BugStatsView.as_view(), name='bug-stats'),
    path('bugs/<int:pk>', BugDetailView.as_view(), name='bug-detail'),
]
