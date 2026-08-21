from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.blood_requests.models import BloodRequest
from apps.donors.models import BloodGroup, Donor
from apps.notifications.models import Notification


class SOSStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    EXPIRED = "EXPIRED", "Expired"


class SOSBroadcast(models.Model):
    """
    Emergency SOS Broadcast entity created for legitimate critical blood shortages.
    Tracks target parameters, shortage snapshot, matched donor count, and audit timestamps.
    """
    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        related_name="sos_broadcasts",
        help_text="Critical blood request that triggered this emergency broadcast."
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="triggered_sos_broadcasts",
        help_text="Staff member who authorized the emergency broadcast."
    )
    status = models.CharField(
        max_length=20,
        choices=SOSStatus.choices,
        default=SOSStatus.ACTIVE,
        help_text="Current operational status of this SOS broadcast."
    )
    blood_group = models.CharField(
        max_length=5,
        choices=BloodGroup.choices,
        help_text="Target requested blood group."
    )
    units_needed = models.PositiveIntegerField(
        help_text="Total blood units required by the critical request."
    )
    available_units_at_trigger = models.PositiveIntegerField(
        help_text="Available stock units at the target blood bank when broadcast was triggered."
    )
    shortage_units = models.PositiveIntegerField(
        help_text="Quantity shortage (units_needed - available_units_at_trigger)."
    )
    radius_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional geographical radius filter applied in kilometers."
    )
    total_donors_targeted = models.PositiveIntegerField(
        default=0,
        help_text="Total count of eligible compatible donors notified."
    )
    title = models.CharField(
        max_length=255,
        help_text="Broadcast summary title."
    )
    message = models.TextField(
        help_text="Emergency broadcast message sent to donors."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when SOS broadcast was triggered."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when SOS broadcast was last updated."
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when SOS broadcast was marked completed."
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when SOS broadcast was cancelled."
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cancelled_sos_broadcasts",
        help_text="Staff or admin user who cancelled the broadcast."
    )
    cancellation_reason = models.TextField(
        blank=True,
        default="",
        help_text="Explanation for cancellation."
    )

    class Meta:
        db_table = "sos_broadcasts"
        verbose_name = "SOS Broadcast"
        verbose_name_plural = "SOS Broadcasts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["blood_request", "status"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"SOS #{self.id}: {self.blood_group} ({self.get_status_display()}) - Request #{self.blood_request_id}"

    def clean(self):
        super().clean()
        if self.title is not None:
            self.title = self.title.strip()
        if not self.title:
            raise ValidationError({"title": "SOS title cannot be blank or whitespace-only."})

        if self.message is not None:
            self.message = self.message.strip()
        if not self.message:
            raise ValidationError({"message": "SOS message cannot be blank or whitespace-only."})


class SOSRecipient(models.Model):
    """
    Audit log of individual donor recipients targeted by an SOS broadcast.
    Tracks in-app notification linkage and email delivery attempts.
    """
    sos_broadcast = models.ForeignKey(
        SOSBroadcast,
        on_delete=models.CASCADE,
        related_name="recipients",
        help_text="Associated SOS broadcast."
    )
    donor = models.ForeignKey(
        Donor,
        on_delete=models.CASCADE,
        related_name="sos_deliveries",
        help_text="Targeted donor profile."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sos_notifications_received",
        help_text="User account associated with the donor."
    )
    notification = models.ForeignKey(
        Notification,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sos_delivery_audit",
        help_text="Generated in-app notification record."
    )
    email_attempted = models.BooleanField(
        default=False,
        help_text="Designates whether email dispatch was attempted."
    )
    email_sent = models.BooleanField(
        default=False,
        help_text="Designates whether email dispatch succeeded."
    )
    delivery_error = models.TextField(
        blank=True,
        default="",
        help_text="Safe error description if email delivery failed."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when recipient was notified."
    )

    class Meta:
        db_table = "sos_recipients"
        verbose_name = "SOS Recipient"
        verbose_name_plural = "SOS Recipients"
        ordering = ["-created_at"]
        unique_together = [("sos_broadcast", "donor")]
        indexes = [
            models.Index(fields=["sos_broadcast", "donor"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        status_str = "Email Sent" if self.email_sent else ("Email Attempted" if self.email_attempted else "In-App Only")
        return f"SOS #{self.sos_broadcast_id} -> {self.donor.user.username} ({status_str})"
