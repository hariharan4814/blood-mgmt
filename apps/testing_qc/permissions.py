from rest_framework import permissions
from apps.accounts.models import UserRole


class IsLabTechnicianForWriteOrReadOnly(permissions.BasePermission):
    """
    Permission class governing Laboratory Quality Control access:
    - Write access (POST, PATCH, PUT, DELETE): Restricted strictly to LAB_TECHNICIAN users.
      SUPER_ADMIN and BLOOD_BANK_ADMIN do NOT have routine testing write access.
    - Read access (GET, HEAD, OPTIONS):
      - LAB_TECHNICIAN: Allowed.
      - SUPER_ADMIN: Allowed.
      - BLOOD_BANK_ADMIN: Allowed only for blood units in their assigned blood bank.
    - Other roles (HOSPITAL_STAFF, DONOR, unauthenticated): Denied.
    """
    message = "Only authorized Lab Technicians can perform quality control and screening updates."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Write operations: LAB_TECHNICIAN only
        if request.method not in permissions.SAFE_METHODS:
            return request.user.role == UserRole.LAB_TECHNICIAN

        # Read operations (SAFE_METHODS): LAB_TECHNICIAN, SUPER_ADMIN, BLOOD_BANK_ADMIN
        return (
            request.user.role in [UserRole.LAB_TECHNICIAN, UserRole.BLOOD_BANK_ADMIN]
            or request.user.is_super_admin
        )

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        # Write operations: LAB_TECHNICIAN only
        if request.method not in permissions.SAFE_METHODS:
            return request.user.role == UserRole.LAB_TECHNICIAN

        # Super Admin has read visibility
        if request.user.is_super_admin or request.user.role == UserRole.LAB_TECHNICIAN:
            return True

        # Blood Bank Admin has read visibility only for units belonging to their assigned bank
        if request.user.role == UserRole.BLOOD_BANK_ADMIN:
            if hasattr(obj, "blood_unit"):
                return obj.blood_unit.blood_bank.admin_id == request.user.id
            elif hasattr(obj, "blood_bank"):
                return obj.blood_bank.admin_id == request.user.id

        return False
