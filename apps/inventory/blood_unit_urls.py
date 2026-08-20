from django.urls import path
from .views import BloodUnitListCreateView, BloodUnitDetailView
from apps.testing_qc.views import BloodUnitTestResultDetailView

urlpatterns = [
    path("", BloodUnitListCreateView.as_view(), name="blood-unit-list-create"),
    path("<int:pk>/", BloodUnitDetailView.as_view(), name="blood-unit-detail"),
    path("<int:pk>/test-result/", BloodUnitTestResultDetailView.as_view(), name="blood-unit-test-result"),
]

