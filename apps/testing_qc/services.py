from django.utils import timezone
from apps.inventory.models import BloodUnit, BloodUnitStatus
from .models import TestResult, ScreeningResult


def evaluate_and_update_blood_unit_status(test_result: TestResult, save: bool = True) -> str:
    """
    Evaluates the screening test outcome for a BloodUnit and updates its inventory status.
    
    Business Rules:
    1. If the BloodUnit is already DISCARDED, it can never be reactivated to AVAILABLE.
    2. If ANY of the 5 tests (HIV, Hep B, Hep C, Syphilis, Malaria) is POSITIVE -> Status = DISCARDED.
    3. If ALL five tests are NEGATIVE:
       - If the BloodUnit is NOT expired (expiry_date >= today) -> Status = AVAILABLE.
       - If the BloodUnit IS expired (expiry_date < today) -> Status = DISCARDED (expired stock can never become available).
    4. If one or more tests are PENDING (and none positive) -> Status = TESTING.
    
    Returns the updated BloodUnit status.
    """
    blood_unit = test_result.blood_unit

    # Rule 1: A discarded unit remains discarded
    if blood_unit.status == BloodUnitStatus.DISCARDED:
        return BloodUnitStatus.DISCARDED

    # Rule 2: Any positive result leads to discarding
    if test_result.has_positive:
        new_status = BloodUnitStatus.DISCARDED

    # Rule 3: All five tests negative
    elif test_result.all_negative:
        if blood_unit.is_expired:
            # Expired unit cannot enter usable stock
            new_status = BloodUnitStatus.DISCARDED
        else:
            new_status = BloodUnitStatus.AVAILABLE

    # Rule 4: Tests still incomplete/pending
    else:
        new_status = BloodUnitStatus.TESTING

    blood_unit.status = new_status
    if save:
        blood_unit.save(update_fields=["status", "updated_at"])

    return new_status
