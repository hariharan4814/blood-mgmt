from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .profile_serializers import ProfileImageUploadSerializer, UserProfileSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Current User Profile",
        description="Retrieve the authenticated user's personal profile information.",
        responses={200: UserProfileSerializer, 401: OpenApiTypes.OBJECT},
        tags=["Profile"],
    ),
    put=extend_schema(
        summary="Update Current User Profile (Full)",
        description="Fully update personal profile safe fields (first_name, last_name, email, phone). Protected fields (role, is_staff, is_superuser, password) are ignored.",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer, 400: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT},
        tags=["Profile"],
    ),
    patch=extend_schema(
        summary="Update Current User Profile (Partial)",
        description="Partially update personal profile safe fields (first_name, last_name, email, phone). Protected fields (role, is_staff, is_superuser, password) are ignored.",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer, 400: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT},
        tags=["Profile"],
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update personal profile of the currently authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_object(self):
        return self.request.user


@extend_schema_view(
    post=extend_schema(
        summary="Upload / Change Profile Image",
        description="Upload or change the profile image of the currently authenticated user. Allowed formats: JPEG, PNG, WEBP (Max 2 MB).",
        request=ProfileImageUploadSerializer,
        responses={
            200: OpenApiResponse(response=UserProfileSerializer, description="Profile image updated successfully"),
            400: OpenApiResponse(description="Invalid file or format"),
            401: OpenApiResponse(description="Authentication credentials required"),
        },
        tags=["Profile"],
    ),
    delete=extend_schema(
        summary="Remove Profile Image",
        description="Remove the profile image of the currently authenticated user and delete the stored file.",
        responses={
            200: OpenApiResponse(description="Profile image removed successfully"),
            401: OpenApiResponse(description="Authentication credentials required"),
        },
        tags=["Profile"],
    ),
)
class ProfileImageView(APIView):
    """
    Upload or remove the profile image for the currently authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = ProfileImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        uploaded_image = serializer.validated_data["profile_image"]

        # If user already has an image, delete previous file from storage
        if user.profile_image:
            try:
                user.profile_image.delete(save=False)
            except Exception:
                pass

        user.profile_image = uploaded_image
        user.save(update_fields=["profile_image"])

        profile_data = UserProfileSerializer(user, context={"request": request}).data
        return Response(
            {
                "detail": "Profile image updated successfully.",
                "user": profile_data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, *args, **kwargs):
        user = request.user
        if user.profile_image:
            try:
                user.profile_image.delete(save=False)
            except Exception:
                pass
            user.profile_image = None
            user.save(update_fields=["profile_image"])

        return Response(
            {
                "detail": "Profile image removed successfully.",
                "profile_image": None,
            },
            status=status.HTTP_200_OK,
        )
