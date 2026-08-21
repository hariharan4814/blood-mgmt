import logging
from typing import Any, Dict, List, Optional, Union
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import EmailRecipient

logger = logging.getLogger(__name__)
User = get_user_model()


def extract_recipient_email(recipient: Union[str, Any]) -> str:
    """
    Extracts, normalizes, and validates the email address from a User instance,
    EmailRecipient instance, or raw email string.
    """
    if not recipient:
        raise ValidationError({"recipient": "Recipient cannot be empty or null."})

    if isinstance(recipient, User):
        email_str = recipient.email
    elif isinstance(recipient, EmailRecipient):
        email_str = recipient.email
    elif isinstance(recipient, str):
        email_str = recipient
    elif hasattr(recipient, "email"):
        email_str = getattr(recipient, "email")
    else:
        raise ValidationError({"recipient": "Invalid recipient format."})

    if not email_str or not isinstance(email_str, str) or not email_str.strip():
        raise ValidationError({"recipient": "Recipient has no valid email address."})

    clean_email = email_str.strip().lower()
    try:
        validate_email(clean_email)
    except ValidationError:
        raise ValidationError({"recipient": f"Invalid email format: {clean_email}"})

    return clean_email


def validate_email_content(subject: str, message: str) -> tuple[str, str]:
    """
    Validates subject and message content. Rejects blank or whitespace-only inputs.
    """
    if not subject or not isinstance(subject, str) or not subject.strip():
        raise ValidationError({"subject": "Email subject cannot be blank or whitespace-only."})

    if not message or not isinstance(message, str) or not message.strip():
        raise ValidationError({"message": "Email message cannot be blank or whitespace-only."})

    return subject.strip(), message.strip()


def send_notification_email(
    recipient: Union[str, Any],
    subject: str,
    message: str,
    template_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    html_message: Optional[str] = None,
    from_email: Optional[str] = None,
    fail_silently: bool = True,
) -> bool:
    """
    Core reusable email delivery service for the Blood Management System.

    Features:
    - Validates email recipient, subject, and content.
    - Supports responsive HTML templates with plain-text fallback.
    - Uses configured Django SMTP / Console / In-memory backend safely.
    - Gracefully fails with logging if email server is unreachable or unconfigured.

    Returns:
        bool: True if email was successfully dispatched, False otherwise.
    """
    to_email = extract_recipient_email(recipient)
    clean_subject, clean_message = validate_email_content(subject, message)
    sender = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "Blood Management System <noreply@bloodmgmt.org>")

    template_context = context.copy() if context else {}
    template_context.setdefault("subject", clean_subject)
    template_context.setdefault("title", clean_subject)
    template_context.setdefault("message", clean_message)

    rendered_html = html_message
    if template_name:
        try:
            rendered_html = render_to_string(template_name, template_context)
        except Exception as e:
            logger.warning("Failed to render email template '%s': %s. Falling back to default layout.", template_name, e)
            try:
                rendered_html = render_to_string("notifications/emails/notification_email.html", template_context)
            except Exception:
                rendered_html = None
    elif not rendered_html:
        try:
            rendered_html = render_to_string("notifications/emails/notification_email.html", template_context)
        except Exception:
            rendered_html = None

    plain_text_body = clean_message
    if rendered_html and not clean_message:
        plain_text_body = strip_tags(rendered_html)

    email = EmailMultiAlternatives(
        subject=clean_subject,
        body=plain_text_body,
        from_email=sender,
        to=[to_email],
    )

    if rendered_html:
        email.attach_alternative(rendered_html, "text/html")

    try:
        email.send(fail_silently=False)
        return True
    except Exception as exc:
        logger.error("Failed to send notification email to %s: %s", to_email, exc)
        if not fail_silently:
            raise exc
        return False


def send_blood_request_email(
    recipient: Union[str, Any],
    subject: str,
    message: str,
    request_data: Dict[str, Any],
    action_url: Optional[str] = None,
    fail_silently: bool = True,
) -> bool:
    """
    Specialized helper to dispatch blood request notifications using professional templates.
    """
    ctx = {
        "title": subject,
        "message": message,
        "request_id": request_data.get("id") or request_data.get("request_id", "N/A"),
        "patient_name": request_data.get("patient_name", "N/A"),
        "blood_group": request_data.get("blood_group", "N/A"),
        "units_requested": request_data.get("units_requested", 1),
        "urgency": request_data.get("urgency", "NORMAL"),
        "status": request_data.get("status", ""),
        "hospital_name": request_data.get("hospital_name", ""),
        "action_url": action_url,
    }
    return send_notification_email(
        recipient=recipient,
        subject=subject,
        message=message,
        template_name="notifications/emails/blood_request_email.html",
        context=ctx,
        fail_silently=fail_silently,
    )


def send_donation_email(
    recipient: Union[str, Any],
    subject: str,
    message: str,
    donation_data: Dict[str, Any],
    action_url: Optional[str] = None,
    fail_silently: bool = True,
) -> bool:
    """
    Specialized helper to dispatch blood donation updates and confirmations.
    """
    ctx = {
        "title": subject,
        "message": message,
        "donor_name": donation_data.get("donor_name", "Valued Donor"),
        "donation_date": donation_data.get("donation_date", ""),
        "blood_group": donation_data.get("blood_group", ""),
        "blood_bank_name": donation_data.get("blood_bank_name", ""),
        "unit_id": donation_data.get("unit_id", ""),
        "next_eligible_date": donation_data.get("next_eligible_date", ""),
        "action_url": action_url,
    }
    return send_notification_email(
        recipient=recipient,
        subject=subject,
        message=message,
        template_name="notifications/emails/donation_email.html",
        context=ctx,
        fail_silently=fail_silently,
    )


def send_camp_email(
    recipient: Union[str, Any],
    subject: str,
    message: str,
    camp_data: Dict[str, Any],
    action_url: Optional[str] = None,
    fail_silently: bool = True,
) -> bool:
    """
    Specialized helper to dispatch donation camp updates and registrations.
    """
    ctx = {
        "title": subject,
        "message": message,
        "camp_name": camp_data.get("camp_name", "Donation Camp"),
        "venue": camp_data.get("venue", ""),
        "start_date": camp_data.get("start_date", ""),
        "end_date": camp_data.get("end_date", ""),
        "organizer_name": camp_data.get("organizer_name", ""),
        "blood_bank_name": camp_data.get("blood_bank_name", ""),
        "registration_status": camp_data.get("registration_status", ""),
        "action_url": action_url,
    }
    return send_notification_email(
        recipient=recipient,
        subject=subject,
        message=message,
        template_name="notifications/emails/camp_email.html",
        context=ctx,
        fail_silently=fail_silently,
    )


def send_eligibility_email(
    recipient: Union[str, Any],
    subject: str,
    message: str,
    eligibility_data: Dict[str, Any],
    action_url: Optional[str] = None,
    fail_silently: bool = True,
) -> bool:
    """
    Specialized helper to dispatch donor eligibility notifications.
    """
    ctx = {
        "title": subject,
        "message": message,
        "donor_name": eligibility_data.get("donor_name", "Valued Donor"),
        "is_eligible": eligibility_data.get("is_eligible", False),
        "next_eligible_date": eligibility_data.get("next_eligible_date", ""),
        "reasons": eligibility_data.get("reasons", []),
        "action_url": action_url,
    }
    return send_notification_email(
        recipient=recipient,
        subject=subject,
        message=message,
        template_name="notifications/emails/eligibility_email.html",
        context=ctx,
        fail_silently=fail_silently,
    )
