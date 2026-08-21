from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models


class NotificationType(models.TextChoices):
    """
    Standardized notification categories across the Blood Management System.
    """
    GENERAL = "GENERAL", "General Notification"
    SYSTEM = "SYSTEM", "System Alert"
    BLOOD_REQUEST = "BLOOD_REQUEST", "Blood Request Update"
    DONATION = "DONATION", "Donation Update"
    CAMP = "CAMP", "Donation Camp Update"
    ELIGIBILITY = "ELIGIBILITY", "Donor Eligibility Alert"
    INVENTORY = "INVENTORY", "Inventory Notice"
    SOS = "SOS", "Emergency Alert"  # Choice category placeholder only (no SOS workflow)


class Notification(models.Model):
    """
    In-app database-backed notification attached directly to a User.
    Provides personal notification history with read/unread tracking.
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User receiving the notification."
    )
    title = models.CharField(
        max_length=255,
        help_text="Concise summary title of the notification."
    )
    message = models.TextField(
        help_text="Detailed notification content body."
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
        help_text="Category of the notification."
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Designates whether the recipient has read this notification."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when notification was generated."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when notification was last updated."
    )

    class Meta:
        db_table = "notifications"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "notification_type"]),
        ]

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"[{self.notification_type}] {self.title} -> {self.recipient.username} ({status})"

    def clean(self):
        super().clean()
        if self.title is not None:
            self.title = self.title.strip()
        if not self.title:
            raise ValidationError({"title": "Notification title cannot be blank or whitespace-only."})

        if self.message is not None:
            self.message = self.message.strip()
        if not self.message:
            raise ValidationError({"message": "Notification message cannot be blank or whitespace-only."})

        if not hasattr(self, "recipient") or self.recipient is None:
            raise ValidationError({"recipient": "Notification recipient must be specified."})

    def save(self, *args, **kwargs):
        if self.title:
            self.title = self.title.strip()
        if self.message:
            self.message = self.message.strip()
        self.full_clean()
        super().save(*args, **kwargs)


class EmailRecipientType(models.TextChoices):
    """
    Designated categories for managed email recipients.
    """
    ADMIN = "ADMIN", "Administrator"
    BLOOD_BANK = "BLOOD_BANK", "Blood Bank Coordinator"
    HOSPITAL = "HOSPITAL", "Hospital Contact"
    STAFF = "STAFF", "Staff Member"
    GENERAL = "GENERAL", "General Subscriber"
    EMERGENCY_DESK = "EMERGENCY_DESK", "Emergency Desk Contact"


class EmailRecipient(models.Model):
    """
    Managed email recipient record for administrative distribution lists.
    Guarantees validated, unique email addresses and role-protected management.
    """
    email = models.EmailField(
        unique=True,
        help_text="Validated unique email address for communication."
    )
    name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Recipient full name, organization, or department."
    )
    recipient_type = models.CharField(
        max_length=30,
        choices=EmailRecipientType.choices,
        default=EmailRecipientType.GENERAL,
        help_text="Role classification of the email recipient."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="email_subscriptions",
        help_text="Optional associated system User account."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether automated communications are active for this recipient."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_email_recipients",
        help_text="Administrator who registered this recipient."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when recipient was registered."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when recipient record was last updated."
    )

    class Meta:
        db_table = "email_recipients"
        verbose_name = "Email Recipient"
        verbose_name_plural = "Email Recipients"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["recipient_type", "is_active"]),
        ]

    def __str__(self):
        name_part = f" ({self.name})" if self.name else ""
        return f"{self.email}{name_part} [{self.get_recipient_type_display()}]"

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.strip().lower()
            try:
                validate_email(self.email)
            except ValidationError:
                raise ValidationError({"email": "Enter a valid email address."})
        else:
            raise ValidationError({"email": "Email address is required."})

        if self.name is not None:
            self.name = self.name.strip()

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        if self.name:
            self.name = self.name.strip()
        self.full_clean()
        super().save(*args, **kwargs)
