from django.urls import path
from .views import (
    DonationCampRegistrationListView,
    DonationCampRegistrationCancelView,
)

urlpatterns = [
    path("", DonationCampRegistrationListView.as_view(), name="donation-camp-registration-list"),
    path("<int:pk>/cancel/", DonationCampRegistrationCancelView.as_view(), name="donation-camp-registration-cancel"),
]
