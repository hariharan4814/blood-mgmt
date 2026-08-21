from rest_framework import permissions
from apps.accounts.models import UserRole


class IsNotificationRecipient(permissions.BasePermission):
    """
    Object-level permission allowing access ONLY to the notification recipient.
    Strictly prevents cross-user access.
    """
    message = "You are only permitted to access your own notifications."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.recipient_id == request.user.id
        )


class CanManageEmailRecipients(permissions.BasePermission):
    """
    Administrative permission for managing system email recipient distribution lists.
    Restricted to SUPER_ADMIN and BLOOD_BANK_ADMIN.
    """
    message = "Only Super Administrators and Blood Bank Administrators may manage email recipients."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.role in (UserRole.SUPER_ADMIN, UserRole.BLOOD_BANK_ADMIN)
                or request.user.is_superuser
            )
        )
