from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserRole

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model representation (safe fields only).
    """
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "phone",
            "is_verified",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for public user registration.
    Restricted strictly to DONOR and HOSPITAL_STAFF roles.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="User password meeting system complexity requirements."
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="Password confirmation to prevent typing errors."
    )
    role = serializers.ChoiceField(
        choices=[
            (UserRole.DONOR, "Donor"),
            (UserRole.HOSPITAL_STAFF, "Hospital Staff"),
        ],
        default=UserRole.DONOR,
        help_text="Public registration role (DONOR or HOSPITAL_STAFF only)."
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "password_confirm",
            "role",
            "phone",
        ]
        read_only_fields = ["id"]

    def validate_role(self, value):
        allowed_roles = [UserRole.DONOR, UserRole.HOSPITAL_STAFF]
        if value not in allowed_roles:
            raise serializers.ValidationError(
                f"Public registration is only permitted for {', '.join(allowed_roles)}. "
                "Privileged roles (SUPER_ADMIN, BLOOD_BANK_ADMIN, LAB_TECHNICIAN) must be provisioned by an administrator."
            )
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        # Validate password strength using Django's configured validators
        temp_user = User(
            username=attrs.get("username"),
            email=attrs.get("email"),
            phone=attrs.get("phone", "")
        )
        validate_password(password, user=temp_user)

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(
            password=password,
            is_verified=False,
            **validated_data
        )
        return user


class UserAdminUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for Super Admin user updates (PATCH /api/users/{id}/).
    """
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "phone",
            "is_verified",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    def validate_username(self, value):
        user_id = self.instance.id if self.instance else None
        if User.objects.filter(username__iexact=value).exclude(id=user_id).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        user_id = self.instance.id if self.instance else None
        if User.objects.filter(email__iexact=value).exclude(id=user_id).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that embeds user information in token claims
    and returns user payload in the response body.
    Supports authenticating via either username or email address.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims
        token["username"] = user.username
        token["email"] = user.email
        token["role"] = user.role
        token["is_verified"] = user.is_verified
        return token

    def validate(self, attrs):
        # Allow logging in with either username or email
        username_or_email = attrs.get("username")
        if username_or_email and "@" in username_or_email:
            user_by_email = User.objects.filter(email__iexact=username_or_email.strip()).first()
            if user_by_email:
                attrs["username"] = user_by_email.username

        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": self.user.role,
            "phone": self.user.phone,
            "is_verified": self.user.is_verified,
        }
        return data
