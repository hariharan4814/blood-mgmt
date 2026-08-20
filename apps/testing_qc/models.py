from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.inventory.models import BloodUnit, BloodUnitStatus


class ScreeningResult(models.TextChoices):
    PENDING = "PENDING", "Pending"
    NEGATIVE = "NEGATIVE", "Negative"
    POSITIVE = "POSITIVE", "Positive"


class TestResult(models.Model):
    """
    Laboratory infectious disease screening record for an individual BloodUnit.
    Mandatory screenings: HIV, Hepatitis B, Hepatitis C, Syphilis, and Malaria.
    """
    blood_unit = models.OneToOneField(
        BloodUnit,
        on_delete=models.CASCADE,
        related_name="test_result",
        help_text="Blood unit undergoing laboratory screening."
    )
    hiv_result = models.CharField(
        max_length=20,
        choices=ScreeningResult.choices,
        default=ScreeningResult.PENDING,
        help_text="HIV antibody/antigen screening result."
    )
    hepatitis_b_result = models.CharField(
        max_length=20,
        choices=ScreeningResult.choices,
        default=ScreeningResult.PENDING,
        help_text="Hepatitis B surface antigen (HBsAg) screening result."
    )
    hepatitis_c_result = models.CharField(
        max_length=20,
        choices=ScreeningResult.choices,
        default=ScreeningResult.PENDING,
        help_text="Hepatitis C antibody (Anti-HCV) screening result."
    )
    syphilis_result = models.CharField(
        max_length=20,
        choices=ScreeningResult.choices,
        default=ScreeningResult.PENDING,
        help_text="Syphilis (VDRL/RPR) screening result."
    )
    malaria_result = models.CharField(
        max_length=20,
        choices=ScreeningResult.choices,
        default=ScreeningResult.PENDING,
        help_text="Malaria parasite screening result."
    )
    tested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conducted_tests",
        help_text="Laboratory technician who conducted or updated the test results."
    )
    tested_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the laboratory testing was recorded."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "test_results"
        verbose_name = "Test Result"
        verbose_name_plural = "Test Results"
        ordering = ["-created_at"]

    def __str__(self):
        return f"TestResult for {self.blood_unit.unit_id} ({self.overall_outcome})"

    @property
    def results_list(self):
        return [
            self.hiv_result,
            self.hepatitis_b_result,
            self.hepatitis_c_result,
            self.syphilis_result,
            self.malaria_result,
        ]

    @property
    def has_positive(self):
        """Returns True if any of the 5 required disease screenings is POSITIVE."""
        return ScreeningResult.POSITIVE in self.results_list

    @property
    def all_negative(self):
        """Returns True if all 5 required disease screenings are NEGATIVE."""
        return all(res == ScreeningResult.NEGATIVE for res in self.results_list)

    @property
    def has_pending(self):
        """Returns True if one or more screenings are still PENDING."""
        return ScreeningResult.PENDING in self.results_list

    @property
    def overall_outcome(self):
        """
        Computed overall clinical outcome:
        - 'POSITIVE' if ANY test is positive
        - 'NEGATIVE' if ALL five tests are negative
        - 'PENDING' if tests are still incomplete and none positive
        """
        if self.has_positive:
            return "POSITIVE"
        if self.all_negative:
            return "NEGATIVE"
        return "PENDING"

    def clean(self):
        super().clean()
        if self.tested_by and self.tested_by.role != UserRole.LAB_TECHNICIAN and not self.tested_by.is_superuser:
            raise ValidationError({"tested_by": "Testing must be performed by a LAB_TECHNICIAN."})

    def save(self, *args, **kwargs):
        if not self.tested_at:
            self.tested_at = timezone.now()
        super().save(*args, **kwargs)
