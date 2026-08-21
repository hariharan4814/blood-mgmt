from django.urls import path

from .views import (
    SOSBroadcastCancelView,
    SOSBroadcastDetailView,
    SOSBroadcastListView,
    SOSBroadcastRecipientsListView,
)

app_name = "emergency_sos"

urlpatterns = [
    path("", SOSBroadcastListView.as_view(), name="sos-list"),
    path("<int:pk>/", SOSBroadcastDetailView.as_view(), name="sos-detail"),
    path("<int:pk>/cancel/", SOSBroadcastCancelView.as_view(), name="sos-cancel"),
    path("<int:pk>/recipients/", SOSBroadcastRecipientsListView.as_view(), name="sos-recipients-list"),
]
