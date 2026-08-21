from django.urls import path
from .profile_views import ProfileImageView, UserProfileView

app_name = "profile"

urlpatterns = [
    path("", UserProfileView.as_view(), name="user_profile"),
    path("image/", ProfileImageView.as_view(), name="profile_image"),
]
