from rest_framework import permissions
from apps.accounts.models import UserRole


class IsBankAdminForCampWriteOrReadOnly(permissions.BasePermission):
    """
    Permission class for Donation Camp endpoints:
    - GET (list/detail): Allowed for authenticated DONOR, BLOOD_BANK_ADMIN, and SUPER_ADMIN.
    - POST (create): Allowed for BLOOD_BANK_ADMIN and SUPER_ADMIN.
    - PATCH / PUT / DELETE: Scoped to assigned BLOOD_BANK_ADMIN for that camp's blood bank, or SUPER_ADMIN.
    - Other roles (HOSPITAL_STAFF, LAB_TECHNICIAN, unauthenticated): Denied.
    """
    message = "You do not have permission to manage donation camps."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_super_admin:
            return True

        if request.method in permissions.SAFE_METHODS:
            return request.user.role in [UserRole.DONOR, UserRole.BLOOD_BANK_ADMIN]

        # POST / write operations
        return request.user.role == UserRole.BLOOD_BANK_ADMIN

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_super_admin:
            return True

        if request.method in permissions.SAFE_METHODS:
            return request.user.role in [UserRole.DONOR, UserRole.BLOOD_BANK_ADMIN]

        # Write operations on a specific camp
        if request.user.role == UserRole.BLOOD_BANK_ADMIN:
            return obj.blood_bank.admin_id == request.user.id

        return False


class CanRegisterForCamp(permissions.BasePermission):
    """
    Restricted to authenticated DONOR users who possess a donor profile.
    """
    message = "Only registered Donors can register for a donation camp."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == UserRole.DONOR or request.user.is_super_admin)
            and hasattr(request.user, "donor_profile")
        )


class CanManageOrViewRegistrations(permissions.BasePermission):
    """
    Permission class for Donation Camp Registrations:
    - GET:
      - DONOR: Views only their own registrations.
      - BLOOD_BANK_ADMIN: Views registrations for camps belonging to their assigned blood bank.
      - SUPER_ADMIN: Views all registrations.
    - Cancel / Update:
      - DONOR: Can cancel their own registration.
      - BLOOD_BANK_ADMIN: Can manage registrations for their assigned camps.
      - SUPER_ADMIN: Full access.
    - Other roles: Denied.
    """
    message = "You do not have permission to view or manage camp registrations."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return (
            request.user.role in [UserRole.DONOR, UserRole.BLOOD_BANK_ADMIN]
            or request.user.is_super_admin
        )

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_super_admin:
            return True

        if request.user.role == UserRole.DONOR:
            return obj.donor.user_id == request.user.id

        if request.user.role == UserRole.BLOOD_BANK_ADMIN:
            return obj.camp.blood_bank.admin_id == request.user.id

        return False


class CanRecordOrViewDonations(permissions.BasePermission):
    """
    Permission class for Donation records:
    - POST (record donation): Restricted to assigned BLOOD_BANK_ADMIN (or SUPER_ADMIN).
    - GET (list/detail):
      - DONOR: Views only their own personal donation history.
      - BLOOD_BANK_ADMIN: Views donations recorded at their assigned blood bank.
      - SUPER_ADMIN: Views all donations.
    - Other roles (HOSPITAL_STAFF, LAB_TECHNICIAN, unauthenticated): Denied.
    """
    message = "You do not have permission to record or view donation records."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_super_admin:
            return True

        if request.method == "POST":
            # Only Blood Bank Admins (and Super Admin) can record actual donations
            return request.user.role == UserRole.BLOOD_BANK_ADMIN

        # GET: Donors and Blood Bank Admins
        return request.user.role in [UserRole.DONOR, UserRole.BLOOD_BANK_ADMIN]

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_super_admin:
            return True

        if request.user.role == UserRole.DONOR:
            return obj.donor.user_id == request.user.id

        if request.user.role == UserRole.BLOOD_BANK_ADMIN:
            return obj.blood_bank.admin_id == request.user.id

        return False
