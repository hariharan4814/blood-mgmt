from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsSuperAdmin
from .models import Review, ReviewStatus, ReviewTargetType
from .review_serializers import (
    ReviewCreateSerializer,
    ReviewModerateSerializer,
    ReviewSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary="List Facility Reviews",
        description=(
            "List facility reviews. Regular users and anonymous visitors see only APPROVED reviews (authenticated users also see their own). "
            "Super Admins can see all reviews and filter by moderation status."
        ),
        parameters=[
            OpenApiParameter("status", str, description="Filter by status: PENDING, APPROVED, REJECTED, or ALL", required=False),
            OpenApiParameter("target_type", str, description="Filter by target: HOSPITAL or BLOOD_BANK", required=False),
            OpenApiParameter("hospital", int, description="Filter by hospital ID", required=False),
            OpenApiParameter("blood_bank", int, description="Filter by blood bank ID", required=False),
            OpenApiParameter("rating", int, description="Filter by rating (1-5)", required=False),
            OpenApiParameter("search", str, description="Search reviewer, facility name, or comment text", required=False),
        ],
        responses={200: ReviewSerializer(many=True)},
        tags=["Facility Reviews"],
    ),
    post=extend_schema(
        summary="Submit Facility Review",
        description="Authenticated users submit a review for a Hospital or Blood Bank. Starts in PENDING state.",
        request=ReviewCreateSerializer,
        responses={201: ReviewSerializer, 200: ReviewSerializer, 400: OpenApiResponse(description="Validation error")},
        tags=["Facility Reviews"],
    ),
)
class ReviewListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_queryset(self):
        user = self.request.user
        if not (user and user.is_authenticated):
            qs = Review.objects.filter(status=ReviewStatus.APPROVED)
        else:
            is_admin = getattr(user, "is_super_admin", False) or user.is_superuser
            if is_admin:
                qs = Review.objects.all()
            else:
                qs = Review.objects.filter(Q(status=ReviewStatus.APPROVED) | Q(reviewer=user))

        params = self.request.query_params

        # Status filter
        status_param = params.get("status")
        if status_param and status_param.upper() != "ALL":
            qs = qs.filter(status=status_param.upper())

        # Target type filter
        target_type = params.get("target_type")
        if target_type == ReviewTargetType.HOSPITAL:
            qs = qs.filter(hospital__isnull=False)
        elif target_type == ReviewTargetType.BLOOD_BANK:
            qs = qs.filter(blood_bank__isnull=False)

        # Specific facility filters
        hospital_id = params.get("hospital")
        if hospital_id:
            qs = qs.filter(hospital_id=hospital_id)

        blood_bank_id = params.get("blood_bank")
        if blood_bank_id:
            qs = qs.filter(blood_bank_id=blood_bank_id)

        # Rating filter
        rating_param = params.get("rating")
        if rating_param and rating_param.isdigit():
            qs = qs.filter(rating=int(rating_param))

        # Search term filter
        search = params.get("search")
        if search:
            search = search.strip()
            qs = qs.filter(
                Q(reviewer__username__icontains=search)
                | Q(reviewer__first_name__icontains=search)
                | Q(reviewer__last_name__icontains=search)
                | Q(hospital__name__icontains=search)
                | Q(blood_bank__name__icontains=search)
                | Q(comment__icontains=search)
            )

        return qs.select_related("reviewer", "hospital", "blood_bank", "reviewed_by").order_by("-created_at")

    def create(self, request, *args, **kwargs):
        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        review = input_serializer.save()
        output_serializer = ReviewSerializer(review)
        status_code = status.HTTP_201_CREATED
        return Response(output_serializer.data, status=status_code)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Review Details",
        description="Retrieve a single review by ID.",
        responses={200: ReviewSerializer, 404: OpenApiResponse(description="Review not found.")},
        tags=["Facility Reviews"],
    ),
    patch=extend_schema(
        summary="Update Pending Review",
        description="Reviewer may update rating and comment while the review is still PENDING.",
        request=ReviewCreateSerializer,
        responses={200: ReviewSerializer, 400: OpenApiResponse(description="Validation error."), 403: OpenApiResponse(description="Permission denied.")},
        tags=["Facility Reviews"],
    ),
    delete=extend_schema(
        summary="Delete Review",
        description="Delete a review. Permitted to the reviewer while PENDING or to Super Admin.",
        responses={204: OpenApiResponse(description="Review deleted."), 403: OpenApiResponse(description="Permission denied.")},
        tags=["Facility Reviews"],
    ),
)
class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.select_related("reviewer", "hospital", "blood_bank", "reviewed_by").all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        user = request.user
        is_admin = getattr(user, "is_super_admin", False) or user.is_superuser

        if request.method in permissions.SAFE_METHODS:
            if not is_admin and obj.status != ReviewStatus.APPROVED and obj.reviewer_id != user.id:
                raise PermissionDenied("You do not have permission to view this pending/rejected review.")

        if request.method in ["PUT", "PATCH"]:
            if not is_admin:
                if obj.reviewer_id != user.id:
                    raise PermissionDenied("You cannot edit another user's review.")
                if obj.status != ReviewStatus.PENDING:
                    raise PermissionDenied("Only pending reviews can be edited. Submitted reviews are locked once moderated.")

        if request.method == "DELETE":
            if not is_admin and obj.reviewer_id != user.id:
                raise PermissionDenied("You cannot delete another user's review.")


class ReviewApproveView(APIView):
    """
    Super Admin Moderation: Approve a pending review.
    Marks review as APPROVED and makes it publicly visible.
    """
    permission_classes = [IsSuperAdmin]

    @extend_schema(
        summary="Approve Review",
        description="Approve a submitted review. Super Admin only.",
        responses={200: ReviewSerializer, 404: OpenApiResponse(description="Review not found.")},
        tags=["Facility Reviews"],
    )
    def post(self, request, pk):
        try:
            review = Review.objects.select_related("reviewer", "hospital", "blood_bank").get(pk=pk)
        except Review.DoesNotExist:
            return Response({"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

        review.status = ReviewStatus.APPROVED
        review.reviewed_by = request.user
        review.reviewed_at = timezone.now()
        review.rejection_reason = ""
        review.save(update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason", "updated_at"])

        return Response(ReviewSerializer(review).data, status=status.HTTP_200_OK)


class ReviewRejectView(APIView):
    """
    Super Admin Moderation: Reject a review.
    Marks review as REJECTED with an optional reason. Excluded from public display.
    """
    permission_classes = [IsSuperAdmin]

    @extend_schema(
        summary="Reject Review",
        description="Reject a submitted review with an optional explanation. Super Admin only.",
        request=ReviewModerateSerializer,
        responses={200: ReviewSerializer, 404: OpenApiResponse(description="Review not found.")},
        tags=["Facility Reviews"],
    )
    def post(self, request, pk):
        try:
            review = Review.objects.select_related("reviewer", "hospital", "blood_bank").get(pk=pk)
        except Review.DoesNotExist:
            return Response({"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewModerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review.status = ReviewStatus.REJECTED
        review.reviewed_by = request.user
        review.reviewed_at = timezone.now()
        review.rejection_reason = serializer.validated_data.get("rejection_reason", "").strip()
        review.save(update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason", "updated_at"])

        return Response(ReviewSerializer(review).data, status=status.HTTP_200_OK)
