from django.urls import path
from .views import (
    DonationCampListCreateView,
    DonationCampDetailView,
    DonationCampRegisterView,
)

urlpatterns = [
    path("", DonationCampListCreateView.as_view(), name="donation-camp-list-create"),
    path("<int:pk>/", DonationCampDetailView.as_view(), name="donation-camp-detail"),
    path("<int:pk>/register/", DonationCampRegisterView.as_view(), name="donation-camp-register"),
]
