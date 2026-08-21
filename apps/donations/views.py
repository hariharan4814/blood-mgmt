from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse

from apps.accounts.models import UserRole
from .models import (
    DonationCamp,
    DonationCampRegistration,
    Donation,
    CampStatus,
    CampRegistrationStatus,
)
from .permissions import (
    IsBankAdminForCampWriteOrReadOnly,
    CanRegisterForCamp,
    CanManageOrViewRegistrations,
    CanRecordOrViewDonations,
)
from .serializers import (
    DonationCampSerializer,
    DonationCampCreateUpdateSerializer,
    DonationCampRegistrationSerializer,
    DonationSerializer,
    DonationCreateSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary="List Donation Camps",
        description="Retrieve a list of blood donation camps. Donors can view scheduled camps; Blood Bank Admins can view and filter camps; Super Admins see all.",
        parameters=[
            OpenApiParameter("status", str, description="Filter by camp status (UPCOMING, ACTIVE, COMPLETED, CANCELLED)", required=False),
            OpenApiParameter("blood_bank", int, description="Filter by Blood Bank ID", required=False),
            OpenApiParameter("camp_date", str, description="Filter by date (YYYY-MM-DD)", required=False),
        ],
        responses={200: DonationCampSerializer(many=True)},
        tags=["Donation Camps"],
    ),
    post=extend_schema(
        summary="Create Donation Camp",
        description="Create a new blood donation camp record for an assigned Blood Bank. Restricted to BLOOD_BANK_ADMIN and SUPER_ADMIN.",
        request=DonationCampCreateUpdateSerializer,
        responses={
            201: DonationCampSerializer,
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Permission denied."),
        },
        tags=["Donation Camps"],
    ),
)
class DonationCampListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsBankAdminForCampWriteOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DonationCampCreateUpdateSerializer
        return DonationCampSerializer

    def get_queryset(self):
        user = self.request.user
        if not (user and user.is_authenticated):
            return DonationCamp.objects.none()

        queryset = (
            DonationCamp.objects.select_related("blood_bank", "created_by")
            .prefetch_related("registrations", "donations")
            .all()
            .order_by("-camp_date", "-created_at")
        )

        # Query filters
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status__iexact=status_param)

        blood_bank_param = self.request.query_params.get("blood_bank")
        if blood_bank_param:
            queryset = queryset.filter(blood_bank_id=blood_bank_param)

        camp_date_param = self.request.query_params.get("camp_date")
        if camp_date_param:
            queryset = queryset.filter(camp_date=camp_date_param)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        camp = serializer.save()
        output_serializer = DonationCampSerializer(camp)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Donation Camp Details",
        description="Retrieve details of a specific donation camp.",
        responses={200: DonationCampSerializer, 404: OpenApiResponse(description="Not found.")},
        tags=["Donation Camps"],
    ),
    patch=extend_schema(
        summary="Update Donation Camp",
        description="Update fields or status of a donation camp. Restricted to the assigned Blood Bank Administrator or Super Admin.",
        request=DonationCampCreateUpdateSerializer,
        responses={
            200: DonationCampSerializer,
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Permission denied."),
        },
        tags=["Donation Camps"],
    ),
)
class DonationCampDetailView(generics.RetrieveUpdateAPIView):
    queryset = DonationCamp.objects.select_related("blood_bank", "created_by").prefetch_related("registrations", "donations").all()
    permission_classes = [IsBankAdminForCampWriteOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return DonationCampCreateUpdateSerializer
        return DonationCampSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        output_serializer = DonationCampSerializer(updated_instance)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        summary="Register Donor for Camp",
        description="Allows an authenticated Donor to register their interest for a scheduled donation camp. Duplicate registrations are rejected.",
        request=None,
        responses={
            201: DonationCampRegistrationSerializer,
            400: OpenApiResponse(description="Duplicate registration or camp is cancelled."),
            403: OpenApiResponse(description="Only Donors can register."),
            404: OpenApiResponse(description="Camp not found."),
        },
        tags=["Donation Camps"],
    ),
)
class DonationCampRegisterView(APIView):
    permission_classes = [CanRegisterForCamp]

    def post(self, request, pk):
        camp = DonationCamp.objects.filter(pk=pk).first()
        if not camp:
            return Response({"detail": "Donation camp not found."}, status=status.HTTP_404_NOT_FOUND)

        if camp.status == CampStatus.CANCELLED:
            return Response(
                {"detail": "Cannot register for a CANCELLED donation camp."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        donor = getattr(request.user, "donor_profile", None)
        if not donor:
            return Response(
                {"detail": "Authenticated user does not have a donor profile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent duplicate registration
        if DonationCampRegistration.objects.filter(donor=donor, camp=camp).exists():
            return Response(
                {"detail": "You have already registered for this donation camp."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration = DonationCampRegistration.objects.create(
            donor=donor,
            camp=camp,
            status=CampRegistrationStatus.REGISTERED,
        )

        serializer = DonationCampRegistrationSerializer(registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="List Donation Camp Registrations",
        description="List camp registrations. Donors see only their own registrations; Blood Bank Admins see registrations for their bank's camps; Super Admins see all.",
        parameters=[
            OpenApiParameter("camp", int, description="Filter by Donation Camp ID", required=False),
            OpenApiParameter("status", str, description="Filter by status (REGISTERED, CANCELLED, ATTENDED)", required=False),
        ],
        responses={200: DonationCampRegistrationSerializer(many=True)},
        tags=["Donation Camps"],
    ),
)
class DonationCampRegistrationListView(generics.ListAPIView):
    serializer_class = DonationCampRegistrationSerializer
    permission_classes = [CanManageOrViewRegistrations]

    def get_queryset(self):
        user = self.request.user
        if not (user and user.is_authenticated):
            return DonationCampRegistration.objects.none()

        queryset = (
            DonationCampRegistration.objects.select_related("donor", "donor__user", "camp", "camp__blood_bank")
            .all()
            .order_by("-registered_at")
        )

        if user.role == UserRole.DONOR and not user.is_super_admin:
            if hasattr(user, "donor_profile"):
                queryset = queryset.filter(donor=user.donor_profile)
            else:
                return DonationCampRegistration.objects.none()
        elif user.role == UserRole.BLOOD_BANK_ADMIN and not user.is_super_admin:
            queryset = queryset.filter(camp__blood_bank__admin=user)
        elif not user.is_super_admin:
            return DonationCampRegistration.objects.none()

        camp_param = self.request.query_params.get("camp")
        if camp_param:
            queryset = queryset.filter(camp_id=camp_param)

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status__iexact=status_param)

        return queryset


@extend_schema_view(
    post=extend_schema(
        summary="Cancel Camp Registration",
        description="Allows a Donor to cancel their own registration for a donation camp.",
        request=None,
        responses={
            200: DonationCampRegistrationSerializer,
            400: OpenApiResponse(description="Already cancelled or attended."),
            403: OpenApiResponse(description="Permission denied."),
            404: OpenApiResponse(description="Registration not found."),
        },
        tags=["Donation Camps"],
    ),
)
class DonationCampRegistrationCancelView(APIView):
    permission_classes = [CanManageOrViewRegistrations]

    def post(self, request, pk):
        registration = DonationCampRegistration.objects.filter(pk=pk).first()
        if not registration:
            return Response({"detail": "Registration not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, registration)

        if registration.status == CampRegistrationStatus.CANCELLED:
            return Response(
                {"detail": "Registration is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if registration.status == CampRegistrationStatus.ATTENDED:
            return Response(
                {"detail": "Cannot cancel a registration that has already been attended."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration.status = CampRegistrationStatus.CANCELLED
        registration.save(update_fields=["status", "updated_at"])

        serializer = DonationCampRegistrationSerializer(registration)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="List Donations",
        description="List completed blood donations. Donors see only their own personal donation history; Blood Bank Admins see collections recorded at their bank; Super Admins see all.",
        parameters=[
            OpenApiParameter("blood_bank", int, description="Filter by Blood Bank ID", required=False),
            OpenApiParameter("camp", int, description="Filter by Donation Camp ID", required=False),
            OpenApiParameter("donor", int, description="Filter by Donor ID", required=False),
        ],
        responses={200: DonationSerializer(many=True)},
        tags=["Donations"],
    ),
    post=extend_schema(
        summary="Record Blood Donation",
        description="Record an actual blood donation (walk-in or camp). Atomically creates a BloodUnit in TESTING status and updates the donor's last donation date. Restricted to BLOOD_BANK_ADMIN.",
        request=DonationCreateSerializer,
        responses={
            201: DonationSerializer,
            400: OpenApiResponse(description="Validation or eligibility error."),
            403: OpenApiResponse(description="Permission denied."),
        },
        tags=["Donations"],
    ),
)
class DonationListCreateView(generics.ListCreateAPIView):
    permission_classes = [CanRecordOrViewDonations]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DonationCreateSerializer
        return DonationSerializer

    def get_queryset(self):
        user = self.request.user
        if not (user and user.is_authenticated):
            return Donation.objects.none()

        queryset = (
            Donation.objects.select_related("donor", "donor__user", "blood_bank", "camp", "blood_unit", "created_by")
            .all()
            .order_by("-donation_date", "-created_at")
        )

        if user.role == UserRole.DONOR and not user.is_super_admin:
            if hasattr(user, "donor_profile"):
                queryset = queryset.filter(donor=user.donor_profile)
            else:
                return Donation.objects.none()
        elif user.role == UserRole.BLOOD_BANK_ADMIN and not user.is_super_admin:
            queryset = queryset.filter(blood_bank__admin=user)
        elif not user.is_super_admin:
            return Donation.objects.none()

        # Query filters
        blood_bank_param = self.request.query_params.get("blood_bank")
        if blood_bank_param:
            queryset = queryset.filter(blood_bank_id=blood_bank_param)

        camp_param = self.request.query_params.get("camp")
        if camp_param:
            queryset = queryset.filter(camp_id=camp_param)

        donor_param = self.request.query_params.get("donor")
        if donor_param:
            queryset = queryset.filter(donor_id=donor_param)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        donation = serializer.save()
        output_serializer = DonationSerializer(donation)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Donation Details",
        description="Retrieve details of a specific blood donation collection record.",
        responses={200: DonationSerializer, 403: OpenApiResponse(description="Permission denied."), 404: OpenApiResponse(description="Not found.")},
        tags=["Donations"],
    ),
)
class DonationDetailView(generics.RetrieveAPIView):
    queryset = Donation.objects.select_related("donor", "donor__user", "blood_bank", "camp", "blood_unit", "created_by").all()
    serializer_class = DonationSerializer
    permission_classes = [CanRecordOrViewDonations]
