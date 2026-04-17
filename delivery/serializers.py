from rest_framework import serializers
from .models import (
    OnboardingProject, OnboardingPhase, OnboardingTask,
    Feature, FeatureRequest, FeatureVote,
    Release, Bug,
)


# ── Onboarding ────────────────────────────────────────────────────────────────

class OnboardingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingTask
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class OnboardingPhaseSerializer(serializers.ModelSerializer):
    tasks = OnboardingTaskSerializer(many=True, read_only=True)
    completion_pct = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingPhase
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_completion_pct(self, obj):
        return obj.completion_percentage()


class OnboardingProjectSerializer(serializers.ModelSerializer):
    phases = OnboardingPhaseSerializer(many=True, read_only=True)
    overall_completion_pct = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingProject
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_overall_completion_pct(self, obj):
        tasks = OnboardingTask.objects.filter(phase__project=obj)
        if not tasks.exists():
            return 0
        done = tasks.filter(status='COMPLETED').count()
        return round((done / tasks.count()) * 100)


class OnboardingProjectListSerializer(serializers.ModelSerializer):
    overall_completion_pct = serializers.SerializerMethodField()
    phase_count = serializers.SerializerMethodField()
    blocker_count = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingProject
        fields = [
            'id', 'tenant_id', 'tenant_name', 'assigned_lead', 'status',
            'health_score', 'estimated_go_live', 'actual_go_live',
            'overall_completion_pct', 'phase_count', 'blocker_count',
            'created_at', 'updated_at',
        ]

    def get_overall_completion_pct(self, obj):
        tasks = OnboardingTask.objects.filter(phase__project=obj)
        if not tasks.exists():
            return 0
        done = tasks.filter(status='COMPLETED').count()
        return round((done / tasks.count()) * 100)

    def get_phase_count(self, obj):
        return obj.phases.count()

    def get_blocker_count(self, obj):
        return OnboardingTask.objects.filter(phase__project=obj, is_blocker=True, status__in=['TODO', 'IN_PROGRESS', 'BLOCKED']).count()


# ── Feature & Release ─────────────────────────────────────────────────────────

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = '__all__'
        read_only_fields = ['id', 'vote_count', 'created_at', 'updated_at']


class FeatureRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureRequest
        fields = '__all__'
        read_only_fields = ['id', 'upvotes', 'created_at', 'updated_at']


class FeatureVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureVote
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class ReleaseSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True, read_only=True)
    bug_count = serializers.SerializerMethodField()

    class Meta:
        model = Release
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_bug_count(self, obj):
        return obj.bugs.count()


class ReleaseListSerializer(serializers.ModelSerializer):
    feature_count = serializers.SerializerMethodField()
    bug_count = serializers.SerializerMethodField()

    class Meta:
        model = Release
        fields = [
            'id', 'version', 'title', 'summary', 'status', 'is_hotfix',
            'release_date', 'published_at', 'created_by',
            'feature_count', 'bug_count', 'created_at', 'updated_at',
        ]

    def get_feature_count(self, obj):
        return obj.features.count()

    def get_bug_count(self, obj):
        return obj.bugs.count()


# ── Bug ───────────────────────────────────────────────────────────────────────

class BugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bug
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class BugListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bug
        fields = [
            'id', 'title', 'severity', 'status', 'assignee',
            'affected_tenants', 'linked_ticket_ids', 'linked_release_id',
            'created_by', 'deployed_at', 'created_at', 'updated_at',
        ]
