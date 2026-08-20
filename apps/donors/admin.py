from django.contrib import admin
from .models import Donor


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "blood_group",
        "date_of_birth",
        "age",
        "weight_kg",
        "last_donation_date",
        "is_eligible",
        "created_at",
    )
    list_filter = ("blood_group", "created_at")
    search_fields = ("user__username", "user__email", "user__phone")
    readonly_fields = ("age", "is_eligible", "created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("User Account", {"fields": ("user",)}),
        ("Medical & Eligibility Details", {"fields": ("blood_group", "date_of_birth", "age", "weight_kg", "last_donation_date", "is_eligible")}),
        ("Location Coordinates", {"fields": ("latitude", "longitude")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Age (Years)")
    def age(self, obj):
        return obj.age

    @admin.display(description="Eligible?", boolean=True)
    def is_eligible(self, obj):
        return obj.is_eligible
