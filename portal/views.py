from django.db.models import Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.decorators import require_permission
from .models import Ticket, Comment
from .services.email_service import (
    send_ticket_created_email,
    send_ticket_updated_email,
    send_comment_created_email,
    send_comment_updated_email,
)
from .services.notification_service import notify_ticket_created
from .serializers import (
    TicketCreateSerializer,
    TicketSerializer,
    TicketUpdateSerializer,
    CommentCreateSerializer,
    CommentUpdateSerializer,
    CommentSerializer,
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

    @require_permission('CREATE')
    def post(self, request):
        serializer = TicketCreateSerializer(data={**request.data,"created_by":request.created_by})
        if serializer.is_valid():
            ticket = serializer.save(tenant_id=request.tenant_id)
            # send_ticket_created_email(ticket)
            notify_ticket_created(ticket)
            data = TicketSerializer(ticket).data
            return Response({"data":data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketListView(APIView):
    """
    GET /portal/tickets?tenant_id=TENANT_1
    """

    def get(self, request):
        tickets = Ticket.objects.filter(tenant_id=request.tenant_id)
        data = TicketSerializer(tickets, many=True).data
        return Response({"data":data,"total":1,"page":1,"page_size":1,"total_pages":1})


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

        serializer = TicketUpdateSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            send_ticket_updated_email(updated)
            data = TicketSerializer(updated).data
            return Response({"data":data})
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
            comment = serializer.save(tenant_id=request.tenant_id)
            ticket = Ticket.objects.filter(pk=comment.ticket_id).first()
            if ticket:
                send_comment_created_email(comment, ticket)
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
            if ticket:
                send_comment_updated_email(updated, ticket)
            data = CommentSerializer(updated).data    
            return Response({"data":data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketKPIView(APIView):
    """
    GET /portal/tickets/kpis?tenant_id=<tenant_id>
    Returns an overview of ticket counts grouped by status and priority.
    """

    def get(self, request):
        qs = Ticket.objects.filter(tenant_id=request.tenant_id)

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
