from django.contrib import admin
from .models import DonationCamp, DonationCampRegistration, Donation


@admin.register(DonationCamp)
class DonationCampAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "blood_bank",
        "camp_date",
        "organizer",
        "target_units",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "blood_bank", "camp_date", "created_at")
    search_fields = ("name", "location", "organizer", "blood_bank__name")
    raw_id_fields = ("blood_bank", "created_by")
    date_hierarchy = "camp_date"


@admin.register(DonationCampRegistration)
class DonationCampRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "donor",
        "camp",
        "status",
        "registered_at",
        "updated_at",
    )
    list_filter = ("status", "camp__blood_bank", "registered_at")
    search_fields = (
        "donor__user__username",
        "donor__user__email",
        "camp__name",
    )
    raw_id_fields = ("donor", "camp")
    date_hierarchy = "registered_at"


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "donor",
        "blood_bank",
        "camp",
        "blood_unit",
        "donation_date",
        "created_by",
        "created_at",
    )
    list_filter = ("blood_bank", "donation_date", "camp", "created_at")
    search_fields = (
        "donor__user__username",
        "donor__user__email",
        "blood_bank__name",
        "camp__name",
        "blood_unit__unit_id",
    )
    raw_id_fields = ("donor", "blood_bank", "camp", "blood_unit", "created_by")
    date_hierarchy = "donation_date"
