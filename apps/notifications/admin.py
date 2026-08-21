from django.contrib import admin

from .models import EmailRecipient, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "recipient", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "recipient__username", "recipient__email")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "name", "recipient_type", "is_active", "user", "created_at")
    list_filter = ("recipient_type", "is_active", "created_at")
    search_fields = ("email", "name", "user__username")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
