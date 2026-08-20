from django.urls import path
from .views import TestResultListCreateView, TestResultDetailView

urlpatterns = [
    path("", TestResultListCreateView.as_view(), name="test-result-list-create"),
    path("<int:pk>/", TestResultDetailView.as_view(), name="test-result-detail"),
]
