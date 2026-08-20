from django.urls import path
from .views import (
    DonorMeProfileView,
    DonorMeEligibilityView,
    DonorAdminListView,
    DonorAdminDetailView,
)

app_name = "donors"

urlpatterns = [
    path("me/", DonorMeProfileView.as_view(), name="donor_me"),
    path("me/eligibility/", DonorMeEligibilityView.as_view(), name="donor_me_eligibility"),
    path("", DonorAdminListView.as_view(), name="donor_list"),
    path("<int:pk>/", DonorAdminDetailView.as_view(), name="donor_detail"),
]
