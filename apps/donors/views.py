from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from apps.accounts.models import UserRole
from apps.accounts.permissions import IsDonor, IsSuperAdmin, HasRoles
from .models import Donor, BloodGroup
from .serializers import (
    DonorProfileSerializer,
    DonorProfileInputSerializer,
    DonorEligibilityResponseSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary="Get Current Donor Profile",
        description="Retrieve the profile of the currently authenticated donor.",
        responses={
            200: DonorProfileSerializer,
            404: OpenApiResponse(description="Donor profile has not been completed yet."),
        },
        tags=["Donor Management"],
    ),
    put=extend_schema(
        summary="Create / Full Update Donor Profile",
        description="Create or fully update the donor profile for the authenticated donor.",
        request=DonorProfileInputSerializer,
        responses={200: DonorProfileSerializer, 201: DonorProfileSerializer},
        tags=["Donor Management"],
    ),
    patch=extend_schema(
        summary="Partial Update Donor Profile",
        description="Partially update donor attributes (e.g. blood group, weight, location coordinates, last donation date).",
        request=DonorProfileInputSerializer,
        responses={200: DonorProfileSerializer, 201: DonorProfileSerializer},
        tags=["Donor Management"],
    ),
    post=extend_schema(
        summary="Create Donor Profile",
        description="Create donor profile for authenticated donor if not already existing.",
        request=DonorProfileInputSerializer,
        responses={201: DonorProfileSerializer, 400: OpenApiResponse(description="Validation error or profile already exists.")},
        tags=["Donor Management"],
    )
)
class DonorMeProfileView(APIView):
    """
    Profile endpoint for the authenticated DONOR.
    Allows retrieval and seamless creation/updating of the donor profile.
    """
    permission_classes = [IsDonor]

    def get(self, request):
        donor = Donor.objects.filter(user=request.user).first()
        if not donor:
            return Response(
                {"detail": "Donor profile not found. Please complete your donor profile."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DonorProfileSerializer(donor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        return self._save_profile(request, partial=False)

    def patch(self, request):
        return self._save_profile(request, partial=True)

    def post(self, request):
        if Donor.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "Donor profile already exists. Use PUT or PATCH to update."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._save_profile(request, partial=False)

    def _save_profile(self, request, partial=False):
        donor = Donor.objects.filter(user=request.user).first()
        is_new = donor is None

        save_data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        if is_new:
            if not save_data.get("blood_group"):
                save_data["blood_group"] = BloodGroup.O_POSITIVE
            if not save_data.get("date_of_birth"):
                save_data["date_of_birth"] = "2000-01-01"
            if not save_data.get("weight_kg"):
                save_data["weight_kg"] = "60.00"

        serializer = DonorProfileInputSerializer(
            instance=donor,
            data=save_data,
            partial=partial if not is_new else False,
        )
        serializer.is_valid(raise_exception=True)

        if is_new:
            donor = serializer.save(user=request.user)
            res_status = status.HTTP_201_CREATED
        else:
            donor = serializer.save()
            res_status = status.HTTP_200_OK

        return Response(DonorProfileSerializer(donor).data, status=res_status)


@extend_schema_view(
    get=extend_schema(
        summary="Check Current Donor Eligibility",
        description="Dynamically evaluates and returns the donor's medical eligibility status and criteria breakdown (age, weight, 90-day cooldown).",
        responses={
            200: DonorEligibilityResponseSerializer,
            404: OpenApiResponse(description="Donor profile not found."),
        },
        tags=["Donor Management"],
    )
)
class DonorMeEligibilityView(APIView):
    """
    Dynamically computes donation eligibility for the authenticated DONOR.
    """
    permission_classes = [IsDonor]

    def get(self, request):
        donor = Donor.objects.filter(user=request.user).first()
        if not donor:
            return Response(
                {"detail": "Donor profile not found. Please complete your profile to check eligibility."},
                status=status.HTTP_404_NOT_FOUND,
            )
        eligibility_data = donor.calculate_eligibility()
        return Response(eligibility_data, status=status.HTTP_200_OK)


# ========================================================
# SUPER ADMIN DONOR ADMINISTRATION ENDPOINTS
# ========================================================

@extend_schema_view(
    get=extend_schema(
        summary="List All Donors (Admin)",
        description="List all donor profiles with pagination and optional filtering by blood group. Restricted to Super Administrators.",
        responses={200: DonorProfileSerializer(many=True)},
        tags=["Donor Management (Admin)"],
    )
)
class DonorAdminListView(generics.ListAPIView):
    """
    Super Admin and Blood Bank Admin endpoint to inspect donor records across the platform.
    """
    serializer_class = DonorProfileSerializer
    permission_classes = [HasRoles(UserRole.SUPER_ADMIN, UserRole.BLOOD_BANK_ADMIN)]

    def get_queryset(self):
        queryset = Donor.objects.select_related("user").all().order_by("-created_at")
        blood_group = self.request.query_params.get("blood_group")
        if blood_group:
            queryset = queryset.filter(blood_group__iexact=blood_group)
        return queryset


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Donor Profile (Admin)",
        description="Retrieve a specific donor's profile by ID. Restricted to Super Administrators and Blood Bank Administrators.",
        responses={200: DonorProfileSerializer},
        tags=["Donor Management (Admin)"],
    )
)
class DonorAdminDetailView(generics.RetrieveAPIView):
    """
    Super Admin and Blood Bank Admin endpoint to view an individual donor profile.
    """
    queryset = Donor.objects.select_related("user").all()
    serializer_class = DonorProfileSerializer
    permission_classes = [HasRoles(UserRole.SUPER_ADMIN, UserRole.BLOOD_BANK_ADMIN)]
