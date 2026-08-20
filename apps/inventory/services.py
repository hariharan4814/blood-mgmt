import uuid
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q

from apps.donors.models import BloodGroup
from .models import BloodBank, BloodUnit, BloodUnitStatus, RBC_SHELF_LIFE_DAYS


def generate_unit_id(prefix="BU"):
    """
    Generates a unique, human-readable blood unit identifier.
    Format: BU-YYYYMMDD-XXXXXX (e.g. BU-20260820-A1B2C3)
    """
    today_str = timezone.now().strftime("%Y%m%d")
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{today_str}-{short_uuid}"


def calculate_blood_unit_expiry(collection_date):
    """
    Calculates blood unit expiry date based on standard 42-day RBC shelf life.
    """
    return collection_date + timedelta(days=RBC_SHELF_LIFE_DAYS)


def get_bank_inventory_summary(blood_bank):
    """
    Computes available stock summary for a specific blood bank.
    Strictly includes only units where:
      - status == BloodUnitStatus.AVAILABLE
      - expiry_date >= today (non-expired)
    
    Excludes TESTING, RESERVED, DISPATCHED, DISCARDED, and expired units.
    """
    today = timezone.now().date()

    # Query only usable available units
    available_units = BloodUnit.objects.filter(
        blood_bank=blood_bank,
        status=BloodUnitStatus.AVAILABLE,
        expiry_date__gte=today,
    )

    # Group counts by blood group
    group_counts = (
        available_units.values("blood_group")
        .annotate(count=Count("id"))
    )
    counts_map = {item["blood_group"]: item["count"] for item in group_counts}

    # Construct complete breakdown for all 8 standard blood groups
    all_groups = [choice[0] for choice in BloodGroup.choices]
    inventory_breakdown = [
        {
            "blood_group": group,
            "available_units": counts_map.get(group, 0),
        }
        for group in all_groups
    ]

    total_available = sum(item["available_units"] for item in inventory_breakdown)

    return {
        "blood_bank": {
            "id": blood_bank.id,
            "name": blood_bank.name,
            "city": blood_bank.city,
            "state": blood_bank.state,
        },
        "inventory": inventory_breakdown,
        "total_available_units": total_available,
    }


def get_all_banks_inventory_summary(queryset=None):
    """
    Computes inventory summaries across all matching blood banks.
    """
    if queryset is None:
        queryset = BloodBank.objects.filter(is_active=True).order_by("name")

    summaries = []
    for bank in queryset:
        summaries.append(get_bank_inventory_summary(bank))
    return summaries
