from django.contrib import admin
from .models import BloodBank, BloodUnit


@admin.register(BloodBank)
class BloodBankAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "contact_number",
        "capacity",
        "is_active",
        "admin",
        "created_at",
    )
    list_filter = ("is_active", "city", "state")
    search_fields = ("name", "city", "state", "email", "contact_number")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "is_active", "admin")
        }),
        ("Location & Contact", {
            "fields": ("address", "city", "state", "contact_number", "email", "latitude", "longitude")
        }),
        ("Storage Capacity", {
            "fields": ("capacity",)
        }),
        ("Audit Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(BloodUnit)
class BloodUnitAdmin(admin.ModelAdmin):
    list_display = (
        "unit_id",
        "blood_bank",
        "blood_group",
        "collection_date",
        "expiry_date",
        "status",
        "is_expired",
    )
    list_filter = ("status", "blood_group", "blood_bank")
    search_fields = ("unit_id", "blood_bank__name")
    readonly_fields = ("expiry_date", "created_at", "updated_at", "is_expired")
    fieldsets = (
        ("Unit Identification", {
            "fields": ("unit_id", "blood_bank", "blood_group")
        }),
        ("Lifecycle & Dates", {
            "fields": ("collection_date", "expiry_date", "status")
        }),
        ("Audit Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(boolean=True, description="Expired")
    def is_expired(self, obj):
        return obj.is_expired
