from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .validators import validate_phone_number, validate_profile_image

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and updating personal user profile details.
    Restricts edits to safe fields only (first_name, last_name, email, phone).
    """
    full_name = serializers.CharField(read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    profile_image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "role_display",
            "phone",
            "profile_image",
            "profile_image_url",
            "is_verified",
            "is_active",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "username",
            "role",
            "role_display",
            "full_name",
            "profile_image",
            "profile_image_url",
            "is_verified",
            "is_active",
            "date_joined",
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_profile_image_url(self, obj):
        if obj.profile_image and hasattr(obj.profile_image, "url"):
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None

    def validate_first_name(self, value):
        if value is not None:
            return value.strip()
        return ""

    def validate_last_name(self, value):
        if value is not None:
            return value.strip()
        return ""

    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Email address cannot be empty.")

        clean_email = value.strip().lower()
        user_id = self.instance.id if self.instance else None
        if User.objects.filter(email__iexact=clean_email).exclude(id=user_id).exists():
            raise serializers.ValidationError("A user with this email address already exists.")

        return clean_email

    def validate_phone(self, value):
        if not value or not str(value).strip():
            return None
        try:
            return validate_phone_number(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0] if hasattr(e, "messages") else str(e))

    def validate(self, attrs):
        # Strict security filter: strip out any administrative or security fields if present
        protected_fields = [
            "role", "is_staff", "is_superuser", "is_verified",
            "is_active", "password", "date_joined", "last_login", "id"
        ]
        for field in protected_fields:
            attrs.pop(field, None)
        return attrs


class ProfileImageUploadSerializer(serializers.Serializer):
    """
    Serializer for multipart/form-data profile image upload.
    """
    profile_image = serializers.ImageField(
        required=True,
        help_text="Image file in JPEG, PNG, or WEBP format (max 2 MB)."
    )

    def validate_profile_image(self, value):
        try:
            return validate_profile_image(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0] if hasattr(e, "messages") else str(e))
