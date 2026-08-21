from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "phone",
        "is_verified",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("role", "is_verified", "is_staff", "is_active", "date_joined")
    search_fields = ("username", "email", "phone", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal Information",
            {"fields": ("first_name", "last_name", "email", "phone", "profile_image")},
        ),
        (
            "Role & Verification",
            {"fields": ("role", "is_verified")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Additional Info",
            {
                "classes": ("wide",),
                "fields": ("email", "role", "phone", "is_verified"),
            },
        ),
    )
