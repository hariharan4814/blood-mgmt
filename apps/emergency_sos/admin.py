from django.contrib import admin

from .models import SOSBroadcast, SOSRecipient


class SOSRecipientInline(admin.TabularInline):
    model = SOSRecipient
    extra = 0
    readonly_fields = ("donor", "user", "notification", "email_attempted", "email_sent", "delivery_error", "created_at")
    can_delete = False


@admin.register(SOSBroadcast)
class SOSBroadcastAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "blood_request",
        "blood_group",
        "units_needed",
        "available_units_at_trigger",
        "shortage_units",
        "status",
        "total_donors_targeted",
        "triggered_by",
        "created_at",
    )
    list_filter = ("status", "blood_group", "created_at")
    search_fields = ("title", "message", "blood_request__id", "triggered_by__username")
    readonly_fields = (
        "blood_request",
        "triggered_by",
        "blood_group",
        "units_needed",
        "available_units_at_trigger",
        "shortage_units",
        "total_donors_targeted",
        "created_at",
        "updated_at",
        "completed_at",
        "cancelled_at",
        "cancelled_by",
    )
    inlines = [SOSRecipientInline]
    ordering = ("-created_at",)


@admin.register(SOSRecipient)
class SOSRecipientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sos_broadcast",
        "donor",
        "user",
        "email_attempted",
        "email_sent",
        "created_at",
    )
    list_filter = ("email_attempted", "email_sent", "created_at")
    search_fields = ("user__username", "user__email", "sos_broadcast__id")
    readonly_fields = ("sos_broadcast", "donor", "user", "notification", "created_at")
    ordering = ("-created_at",)
