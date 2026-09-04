from django.urls import path
from .views import HospitalListCreateView, HospitalDetailView

urlpatterns = [
    path("", HospitalListCreateView.as_view(), name="hospital-list-create"),
    path("<int:pk>/", HospitalDetailView.as_view(), name="hospital-detail"),
]
