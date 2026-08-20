from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.inventory.models import BloodUnit, BloodUnitStatus
from .models import BloodRequest, RequestStatus


def approve_blood_request(blood_request: BloodRequest, approved_by_user) -> BloodRequest:
    """
    Atomically approves a PENDING BloodRequest by reserving the required number of
    eligible AVAILABLE BloodUnits matching the bank and blood group.
    
    Rules:
    - Request must be in PENDING status.
    - Eligible units must have status=AVAILABLE and expiry_date >= today.
    - If available units < units_needed, raises ValidationError and leaves request PENDING.
    - No partial reservations are performed on insufficient stock.
    - On success, transitions exact units to RESERVED, links to request, and marks APPROVED.
    """
    if blood_request.status == RequestStatus.APPROVED:
        raise ValidationError("Blood request is already approved.")
    if blood_request.status == RequestStatus.REJECTED:
        raise ValidationError("Cannot approve a rejected blood request.")
    if blood_request.status != RequestStatus.PENDING:
        raise ValidationError(f"Cannot approve request with current status: '{blood_request.status}'.")

    today = timezone.now().date()

    with transaction.atomic():
        # Query eligible units strictly matching bank, blood group, AVAILABLE status, non-expired
        eligible_units = (
            BloodUnit.objects.select_for_update()
            .filter(
                blood_bank=blood_request.blood_bank,
                blood_group=blood_request.blood_group,
                status=BloodUnitStatus.AVAILABLE,
                expiry_date__gte=today,
            )
            .order_by("expiry_date", "collection_date")
        )

        available_count = eligible_units.count()
        if available_count < blood_request.units_needed:
            raise ValidationError(
                f"Insufficient stock for blood group {blood_request.blood_group}. "
                f"Required: {blood_request.units_needed} units, Available: {available_count} units."
            )

        # Select the exact quantity needed (FIFO based on expiry date)
        selected_units = list(eligible_units[: blood_request.units_needed])

        # Atomically update units to RESERVED
        for unit in selected_units:
            unit.status = BloodUnitStatus.RESERVED
            unit.save(update_fields=["status", "updated_at"])

        # Link reserved units to request
        blood_request.reserved_units.set(selected_units)
        blood_request.status = RequestStatus.APPROVED
        blood_request.approved_by = approved_by_user
        blood_request.approved_at = timezone.now()
        blood_request.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    return blood_request


def reject_blood_request(blood_request: BloodRequest, rejection_reason: str) -> BloodRequest:
    """
    Rejects a PENDING BloodRequest with a mandatory explanation reason.
    Does not modify inventory stock.
    """
    if blood_request.status == RequestStatus.REJECTED:
        raise ValidationError("Blood request is already rejected.")
    if blood_request.status == RequestStatus.APPROVED:
        raise ValidationError("Cannot reject an already approved blood request.")
    if blood_request.status != RequestStatus.PENDING:
        raise ValidationError(f"Cannot reject request with current status: '{blood_request.status}'.")

    if not rejection_reason or not rejection_reason.strip():
        raise ValidationError({"rejection_reason": "A valid rejection reason is required."})

    blood_request.status = RequestStatus.REJECTED
    blood_request.rejection_reason = rejection_reason.strip()
    blood_request.approved_by = None
    blood_request.approved_at = None
    blood_request.save(update_fields=["status", "rejection_reason", "approved_by", "approved_at", "updated_at"])

    return blood_request
