from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse

from apps.accounts.models import UserRole
from .models import BloodRequest
from .permissions import CanManageOrViewBloodRequests, IsAssignedBankAdminForAction
from .serializers import (
    BloodRequestSerializer,
    BloodRequestCreateSerializer,
    BloodRequestRejectSerializer,
)
from .services import approve_blood_request, reject_blood_request


@extend_schema_view(
    get=extend_schema(
        summary="List Blood Requests",
        description="Retrieve blood requests. Hospital Staff see only their own requests; Blood Bank Admins see requests for their assigned bank; Super Admins see all.",
        parameters=[
            OpenApiParameter("status", str, description="Filter by status (PENDING, APPROVED, REJECTED)", required=False),
            OpenApiParameter("urgency", str, description="Filter by urgency (NORMAL, HIGH, CRITICAL)", required=False),
            OpenApiParameter("blood_group", str, description="Filter by blood group (e.g. A+, O-)", required=False),
            OpenApiParameter("blood_bank", int, description="Filter by Blood Bank ID", required=False),
        ],
        responses={200: BloodRequestSerializer(many=True)},
        tags=["Blood Requests"],
    ),
    post=extend_schema(
        summary="Create Blood Request",
        description="Submit a new blood request to a designated blood bank. Restricted to HOSPITAL_STAFF.",
        request=BloodRequestCreateSerializer,
        responses={201: BloodRequestSerializer, 400: OpenApiResponse(description="Validation error."), 403: OpenApiResponse(description="Permission denied.")},
        tags=["Blood Requests"],
    )
)
class BloodRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [CanManageOrViewBloodRequests]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BloodRequestCreateSerializer
        return BloodRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if not (user and user.is_authenticated):
            return BloodRequest.objects.none()

        queryset = (
            BloodRequest.objects.select_related("hospital_staff", "blood_bank", "approved_by")
            .prefetch_related("reserved_units")
            .all()
            .order_by("-created_at")
        )

        # RBAC and data isolation
        if user.role == UserRole.HOSPITAL_STAFF and not user.is_super_admin:
            queryset = queryset.filter(hospital_staff=user)
        elif user.role == UserRole.BLOOD_BANK_ADMIN and not user.is_super_admin:
            queryset = queryset.filter(blood_bank__admin=user)
        elif not user.is_super_admin:
            return BloodRequest.objects.none()

        # Query filters
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status__iexact=status_param)

        urgency_param = self.request.query_params.get("urgency")
        if urgency_param:
            queryset = queryset.filter(urgency__iexact=urgency_param)

        blood_group_param = self.request.query_params.get("blood_group")
        if blood_group_param:
            queryset = queryset.filter(blood_group__iexact=blood_group_param)

        blood_bank_param = self.request.query_params.get("blood_bank")
        if blood_bank_param:
            queryset = queryset.filter(blood_bank_id=blood_bank_param)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        blood_request = serializer.save()
        output_serializer = BloodRequestSerializer(blood_request)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Blood Request Details",
        description="Retrieve details of a specific blood request, including reserved units if approved.",
        responses={200: BloodRequestSerializer, 403: OpenApiResponse(description="Permission denied."), 404: OpenApiResponse(description="Not found.")},
        tags=["Blood Requests"],
    )
)
class BloodRequestDetailView(generics.RetrieveAPIView):
    queryset = BloodRequest.objects.select_related("hospital_staff", "blood_bank", "approved_by").prefetch_related("reserved_units").all()
    serializer_class = BloodRequestSerializer
    permission_classes = [CanManageOrViewBloodRequests]


@extend_schema_view(
    post=extend_schema(
        summary="Approve Blood Request",
        description="Atomically approves a PENDING blood request by reserving the exact requested number of eligible AVAILABLE BloodUnits. "
                    "Restricted to the assigned Blood Bank Administrator.",
        request=None,
        responses={
            200: BloodRequestSerializer,
            400: OpenApiResponse(description="Insufficient stock or invalid request state."),
            403: OpenApiResponse(description="Permission denied."),
        },
        tags=["Blood Requests"],
    )
)
class BloodRequestApproveView(APIView):
    permission_classes = [IsAssignedBankAdminForAction]

    def post(self, request, pk):
        blood_request = BloodRequest.objects.filter(pk=pk).first()
        if not blood_request:
            return Response({"detail": "Blood request not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, blood_request)

        try:
            approved_request = approve_blood_request(blood_request, approved_by_user=request.user)
        except DjangoValidationError as e:
            msg = e.message if hasattr(e, "message") else (e.messages[0] if hasattr(e, "messages") else str(e))
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

        serializer = BloodRequestSerializer(approved_request)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        summary="Reject Blood Request",
        description="Rejects a PENDING blood request with a required explanation reason. "
                    "Restricted to the assigned Blood Bank Administrator.",
        request=BloodRequestRejectSerializer,
        responses={
            200: BloodRequestSerializer,
            400: OpenApiResponse(description="Missing rejection reason or invalid request state."),
            403: OpenApiResponse(description="Permission denied."),
        },
        tags=["Blood Requests"],
    )
)
class BloodRequestRejectView(APIView):
    permission_classes = [IsAssignedBankAdminForAction]

    def post(self, request, pk):
        blood_request = BloodRequest.objects.filter(pk=pk).first()
        if not blood_request:
            return Response({"detail": "Blood request not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, blood_request)

        serializer = BloodRequestRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rejection_reason = serializer.validated_data["rejection_reason"]

        try:
            rejected_request = reject_blood_request(blood_request, rejection_reason=rejection_reason)
        except DjangoValidationError as e:
            msg = e.message if hasattr(e, "message") else (e.messages[0] if hasattr(e, "messages") else str(e))
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

        output_serializer = BloodRequestSerializer(rejected_request)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
