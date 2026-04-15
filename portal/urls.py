from django.urls import path
from .views import (
    TicketCreateView, TicketListView, TicketDetailView, TicketUpdateView,
    TicketAttachmentView, CommentCreateView, CommentUpdateView, TicketKPIView,
    TicketCommentListView,
)

urlpatterns = [
    path('dashboard/kpis', TicketKPIView.as_view(), name='ticket-kpis'),
    path('tickets', TicketCreateView.as_view(), name='ticket-create'),
    path('tickets/list', TicketListView.as_view(), name='ticket-list'),
    path('tickets/<int:pk>', TicketDetailView.as_view(), name='ticket-detail'),
    path('tickets/<int:pk>/update', TicketUpdateView.as_view(), name='ticket-update'),
    path('tickets/<int:pk>/comments', TicketCommentListView.as_view(), name='ticket-comments'),
    path('attachments', TicketAttachmentView.as_view(), name='ticket-attachments'),
    path('comments', CommentCreateView.as_view(), name='comment-create'),
    path('comments/<int:pk>/update', CommentUpdateView.as_view(), name='comment-update'),
]
