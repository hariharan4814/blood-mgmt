from django.urls import path
from .review_views import (
    ReviewApproveView,
    ReviewDetailView,
    ReviewListCreateView,
    ReviewRejectView,
)

urlpatterns = [
    path("", ReviewListCreateView.as_view(), name="review-list-create"),
    path("<int:pk>/", ReviewDetailView.as_view(), name="review-detail"),
    path("<int:pk>/approve/", ReviewApproveView.as_view(), name="review-approve"),
    path("<int:pk>/reject/", ReviewRejectView.as_view(), name="review-reject"),
]
