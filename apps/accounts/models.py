from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    BLOOD_BANK_ADMIN = "BLOOD_BANK_ADMIN", "Blood Bank Admin"
    HOSPITAL_STAFF = "HOSPITAL_STAFF", "Hospital Staff"
    LAB_TECHNICIAN = "LAB_TECHNICIAN", "Lab Technician"
    DONOR = "DONOR", "Donor"


class User(AbstractUser):
    """
    Centralized Custom User model supporting Role-Based Access Control (RBAC).
    """
    email = models.EmailField(unique=True, help_text="Unique email address for user authentication.")
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.DONOR,
        help_text="Role-based access level for the user."
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Primary contact phone number."
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Designates whether the user's email/account has been verified."
    )

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN or self.is_superuser

    @property
    def is_blood_bank_admin(self):
        return self.role == UserRole.BLOOD_BANK_ADMIN

    @property
    def is_hospital_staff(self):
        return self.role == UserRole.HOSPITAL_STAFF

    @property
    def is_lab_technician(self):
        return self.role == UserRole.LAB_TECHNICIAN

    @property
    def is_donor(self):
        return self.role == UserRole.DONOR
