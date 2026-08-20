from django.utils import timezone
from rest_framework import serializers

from apps.inventory.models import BloodUnit, BloodUnitStatus
from .models import TestResult, ScreeningResult
from .services import evaluate_and_update_blood_unit_status


class TestResultSerializer(serializers.ModelSerializer):
    """
    Detailed representation serializer for BloodUnit laboratory screening results.
    """
    blood_unit_id = serializers.ReadOnlyField(source="blood_unit.id")
    unit_id = serializers.ReadOnlyField(source="blood_unit.unit_id")
    blood_group = serializers.ReadOnlyField(source="blood_unit.blood_group")
    blood_unit_status = serializers.ReadOnlyField(source="blood_unit.status")
    blood_bank_id = serializers.ReadOnlyField(source="blood_unit.blood_bank.id")
    blood_bank_name = serializers.ReadOnlyField(source="blood_unit.blood_bank.name")
    overall_outcome = serializers.ReadOnlyField()
    tested_by_id = serializers.ReadOnlyField(source="tested_by.id")
    tested_by_username = serializers.ReadOnlyField(source="tested_by.username")

    class Meta:
        model = TestResult
        fields = [
            "id",
            "blood_unit",
            "blood_unit_id",
            "unit_id",
            "blood_group",
            "blood_unit_status",
            "blood_bank_id",
            "blood_bank_name",
            "hiv_result",
            "hepatitis_b_result",
            "hepatitis_c_result",
            "syphilis_result",
            "malaria_result",
            "overall_outcome",
            "tested_by_id",
            "tested_by_username",
            "tested_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "blood_unit_id",
            "unit_id",
            "blood_group",
            "blood_unit_status",
            "blood_bank_id",
            "blood_bank_name",
            "overall_outcome",
            "tested_by_id",
            "tested_by_username",
            "tested_at",
            "created_at",
            "updated_at",
        ]


class TestResultCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new TestResult record for a BloodUnit.
    - Restricted to LAB_TECHNICIAN.
    - Enforces unit must be currently in TESTING status.
    - Sets tested_by and tested_at automatically from request.
    - Evaluates and updates the BloodUnit's status immediately upon save.
    """
    blood_unit = serializers.PrimaryKeyRelatedField(
        queryset=BloodUnit.objects.all(),
        required=True,
        help_text="Blood Unit ID undergoing laboratory screening."
    )
    hiv_result = serializers.ChoiceField(
        choices=ScreeningResult.choices,
        default=ScreeningResult.PENDING,
        help_text="HIV result (PENDING, NEGATIVE, POSITIVE)."
    )
    hepatitis_b_result = serializers.ChoiceField(
        choices=ScreeningResult.choices,
        default=ScreeningResult.PENDING,
        help_text="Hepatitis B result (PENDING, NEGATIVE, POSITIVE)."
    )
    hepatitis_c_result = serializers.ChoiceField(
        choices=ScreeningResult.choices,
        default=ScreeningResult.PENDING,
        help_text="Hepatitis C result (PENDING, NEGATIVE, POSITIVE)."
    )
    syphilis_result = serializers.ChoiceField(
        choices=ScreeningResult.choices,
        default=ScreeningResult.PENDING,
        help_text="Syphilis result (PENDING, NEGATIVE, POSITIVE)."
    )
    malaria_result = serializers.ChoiceField(
        choices=ScreeningResult.choices,
        default=ScreeningResult.PENDING,
        help_text="Malaria result (PENDING, NEGATIVE, POSITIVE)."
    )

    class Meta:
        model = TestResult
        fields = [
            "blood_unit",
            "hiv_result",
            "hepatitis_b_result",
            "hepatitis_c_result",
            "syphilis_result",
            "malaria_result",
        ]

    def validate_blood_unit(self, blood_unit):
        # Enforce One-to-One constraint
        if hasattr(blood_unit, "test_result"):
            raise serializers.ValidationError(
                "A TestResult record already exists for this blood unit. Use PATCH to update screening results."
            )

        # Enforce that testing can only be performed on units currently in TESTING status
        if blood_unit.status == BloodUnitStatus.AVAILABLE:
            raise serializers.ValidationError(
                "Testing cannot be initiated on a blood unit that is already AVAILABLE."
            )
        if blood_unit.status == BloodUnitStatus.DISCARDED:
            raise serializers.ValidationError(
                "Testing cannot be initiated on a blood unit that is already DISCARDED."
            )
        if blood_unit.status != BloodUnitStatus.TESTING:
            raise serializers.ValidationError(
                f"Testing can only be initiated on units in TESTING status. Current status: '{blood_unit.status}'."
            )

        return blood_unit

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        validated_data["tested_by"] = user
        validated_data["tested_at"] = timezone.now()

        test_result = TestResult.objects.create(**validated_data)

        # Automatically evaluate screening results and update the BloodUnit inventory status
        evaluate_and_update_blood_unit_status(test_result, save=True)

        return test_result


class TestResultUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating individual screening test results.
    - Restricted to LAB_TECHNICIAN.
    - Automatically re-evaluates the BloodUnit status upon update.
    """
    hiv_result = serializers.ChoiceField(choices=ScreeningResult.choices, required=False)
    hepatitis_b_result = serializers.ChoiceField(choices=ScreeningResult.choices, required=False)
    hepatitis_c_result = serializers.ChoiceField(choices=ScreeningResult.choices, required=False)
    syphilis_result = serializers.ChoiceField(choices=ScreeningResult.choices, required=False)
    malaria_result = serializers.ChoiceField(choices=ScreeningResult.choices, required=False)

    class Meta:
        model = TestResult
        fields = [
            "hiv_result",
            "hepatitis_b_result",
            "hepatitis_c_result",
            "syphilis_result",
            "malaria_result",
        ]

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if user:
            instance.tested_by = user
        instance.tested_at = timezone.now()
        instance.save()

        # Automatically re-evaluate screening outcome and update BloodUnit status
        evaluate_and_update_blood_unit_status(instance, save=True)

        return instance
