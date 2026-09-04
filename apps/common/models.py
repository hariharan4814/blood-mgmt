from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ReviewStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class ReviewTargetType(models.TextChoices):
    HOSPITAL = "HOSPITAL", "Hospital"
    BLOOD_BANK = "BLOOD_BANK", "Blood Bank"


class Review(models.Model):
    """
    Facility Review and Rating model.
    Enables authenticated users to review partner Hospitals and Blood Banks.
    Requires Super Admin approval before appearing publicly or affecting ratings.
    """
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submitted_reviews",
        help_text="Authenticated user who submitted this review."
    )
    hospital = models.ForeignKey(
        "blood_requests.Hospital",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reviews",
        help_text="Target hospital facility."
    )
    blood_bank = models.ForeignKey(
        "inventory.BloodBank",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reviews",
        help_text="Target blood bank facility."
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Numerical rating from 1 to 5 stars."
    )
    comment = models.TextField(
        help_text="Detailed feedback or review commentary."
    )
    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        db_index=True,
        help_text="Moderation status (PENDING, APPROVED, REJECTED)."
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_reviews",
        help_text="Administrator who reviewed and decided upon this review."
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the review was moderated."
    )
    rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Optional explanation recorded if the review is rejected."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "facility_reviews"
        verbose_name = "Facility Review"
        verbose_name_plural = "Facility Reviews"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(hospital__isnull=False) & models.Q(blood_bank__isnull=True)) |
                    (models.Q(hospital__isnull=True) & models.Q(blood_bank__isnull=False))
                ),
                name="review_must_target_exactly_one_facility"
            )
        ]

    @property
    def target_type(self) -> str:
        if self.hospital_id:
            return ReviewTargetType.HOSPITAL
        if self.blood_bank_id:
            return ReviewTargetType.BLOOD_BANK
        return ""

    @property
    def target_name(self) -> str:
        if self.hospital_id and self.hospital:
            return self.hospital.name
        if self.blood_bank_id and self.blood_bank:
            return self.blood_bank.name
        return ""

    def __str__(self):
        target = self.hospital.name if self.hospital else (self.blood_bank.name if self.blood_bank else "Unknown")
        return f"Review by {self.reviewer.username} on {target} ({self.rating}★ - {self.status})"
