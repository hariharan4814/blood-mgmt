from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any
from django.utils import timezone

MIN_DONOR_AGE = 18
MAX_DONOR_AGE = 65
MIN_DONOR_WEIGHT_KG = Decimal("50.0")
DONATION_COOLDOWN_DAYS = 90


def calculate_donor_eligibility(
    date_of_birth: Optional[date],
    weight_kg: Optional[Decimal],
    last_donation_date: Optional[date] = None,
    reference_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Dynamically evaluates donor eligibility based on medical criteria:
    1. Age must be between 18 and 65 years inclusive.
    2. Weight must be at least 50.0 kg.
    3. At least 90 days must have passed since the previous donation (or never donated before).

    Returns a structured dictionary with boolean status, granular criteria breakdown,
    and human-readable reason(s) if ineligible.
    """
    if reference_date is None:
        reference_date = timezone.now().date()

    reasons = []

    # 1. Age condition (18 - 65 inclusive)
    if not date_of_birth:
        age = None
        age_passed = False
        reasons.append("Date of birth is required to evaluate eligibility.")
    else:
        # Exact calendar age
        age = (
            reference_date.year
            - date_of_birth.year
            - ((reference_date.month, reference_date.day) < (date_of_birth.month, date_of_birth.day))
        )
        if age < MIN_DONOR_AGE:
            age_passed = False
            reasons.append(
                f"Donor must be at least {MIN_DONOR_AGE} years old (current age: {age})."
            )
        elif age > MAX_DONOR_AGE:
            age_passed = False
            reasons.append(
                f"Donor must be at most {MAX_DONOR_AGE} years old (current age: {age})."
            )
        else:
            age_passed = True

    # 2. Weight condition (>= 50 kg)
    if weight_kg is None:
        weight_passed = False
        reasons.append("Weight is required to evaluate eligibility.")
    else:
        weight_decimal = Decimal(str(weight_kg))
        if weight_decimal < MIN_DONOR_WEIGHT_KG:
            weight_passed = False
            reasons.append(
                f"Donor must weigh at least {MIN_DONOR_WEIGHT_KG} kg (current weight: {weight_decimal} kg)."
            )
        else:
            weight_passed = True

    # 3. Donation cooldown interval (>= 90 days)
    days_since_last_donation = None
    days_until_next_eligible = 0
    if last_donation_date is None:
        interval_passed = True
    else:
        days_since = (reference_date - last_donation_date).days
        days_since_last_donation = max(0, days_since)
        if days_since < DONATION_COOLDOWN_DAYS:
            interval_passed = False
            days_remaining = DONATION_COOLDOWN_DAYS - days_since
            days_until_next_eligible = days_remaining
            reasons.append(
                f"Must wait at least {DONATION_COOLDOWN_DAYS} days between donations "
                f"({days_since} days elapsed, {days_remaining} days remaining until eligible)."
            )
        else:
            interval_passed = True

    is_eligible = bool(age_passed and weight_passed and interval_passed)

    return {
        "is_eligible": is_eligible,
        "criteria": {
            "age": {
                "passed": age_passed,
                "value": age,
                "requirement": f"Between {MIN_DONOR_AGE} and {MAX_DONOR_AGE} years inclusive",
            },
            "weight": {
                "passed": weight_passed,
                "value_kg": float(weight_kg) if weight_kg is not None else None,
                "requirement": f"Minimum {MIN_DONOR_WEIGHT_KG} kg",
            },
            "donation_interval": {
                "passed": interval_passed,
                "last_donation_date": last_donation_date.isoformat() if last_donation_date else None,
                "days_since_last_donation": days_since_last_donation,
                "days_until_next_eligible": days_until_next_eligible,
                "requirement": f"Minimum {DONATION_COOLDOWN_DAYS} days since last donation",
            },
        },
        "reasons": reasons,
    }
