from django.urls import path
from .views import HealthCheckView
from .nearby_views import NearbySearchView

app_name = "common"

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health_check"),
    path("nearby/", NearbySearchView.as_view(), name="nearby_search"),
]
