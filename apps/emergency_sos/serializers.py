from rest_framework import serializers

from apps.accounts.models import User
from apps.blood_requests.models import BloodRequest
from .models import SOSBroadcast, SOSRecipient, SOSStatus


class TriggerSOSRequestSerializer(serializers.Serializer):
    """
    Serializer for triggering an Emergency SOS Broadcast.
    """
    radius_km = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Optional radius in kilometers to filter eligible donors by location.",
    )
    custom_message = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text="Optional custom broadcast alert message (defaults to standard emergency notice).",
    )


class SOSCancelRequestSerializer(serializers.Serializer):
    """
    Serializer for cancelling an active SOS broadcast.
    """
    reason = serializers.CharField(
        required=True,
        max_length=1000,
        help_text="Mandatory explanation for cancelling the active SOS broadcast.",
    )

    def validate_reason(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("A cancellation reason is required.")
        return value.strip()


class SOSBloodRequestSummarySerializer(serializers.ModelSerializer):
    """
    Summary representation of associated Blood Request for SOS endpoints.
    """
    hospital_staff_username = serializers.CharField(source="hospital_staff.username", read_only=True)
    blood_bank_name = serializers.CharField(source="blood_bank.name", read_only=True)
    urgency_display = serializers.CharField(source="get_urgency_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = BloodRequest
        fields = [
            "id",
            "hospital_staff_username",
            "blood_bank_name",
            "blood_group",
            "units_needed",
            "urgency",
            "urgency_display",
            "status",
            "status_display",
            "created_at",
        ]


class SOSBroadcastSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing Emergency SOS Broadcasts.
    """
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    triggered_by_username = serializers.CharField(source="triggered_by.username", read_only=True)
    cancelled_by_username = serializers.CharField(source="cancelled_by.username", read_only=True)
    blood_request_detail = SOSBloodRequestSummarySerializer(source="blood_request", read_only=True)

    class Meta:
        model = SOSBroadcast
        fields = [
            "id",
            "blood_request",
            "blood_request_detail",
            "triggered_by",
            "triggered_by_username",
            "status",
            "status_display",
            "blood_group",
            "units_needed",
            "available_units_at_trigger",
            "shortage_units",
            "radius_km",
            "total_donors_targeted",
            "title",
            "message",
            "created_at",
            "updated_at",
            "completed_at",
            "cancelled_at",
            "cancelled_by",
            "cancelled_by_username",
            "cancellation_reason",
        ]
        read_only_fields = fields


class SOSRecipientSerializer(serializers.ModelSerializer):
    """
    Serializer for auditing donor recipients targeted by an SOS broadcast.
    """
    donor_username = serializers.CharField(source="user.username", read_only=True)
    donor_blood_group = serializers.CharField(source="donor.blood_group", read_only=True)

    class Meta:
        model = SOSRecipient
        fields = [
            "id",
            "sos_broadcast",
            "donor",
            "donor_username",
            "donor_blood_group",
            "notification",
            "email_attempted",
            "email_sent",
            "delivery_error",
            "created_at",
        ]
        read_only_fields = fields
