import math
from decimal import Decimal
from typing import List, Optional, Union

from apps.donors.models import BloodGroup

# Mapping of all 16 canonical blood groups to their primary ABO/Rh compatibility family.
BLOOD_GROUP_FAMILY_MAP = {
    BloodGroup.O_POSITIVE: BloodGroup.O_POSITIVE,
    BloodGroup.O_NEGATIVE: BloodGroup.O_NEGATIVE,
    BloodGroup.A_POSITIVE: BloodGroup.A_POSITIVE,
    BloodGroup.A_NEGATIVE: BloodGroup.A_NEGATIVE,
    BloodGroup.B_POSITIVE: BloodGroup.B_POSITIVE,
    BloodGroup.B_NEGATIVE: BloodGroup.B_NEGATIVE,
    BloodGroup.AB_POSITIVE: BloodGroup.AB_POSITIVE,
    BloodGroup.AB_NEGATIVE: BloodGroup.AB_NEGATIVE,
    # Subgroups
    BloodGroup.A1_POSITIVE: BloodGroup.A_POSITIVE,
    BloodGroup.A2_POSITIVE: BloodGroup.A_POSITIVE,
    BloodGroup.A1_NEGATIVE: BloodGroup.A_NEGATIVE,
    BloodGroup.A2_NEGATIVE: BloodGroup.A_NEGATIVE,
    BloodGroup.A1B_POSITIVE: BloodGroup.AB_POSITIVE,
    BloodGroup.A2B_POSITIVE: BloodGroup.AB_POSITIVE,
    BloodGroup.A1B_NEGATIVE: BloodGroup.AB_NEGATIVE,
    BloodGroup.A2B_NEGATIVE: BloodGroup.AB_NEGATIVE,
}

# Members of each primary ABO/Rh family
FAMILY_MEMBERS_MAP = {
    BloodGroup.O_POSITIVE: [BloodGroup.O_POSITIVE],
    BloodGroup.O_NEGATIVE: [BloodGroup.O_NEGATIVE],
    BloodGroup.A_POSITIVE: [BloodGroup.A_POSITIVE, BloodGroup.A1_POSITIVE, BloodGroup.A2_POSITIVE],
    BloodGroup.A_NEGATIVE: [BloodGroup.A_NEGATIVE, BloodGroup.A1_NEGATIVE, BloodGroup.A2_NEGATIVE],
    BloodGroup.B_POSITIVE: [BloodGroup.B_POSITIVE],
    BloodGroup.B_NEGATIVE: [BloodGroup.B_NEGATIVE],
    BloodGroup.AB_POSITIVE: [BloodGroup.AB_POSITIVE, BloodGroup.A1B_POSITIVE, BloodGroup.A2B_POSITIVE],
    BloodGroup.AB_NEGATIVE: [BloodGroup.AB_NEGATIVE, BloodGroup.A1B_NEGATIVE, BloodGroup.A2B_NEGATIVE],
}

# Standard Red Blood Cell (RBC) transfusion compatibility mapping for base ABO/Rh families.
# Maps recipient base family -> list of medically compatible base donor blood groups.
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
        # Universal recipient (base 8 blood groups)
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


def get_base_blood_group_family(blood_group: str) -> str:
    """
    Returns the base ABO/Rh family for any blood group or subgroup.
    """
    cleaned = (blood_group or "").strip()
    return BLOOD_GROUP_FAMILY_MAP.get(cleaned, cleaned)


def get_compatible_donor_blood_groups(recipient_blood_group: str) -> List[str]:
    """
    Returns list of base donor blood group codes capable of donating red blood cells
    to a recipient with the specified blood group.
    Normalizes subgroups to their base ABO/Rh family.
    """
    base_family = get_base_blood_group_family(recipient_blood_group)
    return RBC_COMPATIBILITY_MAP.get(base_family, [recipient_blood_group])


def get_all_compatible_donor_blood_groups(recipient_blood_group: str) -> List[str]:
    """
    Returns all compatible donor blood groups, including both base groups and all
    corresponding subgroups.
    """
    base_compatible = get_compatible_donor_blood_groups(recipient_blood_group)
    all_compatible = []
    for base_grp in base_compatible:
        members = FAMILY_MEMBERS_MAP.get(base_grp, [base_grp])
        for m in members:
            if m not in all_compatible:
                all_compatible.append(m)
    return all_compatible


def is_blood_compatible(donor_blood_group: str, recipient_blood_group: str) -> bool:
    """
    Evaluates whether donor's blood group is compatible for a recipient,
    respecting ABO/Rh compatibility families for all 16 canonical blood groups.
    """
    donor_family = get_base_blood_group_family(donor_blood_group)
    base_compatible = get_compatible_donor_blood_groups(recipient_blood_group)
    return donor_family in base_compatible


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
