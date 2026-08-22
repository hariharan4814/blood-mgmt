from django.urls import path

from .views import (
    EmailRecipientDetailView,
    EmailRecipientListCreateView,
    EmailStatusView,
    NotificationDetailView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    NotificationUnreadCountView,
    TestEmailView,
)

urlpatterns = [
    # In-App Notifications
    path("", NotificationListView.as_view(), name="notification-list"),
    path("unread-count/", NotificationUnreadCountView.as_view(), name="notification-unread-count"),
    path("mark-all-read/", NotificationMarkAllReadView.as_view(), name="notification-mark-all-read"),
    path("<int:pk>/", NotificationDetailView.as_view(), name="notification-detail"),
    path("<int:pk>/mark-read/", NotificationMarkReadView.as_view(), name="notification-mark-read"),

    # Administrative Email Management
    path("email-status/", EmailStatusView.as_view(), name="email-status"),
    path("test-email/", TestEmailView.as_view(), name="test-email"),
    path("recipients/", EmailRecipientListCreateView.as_view(), name="email-recipient-list-create"),
    path("recipients/<int:pk>/", EmailRecipientDetailView.as_view(), name="email-recipient-detail"),
]
