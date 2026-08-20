from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.accounts.models import UserRole
from apps.donors.models import BloodGroup
from apps.inventory.models import BloodBank, BloodUnit


class RequestUrgency(models.TextChoices):
    NORMAL = "NORMAL", "Normal"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class RequestStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    DISPATCHED = "DISPATCHED", "Dispatched"
    COMPLETED = "COMPLETED", "Completed"


class BloodRequest(models.Model):
    """
    Blood Request raised by Hospital Staff to a designated Blood Bank.
    Tracks unit-level reservations, clinical urgency, approval, and rejection reasons.
    """
    hospital_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blood_requests",
        help_text="Hospital staff user who submitted this blood request."
    )
    blood_bank = models.ForeignKey(
        BloodBank,
        on_delete=models.CASCADE,
        related_name="blood_requests",
        help_text="Target blood bank facility."
    )
    blood_group = models.CharField(
        max_length=5,
        choices=BloodGroup.choices,
        help_text="Requested ABO and Rh blood group."
    )
    units_needed = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of blood units needed (must be at least 1)."
    )
    urgency = models.CharField(
        max_length=20,
        choices=RequestUrgency.choices,
        default=RequestUrgency.NORMAL,
        help_text="Clinical urgency level of the request."
    )
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
        help_text="Current processing status of the blood request."
    )
    rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason provided by the Blood Bank Administrator if the request is rejected."
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_blood_requests",
        help_text="Blood bank administrator user who approved this request."
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the request was approved."
    )
    reserved_units = models.ManyToManyField(
        BloodUnit,
        blank=True,
        related_name="reserved_for_requests",
        help_text="Specific BloodUnit entities reserved for this approved request."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blood_requests"
        verbose_name = "Blood Request"
        verbose_name_plural = "Blood Requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Request #{self.id}: {self.units_needed} units of {self.blood_group} ({self.get_urgency_display()}) - {self.get_status_display()}"

    def clean(self):
        super().clean()
        if self.units_needed is not None and self.units_needed < 1:
            raise ValidationError({"units_needed": "Units needed must be at least 1."})

        if self.status == RequestStatus.REJECTED and not self.rejection_reason.strip():
            raise ValidationError({"rejection_reason": "A rejection reason is required when rejecting a request."})

        if self.hospital_staff and self.hospital_staff.role != UserRole.HOSPITAL_STAFF:
            raise ValidationError({"hospital_staff": "Only Hospital Staff users can raise blood requests."})
