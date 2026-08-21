from django.urls import path
from apps.emergency_sos.views import TriggerBloodRequestSOSView
from .views import (
    BloodRequestListCreateView,
    BloodRequestDetailView,
    BloodRequestApproveView,
    BloodRequestRejectView,
)

urlpatterns = [
    path("", BloodRequestListCreateView.as_view(), name="blood-request-list-create"),
    path("<int:pk>/", BloodRequestDetailView.as_view(), name="blood-request-detail"),
    path("<int:pk>/approve/", BloodRequestApproveView.as_view(), name="blood-request-approve"),
    path("<int:pk>/reject/", BloodRequestRejectView.as_view(), name="blood-request-reject"),
    path("<int:pk>/sos/", TriggerBloodRequestSOSView.as_view(), name="blood-request-sos"),
]
