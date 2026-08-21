from django.urls import path
from .views import (
    DonationListCreateView,
    DonationDetailView,
)

urlpatterns = [
    path("", DonationListCreateView.as_view(), name="donation-list-create"),
    path("<int:pk>/", DonationDetailView.as_view(), name="donation-detail"),
]
