from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Notification, NotificationType, EmailRecipient, EmailRecipientType

User = get_user_model()


class NotificationRecipientSummarySerializer(serializers.ModelSerializer):
    """
    Compact user summary for notification metadata.
    """
    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing in-app notifications.
    """
    recipient_detail = NotificationRecipientSummarySerializer(source="recipient", read_only=True)
    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "recipient_detail",
            "title",
            "message",
            "notification_type",
            "notification_type_display",
            "is_read",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "recipient",
            "recipient_detail",
            "title",
            "message",
            "notification_type",
            "notification_type_display",
            "is_read",
            "created_at",
            "updated_at",
        ]


class UnreadCountSerializer(serializers.Serializer):
    """
    Serializer for returning the user's unread notification count.
    """
    unread_count = serializers.IntegerField(help_text="Total number of unread notifications.")


class MarkAllReadResponseSerializer(serializers.Serializer):
    """
    Serializer for mark-all-read response.
    """
    marked_count = serializers.IntegerField(help_text="Number of notifications marked as read.")
    detail = serializers.CharField(help_text="Status summary message.")


class EmailRecipientSerializer(serializers.ModelSerializer):
    """
    Serializer for managing administrative email recipients.
    """
    recipient_type_display = serializers.CharField(source="get_recipient_type_display", read_only=True)
    user_detail = NotificationRecipientSummarySerializer(source="user", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = EmailRecipient
        fields = [
            "id",
            "email",
            "name",
            "recipient_type",
            "recipient_type_display",
            "user",
            "user_detail",
            "is_active",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "recipient_type_display",
            "user_detail",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
        ]

    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Email address cannot be empty.")
        clean_email = value.strip().lower()
        
        # Check uniqueness on create or when email changed on update
        qs = EmailRecipient.objects.filter(email=clean_email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("An email recipient with this email address already exists.")
        return clean_email

    def create(self, validated_data):
        # Attach requesting administrator as created_by
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        return super().create(validated_data)
