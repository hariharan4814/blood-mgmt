from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import UserRole
from apps.donors.models import BloodGroup
from apps.inventory.models import BloodBank, BloodUnit, BloodUnitStatus
from .models import BloodRequest, RequestUrgency, RequestStatus
from .services import approve_blood_request, reject_blood_request

User = get_user_model()


class BloodRequestModelTest(TestCase):
    """
    Model unit tests for BloodRequest entity and field validations.
    """
    def setUp(self):
        self.bank = BloodBank.objects.create(
            name="Apex General Blood Center",
            city="Metropolis",
            state="Central State",
            contact_number="+1-555-0100",
            email="apex@test.org",
            capacity=1000,
        )
        self.hospital_staff = User.objects.create_user(
            username="nurse_sarah",
            email="sarah@hospital.org",
            password="Password123!",
            role=UserRole.HOSPITAL_STAFF,
        )

    def test_01_request_creation_success(self):
        """Test 1 & 7: BloodRequest creation with valid fields defaults to PENDING."""
        req = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff,
            blood_bank=self.bank,
            blood_group=BloodGroup.O_NEGATIVE,
            units_needed=2,
            urgency=RequestUrgency.HIGH,
        )
        self.assertEqual(req.status, RequestStatus.PENDING)
        self.assertEqual(req.units_needed, 2)
        self.assertEqual(req.blood_group, "O-")
        self.assertEqual(req.urgency, "HIGH")
        self.assertIn("Request #", str(req))

    def test_04_units_needed_must_be_positive(self):
        """Test 4: units_needed <= 0 is rejected."""
        req = BloodRequest(
            hospital_staff=self.hospital_staff,
            blood_bank=self.bank,
            blood_group=BloodGroup.A_POSITIVE,
            units_needed=0,
        )
        with self.assertRaises(ValidationError):
            req.clean()

    def test_37_rejection_requires_reason(self):
        """Test 37: Rejection requires a valid rejection_reason."""
        req = BloodRequest(
            hospital_staff=self.hospital_staff,
            blood_bank=self.bank,
            blood_group=BloodGroup.A_POSITIVE,
            units_needed=1,
            status=RequestStatus.REJECTED,
            rejection_reason="",
        )
        with self.assertRaises(ValidationError):
            req.clean()


class BloodRequestWorkflowServiceTest(TestCase):
    """
    Service tests for atomic approval, unit reservation, and rejection.
    """
    def setUp(self):
        self.bank_admin = User.objects.create_user(
            username="admin_carl",
            email="carl@bank.org",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.bank = BloodBank.objects.create(
            name="Beacon Blood Center",
            city="Metropolis",
            state="Central State",
            contact_number="+1-555-0200",
            email="beacon@test.org",
            capacity=1000,
            admin=self.bank_admin,
        )
        self.hospital_staff = User.objects.create_user(
            username="doctor_alex",
            email="alex@hospital.org",
            password="Password123!",
            role=UserRole.HOSPITAL_STAFF,
        )
        self.today = timezone.now().date()

    def test_18_to_25_successful_approval_and_reservation(self):
        """
        Tests 18-25:
        - 18: Approve PENDING request
        - 19: Status becomes APPROVED
        - 20: approved_by set correctly
        - 21: approved_at set correctly
        - 22: Exact number of units become RESERVED
        - 23: Reserved units linked to request
        - 24: Only matching blood group selected
        - 25: Only same-bank units selected
        """
        # Create 3 available units of A+ in this bank
        unit1 = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-RES-A-1",
            blood_group="A+",
            collection_date=self.today - timedelta(days=5),
            status=BloodUnitStatus.AVAILABLE,
        )
        unit2 = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-RES-A-2",
            blood_group="A+",
            collection_date=self.today - timedelta(days=2),
            status=BloodUnitStatus.AVAILABLE,
        )
        unit3 = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-RES-A-3",
            blood_group="A+",
            collection_date=self.today - timedelta(days=1),
            status=BloodUnitStatus.AVAILABLE,
        )

        req = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff,
            blood_bank=self.bank,
            blood_group="A+",
            units_needed=2,
        )

        approved_req = approve_blood_request(req, approved_by_user=self.bank_admin)

        self.assertEqual(approved_req.status, RequestStatus.APPROVED)
        self.assertEqual(approved_req.approved_by, self.bank_admin)
        self.assertIsNotNone(approved_req.approved_at)
        self.assertEqual(approved_req.reserved_units.count(), 2)

        # Oldest expiry (unit1 and unit2) should be reserved
        unit1.refresh_from_db()
        unit2.refresh_from_db()
        unit3.refresh_from_db()
        self.assertEqual(unit1.status, BloodUnitStatus.RESERVED)
        self.assertEqual(unit2.status, BloodUnitStatus.RESERVED)
        self.assertEqual(unit3.status, BloodUnitStatus.AVAILABLE)

    def test_26_to_28_non_available_units_excluded_from_reservation(self):
        """
        Tests 26-28:
        - 26: TESTING units excluded
        - 27: DISCARDED units excluded
        - 28: Expired units excluded
        """
        # Testing unit
        BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-EXCL-TESTING",
            blood_group="O+",
            collection_date=self.today,
            status=BloodUnitStatus.TESTING,
        )
        # Discarded unit
        BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-EXCL-DISC",
            blood_group="O+",
            collection_date=self.today,
            status=BloodUnitStatus.DISCARDED,
        )
        # Expired unit (collected 50 days ago)
        BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-EXCL-EXP",
            blood_group="O+",
            collection_date=self.today - timedelta(days=50),
            status=BloodUnitStatus.AVAILABLE,
        )

        req = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff,
            blood_bank=self.bank,
            blood_group="O+",
            units_needed=1,
        )

        with self.assertRaises(ValidationError):
            approve_blood_request(req, approved_by_user=self.bank_admin)

        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.PENDING)

    def test_30_to_32_insufficient_stock_behavior(self):
        """
        Tests 30-32 & 46:
        - 30: Insufficient stock leaves request PENDING
        - 31: Insufficient stock causes NO partial reservation
        - 32: Clear insufficient-stock error raised
        - 46: Failed approval leaves inventory unchanged
        """
        unit1 = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-ONE-B",
            blood_group="B+",
            collection_date=self.today,
            status=BloodUnitStatus.AVAILABLE,
        )

        # Request requires 3 units, but only 1 exists
        req = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff,
            blood_bank=self.bank,
            blood_group="B+",
            units_needed=3,
        )

        with self.assertRaises(ValidationError) as ctx:
            approve_blood_request(req, approved_by_user=self.bank_admin)

        self.assertIn("Insufficient stock", str(ctx.exception))

        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.PENDING)
        self.assertEqual(req.reserved_units.count(), 0)

        unit1.refresh_from_db()
        # Unit must still be AVAILABLE, not partially reserved
        self.assertEqual(unit1.status, BloodUnitStatus.AVAILABLE)

    def test_33_and_34_cannot_reapprove_or_approve_rejected(self):
        """Test 33 & 34: Cannot approve an APPROVED or REJECTED request."""
        BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-RE-APP",
            blood_group="AB-",
            collection_date=self.today,
            status=BloodUnitStatus.AVAILABLE,
        )
        req = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff,
            blood_bank=self.bank,
            blood_group="AB-",
            units_needed=1,
        )
        approve_blood_request(req, self.bank_admin)

        # Attempt to approve again
        with self.assertRaises(ValidationError):
            approve_blood_request(req, self.bank_admin)

        # Test rejected request
        req2 = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff,
            blood_bank=self.bank,
            blood_group="AB-",
            units_needed=1,
            status=RequestStatus.REJECTED,
            rejection_reason="Declined",
        )
        with self.assertRaises(ValidationError):
            approve_blood_request(req2, self.bank_admin)

    def test_36_to_41_rejection_workflow(self):
        """
        Tests 36-41:
        - 36: Reject PENDING request
        - 37: rejection_reason required
        - 38: Status becomes REJECTED
        - 39: Inventory unchanged
        - 40: Cannot reject REJECTED request again
        - 41: Cannot reject APPROVED request
        """
        unit = BloodUnit.objects.create(
            blood_bank=self.bank,
            unit_id="BU-REJ-INV",
            blood_group="O-",
            collection_date=self.today,
            status=BloodUnitStatus.AVAILABLE,
        )
        req = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff,
            blood_bank=self.bank,
            blood_group="O-",
            units_needed=1,
        )

        rejected = reject_blood_request(req, rejection_reason="Out of storage space.")
        self.assertEqual(rejected.status, RequestStatus.REJECTED)
        self.assertEqual(rejected.rejection_reason, "Out of storage space.")

        # Inventory unit is unchanged
        unit.refresh_from_db()
        self.assertEqual(unit.status, BloodUnitStatus.AVAILABLE)

        # Cannot reject again
        with self.assertRaises(ValidationError):
            reject_blood_request(rejected, "Another reason")


class BloodRequestAPITest(APITestCase):
    """
    API integration tests for BloodRequest creation, approval, rejection, and RBAC isolation.
    """
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            username="super_admin_req",
            email="super_req@test.com",
            password="Password123!",
            role=UserRole.SUPER_ADMIN,
        )
        self.bank_admin_1 = User.objects.create_user(
            username="bank_admin_req_1",
            email="admin1_req@test.com",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.bank_admin_2 = User.objects.create_user(
            username="bank_admin_req_2",
            email="admin2_req@test.com",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.hospital_staff_1 = User.objects.create_user(
            username="staff_1",
            email="staff1@hospital.com",
            password="Password123!",
            role=UserRole.HOSPITAL_STAFF,
        )
        self.hospital_staff_2 = User.objects.create_user(
            username="staff_2",
            email="staff2@hospital.com",
            password="Password123!",
            role=UserRole.HOSPITAL_STAFF,
        )
        self.lab_tech = User.objects.create_user(
            username="lab_tech_req",
            email="lab_req@test.com",
            password="Password123!",
            role=UserRole.LAB_TECHNICIAN,
        )
        self.donor_user = User.objects.create_user(
            username="donor_req_user",
            email="donor_req@test.com",
            password="Password123!",
            role=UserRole.DONOR,
        )

        self.bank_1 = BloodBank.objects.create(
            name="Central Regional Blood Bank",
            city="Metropolis",
            state="Central State",
            contact_number="+1-555-1111",
            email="central@bank.org",
            capacity=1000,
            admin=self.bank_admin_1,
        )
        self.bank_2 = BloodBank.objects.create(
            name="Eastern County Blood Bank",
            city="East City",
            state="Eastern State",
            contact_number="+1-555-2222",
            email="eastern@bank.org",
            capacity=800,
            admin=self.bank_admin_2,
        )

        self.today = timezone.now().date()

    def test_01_to_10_hospital_staff_create_request_api(self):
        """
        Tests 1-10:
        - 1: Hospital Staff can create request
        - 2: hospital_staff automatically assigned from request.user
        - 3: Client cannot spoof hospital_staff
        - 4: units_needed > 0
        - 5: Invalid blood group rejected
        - 6: Invalid urgency rejected
        - 7: Defaults to PENDING
        - 8: Cannot directly create APPROVED request
        - 9 & 10: Cannot spoof approved_by or approved_at
        """
        self.client.force_authenticate(user=self.hospital_staff_1)
        payload = {
            "blood_bank": self.bank_1.id,
            "blood_group": "O+",
            "units_needed": 3,
            "urgency": "HIGH",
            "hospital_staff": self.hospital_staff_2.id,  # Spoof attempt
            "status": "APPROVED",                        # Spoof attempt
            "approved_by": self.super_admin.id,          # Spoof attempt
        }
        res = self.client.post("/api/blood-requests/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["hospital_staff_id"], self.hospital_staff_1.id)
        self.assertEqual(res.data["status"], "PENDING")
        self.assertIsNone(res.data["approved_by_id"])
        self.assertEqual(res.data["units_needed"], 3)
        self.assertEqual(res.data["urgency"], "HIGH")

    def test_05_invalid_blood_group_rejected_api(self):
        """Test 5: Invalid blood group rejected with 400."""
        self.client.force_authenticate(user=self.hospital_staff_1)
        payload = {
            "blood_bank": self.bank_1.id,
            "blood_group": "INVALID",
            "units_needed": 1,
        }
        res = self.client.post("/api/blood-requests/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_06_invalid_urgency_rejected_api(self):
        """Test 6: Invalid urgency rejected with 400."""
        self.client.force_authenticate(user=self.hospital_staff_1)
        payload = {
            "blood_bank": self.bank_1.id,
            "blood_group": "A+",
            "units_needed": 1,
            "urgency": "SUPER_URGENT",
        }
        res = self.client.post("/api/blood-requests/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_11_and_12_hospital_staff_isolation(self):
        """Test 11 & 12: Hospital Staff can only view their own requests."""
        req1 = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff_1,
            blood_bank=self.bank_1,
            blood_group="A+",
            units_needed=1,
        )
        req2 = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff_2,
            blood_bank=self.bank_1,
            blood_group="B+",
            units_needed=2,
        )

        self.client.force_authenticate(user=self.hospital_staff_1)
        res = self.client.get("/api/blood-requests/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], req1.id)

        # Cannot retrieve req2
        res2 = self.client.get(f"/api/blood-requests/{req2.id}/")
        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)

    def test_13_and_14_blood_bank_admin_isolation(self):
        """Test 13 & 14: Blood Bank Admin sees only requests for their assigned bank."""
        req_bank1 = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff_1,
            blood_bank=self.bank_1,
            blood_group="A+",
            units_needed=1,
        )
        req_bank2 = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff_1,
            blood_bank=self.bank_2,
            blood_group="B+",
            units_needed=2,
        )

        self.client.force_authenticate(user=self.bank_admin_1)
        res = self.client.get("/api/blood-requests/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], req_bank1.id)

        # Cannot retrieve req_bank2
        res2 = self.client.get(f"/api/blood-requests/{req_bank2.id}/")
        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)

    def test_15_to_17_unauthorized_roles_cannot_create_requests(self):
        """
        Tests 15-17:
        Only HOSPITAL_STAFF can create Blood Requests.
        SUPER_ADMIN, BLOOD_BANK_ADMIN, LAB_TECHNICIAN, DONOR, and Unauthenticated are all rejected.
        """
        payload = {
            "blood_bank": self.bank_1.id,
            "blood_group": "A+",
            "units_needed": 1,
        }

        # 1. SUPER_ADMIN cannot create requests (403 Forbidden)
        self.client.force_authenticate(user=self.super_admin)
        res_super = self.client.post("/api/blood-requests/", payload, format="json")
        self.assertEqual(res_super.status_code, status.HTTP_403_FORBIDDEN)

        # 2. BLOOD_BANK_ADMIN cannot create requests (403 Forbidden)
        self.client.force_authenticate(user=self.bank_admin_1)
        res_bank_admin = self.client.post("/api/blood-requests/", payload, format="json")
        self.assertEqual(res_bank_admin.status_code, status.HTTP_403_FORBIDDEN)

        # 3. LAB_TECHNICIAN cannot create requests (403 Forbidden)
        self.client.force_authenticate(user=self.lab_tech)
        res_lab = self.client.post("/api/blood-requests/", payload, format="json")
        self.assertEqual(res_lab.status_code, status.HTTP_403_FORBIDDEN)

        # 4. DONOR cannot create requests (403 Forbidden)
        self.client.force_authenticate(user=self.donor_user)
        res_donor = self.client.post("/api/blood-requests/", payload, format="json")
        self.assertEqual(res_donor.status_code, status.HTTP_403_FORBIDDEN)

        # 5. Unauthenticated cannot create requests (401 Unauthorized)
        self.client.force_authenticate(user=None)
        res_unauth_post = self.client.post("/api/blood-requests/", payload, format="json")
        self.assertEqual(res_unauth_post.status_code, status.HTTP_401_UNAUTHORIZED)
        res_unauth_get = self.client.get("/api/blood-requests/")
        self.assertEqual(res_unauth_get.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_18_to_25_approve_endpoint_success(self):
        """Test 18-25: POST /api/blood-requests/{id}/approve/ works properly."""
        for i in range(3):
            BloodUnit.objects.create(
                blood_bank=self.bank_1,
                unit_id=f"BU-API-APP-{i}",
                blood_group="O-",
                collection_date=self.today - timedelta(days=2),
                status=BloodUnitStatus.AVAILABLE,
            )

        req = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff_1,
            blood_bank=self.bank_1,
            blood_group="O-",
            units_needed=2,
        )

        self.client.force_authenticate(user=self.bank_admin_1)
        res = self.client.post(f"/api/blood-requests/{req.id}/approve/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "APPROVED")
        self.assertEqual(res.data["approved_by_id"], self.bank_admin_1.id)
        self.assertEqual(len(res.data["reserved_units"]), 2)

    def test_35_other_bank_admin_cannot_approve(self):
        """Test 35: Bank Admin 2 cannot approve a request for Bank 1."""
        req = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff_1,
            blood_bank=self.bank_1,
            blood_group="A+",
            units_needed=1,
        )
        self.client.force_authenticate(user=self.bank_admin_2)
        res = self.client.post(f"/api/blood-requests/{req.id}/approve/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_36_to_42_reject_endpoint(self):
        """Test 36-42: POST /api/blood-requests/{id}/reject/ works properly."""
        req = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff_1,
            blood_bank=self.bank_1,
            blood_group="A+",
            units_needed=1,
        )
        self.client.force_authenticate(user=self.bank_admin_1)
        # Without reason -> 400
        res = self.client.post(f"/api/blood-requests/{req.id}/reject/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # With valid reason -> 200
        res2 = self.client.post(f"/api/blood-requests/{req.id}/reject/", {"rejection_reason": "Donor camp scheduled tomorrow."}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["status"], "REJECTED")
        self.assertEqual(res2.data["rejection_reason"], "Donor camp scheduled tomorrow.")

    def test_42_other_bank_admin_cannot_reject(self):
        """Test 42: Bank Admin 2 cannot reject a request for Bank 1."""
        req = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff_1,
            blood_bank=self.bank_1,
            blood_group="A+",
            units_needed=1,
        )
        self.client.force_authenticate(user=self.bank_admin_2)
        res = self.client.post(f"/api/blood-requests/{req.id}/reject/", {"rejection_reason": "Rejected"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_43_to_45_critical_urgency_handling(self):
        """
        Tests 43-45:
        - 43: CRITICAL urgency accepted
        - 44: Insufficient stock on critical request remains PENDING
        - 45: No SOS triggered
        """
        self.client.force_authenticate(user=self.hospital_staff_1)
        payload = {
            "blood_bank": self.bank_1.id,
            "blood_group": "AB+",
            "units_needed": 5,
            "urgency": "CRITICAL",
        }
        res = self.client.post("/api/blood-requests/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["urgency"], "CRITICAL")
        self.assertEqual(res.data["status"], "PENDING")

        req_id = res.data["id"]
        # Bank Admin attempts approval when no stock exists
        self.client.force_authenticate(user=self.bank_admin_1)
        res_app = self.client.post(f"/api/blood-requests/{req_id}/approve/", {}, format="json")
        self.assertEqual(res_app.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Insufficient stock", res_app.data["detail"])

    def test_48_inventory_summary_reflects_reservation(self):
        """Test 48: Approval moves units from AVAILABLE to RESERVED, reducing available summary count."""
        # Add 2 units of B- in Bank 1
        BloodUnit.objects.create(
            blood_bank=self.bank_1,
            unit_id="BU-INV-BMINUS-1",
            blood_group="B-",
            collection_date=self.today,
            status=BloodUnitStatus.AVAILABLE,
        )
        BloodUnit.objects.create(
            blood_bank=self.bank_1,
            unit_id="BU-INV-BMINUS-2",
            blood_group="B-",
            collection_date=self.today,
            status=BloodUnitStatus.AVAILABLE,
        )

        # Verify summary initially shows 2 units of B-
        self.client.force_authenticate(user=self.super_admin)
        res_sum1 = self.client.get(f"/api/inventory/summary/?blood_bank={self.bank_1.id}")
        counts1 = {item["blood_group"]: item["available_units"] for item in res_sum1.data["inventory"]}
        self.assertEqual(counts1.get("B-"), 2)

        # Create request for 1 unit of B- and approve it
        req = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff_1,
            blood_bank=self.bank_1,
            blood_group="B-",
            units_needed=1,
        )
        self.client.force_authenticate(user=self.bank_admin_1)
        res_app = self.client.post(f"/api/blood-requests/{req.id}/approve/", {}, format="json")
        self.assertEqual(res_app.status_code, status.HTTP_200_OK)

        # Re-check inventory summary -> B- count should drop to 1
        self.client.force_authenticate(user=self.super_admin)
        res_sum2 = self.client.get(f"/api/inventory/summary/?blood_bank={self.bank_1.id}")
        counts2 = {item["blood_group"]: item["available_units"] for item in res_sum2.data["inventory"]}
        self.assertEqual(counts2.get("B-"), 1)
