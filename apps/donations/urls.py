from django.urls import path, include

urlpatterns = [
    path("donation-camps/", include("apps.donations.camp_urls")),
    path("donation-camp-registrations/", include("apps.donations.registration_urls")),
    path("donations/", include("apps.donations.donation_urls")),
]
