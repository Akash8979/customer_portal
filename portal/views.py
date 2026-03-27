from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Ticket
from .serializers import (
    TicketCreateSerializer,
    TicketSerializer,
    TicketUpdateSerializer,
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

    def post(self, request):
        serializer = TicketCreateSerializer(data=request.data)
        if serializer.is_valid():
            ticket = serializer.save()
            return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketDetailView(APIView):
    """
    GET /api/portal/tickets/<id>/
    """

    def get(self, _request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response({'error': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TicketSerializer(ticket).data)


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
            return Response(TicketSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketAttachmentView(APIView):
    """
    POST /api/portal/attachments/
    Body: { "file_name": "log.txt", "file_type": "text/plain", "file_path": "/uploads/log.txt", "metadata": {} }
    """

    def post(self, request):
        from .serializers import AttachmentSerializer
        serializer = AttachmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
