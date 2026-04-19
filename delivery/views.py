import math
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.decorators import require_permission
from accounts.audit import log_action
from .models import (
    OnboardingProject, OnboardingPhase, OnboardingTask,
    Feature, FeatureRequest, FeatureVote,
    Release, Bug,
)
from .serializers import (
    OnboardingProjectSerializer, OnboardingProjectListSerializer,
    OnboardingPhaseSerializer, OnboardingTaskSerializer,
    FeatureSerializer, FeatureRequestSerializer, FeatureVoteSerializer,
    ReleaseSerializer, ReleaseListSerializer,
    BugSerializer, BugListSerializer,
)


def paginate(qs, request, serializer_class, **kwargs):
    total = qs.count()
    try:
        page = max(1, int(request.query_params.get('page', 1)))
        page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
    except ValueError:
        page, page_size = 1, 20
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    page = min(page, total_pages) if total_pages > 0 else 1
    offset = (page - 1) * page_size
    data = serializer_class(qs[offset:offset + page_size], many=True, **kwargs).data
    return Response({'data': data, 'total': total, 'page': page, 'page_size': page_size, 'total_pages': total_pages})


# ── Onboarding ────────────────────────────────────────────────────────────────

class OnboardingProjectListView(APIView):
    """GET /delivery/onboarding — list all (internal) or own tenant (client)"""

    def get(self, request):
        role = request.role or ''
        if request.tenant_id:
            qs = OnboardingProject.objects.filter(tenant_id=request.tenant_id)
        else:
            qs = OnboardingProject.objects.all()

        health = request.query_params.get('health_score')
        if health:
            qs = qs.filter(health_score=health)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return paginate(qs, request, OnboardingProjectListSerializer)


class OnboardingProjectCreateView(APIView):
    """POST /delivery/onboarding — admin/lead only"""

    @require_permission('TICKET_VIEW_ALL')
    def post(self, request):
        serializer = OnboardingProjectSerializer(data=request.data)
        if serializer.is_valid():
            project = serializer.save()
            return Response({'data': OnboardingProjectSerializer(project).data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingProjectDetailView(APIView):
    """GET/PATCH /delivery/onboarding/<pk>"""

    def _get(self, pk, tenant_id=None):
        qs = OnboardingProject.objects.filter(pk=pk)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs.first()

    def get(self, request, pk):
        role = request.role or ''
        tenant_id = request.tenant_id or None
        project = self._get(pk, tenant_id)
        if not project:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'data': OnboardingProjectSerializer(project).data})

    @require_permission('TICKET_VIEW_ALL')
    def patch(self, request, pk):
        project = OnboardingProject.objects.filter(pk=pk).first()
        if not project:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = OnboardingProjectSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingPhaseView(APIView):
    """POST /delivery/onboarding/<project_pk>/phases"""

    @require_permission('TICKET_VIEW_ALL')
    def post(self, request, project_pk):
        project = OnboardingProject.objects.filter(pk=project_pk).first()
        if not project:
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = OnboardingPhaseSerializer(data={**request.data, 'project': project_pk})
        if serializer.is_valid():
            phase = serializer.save()
            return Response({'data': OnboardingPhaseSerializer(phase).data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingPhaseDetailView(APIView):
    """PATCH /delivery/phases/<pk>"""

    @require_permission('TICKET_VIEW_ALL')
    def patch(self, request, pk):
        phase = OnboardingPhase.objects.filter(pk=pk).first()
        if not phase:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = OnboardingPhaseSerializer(phase, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingTaskView(APIView):
    """POST /delivery/phases/<phase_pk>/tasks"""

    @require_permission('TICKET_VIEW_ALL')
    def post(self, request, phase_pk):
        phase = OnboardingPhase.objects.filter(pk=phase_pk).first()
        if not phase:
            return Response({'error': 'Phase not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = OnboardingTaskSerializer(data={**request.data, 'phase': phase_pk})
        if serializer.is_valid():
            task = serializer.save()
            return Response({'data': OnboardingTaskSerializer(task).data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingTaskDetailView(APIView):
    """PATCH /delivery/tasks/<pk>"""

    def patch(self, request, pk):
        task = OnboardingTask.objects.filter(pk=pk).first()
        if not task:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = OnboardingTaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            if updated.status == 'COMPLETED' and not updated.completed_at:
                updated.completed_at = timezone.now()
                updated.save(update_fields=['completed_at'])
            return Response({'data': OnboardingTaskSerializer(updated).data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Feature ───────────────────────────────────────────────────────────────────

class FeatureListView(APIView):
    """GET /delivery/features — roadmap (public + status filter)"""

    def get(self, request):
        role = request.role or ''
        qs = Feature.objects.all()
        if request.tenant_id:
            qs = qs.filter(is_public=True)

        for field in ('status', 'quarter', 'year', 'assignee'):
            val = request.query_params.get(field)
            if val:
                qs = qs.filter(**{field: val})

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        return paginate(qs, request, FeatureSerializer)


class FeatureCreateView(APIView):
    """POST /delivery/features"""

    @require_permission('TICKET_VIEW_ALL')
    def post(self, request):
        serializer = FeatureSerializer(data=request.data)
        if serializer.is_valid():
            feature = serializer.save()
            return Response({'data': FeatureSerializer(feature).data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeatureDetailView(APIView):
    """GET/PATCH /delivery/features/<pk>"""

    def get(self, request, pk):
        feature = Feature.objects.filter(pk=pk).first()
        if not feature:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'data': FeatureSerializer(feature).data})

    @require_permission('TICKET_VIEW_ALL')
    def patch(self, request, pk):
        feature = Feature.objects.filter(pk=pk).first()
        if not feature:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = FeatureSerializer(feature, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeatureVoteView(APIView):
    """POST /delivery/features/<pk>/vote"""

    def post(self, request, pk):
        feature = Feature.objects.filter(pk=pk, is_public=True).first()
        if not feature:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        _, created = FeatureVote.objects.get_or_create(
            feature=feature,
            user_email=request.email,
            defaults={'tenant_id': request.tenant_id or ''},
        )
        if created:
            feature.vote_count += 1
            feature.save(update_fields=['vote_count'])
            return Response({'data': 'Vote registered.'}, status=status.HTTP_201_CREATED)
        return Response({'data': 'Already voted.'}, status=status.HTTP_200_OK)


class FeatureRequestListView(APIView):
    """GET /delivery/feature-requests"""

    def get(self, request):
        role = request.role or ''
        qs = FeatureRequest.objects.all()
        if request.tenant_id:
            qs = qs.filter(tenant_id=request.tenant_id)

        for field in ('status', 'tenant_id'):
            val = request.query_params.get(field)
            if val:
                qs = qs.filter(**{field: val})

        return paginate(qs, request, FeatureRequestSerializer)


class FeatureRequestCreateView(APIView):
    """POST /delivery/feature-requests"""

    @require_permission('TICKET_CREATE')
    def post(self, request):
        data = {**request.data, 'tenant_id': request.tenant_id, 'requested_by': request.email}
        serializer = FeatureRequestSerializer(data=data)
        if serializer.is_valid():
            fr = serializer.save()
            return Response({'data': FeatureRequestSerializer(fr).data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeatureRequestDetailView(APIView):
    """PATCH /delivery/feature-requests/<pk>"""

    @require_permission('TICKET_VIEW_ALL')
    def patch(self, request, pk):
        fr = FeatureRequest.objects.filter(pk=pk).first()
        if not fr:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = FeatureRequestSerializer(fr, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Release ───────────────────────────────────────────────────────────────────

class ReleaseListView(APIView):
    """GET /delivery/releases"""

    def get(self, request):
        qs = Release.objects.all()
        role = request.role or ''
        if request.tenant_id:
            qs = qs.filter(status=Release.STATUS_PUBLISHED)

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        hotfix = request.query_params.get('is_hotfix')
        if hotfix is not None:
            qs = qs.filter(is_hotfix=hotfix.lower() == 'true')

        return paginate(qs, request, ReleaseListSerializer)


class ReleaseCreateView(APIView):
    """POST /delivery/releases"""

    @require_permission('TICKET_VIEW_ALL')
    def post(self, request):
        data = {**request.data, 'created_by': request.email}
        serializer = ReleaseSerializer(data=data)
        if serializer.is_valid():
            release = serializer.save()
            return Response({'data': ReleaseSerializer(release).data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReleaseDetailView(APIView):
    """GET/PATCH /delivery/releases/<pk>"""

    def get(self, request, pk):
        release = Release.objects.filter(pk=pk).first()
        if not release:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'data': ReleaseSerializer(release).data})

    @require_permission('TICKET_VIEW_ALL')
    def patch(self, request, pk):
        release = Release.objects.filter(pk=pk).first()
        if not release:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReleaseSerializer(release, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            if updated.status == Release.STATUS_PUBLISHED and not updated.published_at:
                updated.published_at = timezone.now()
                updated.save(update_fields=['published_at'])
            return Response({'data': ReleaseSerializer(updated).data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Bug ───────────────────────────────────────────────────────────────────────

class BugListView(APIView):
    """GET /delivery/bugs — internal only"""

    @require_permission('TICKET_VIEW_ALL')
    def get(self, request):
        qs = Bug.objects.all()

        for field in ('severity', 'status', 'assignee'):
            val = request.query_params.get(field)
            if val:
                qs = qs.filter(**{field: val})

        tenant = request.query_params.get('tenant_id')
        if tenant:
            qs = qs.filter(affected_tenants__contains=[tenant])

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        return paginate(qs, request, BugListSerializer)


class BugCreateView(APIView):
    """POST /delivery/bugs"""

    @require_permission('TICKET_VIEW_ALL')
    def post(self, request):
        data = {**request.data, 'created_by': request.email}
        serializer = BugSerializer(data=data)
        if serializer.is_valid():
            bug = serializer.save()
            log_action(request, 'BUG_CREATE', 'BUG', bug.id,
                       {'title': bug.title, 'severity': bug.severity})
            return Response({'data': BugSerializer(bug).data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BugDetailView(APIView):
    """GET/PATCH /delivery/bugs/<pk>"""

    @require_permission('TICKET_VIEW_ALL')
    def get(self, request, pk):
        bug = Bug.objects.filter(pk=pk).first()
        if not bug:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'data': BugSerializer(bug).data})

    @require_permission('TICKET_VIEW_ALL')
    def patch(self, request, pk):
        bug = Bug.objects.filter(pk=pk).first()
        if not bug:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        old_status = bug.status
        serializer = BugSerializer(bug, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            if updated.status == Bug.STATUS_DEPLOYED and not updated.deployed_at:
                updated.deployed_at = timezone.now()
                updated.save(update_fields=['deployed_at'])
            if old_status != updated.status:
                log_action(request, 'BUG_STATUS_UPDATE', 'BUG', pk,
                           {'from': old_status, 'to': updated.status})
            else:
                log_action(request, 'BUG_UPDATE', 'BUG', pk, {'title': updated.title})
            return Response({'data': BugSerializer(updated).data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BugStatsView(APIView):
    """GET /delivery/bugs/stats — aging + severity breakdown"""

    @require_permission('TICKET_VIEW_ALL')
    def get(self, request):
        from django.utils.timezone import now
        from datetime import timedelta
        now_ = now()
        open_qs = Bug.objects.exclude(status__in=[Bug.STATUS_CLOSED, Bug.STATUS_VERIFIED])

        return Response({'data': {
            'total_open': open_qs.count(),
            'critical': open_qs.filter(severity=Bug.SEVERITY_CRITICAL).count(),
            'high': open_qs.filter(severity=Bug.SEVERITY_HIGH).count(),
            'medium': open_qs.filter(severity=Bug.SEVERITY_MEDIUM).count(),
            'low': open_qs.filter(severity=Bug.SEVERITY_LOW).count(),
            'aging_7d': open_qs.filter(created_at__lt=now_ - timedelta(days=7)).count(),
            'aging_14d': open_qs.filter(created_at__lt=now_ - timedelta(days=14)).count(),
            'aging_30d': open_qs.filter(created_at__lt=now_ - timedelta(days=30)).count(),
        }})
