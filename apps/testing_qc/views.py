from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse

from apps.accounts.models import UserRole
from apps.inventory.models import BloodUnit
from .models import TestResult
from .permissions import IsLabTechnicianForWriteOrReadOnly
from .serializers import (
    TestResultSerializer,
    TestResultCreateSerializer,
    TestResultUpdateSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary="List Test Results",
        description="Retrieve laboratory screening test results. Scoped by user role (Lab Tech, Super Admin, Blood Bank Admin).",
        parameters=[
            OpenApiParameter("blood_unit", int, description="Filter by Blood Unit ID", required=False),
            OpenApiParameter("blood_bank", int, description="Filter by Blood Bank ID", required=False),
        ],
        responses={200: TestResultSerializer(many=True)},
        tags=["Testing & Quality Control"],
    ),
    post=extend_schema(
        summary="Record Test Results for Blood Unit",
        description="Record initial laboratory screening results for a blood unit in TESTING status. Restricted to LAB_TECHNICIAN.",
        request=TestResultCreateSerializer,
        responses={201: TestResultSerializer, 400: OpenApiResponse(description="Validation error."), 403: OpenApiResponse(description="Permission denied.")},
        tags=["Testing & Quality Control"],
    )
)
class TestResultListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsLabTechnicianForWriteOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TestResultCreateSerializer
        return TestResultSerializer

    def get_queryset(self):
        user = self.request.user
        if not (user and user.is_authenticated):
            return TestResult.objects.none()

        queryset = TestResult.objects.select_related("blood_unit", "blood_unit__blood_bank", "tested_by").all().order_by("-created_at")

        # Bank-level isolation for Blood Bank Admins
        if user.role == UserRole.BLOOD_BANK_ADMIN and not user.is_super_admin:
            queryset = queryset.filter(blood_unit__blood_bank__admin=user)
        elif not (user.is_super_admin or user.role == UserRole.LAB_TECHNICIAN):
            return TestResult.objects.none()

        # Query parameter filters
        blood_unit_param = self.request.query_params.get("blood_unit")
        if blood_unit_param:
            queryset = queryset.filter(blood_unit_id=blood_unit_param)

        blood_bank_param = self.request.query_params.get("blood_bank")
        if blood_bank_param:
            queryset = queryset.filter(blood_unit__blood_bank_id=blood_bank_param)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        test_result = serializer.save()
        output_serializer = TestResultSerializer(test_result)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Test Result Details",
        description="Retrieve laboratory screening result details for a specific test result record.",
        responses={200: TestResultSerializer, 403: OpenApiResponse(description="Permission denied."), 404: OpenApiResponse(description="Not found.")},
        tags=["Testing & Quality Control"],
    ),
    patch=extend_schema(
        summary="Update Test Results",
        description="Update disease screening results (e.g. from PENDING to NEGATIVE/POSITIVE). Restricted to LAB_TECHNICIAN.",
        request=TestResultUpdateSerializer,
        responses={200: TestResultSerializer, 400: OpenApiResponse(description="Validation error."), 403: OpenApiResponse(description="Permission denied.")},
        tags=["Testing & Quality Control"],
    ),
)
class TestResultDetailView(generics.RetrieveUpdateAPIView):
    queryset = TestResult.objects.select_related("blood_unit", "blood_unit__blood_bank", "tested_by").all()
    permission_classes = [IsLabTechnicianForWriteOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return TestResultUpdateSerializer
        return TestResultSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        output_serializer = TestResultSerializer(updated_instance)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="Get Test Result for Blood Unit",
        description="Retrieve the test result record associated with a specific blood unit ID.",
        responses={200: TestResultSerializer, 404: OpenApiResponse(description="No test result found.")},
        tags=["Testing & Quality Control"],
    )
)
class BloodUnitTestResultDetailView(APIView):
    permission_classes = [IsLabTechnicianForWriteOrReadOnly]

    def get(self, request, pk):
        blood_unit = BloodUnit.objects.filter(pk=pk).first()
        if not blood_unit:
            return Response({"detail": "Blood unit not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check object level permission
        if request.user.role == UserRole.BLOOD_BANK_ADMIN and not request.user.is_super_admin:
            if blood_unit.blood_bank.admin_id != request.user.id:
                return Response({"detail": "You do not have permission to view test results for this blood unit."}, status=status.HTTP_403_FORBIDDEN)

        test_result = TestResult.objects.filter(blood_unit=blood_unit).first()
        if not test_result:
            return Response(
                {"detail": "No laboratory screening results have been recorded for this blood unit yet."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TestResultSerializer(test_result)
        return Response(serializer.data, status=status.HTTP_200_OK)
