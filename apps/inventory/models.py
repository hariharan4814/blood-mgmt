from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.donors.models import BloodGroup

# Standard RBC shelf life in days
RBC_SHELF_LIFE_DAYS = 42


class BloodUnitStatus(models.TextChoices):
    TESTING = "TESTING", "Testing"
    AVAILABLE = "AVAILABLE", "Available"
    RESERVED = "RESERVED", "Reserved"
    DISPATCHED = "DISPATCHED", "Dispatched"
    DISCARDED = "DISCARDED", "Discarded"


class BloodBank(models.Model):
    """
    Blood Bank facility entity.
    Stores location, storage capacity, and designated administrative user.
    """
    name = models.CharField(
        max_length=255,
        help_text="Official name of the blood bank facility."
    )
    address = models.TextField(
        blank=True,
        default="",
        help_text="Physical street address of the blood bank."
    )
    city = models.CharField(
        max_length=100,
        help_text="City where the blood bank is situated."
    )
    state = models.CharField(
        max_length=100,
        help_text="State or province."
    )
    contact_number = models.CharField(
        max_length=30,
        help_text="Primary telephone/contact number."
    )
    email = models.EmailField(
        help_text="Official contact email address."
    )
    capacity = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Maximum total blood unit storage capacity (units)."
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("-90.000000")),
            MaxValueValidator(Decimal("90.000000")),
        ],
        help_text="Latitude coordinate for geographical location (-90.0 to 90.0)."
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("-180.000000")),
            MaxValueValidator(Decimal("180.000000")),
        ],
        help_text="Longitude coordinate for geographical location (-180.0 to 180.0)."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this blood bank is actively operational."
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_blood_banks",
        help_text="Assigned Blood Bank Administrator user account."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blood_banks"
        verbose_name = "Blood Bank"
        verbose_name_plural = "Blood Banks"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"

    def clean(self):
        super().clean()
        if self.capacity is not None and self.capacity < 0:
            raise ValidationError({"capacity": "Capacity cannot be negative."})

        if self.latitude is not None and (self.latitude < Decimal("-90.000000") or self.latitude > Decimal("90.000000")):
            raise ValidationError({"latitude": "Latitude must be between -90.0 and 90.0 degrees."})

        if self.longitude is not None and (self.longitude < Decimal("-180.000000") or self.longitude > Decimal("180.000000")):
            raise ValidationError({"longitude": "Longitude must be between -180.0 and 180.0 degrees."})

        if self.admin and self.admin.role not in [UserRole.BLOOD_BANK_ADMIN, UserRole.SUPER_ADMIN] and not self.admin.is_superuser:
            raise ValidationError({"admin": "Assigned admin must have the BLOOD_BANK_ADMIN or SUPER_ADMIN role."})


class BloodUnit(models.Model):
    """
    Unit-level tracking entity for collected blood units.
    Implements 42-day RBC expiry and strict inventory status tracking.
    """
    blood_bank = models.ForeignKey(
        BloodBank,
        on_delete=models.CASCADE,
        related_name="blood_units",
        help_text="Blood bank where this unit is stored."
    )
    unit_id = models.CharField(
        max_length=60,
        unique=True,
        db_index=True,
        help_text="Unique, human-readable identifier for this blood unit."
    )
    blood_group = models.CharField(
        max_length=5,
        choices=BloodGroup.choices,
        help_text="ABO and Rh blood group."
    )
    collection_date = models.DateField(
        help_text="Date the blood unit was collected from the donor."
    )
    expiry_date = models.DateField(
        help_text="Expiry date calculated strictly as collection_date + 42 days."
    )
    status = models.CharField(
        max_length=20,
        choices=BloodUnitStatus.choices,
        default=BloodUnitStatus.TESTING,
        help_text="Current lifecycle and quality status of the blood unit."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blood_units"
        verbose_name = "Blood Unit"
        verbose_name_plural = "Blood Units"
        ordering = ["-collection_date", "-created_at"]

    def __str__(self):
        return f"{self.unit_id} ({self.blood_group}) - {self.get_status_display()}"

    def clean(self):
        super().clean()
        today = timezone.now().date()

        if self.collection_date and self.collection_date > today:
            raise ValidationError({"collection_date": "Collection date cannot be in the future."})

        # Calculate or validate expiry date based on standard 42-day rule
        if self.collection_date:
            expected_expiry = self.collection_date + timedelta(days=RBC_SHELF_LIFE_DAYS)
            if self.expiry_date and self.expiry_date != expected_expiry:
                raise ValidationError({
                    "expiry_date": f"Expiry date must be exactly {RBC_SHELF_LIFE_DAYS} days from collection date ({expected_expiry})."
                })
            elif not self.expiry_date:
                self.expiry_date = expected_expiry

    def save(self, *args, **kwargs):
        if self.collection_date and not self.expiry_date:
            self.expiry_date = self.collection_date + timedelta(days=RBC_SHELF_LIFE_DAYS)
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Returns True if the blood unit has passed its expiry date."""
        return self.expiry_date < timezone.now().date()

    @property
    def is_available_stock(self):
        """
        Returns True if the unit is counted as available inventory:
        Status must be AVAILABLE and expiry date must not be in the past.
        """
        return self.status == BloodUnitStatus.AVAILABLE and not self.is_expired
