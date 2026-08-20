from django.contrib import admin
from .models import TestResult


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = (
        "blood_unit_code",
        "blood_group",
        "hiv_result",
        "hepatitis_b_result",
        "hepatitis_c_result",
        "syphilis_result",
        "malaria_result",
        "overall_outcome",
        "tested_by",
        "tested_at",
    )
    list_filter = (
        "hiv_result",
        "hepatitis_b_result",
        "hepatitis_c_result",
        "syphilis_result",
        "malaria_result",
        "tested_at",
    )
    search_fields = (
        "blood_unit__unit_id",
        "blood_unit__blood_bank__name",
        "tested_by__username",
    )
    readonly_fields = ("overall_outcome", "created_at", "updated_at")
    fieldsets = (
        ("Blood Unit Information", {
            "fields": ("blood_unit",)
        }),
        ("Infectious Disease Screenings", {
            "fields": (
                "hiv_result",
                "hepatitis_b_result",
                "hepatitis_c_result",
                "syphilis_result",
                "malaria_result",
            )
        }),
        ("Evaluation Outcome & Technician", {
            "fields": ("overall_outcome", "tested_by", "tested_at")
        }),
        ("Audit Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Unit Code")
    def blood_unit_code(self, obj):
        return obj.blood_unit.unit_id

    @admin.display(description="Blood Group")
    def blood_group(self, obj):
        return obj.blood_unit.blood_group
