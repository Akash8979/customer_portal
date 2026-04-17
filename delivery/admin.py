from django.contrib import admin
from .models import OnboardingProject, OnboardingPhase, OnboardingTask, Feature, FeatureRequest, FeatureVote, Release, Bug

admin.site.register(OnboardingProject)
admin.site.register(OnboardingPhase)
admin.site.register(OnboardingTask)
admin.site.register(Feature)
admin.site.register(FeatureRequest)
admin.site.register(FeatureVote)
admin.site.register(Release)
admin.site.register(Bug)
