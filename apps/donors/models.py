from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from apps.accounts.models import UserRole
from .services import calculate_donor_eligibility


class BloodGroup(models.TextChoices):
    A_POSITIVE = "A+", "A+"
    A_NEGATIVE = "A-", "A-"
    B_POSITIVE = "B+", "B+"
    B_NEGATIVE = "B-", "B-"
    AB_POSITIVE = "AB+", "AB+"
    AB_NEGATIVE = "AB-", "AB-"
    O_POSITIVE = "O+", "O+"
    O_NEGATIVE = "O-", "O-"


class Donor(models.Model):
    """
    Donor profile entity linked One-to-One with User.
    Stores medical attributes, location coordinates, and donation history.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="donor_profile",
        help_text="User account associated with this donor profile.",
    )
    blood_group = models.CharField(
        max_length=5,
        choices=BloodGroup.choices,
        help_text="Verified or self-reported ABO and Rh blood group.",
    )
    date_of_birth = models.DateField(
        help_text="Date of birth to verify age eligibility (18–65 years).",
    )
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1.00"))],
        help_text="Body weight in kilograms (minimum 50.0 kg required for donation).",
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
        help_text="Donor coordinate latitude for emergency radius matching.",
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
        help_text="Donor coordinate longitude for emergency radius matching.",
    )
    last_donation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of the most recent blood donation (null for first-time donors).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "donors"
        verbose_name = "Donor"
        verbose_name_plural = "Donors"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} ({self.blood_group})"

    def clean(self):
        super().clean()
        today = timezone.now().date()

        # Enforce that only DONOR role users have a donor profile
        if hasattr(self, "user") and self.user:
            if self.user.role != UserRole.DONOR:
                raise ValidationError(
                    {"user": f"Only users with the '{UserRole.DONOR}' role can have a Donor profile."}
                )

        if self.date_of_birth and self.date_of_birth > today:
            raise ValidationError({"date_of_birth": "Date of birth cannot be in the future."})

        if self.last_donation_date:
            if self.last_donation_date > today:
                raise ValidationError({"last_donation_date": "Last donation date cannot be in the future."})
            if self.date_of_birth and self.last_donation_date < self.date_of_birth:
                raise ValidationError({"last_donation_date": "Last donation date cannot precede date of birth."})

        if self.weight_kg is not None and self.weight_kg <= Decimal("0.00"):
            raise ValidationError({"weight_kg": "Weight must be greater than 0 kg."})

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )

    def calculate_eligibility(self, reference_date=None):
        return calculate_donor_eligibility(
            date_of_birth=self.date_of_birth,
            weight_kg=self.weight_kg,
            last_donation_date=self.last_donation_date,
            reference_date=reference_date,
        )

    @property
    def is_eligible(self):
        return self.calculate_eligibility().get("is_eligible", False)
