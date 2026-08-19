from rest_framework import permissions
from .models import UserRole


class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to super admin users (role == SUPER_ADMIN or is_superuser).
    """
    message = "Only Super Administrators are authorized to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == UserRole.SUPER_ADMIN or request.user.is_superuser)
        )


class IsBloodBankAdmin(permissions.BasePermission):
    """
    Allows access only to blood bank admin users.
    """
    message = "Only Blood Bank Administrators are authorized to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == UserRole.BLOOD_BANK_ADMIN or request.user.is_superuser)
        )


class IsHospitalStaff(permissions.BasePermission):
    """
    Allows access only to hospital staff users.
    """
    message = "Only Hospital Staff are authorized to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == UserRole.HOSPITAL_STAFF or request.user.is_superuser)
        )


class IsLabTechnician(permissions.BasePermission):
    """
    Allows access only to lab technicians.
    """
    message = "Only Lab Technicians are authorized to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == UserRole.LAB_TECHNICIAN or request.user.is_superuser)
        )


class IsDonor(permissions.BasePermission):
    """
    Allows access only to registered donors.
    """
    message = "Only Donors are authorized to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == UserRole.DONOR or request.user.is_superuser)
        )


class HasAnyRole(permissions.BasePermission):
    """
    Reusable permission class that checks if the authenticated user has any of the roles
    specified in `allowed_roles` attribute on the view class.
    """
    message = "You do not have the required role to access this resource."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser or request.user.role == UserRole.SUPER_ADMIN:
            return True
        allowed_roles = getattr(view, "allowed_roles", None)
        if not allowed_roles:
            return True
        return request.user.role in allowed_roles


def HasRoles(*roles):
    """
    Factory function returning a dynamic DRF permission class that permits access
    if the authenticated user's role is in the provided roles (or is super admin).
    Example:
        permission_classes = [HasRoles(UserRole.DONOR, UserRole.HOSPITAL_STAFF)]
    """
    class DynamicRolePermission(permissions.BasePermission):
        allowed_roles = set(roles)
        message = f"Access restricted to roles: {', '.join(roles)}."

        def has_permission(self, request, view):
            return bool(
                request.user
                and request.user.is_authenticated
                and (request.user.role in self.allowed_roles or request.user.is_super_admin)
            )

    return DynamicRolePermission
