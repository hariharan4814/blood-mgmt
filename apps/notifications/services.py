from typing import Iterable, List, Optional
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Notification, NotificationType

User = get_user_model()


def validate_notification_content(title: str, message: str) -> tuple[str, str]:
    """
    Validates and normalizes notification title and message content.
    Raises ValidationError if either is empty or whitespace-only.
    """
    if not title or not isinstance(title, str) or not title.strip():
        raise ValidationError({"title": "Notification title cannot be blank or whitespace-only."})

    if not message or not isinstance(message, str) or not message.strip():
        raise ValidationError({"message": "Notification message cannot be blank or whitespace-only."})

    return title.strip(), message.strip()


def create_notification(
    recipient,
    title: str,
    message: str,
    notification_type: str = NotificationType.GENERAL,
) -> Notification:
    """
    Reusable service to create a single database-backed in-app notification.

    Args:
        recipient: User model instance or valid User pk.
        title: Summary title (required, non-blank).
        message: Notification body (required, non-blank).
        notification_type: Valid NotificationType choice string.

    Returns:
        The created Notification model instance.
    """
    clean_title, clean_message = validate_notification_content(title, message)

    # Resolve recipient if passed as pk
    if not isinstance(recipient, User):
        try:
            recipient = User.objects.get(pk=recipient)
        except (User.DoesNotExist, ValueError):
            raise ValidationError({"recipient": "A valid recipient user must be specified."})

    if notification_type not in NotificationType.values:
        notification_type = NotificationType.GENERAL

    notification = Notification(
        recipient=recipient,
        title=clean_title,
        message=clean_message,
        notification_type=notification_type,
        is_read=False,
    )
    notification.full_clean()
    notification.save()
    return notification


def create_bulk_notifications(
    recipients: Iterable,
    title: str,
    message: str,
    notification_type: str = NotificationType.GENERAL,
) -> List[Notification]:
    """
    Atomically creates notifications for multiple recipients with shared content.

    Args:
        recipients: Iterable of User model instances or user IDs.
        title: Summary title.
        message: Notification body.
        notification_type: Valid NotificationType choice string.

    Returns:
        List of created Notification model instances.
    """
    clean_title, clean_message = validate_notification_content(title, message)

    if notification_type not in NotificationType.values:
        notification_type = NotificationType.GENERAL

    notifications_to_create = []
    for recipient in recipients:
        user_obj = recipient if isinstance(recipient, User) else None
        if user_obj is None:
            try:
                user_obj = User.objects.get(pk=recipient)
            except (User.DoesNotExist, ValueError):
                continue
        notifications_to_create.append(
            Notification(
                recipient=user_obj,
                title=clean_title,
                message=clean_message,
                notification_type=notification_type,
                is_read=False,
            )
        )

    if not notifications_to_create:
        return []

    with transaction.atomic():
        return Notification.objects.bulk_create(notifications_to_create)


def mark_notification_as_read(notification: Notification, user) -> Notification:
    """
    Marks a single notification as read, ensuring ownership verification.
    """
    user_id = user.id if hasattr(user, "id") else user
    if notification.recipient_id != user_id:
        raise ValidationError("You do not have permission to mark another user's notification as read.")

    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])

    return notification


def mark_all_notifications_as_read(user) -> int:
    """
    Marks all unread notifications for the specified user as read.

    Returns:
        The integer count of notifications updated.
    """
    user_id = user.id if hasattr(user, "id") else user
    count = Notification.objects.filter(recipient_id=user_id, is_read=False).update(is_read=True)
    return count


def get_unread_notification_count(user) -> int:
    """
    Returns the total count of unread notifications for the specified user.
    """
    user_id = user.id if hasattr(user, "id") else user
    return Notification.objects.filter(recipient_id=user_id, is_read=False).count()
