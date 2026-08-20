from django.urls import path
from .views import BloodBankListCreateView, BloodBankDetailView

urlpatterns = [
    path("", BloodBankListCreateView.as_view(), name="blood-bank-list-create"),
    path("<int:pk>/", BloodBankDetailView.as_view(), name="blood-bank-detail"),
]
