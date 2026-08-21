import math
from decimal import Decimal
from typing import List, Optional, Union

from apps.donors.models import BloodGroup

# Standard Red Blood Cell (RBC) transfusion compatibility mapping.
# Maps recipient blood group -> list of medically compatible donor blood groups.
RBC_COMPATIBILITY_MAP = {
    BloodGroup.A_POSITIVE: [
        BloodGroup.A_POSITIVE,
        BloodGroup.A_NEGATIVE,
        BloodGroup.O_POSITIVE,
        BloodGroup.O_NEGATIVE,
    ],
    BloodGroup.A_NEGATIVE: [
        BloodGroup.A_NEGATIVE,
        BloodGroup.O_NEGATIVE,
    ],
    BloodGroup.B_POSITIVE: [
        BloodGroup.B_POSITIVE,
        BloodGroup.B_NEGATIVE,
        BloodGroup.O_POSITIVE,
        BloodGroup.O_NEGATIVE,
    ],
    BloodGroup.B_NEGATIVE: [
        BloodGroup.B_NEGATIVE,
        BloodGroup.O_NEGATIVE,
    ],
    BloodGroup.AB_POSITIVE: [
        # Universal recipient
        BloodGroup.A_POSITIVE,
        BloodGroup.A_NEGATIVE,
        BloodGroup.B_POSITIVE,
        BloodGroup.B_NEGATIVE,
        BloodGroup.AB_POSITIVE,
        BloodGroup.AB_NEGATIVE,
        BloodGroup.O_POSITIVE,
        BloodGroup.O_NEGATIVE,
    ],
    BloodGroup.AB_NEGATIVE: [
        BloodGroup.AB_NEGATIVE,
        BloodGroup.A_NEGATIVE,
        BloodGroup.B_NEGATIVE,
        BloodGroup.O_NEGATIVE,
    ],
    BloodGroup.O_POSITIVE: [
        BloodGroup.O_POSITIVE,
        BloodGroup.O_NEGATIVE,
    ],
    BloodGroup.O_NEGATIVE: [
        # Universal donor
        BloodGroup.O_NEGATIVE,
    ],
}


def get_compatible_donor_blood_groups(recipient_blood_group: str) -> List[str]:
    """
    Returns list of donor blood group codes capable of donating red blood cells
    to a recipient with the specified blood group.
    """
    return RBC_COMPATIBILITY_MAP.get(recipient_blood_group, [recipient_blood_group])


def is_blood_compatible(donor_blood_group: str, recipient_blood_group: str) -> bool:
    """
    Evaluates whether donor's blood group is compatible for a recipient.
    """
    compatible_groups = get_compatible_donor_blood_groups(recipient_blood_group)
    return donor_blood_group in compatible_groups


def calculate_haversine_distance_km(
    lat1: Optional[Union[float, Decimal]],
    lon1: Optional[Union[float, Decimal]],
    lat2: Optional[Union[float, Decimal]],
    lon2: Optional[Union[float, Decimal]],
) -> Optional[float]:
    """
    Calculates great-circle distance between two geographical points on Earth in kilometers
    using the Haversine formula.
    Returns None if any coordinate is missing or invalid.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None

    try:
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        delta_phi = math.radians(float(lat2) - float(lat1))
        delta_lambda = math.radians(float(lon2) - float(lon1))

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        radius_earth_km = 6371.0
        return radius_earth_km * c
    except (ValueError, TypeError):
        return None
