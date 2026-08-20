from django.contrib import admin
from .models import BloodRequest


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "hospital_staff",
        "blood_bank",
        "blood_group",
        "units_needed",
        "urgency",
        "status",
        "approved_by",
        "approved_at",
        "created_at",
    )
    list_filter = (
        "status",
        "urgency",
        "blood_group",
        "blood_bank",
        "created_at",
    )
    search_fields = (
        "hospital_staff__username",
        "hospital_staff__email",
        "blood_bank__name",
        "rejection_reason",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "approved_by",
        "approved_at",
        "reserved_units",
    )
    fieldsets = (
        ("Request Details", {
            "fields": (
                "hospital_staff",
                "blood_bank",
                "blood_group",
                "units_needed",
                "urgency",
                "status",
            )
        }),
        ("Approval / Rejection Outcome", {
            "fields": (
                "approved_by",
                "approved_at",
                "rejection_reason",
                "reserved_units",
            )
        }),
        ("Audit Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
