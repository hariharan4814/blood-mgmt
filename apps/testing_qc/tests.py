from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import UserRole
from apps.inventory.models import BloodBank, BloodUnit, BloodUnitStatus
from .models import TestResult, ScreeningResult
from .services import evaluate_and_update_blood_unit_status

User = get_user_model()


class TestResultModelTest(TestCase):
    """
    Model unit tests for TestResult entity, OneToOne constraints, and outcome properties.
    """
    def setUp(self):
        self.bank = BloodBank.objects.create(
            name="Alpha Blood Bank",
            city="Metropolis",
            state="Central State",
            contact_number="+1-555-0100",
            email="alpha@test.com",
            capacity=500,
        )
        self.lab_tech = User.objects.create_user(
            username="lab_tech_model",
            email="lab_model@test.com",
            password="Password123!",
            role=UserRole.LAB_TECHNICIAN,
        )
        self.unit = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-QC-001",
            blood_group="O+",
            collection_date=timezone.now().date(),
        )

    def test_01_test_result_creation(self):
        """Test 1: TestResult creation with valid fields."""
        tr = TestResult.objects.create(
            blood_unit=self.unit,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.NEGATIVE,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        self.assertEqual(tr.blood_unit, self.unit)
        self.assertTrue(tr.all_negative)
        self.assertFalse(tr.has_positive)
        self.assertEqual(tr.overall_outcome, "NEGATIVE")

    def test_02_and_03_one_to_one_relationship_constraint(self):
        """Test 2 & 3: One-to-one relationship with BloodUnit prevents duplicate TestResults."""
        TestResult.objects.create(
            blood_unit=self.unit,
            hiv_result=ScreeningResult.PENDING,
            tested_by=self.lab_tech,
        )
        with self.assertRaises(Exception):
            TestResult.objects.create(
                blood_unit=self.unit,
                hiv_result=ScreeningResult.NEGATIVE,
                tested_by=self.lab_tech,
            )

    def test_04_valid_controlled_test_result_values(self):
        """Test 4: Controlled choices PENDING, NEGATIVE, POSITIVE work as expected."""
        unit2 = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-QC-002",
            blood_group="A+",
            collection_date=timezone.now().date(),
        )
        tr = TestResult.objects.create(
            blood_unit=unit2,
            hiv_result=ScreeningResult.POSITIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.PENDING,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        self.assertTrue(tr.has_positive)
        self.assertEqual(tr.overall_outcome, "POSITIVE")

    def test_05_tested_by_role_validation(self):
        """Test 5: Assigned tester must have LAB_TECHNICIAN role."""
        donor_user = User.objects.create_user(
            username="donor_tester",
            email="donor_tester@test.com",
            password="Password123!",
            role=UserRole.DONOR,
        )
        tr = TestResult(
            blood_unit=self.unit,
            tested_by=donor_user,
        )
        with self.assertRaises(ValidationError):
            tr.clean()


class TestResultWorkflowTest(TestCase):
    """
    Business logic and workflow tests for automatic BloodUnit status transitions.
    """
    def setUp(self):
        self.bank = BloodBank.objects.create(
            name="Beta Blood Bank",
            city="Metropolis",
            state="Central State",
            contact_number="+1-555-0200",
            email="beta@test.com",
            capacity=500,
        )
        self.lab_tech = User.objects.create_user(
            username="lab_tech_workflow",
            email="lab_wf@test.com",
            password="Password123!",
            role=UserRole.LAB_TECHNICIAN,
        )

    def test_13_and_14_pending_results_keep_unit_testing(self):
        """Test 13 & 14: New or incomplete screening keeps unit in TESTING status."""
        today = timezone.now().date()
        unit = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-WF-PENDING",
            blood_group="B+",
            collection_date=today,
        )
        tr = TestResult.objects.create(
            blood_unit=unit,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.PENDING,  # Still pending
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        new_status = evaluate_and_update_blood_unit_status(tr)
        self.assertEqual(new_status, BloodUnitStatus.TESTING)
        unit.refresh_from_db()
        self.assertEqual(unit.status, BloodUnitStatus.TESTING)

    def test_15_all_negative_makes_valid_unit_available(self):
        """Test 15: All five NEGATIVE results make valid non-expired unit AVAILABLE."""
        today = timezone.now().date()
        unit = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-WF-AVAIL",
            blood_group="AB+",
            collection_date=today,
        )
        tr = TestResult.objects.create(
            blood_unit=unit,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.NEGATIVE,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        new_status = evaluate_and_update_blood_unit_status(tr)
        self.assertEqual(new_status, BloodUnitStatus.AVAILABLE)
        unit.refresh_from_db()
        self.assertEqual(unit.status, BloodUnitStatus.AVAILABLE)
        self.assertTrue(unit.is_available_stock)

    def test_16_hiv_positive_makes_unit_discarded(self):
        """Test 16: HIV POSITIVE makes unit DISCARDED."""
        today = timezone.now().date()
        unit = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-WF-HIV",
            blood_group="O+",
            collection_date=today,
        )
        tr = TestResult.objects.create(
            blood_unit=unit,
            hiv_result=ScreeningResult.POSITIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.NEGATIVE,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        new_status = evaluate_and_update_blood_unit_status(tr)
        self.assertEqual(new_status, BloodUnitStatus.DISCARDED)
        unit.refresh_from_db()
        self.assertEqual(unit.status, BloodUnitStatus.DISCARDED)

    def test_17_hepatitis_b_positive_makes_unit_discarded(self):
        """Test 17: Hepatitis B POSITIVE makes unit DISCARDED."""
        today = timezone.now().date()
        unit = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-WF-HEPB",
            blood_group="O+",
            collection_date=today,
        )
        tr = TestResult.objects.create(
            blood_unit=unit,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.POSITIVE,
            hepatitis_c_result=ScreeningResult.NEGATIVE,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        self.assertEqual(evaluate_and_update_blood_unit_status(tr), BloodUnitStatus.DISCARDED)

    def test_18_hepatitis_c_positive_makes_unit_discarded(self):
        """Test 18: Hepatitis C POSITIVE makes unit DISCARDED."""
        today = timezone.now().date()
        unit = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-WF-HEPC",
            blood_group="O+",
            collection_date=today,
        )
        tr = TestResult.objects.create(
            blood_unit=unit,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.POSITIVE,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        self.assertEqual(evaluate_and_update_blood_unit_status(tr), BloodUnitStatus.DISCARDED)

    def test_19_syphilis_positive_makes_unit_discarded(self):
        """Test 19: Syphilis POSITIVE makes unit DISCARDED."""
        today = timezone.now().date()
        unit = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-WF-SYPH",
            blood_group="O+",
            collection_date=today,
        )
        tr = TestResult.objects.create(
            blood_unit=unit,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.NEGATIVE,
            syphilis_result=ScreeningResult.POSITIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        self.assertEqual(evaluate_and_update_blood_unit_status(tr), BloodUnitStatus.DISCARDED)

    def test_20_malaria_positive_makes_unit_discarded(self):
        """Test 20: Malaria POSITIVE makes unit DISCARDED."""
        today = timezone.now().date()
        unit = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-WF-MAL",
            blood_group="O+",
            collection_date=today,
        )
        tr = TestResult.objects.create(
            blood_unit=unit,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.NEGATIVE,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.POSITIVE,
            tested_by=self.lab_tech,
        )
        self.assertEqual(evaluate_and_update_blood_unit_status(tr), BloodUnitStatus.DISCARDED)

    def test_21_single_positive_overrides_negative_results(self):
        """Test 21: Any single POSITIVE overrides all other NEGATIVE results."""
        today = timezone.now().date()
        unit = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-WF-COMBO",
            blood_group="A-",
            collection_date=today,
        )
        tr = TestResult.objects.create(
            blood_unit=unit,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.NEGATIVE,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.POSITIVE,
            tested_by=self.lab_tech,
        )
        self.assertEqual(evaluate_and_update_blood_unit_status(tr), BloodUnitStatus.DISCARDED)

    def test_26_expired_unit_all_negative_never_becomes_available(self):
        """Test 26: Expired unit with all NEGATIVE results never becomes AVAILABLE."""
        # Collected 50 days ago -> expired 8 days ago
        expired_date = timezone.now().date() - timedelta(days=50)
        unit = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-EXP-QC",
            blood_group="O-",
            collection_date=expired_date,
        )
        self.assertTrue(unit.is_expired)

        tr = TestResult.objects.create(
            blood_unit=unit,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.NEGATIVE,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        new_status = evaluate_and_update_blood_unit_status(tr)
        self.assertEqual(new_status, BloodUnitStatus.DISCARDED)
        unit.refresh_from_db()
        self.assertNotEqual(unit.status, BloodUnitStatus.AVAILABLE)
        self.assertEqual(unit.status, BloodUnitStatus.DISCARDED)


class TestResultAPITest(APITestCase):
    """
    API integration tests for TestResult endpoints, role restrictions, and inventory summary effects.
    """
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            username="super_qc_user",
            email="super_qc@test.com",
            password="Password123!",
            role=UserRole.SUPER_ADMIN,
        )
        self.bank_admin = User.objects.create_user(
            username="bank_admin_qc",
            email="bank_qc@test.com",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.lab_tech = User.objects.create_user(
            username="lab_tech_qc",
            email="lab_qc@test.com",
            password="Password123!",
            role=UserRole.LAB_TECHNICIAN,
        )
        self.hospital_staff = User.objects.create_user(
            username="hospital_qc",
            email="hosp_qc@test.com",
            password="Password123!",
            role=UserRole.HOSPITAL_STAFF,
        )
        self.donor_user = User.objects.create_user(
            username="donor_qc",
            email="donor_qc@test.com",
            password="Password123!",
            role=UserRole.DONOR,
        )

        self.bank = BloodBank.objects.create(
            name="Gamma Blood Bank",
            city="Gamma City",
            state="Gamma State",
            contact_number="+1-555-0300",
            email="gamma@test.com",
            capacity=500,
            admin=self.bank_admin,
        )

        today = timezone.now().date()
        self.unit_testing = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-API-TESTING-1",
            blood_group="A+",
            collection_date=today,
            status=BloodUnitStatus.TESTING,
        )
        self.unit_available = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-API-AVAIL-1",
            blood_group="O+",
            collection_date=today,
            status=BloodUnitStatus.AVAILABLE,
        )
        self.unit_discarded = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-API-DISC-1",
            blood_group="B+",
            collection_date=today,
            status=BloodUnitStatus.DISCARDED,
        )

    def test_06_lab_tech_can_create_test_result(self):
        """Test 6: LAB_TECHNICIAN can create a TestResult."""
        self.client.force_authenticate(user=self.lab_tech)
        payload = {
            "blood_unit": self.unit_testing.id,
            "hiv_result": "NEGATIVE",
            "hepatitis_b_result": "NEGATIVE",
            "hepatitis_c_result": "NEGATIVE",
            "syphilis_result": "NEGATIVE",
            "malaria_result": "NEGATIVE",
        }
        res = self.client.post("/api/test-results/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["overall_outcome"], "NEGATIVE")
        self.assertEqual(res.data["tested_by_username"], self.lab_tech.username)

        # Unit should automatically transition to AVAILABLE
        self.unit_testing.refresh_from_db()
        self.assertEqual(self.unit_testing.status, BloodUnitStatus.AVAILABLE)

    def test_07_lab_tech_can_update_test_result(self):
        """Test 7 & 22: LAB_TECHNICIAN can update a TestResult and transition unit to AVAILABLE."""
        # Create initial pending test
        tr = TestResult.objects.create(
            blood_unit=self.unit_testing,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.PENDING,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        self.unit_testing.refresh_from_db()
        self.assertEqual(self.unit_testing.status, BloodUnitStatus.TESTING)

        # Lab tech updates Hep C to NEGATIVE
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.patch(f"/api/test-results/{tr.id}/", {"hepatitis_c_result": "NEGATIVE"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["hepatitis_c_result"], "NEGATIVE")
        self.assertEqual(res.data["overall_outcome"], "NEGATIVE")

        # Unit should now be AVAILABLE
        self.unit_testing.refresh_from_db()
        self.assertEqual(self.unit_testing.status, BloodUnitStatus.AVAILABLE)

    def test_23_updating_result_to_positive_changes_unit_to_discarded(self):
        """Test 23: Updating any result to POSITIVE changes unit to DISCARDED."""
        tr = TestResult.objects.create(
            blood_unit=self.unit_testing,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.PENDING,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.patch(f"/api/test-results/{tr.id}/", {"hepatitis_c_result": "POSITIVE"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["overall_outcome"], "POSITIVE")

        self.unit_testing.refresh_from_db()
        self.assertEqual(self.unit_testing.status, BloodUnitStatus.DISCARDED)

    def test_08_blood_bank_admin_cannot_write_test_results(self):
        """Test 8: BLOOD_BANK_ADMIN cannot perform routine testing write operations."""
        self.client.force_authenticate(user=self.bank_admin)
        payload = {
            "blood_unit": self.unit_testing.id,
            "hiv_result": "NEGATIVE",
        }
        res = self.client.post("/api/test-results/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_09_super_admin_cannot_write_routine_test_results(self):
        """Test 9: SUPER_ADMIN cannot perform routine testing write operations."""
        self.client.force_authenticate(user=self.super_admin)
        payload = {
            "blood_unit": self.unit_testing.id,
            "hiv_result": "NEGATIVE",
        }
        res = self.client.post("/api/test-results/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_10_hospital_staff_rejected(self):
        """Test 10: HOSPITAL_STAFF is rejected from test results."""
        self.client.force_authenticate(user=self.hospital_staff)
        res = self.client.get("/api/test-results/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        res2 = self.client.post("/api/test-results/", {}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)

    def test_11_donor_rejected(self):
        """Test 11: DONOR is rejected from test results."""
        self.client.force_authenticate(user=self.donor_user)
        res = self.client.get("/api/test-results/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        res2 = self.client.post("/api/test-results/", {}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)

    def test_12_unauthenticated_request_rejected(self):
        """Test 12: Unauthenticated requests are rejected with 401."""
        res = self.client.get("/api/test-results/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        res2 = self.client.post("/api/test-results/", {}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_24_discarded_unit_cannot_be_reactivated_through_testing(self):
        """Test 24: DISCARDED unit cannot be reactivated through testing."""
        tr = TestResult.objects.create(
            blood_unit=self.unit_discarded,
            hiv_result=ScreeningResult.POSITIVE,
            tested_by=self.lab_tech,
        )
        self.client.force_authenticate(user=self.lab_tech)
        # Attempt to change HIV result to NEGATIVE on discarded unit
        res = self.client.patch(f"/api/test-results/{tr.id}/", {
            "hiv_result": "NEGATIVE",
            "hepatitis_b_result": "NEGATIVE",
            "hepatitis_c_result": "NEGATIVE",
            "syphilis_result": "NEGATIVE",
            "malaria_result": "NEGATIVE",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.unit_discarded.refresh_from_db()
        # Must remain DISCARDED
        self.assertEqual(self.unit_discarded.status, BloodUnitStatus.DISCARDED)

    def test_25_available_unit_cannot_receive_new_test_result(self):
        """Test 25: AVAILABLE unit cannot receive a new TestResult."""
        self.client.force_authenticate(user=self.lab_tech)
        payload = {
            "blood_unit": self.unit_available.id,
            "hiv_result": "NEGATIVE",
        }
        res = self.client.post("/api/test-results/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blood_unit", res.data)

    def test_27_to_30_inventory_summary_integration(self):
        """
        Tests 27-30:
        - 28: TESTING unit excluded from inventory summary
        - 29: AVAILABLE non-expired tested unit included in inventory summary
        - 30: DISCARDED unit excluded from inventory summary
        - 27: Expired unit remains excluded from inventory summary
        """
        self.client.force_authenticate(user=self.super_admin)
        res = self.client.get(f"/api/inventory/summary/?blood_bank={self.bank.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        inventory_list = res.data["inventory"]
        counts = {item["blood_group"]: item["available_units"] for item in inventory_list}

        # self.unit_available (O+) is AVAILABLE -> count 1
        self.assertEqual(counts.get("O+"), 1)
        # self.unit_testing (A+) is TESTING -> count 0
        self.assertEqual(counts.get("A+"), 0)
        # self.unit_discarded (B+) is DISCARDED -> count 0
        self.assertEqual(counts.get("B+"), 0)
        self.assertEqual(res.data["total_available_units"], 1)

        # Now lab tech tests self.unit_testing (A+) -> makes it AVAILABLE
        self.client.force_authenticate(user=self.lab_tech)
        test_payload = {
            "blood_unit": self.unit_testing.id,
            "hiv_result": "NEGATIVE",
            "hepatitis_b_result": "NEGATIVE",
            "hepatitis_c_result": "NEGATIVE",
            "syphilis_result": "NEGATIVE",
            "malaria_result": "NEGATIVE",
        }
        self.client.post("/api/test-results/", test_payload, format="json")

        # Now re-check summary as Super Admin
        self.client.force_authenticate(user=self.super_admin)
        res2 = self.client.get(f"/api/inventory/summary/?blood_bank={self.bank.id}")
        counts2 = {item["blood_group"]: item["available_units"] for item in res2.data["inventory"]}

        # A+ is now AVAILABLE -> count 1
        self.assertEqual(counts2.get("A+"), 1)
        # O+ is still 1
        self.assertEqual(counts2.get("O+"), 1)
        # Total = 2
        self.assertEqual(res2.data["total_available_units"], 2)

    def test_convenience_endpoint_get_blood_unit_test_result(self):
        """Test convenience endpoint GET /api/blood-units/{id}/test-result/."""
        tr = TestResult.objects.create(
            blood_unit=self.unit_testing,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.NEGATIVE,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        self.client.force_authenticate(user=self.lab_tech)
        res = self.client.get(f"/api/blood-units/{self.unit_testing.id}/test-result/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], tr.id)
        self.assertEqual(res.data["overall_outcome"], "NEGATIVE")
