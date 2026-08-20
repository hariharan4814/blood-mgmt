from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Admin Panel
    path("admin/", admin.site.urls),

    # Core & Health Check APIs
    path("api/", include("apps.common.urls")),

    # Authentication & Accounts APIs
    path("api/auth/", include("apps.accounts.urls")),

    # Super Admin User Management APIs
    path("api/users/", include("apps.accounts.user_urls")),

    # Donor Management APIs
    path("api/donors/", include("apps.donors.urls")),

    # Blood Bank Management APIs
    path("api/blood-banks/", include("apps.inventory.blood_bank_urls")),

    # Blood Unit Management APIs
    path("api/blood-units/", include("apps.inventory.blood_unit_urls")),

    # Inventory Summary APIs
    path("api/inventory/", include("apps.inventory.urls")),

    # OpenAPI Schema & Interactive Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
