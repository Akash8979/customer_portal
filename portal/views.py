import math
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.decorators import require_permission
from accounts.audit import log_action
from .models import Ticket, Comment, TicketHistory, AuditLog, SLAPolicy
from .services.email_service import (
    send_ticket_created_email,
    send_ticket_updated_email,
    send_comment_created_email,
    send_comment_updated_email,
)
from .services.notification_service import notify_ticket_created
from .services.sla_service import initialize_sla_for_ticket
from .publishers import publish_ticket_created, publish_ticket_status, publish_new_comment
from .serializers import (
    TicketCreateSerializer,
    TicketSerializer,
    TicketStatusUpdateSerializer,
    TicketUpdateSerializer,
    CommentCreateSerializer,
    CommentUpdateSerializer,
    CommentSerializer,
    TicketHistorySerializer,
)

class TicketCreateView(APIView):
    """
    POST /api/portal/tickets/
    Body: {
        "title": "...", "description": "...", "category": "SUPPORT",
        "priority": "HIGH", "created_by": "user@example.com",
        "attachment_ids": [1, 2, 3]
    }
    """

    @require_permission('TICKET_CREATE')
    def post(self, request):
        serializer = TicketCreateSerializer(data={**request.data,"created_by":request.created_by})
        if serializer.is_valid():
            ticket = serializer.save(tenant_id=request.tenant_id)
            initialize_sla_for_ticket(ticket)
            # publish_ticket_created(request.tenant_id, ticket)
            # send_ticket_created_email(ticket)
            notify_ticket_created(ticket)
            log_action(request, 'TICKET_CREATE', 'TICKET', ticket.id,
                       {'title': ticket.title, 'priority': ticket.priority, 'category': ticket.category})
            data = TicketSerializer(ticket).data
            return Response({"data":data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketListView(APIView):
    """
    GET /portal/tickets/list?tenant_id=<tenant_id>

    Query params:
      Pagination : page (default 1), page_size (default 10, max 100)
      Search     : search — matches against title, description
      Filters    : status, priority, category, assigned_to, created_by
    """

    def get(self, request):
        # role = request.role or ''
        if request.tenant_id:
            qs = Ticket.objects.filter(tenant_id=request.tenant_id)
        else:
            qs = Ticket.objects.all()

        # --- Search ---
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # --- Filters ---
        for field in ('status', 'priority', 'category', 'assigned_to', 'created_by'):
            value = request.query_params.get(field, '').strip()
            if value:
                qs = qs.filter(**{field: value})

        # --- Pagination ---
        total = qs.count()
        try:
            page = max(1, int(request.query_params.get('page', 1)))
            page_size = min(100, max(1, int(request.query_params.get('page_size', 10))))
        except ValueError:
            page, page_size = 1, 10

        import math
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        page = min(page, total_pages) if total_pages > 0 else 1
        offset = (page - 1) * page_size

        tickets = qs[offset: offset + page_size]
        data = TicketSerializer(tickets, many=True).data

        return Response({
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        })


class TicketDetailView(APIView):
    """
    GET /api/portal/tickets/<id>/
    """

    def get(self, _request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response({'error': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)
        data = TicketSerializer(ticket).data
        return Response({"data":data})


class TicketUpdateView(APIView):
    """
    PATCH /api/portal/tickets/<id>/update/
    Body: {
        "title": "...", "status": "IN_PROGRESS", "priority": "HIGH",
        "attachment_ids": [4, 5]   (appends new attachments, does not replace)
    }
    """

    def patch(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response({'error': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Capture before-state for tracked fields
        tracked_fields = ['title', 'description', 'status', 'priority', 'severity', 'category', 'assigned_to']
        before = {f: str(getattr(ticket, f) or '') for f in tracked_fields}

        serializer = TicketUpdateSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            # send_ticket_updated_email(updated)

            # Record one history entry per changed field
            user_id = getattr(request, 'user_id', None)
            for field in tracked_fields:
                new_val = str(getattr(updated, field) or '')
                if new_val != before[field]:
                    TicketHistory.objects.create(
                        ticket_id=pk,
                        user_id=user_id,
                        action=f'updated_{field}',
                        field_name=field,
                        old_value=before[field] or None,
                        new_value=new_val or None,
                    )

            log_action(request, 'TICKET_UPDATE', 'TICKET', pk,
                       {'changed_fields': [f for f in tracked_fields if str(getattr(updated, f) or '') != before[f]]})
            data = TicketSerializer(updated).data
            return Response({"data": data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentCreateView(APIView):
    """
    POST /api/portal/comments/
    Body: {
        "ticket_id": 1, "user_id": 1, "message": "...",
        "parent_id": null,           (optional — for replies)
        "attachment_ids": [1, 2]     (optional — links via TicketAttachment)
    }
    """

    def post(self, request):
        serializer = CommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Use ticket's tenant_id so internal-user comments are visible to clients
            ticket_id = serializer.validated_data.get('ticket_id')
            tenant_id = request.tenant_id
            if not tenant_id and ticket_id:
                t = Ticket.objects.filter(pk=ticket_id).first()
                if t:
                    tenant_id = t.tenant_id
            comment = serializer.save(tenant_id=tenant_id)
            log_action(request, 'COMMENT_CREATE', 'COMMENT', comment.id,
                       {'ticket_id': ticket_id})
            data = CommentSerializer(comment).data
            return Response({"data":data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentUpdateView(APIView):
    """
    PATCH /api/portal/comments/<id>/update/
    Body: {
        "message": "...",
        "attachment_ids": [3],        (optional — appends new attachments)
        "mentioned_user_ids": [2, 5]  (optional — adds new mentions)
    }
    """

    def patch(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk, is_deleted=False)
        except Comment.DoesNotExist:
            return Response({'error': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CommentUpdateSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            ticket = Ticket.objects.filter(pk=updated.ticket_id).first()
            # if ticket:
            #     send_comment_updated_email(updated, ticket)
            data = CommentSerializer(updated).data    
            return Response({"data":data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketKPIView(APIView):
    """
    GET /portal/tickets/kpis?tenant_id=<tenant_id>
    Returns an overview of ticket counts grouped by status and priority.
    """

    def get(self, request):
        role = request.role or ''
        if request.tenant_id:
            qs = Ticket.objects.filter(tenant_id=request.tenant_id)
        else:
            qs = Ticket.objects.all()

        status_counts = qs.aggregate(
            open=Count('id', filter=Q(status=Ticket.STATUS_OPEN)),
            acknowledged=Count('id', filter=Q(status=Ticket.STATUS_ACKNOWLEDGED)),
            in_progress=Count('id', filter=Q(status=Ticket.STATUS_IN_PROGRESS)),
            resolved=Count('id', filter=Q(status=Ticket.STATUS_RESOLVED)),
            closed=Count('id', filter=Q(status=Ticket.STATUS_CLOSED)),
            reopened=Count('id', filter=Q(status=Ticket.STATUS_REOPENED)),
        )

        priority_counts = qs.aggregate(
            low=Count('id', filter=Q(priority=Ticket.PRIORITY_LOW)),
            medium=Count('id', filter=Q(priority=Ticket.PRIORITY_MEDIUM)),
            high=Count('id', filter=Q(priority=Ticket.PRIORITY_HIGH)),
            critical=Count('id', filter=Q(priority=Ticket.PRIORITY_CRITICAL)),
        )

        return Response({
            "data": {
                "total": qs.count(),
                "by_status": status_counts,
                "by_priority": priority_counts,
            }
        })


class TicketStatusUpdateView(APIView):
    """
    PATCH /portal/tickets/<pk>/status?tenant_id=<tenant_id>
    Body: { "status": "IN_PROGRESS" }
    """

    def patch(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk, tenant_id=request.tenant_id)
        except Ticket.DoesNotExist:
            return Response({'error': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)

        old_status = ticket.status
        serializer = TicketStatusUpdateSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            ticket.refresh_from_db()
            log_action(request, 'TICKET_STATUS_UPDATE', 'TICKET', pk,
                       {'from': old_status, 'to': ticket.status})
            data = TicketSerializer(ticket).data
            return Response({'data': data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketCommentListView(APIView):
    """
    GET /portal/tickets/<pk>/comments?tenant_id=<tenant_id>
    Returns all non-deleted comments for a ticket with their attachments and mentions.
    """

    def get(self, request, pk):
        role = request.role or ''
        is_internal = role in ('AGENT', 'LEAD', 'ADMIN')

        ticket_qs = Ticket.objects.filter(pk=pk)
        if not is_internal:
            ticket_qs = ticket_qs.filter(tenant_id=request.tenant_id)
        if not ticket_qs.exists():
            return Response({'error': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)

        comments = Comment.objects.filter(ticket_id=pk, is_deleted=False)
        if not is_internal:
            comments = comments.filter(tenant_id=request.tenant_id)

        data = CommentSerializer(comments, many=True).data
        return Response({'data': data})


class TicketHistoryView(APIView):
    """
    GET /portal/tickets/<pk>/history
    Returns the audit trail for a ticket — one entry per field change.
    """

    def get(self, request, pk):
        if not Ticket.objects.filter(pk=pk).exists():
            return Response({'error': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)
        history = TicketHistory.objects.filter(ticket_id=pk)
        data = TicketHistorySerializer(history, many=True).data
        return Response({'data': data})


class TicketAttachmentView(APIView):
    """
    POST /api/portal/attachments/
    Body: {"file_name": "log.txt","file_type": "text/plain","file_path": "/uploads/log.txt","metadata": {}}
    """

    def post(self, request):
        from .serializers import AttachmentSerializer
        serializer = AttachmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=request.tenant_id)
            data = serializer.data
            return Response({"data":data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuditLogListView(APIView):
    """
    GET /portal/audit-logs
    ADMIN-only. Filterable by action, resource_type, user_id, search, from_date, to_date.
    """

    @require_permission('AUDIT_VIEW')
    def get(self, request):
        qs = AuditLog.objects.all()

        action_filter = request.query_params.get('action', '').strip()
        if action_filter:
            qs = qs.filter(action=action_filter)

        resource_type = request.query_params.get('resource_type', '').strip()
        if resource_type:
            qs = qs.filter(resource_type=resource_type)

        user_id_filter = request.query_params.get('user_id', '').strip()
        if user_id_filter:
            qs = qs.filter(user_id=user_id_filter)

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(user_name__icontains=search) |
                Q(action__icontains=search) |
                Q(resource_type__icontains=search) |
                Q(resource_id__icontains=search)
            )

        from_date = request.query_params.get('from_date', '').strip()
        if from_date:
            qs = qs.filter(created_at__date__gte=from_date)

        to_date = request.query_params.get('to_date', '').strip()
        if to_date:
            qs = qs.filter(created_at__date__lte=to_date)

        total = qs.count()
        try:
            page = max(1, int(request.query_params.get('page', 1)))
            page_size = min(100, max(1, int(request.query_params.get('page_size', 50))))
        except ValueError:
            page, page_size = 1, 50

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        page = min(page, total_pages) if total_pages > 0 else 1
        offset = (page - 1) * page_size

        rows = qs[offset:offset + page_size]
        data = [
            {
                'id':            r.id,
                'user_id':       r.user_id,
                'user_name':     r.user_name,
                'user_role':     r.user_role,
                'tenant_id':     r.tenant_id,
                'action':        r.action,
                'resource_type': r.resource_type,
                'resource_id':   r.resource_id,
                'detail':        r.detail,
                'ip_address':    r.ip_address,
                'created_at':    r.created_at.isoformat(),
            }
            for r in rows
        ]
        return Response({'data': data, 'total': total, 'page': page, 'page_size': page_size, 'total_pages': total_pages})


PRIORITY_ORDER = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']


class SLAPolicyListView(APIView):
    """
    GET  /api/portal/sla-policies          — list all policies (optionally filter by tenant_id)
    POST /api/portal/sla-policies          — create or upsert a policy
    """

    @require_permission('view_tickets')
    def get(self, request):
        qs = SLAPolicy.objects.all().order_by('tenant_id', 'priority')
        tenant_id = request.query_params.get('tenant_id', '').strip()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)

        data = [
            {
                'id': p.id,
                'tenant_id': p.tenant_id,
                'priority': p.priority,
                'response_time_minutes': p.response_time_minutes,
                'resolution_time_minutes': p.resolution_time_minutes,
                'updated_at': p.updated_at.isoformat(),
            }
            for p in qs
        ]
        return Response({'data': data, 'total': len(data)})

    @require_permission('manage_users')
    def post(self, request):
        tenant_id = (request.data.get('tenant_id') or '').strip()
        priority = (request.data.get('priority') or '').strip().upper()
        response_time = request.data.get('response_time_minutes')
        resolution_time = request.data.get('resolution_time_minutes')

        if not tenant_id:
            return Response({'error': 'tenant_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if priority not in PRIORITY_ORDER:
            return Response({'error': f'priority must be one of {PRIORITY_ORDER}.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            response_time = int(response_time)
            resolution_time = int(resolution_time)
            if response_time < 1 or resolution_time < 1:
                raise ValueError
        except (TypeError, ValueError):
            return Response({'error': 'response_time_minutes and resolution_time_minutes must be positive integers.'}, status=status.HTTP_400_BAD_REQUEST)

        policy, created = SLAPolicy.objects.update_or_create(
            tenant_id=tenant_id,
            priority=priority,
            defaults={
                'response_time_minutes': response_time,
                'resolution_time_minutes': resolution_time,
            },
        )
        log_action(request, 'SLA_POLICY_UPSERT', 'SLA_POLICY', policy.id,
                   {'tenant_id': tenant_id, 'priority': priority,
                    'response_time_minutes': response_time, 'resolution_time_minutes': resolution_time})
        return Response({
            'id': policy.id,
            'tenant_id': policy.tenant_id,
            'priority': policy.priority,
            'response_time_minutes': policy.response_time_minutes,
            'resolution_time_minutes': policy.resolution_time_minutes,
            'updated_at': policy.updated_at.isoformat(),
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class SLAPolicyDetailView(APIView):
    """
    PATCH  /api/portal/sla-policies/<pk>   — update a policy
    DELETE /api/portal/sla-policies/<pk>   — delete a policy
    """

    def _get(self, pk):
        try:
            return SLAPolicy.objects.get(pk=pk)
        except SLAPolicy.DoesNotExist:
            return None

    @require_permission('manage_users')
    def patch(self, request, pk):
        policy = self._get(pk)
        if not policy:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if 'response_time_minutes' in request.data:
            try:
                val = int(request.data['response_time_minutes'])
                if val < 1:
                    raise ValueError
                policy.response_time_minutes = val
            except (TypeError, ValueError):
                return Response({'error': 'response_time_minutes must be a positive integer.'}, status=status.HTTP_400_BAD_REQUEST)

        if 'resolution_time_minutes' in request.data:
            try:
                val = int(request.data['resolution_time_minutes'])
                if val < 1:
                    raise ValueError
                policy.resolution_time_minutes = val
            except (TypeError, ValueError):
                return Response({'error': 'resolution_time_minutes must be a positive integer.'}, status=status.HTTP_400_BAD_REQUEST)

        policy.save()
        log_action(request, 'SLA_POLICY_UPDATE', 'SLA_POLICY', policy.id,
                   {'tenant_id': policy.tenant_id, 'priority': policy.priority,
                    'response_time_minutes': policy.response_time_minutes,
                    'resolution_time_minutes': policy.resolution_time_minutes})
        return Response({
            'id': policy.id,
            'tenant_id': policy.tenant_id,
            'priority': policy.priority,
            'response_time_minutes': policy.response_time_minutes,
            'resolution_time_minutes': policy.resolution_time_minutes,
            'updated_at': policy.updated_at.isoformat(),
        })

    @require_permission('manage_users')
    def delete(self, request, pk):
        policy = self._get(pk)
        if not policy:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        log_action(request, 'SLA_POLICY_DELETE', 'SLA_POLICY', policy.id,
                   {'tenant_id': policy.tenant_id, 'priority': policy.priority})
        policy.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
