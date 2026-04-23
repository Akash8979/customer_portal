from django.urls import path
from .views import (
    TicketCreateView, TicketListView, TicketDetailView, TicketUpdateView,
    TicketStatusUpdateView, TicketAttachmentView, FileUploadView, CommentCreateView,
    CommentUpdateView, TicketKPIView, TicketCommentListView, TicketHistoryView,
    AuditLogListView, SLAPolicyListView, SLAPolicyDetailView,
    NotificationListView, NotificationMarkAllReadView, NotificationMarkReadView,
)
from .sse import TicketStreamView

urlpatterns = [
    path('dashboard/kpis', TicketKPIView.as_view(), name='ticket-kpis'),
    path('tickets', TicketCreateView.as_view(), name='ticket-create'),
    path('tickets/list', TicketListView.as_view(), name='ticket-list'),
    path('tickets/<int:pk>', TicketDetailView.as_view(), name='ticket-detail'),
    path('tickets/<int:pk>/update', TicketUpdateView.as_view(), name='ticket-update'),
    path('tickets/<int:pk>/status', TicketStatusUpdateView.as_view(), name='ticket-status-update'),
    path('tickets/<int:pk>/comments', TicketCommentListView.as_view(), name='ticket-comments'),
    path('tickets/<int:pk>/history', TicketHistoryView.as_view(), name='ticket-history'),
    path('attachments', TicketAttachmentView.as_view(), name='ticket-attachments'),
    path('attachments/upload', FileUploadView.as_view(), name='file-upload'),
    path('comments', CommentCreateView.as_view(), name='comment-create'),
    path('comments/<int:pk>/update', CommentUpdateView.as_view(), name='comment-update'),
    path('stream', TicketStreamView, name='ticket-stream'),
    path('audit-logs', AuditLogListView.as_view(), name='audit-logs'),
    path('sla-policies', SLAPolicyListView.as_view(), name='sla-policy-list'),
    path('sla-policies/<int:pk>', SLAPolicyDetailView.as_view(), name='sla-policy-detail'),
    # Notifications
    path('notifications', NotificationListView.as_view(), name='notification-list'),
    path('notifications/mark-all', NotificationMarkAllReadView.as_view(), name='notification-mark-all'),
    path('notifications/<int:pk>/read', NotificationMarkReadView.as_view(), name='notification-mark-read'),
]
