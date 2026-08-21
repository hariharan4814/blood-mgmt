from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import UserRole
from apps.blood_requests.models import BloodRequest, RequestStatus, RequestUrgency
from apps.donors.models import BloodGroup, Donor
from apps.emergency_sos.compatibility import (
    calculate_haversine_distance_km,
    get_compatible_donor_blood_groups,
    is_blood_compatible,
)
from apps.emergency_sos.models import SOSBroadcast, SOSRecipient, SOSStatus
from apps.emergency_sos.services import (
    cancel_sos_broadcast,
    check_inventory_shortage,
    find_eligible_compatible_donors,
    trigger_sos_broadcast,
)
from apps.inventory.models import BloodBank, BloodUnit, BloodUnitStatus

User = get_user_model()


class EmergencySOSTestsBase(TestCase):
    """
    Base test class setting up users, blood banks, donors, and inventory.
    """

    def setUp(self):
        self.client = APIClient()
        self.today = timezone.now().date()

        # 1. Users with distinct RBAC roles
        self.super_admin = User.objects.create_user(
            username="super_admin_user",
            email="superadmin@example.com",
            password="StrongPassword123!",
            role=UserRole.SUPER_ADMIN,
        )

        self.bb_admin = User.objects.create_user(
            username="bb_admin_user",
            email="bbadmin@example.com",
            password="StrongPassword123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )

        self.hospital_staff1 = User.objects.create_user(
            username="hospital_staff_one",
            email="staff1@hospital.org",
            password="StrongPassword123!",
            role=UserRole.HOSPITAL_STAFF,
        )

        self.hospital_staff2 = User.objects.create_user(
            username="hospital_staff_two",
            email="staff2@hospital.org",
            password="StrongPassword123!",
            role=UserRole.HOSPITAL_STAFF,
        )

        self.lab_tech = User.objects.create_user(
            username="lab_tech_user",
            email="labtech@example.com",
            password="StrongPassword123!",
            role=UserRole.LAB_TECHNICIAN,
        )

        # 2. Blood Bank (Downtown Metro Blood Bank with GPS coordinates)
        self.blood_bank = BloodBank.objects.create(
            name="Downtown Metro Blood Bank",
            address="100 Healthcare Blvd",
            city="Metropolis",
            state="NY",
            contact_number="+1-555-0100",
            email="downtown@bloodbank.org",
            capacity=1000,
            latitude=Decimal("40.712800"),
            longitude=Decimal("-74.006000"),
            admin=self.bb_admin,
            is_active=True,
        )

        # 3. Donor Accounts & Profiles
        # Donor 1: O- (Universal Donor, Eligible, Near bank)
        self.donor_user_o_neg = User.objects.create_user(
            username="donor_one_oneg",
            email="oneg_donor@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            first_name="Oliver",
            last_name="Negative",
        )
        self.donor_o_neg = Donor.objects.create(
            user=self.donor_user_o_neg,
            blood_group=BloodGroup.O_NEGATIVE,
            date_of_birth=self.today - timedelta(days=30 * 365),  # 30 years old
            weight_kg=Decimal("72.0"),
            last_donation_date=self.today - timedelta(days=120),  # Cooldown passed
            latitude=Decimal("40.720000"),
            longitude=Decimal("-74.000000"),  # ~1 km away
        )

        # Donor 2: A+ (Compatible with A+, Eligible, Near bank)
        self.donor_user_a_pos = User.objects.create_user(
            username="donor_two_apos",
            email="apos_donor@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            first_name="Alice",
            last_name="Positive",
        )
        self.donor_a_pos = Donor.objects.create(
            user=self.donor_user_a_pos,
            blood_group=BloodGroup.A_POSITIVE,
            date_of_birth=self.today - timedelta(days=25 * 365),  # 25 years old
            weight_kg=Decimal("60.0"),
            last_donation_date=self.today - timedelta(days=100),  # Cooldown passed
            latitude=Decimal("40.730000"),
            longitude=Decimal("-73.990000"),  # ~2 km away
        )

        # Donor 3: B+ (Incompatible with A+ recipient, Eligible)
        self.donor_user_b_pos = User.objects.create_user(
            username="donor_three_bpos",
            email="bpos_donor@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            first_name="Bob",
            last_name="Positive",
        )
        self.donor_b_pos = Donor.objects.create(
            user=self.donor_user_b_pos,
            blood_group=BloodGroup.B_POSITIVE,
            date_of_birth=self.today - timedelta(days=28 * 365),
            weight_kg=Decimal("80.0"),
            last_donation_date=None,  # First time donor
        )

        # Donor 4: A+ (Compatible, but Medically INELIGIBLE - recently donated 20 days ago)
        self.donor_user_a_pos_ineligible = User.objects.create_user(
            username="donor_four_ineligible",
            email="ineligible@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            first_name="Ian",
            last_name="Ineligible",
        )
        self.donor_a_pos_ineligible = Donor.objects.create(
            user=self.donor_user_a_pos_ineligible,
            blood_group=BloodGroup.A_POSITIVE,
            date_of_birth=self.today - timedelta(days=35 * 365),
            weight_kg=Decimal("65.0"),
            last_donation_date=self.today - timedelta(days=20),  # In cooldown!
        )

        # 4. Standard Critical Blood Request for 4 units of A+ blood
        self.critical_request = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff1,
            blood_bank=self.blood_bank,
            blood_group=BloodGroup.A_POSITIVE,
            units_needed=4,
            urgency=RequestUrgency.CRITICAL,
            status=RequestStatus.PENDING,
        )

        # 5. Inventory: Add only 1 unit of A+ (available stock = 1, required = 4 -> shortage = 3)
        self.unit1 = BloodUnit.objects.create(
            blood_bank=self.blood_bank,
            unit_id="BU-TEST-001",
            blood_group=BloodGroup.A_POSITIVE,
            collection_date=self.today - timedelta(days=5),
            expiry_date=self.today + timedelta(days=37),
            status=BloodUnitStatus.AVAILABLE,
        )


class CompatibilityAndDistanceUnitTests(TestCase):
    """
    Unit tests for RBC blood compatibility and Haversine distance calculations.
    """

    def test_blood_compatibility_matrix(self):
        # A+ accepts A+, A-, O+, O-
        a_pos_compatible = get_compatible_donor_blood_groups(BloodGroup.A_POSITIVE)
        self.assertIn(BloodGroup.A_POSITIVE, a_pos_compatible)
        self.assertIn(BloodGroup.A_NEGATIVE, a_pos_compatible)
        self.assertIn(BloodGroup.O_POSITIVE, a_pos_compatible)
        self.assertIn(BloodGroup.O_NEGATIVE, a_pos_compatible)
        self.assertNotIn(BloodGroup.B_POSITIVE, a_pos_compatible)
        self.assertNotIn(BloodGroup.AB_POSITIVE, a_pos_compatible)

        # O- accepts ONLY O-
        o_neg_compatible = get_compatible_donor_blood_groups(BloodGroup.O_NEGATIVE)
        self.assertEqual(o_neg_compatible, [BloodGroup.O_NEGATIVE])

        # AB+ (Universal recipient) accepts all 8 blood groups
        ab_pos_compatible = get_compatible_donor_blood_groups(BloodGroup.AB_POSITIVE)
        self.assertEqual(len(ab_pos_compatible), 8)

    def test_is_blood_compatible_helper(self):
        self.assertTrue(is_blood_compatible(BloodGroup.O_NEGATIVE, BloodGroup.AB_POSITIVE))
        self.assertTrue(is_blood_compatible(BloodGroup.O_NEGATIVE, BloodGroup.A_POSITIVE))
        self.assertFalse(is_blood_compatible(BloodGroup.B_POSITIVE, BloodGroup.A_POSITIVE))
        self.assertFalse(is_blood_compatible(BloodGroup.AB_POSITIVE, BloodGroup.O_POSITIVE))

    def test_haversine_distance_calculation(self):
        # Distance between NYC (40.7128, -74.0060) and Philadelphia (39.9526, -75.1652) is ~130 km
        dist = calculate_haversine_distance_km(
            Decimal("40.7128"),
            Decimal("-74.0060"),
            Decimal("39.9526"),
            Decimal("-75.1652"),
        )
        self.assertIsNotNone(dist)
        self.assertAlmostEqual(dist, 130.0, delta=10.0)

    def test_haversine_distance_with_none_coordinates(self):
        dist = calculate_haversine_distance_km(None, Decimal("-74.0"), Decimal("40.0"), Decimal("-75.0"))
        self.assertIsNone(dist)


class SOSTriggerValidationTests(EmergencySOSTestsBase):
    """
    Test suite for SOS trigger validation, shortage calculation, and duplicate protection.
    """

    def test_valid_critical_request_with_shortage_triggers_sos_successfully(self):
        self.client.force_authenticate(user=self.hospital_staff1)
        response = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data

        self.assertEqual(data["blood_request"], self.critical_request.id)
        self.assertEqual(data["status"], "ACTIVE")
        self.assertEqual(data["blood_group"], "A+")
        self.assertEqual(data["units_needed"], 4)
        self.assertEqual(data["available_units_at_trigger"], 1)
        self.assertEqual(data["shortage_units"], 3)
        self.assertEqual(data["total_donors_targeted"], 2)  # donor_o_neg and donor_a_pos
        self.assertIn("🚨 EMERGENCY", data["title"])

        # Check database record
        broadcast = SOSBroadcast.objects.get(pk=data["id"])
        self.assertEqual(broadcast.status, SOSStatus.ACTIVE)
        self.assertEqual(broadcast.triggered_by, self.hospital_staff1)

    def test_non_critical_urgency_rejected(self):
        normal_request = BloodRequest.objects.create(
            hospital_staff=self.hospital_staff1,
            blood_bank=self.blood_bank,
            blood_group=BloodGroup.A_POSITIVE,
            units_needed=4,
            urgency=RequestUrgency.NORMAL,  # Not CRITICAL
            status=RequestStatus.PENDING,
        )
        self.client.force_authenticate(user=self.hospital_staff1)
        response = self.client.post(f"/api/blood-requests/{normal_request.id}/sos/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("CRITICAL", str(response.data))

    def test_sufficient_inventory_prevents_sos(self):
        # Create 5 available units for 4 units needed
        for i in range(5):
            BloodUnit.objects.create(
                blood_bank=self.blood_bank,
                unit_id=f"BU-AVAIL-{i}",
                blood_group=BloodGroup.A_POSITIVE,
                collection_date=self.today,
                expiry_date=self.today + timedelta(days=42),
                status=BloodUnitStatus.AVAILABLE,
            )

        self.client.force_authenticate(user=self.hospital_staff1)
        response = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sufficient stock", str(response.data).lower())

    def test_rejected_or_completed_request_cannot_trigger_sos(self):
        self.critical_request.status = RequestStatus.REJECTED
        self.critical_request.rejection_reason = "Cannot fulfill."
        self.critical_request.save()

        self.client.force_authenticate(user=self.hospital_staff1)
        response = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_blood_request_id_returns_404(self):
        self.client.force_authenticate(user=self.hospital_staff1)
        response = self.client.post("/api/blood-requests/99999/sos/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_active_sos_on_same_request_prevented(self):
        self.client.force_authenticate(user=self.hospital_staff1)
        # First trigger
        res1 = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Second trigger while first is still ACTIVE
        res2 = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ACTIVE", str(res2.data))


class SOSPermissionsTests(EmergencySOSTestsBase):
    """
    Test suite for Role-Based Access Control and ownership restrictions on SOS endpoints.
    """

    def test_hospital_staff_who_owns_request_can_trigger(self):
        self.client.force_authenticate(user=self.hospital_staff1)
        response = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_other_hospital_staff_cannot_trigger_for_unowned_request(self):
        self.client.force_authenticate(user=self.hospital_staff2)  # Different hospital staff
        response = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_admin_can_trigger_sos(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_blood_bank_admin_cannot_trigger_sos(self):
        self.client.force_authenticate(user=self.bb_admin)
        response = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_donor_and_lab_technician_cannot_trigger_sos(self):
        self.client.force_authenticate(user=self.donor_user_o_neg)
        response_donor = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(response_donor.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.lab_tech)
        response_lab = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(response_lab.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_denied_sos_trigger(self):
        response = self.client.post(f"/api/blood-requests/{self.critical_request.id}/sos/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_broadcast_list_scoping_by_role(self):
        broadcast = trigger_sos_broadcast(self.critical_request, self.hospital_staff1)

        # Hospital Staff 1 can see their broadcast
        self.client.force_authenticate(user=self.hospital_staff1)
        res_staff1 = self.client.get("/api/sos/")
        self.assertEqual(res_staff1.status_code, status.HTTP_200_OK)
        results = res_staff1.data.get("results", res_staff1.data)
        self.assertEqual(len(results), 1)

        # Hospital Staff 2 sees 0 broadcasts
        self.client.force_authenticate(user=self.hospital_staff2)
        res_staff2 = self.client.get("/api/sos/")
        self.assertEqual(res_staff2.status_code, status.HTTP_200_OK)
        results2 = res_staff2.data.get("results", res_staff2.data)
        self.assertEqual(len(results2), 0)

        # Blood Bank Admin for the target bank can see the broadcast
        self.client.force_authenticate(user=self.bb_admin)
        res_bb = self.client.get("/api/sos/")
        self.assertEqual(res_bb.status_code, status.HTTP_200_OK)
        results_bb = res_bb.data.get("results", res_bb.data)
        self.assertEqual(len(results_bb), 1)

        # Super Admin sees all broadcasts
        self.client.force_authenticate(user=self.super_admin)
        res_admin = self.client.get("/api/sos/")
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)
        results_admin = res_admin.data.get("results", res_admin.data)
        self.assertEqual(len(results_admin), 1)

        # Donor cannot view SOS broadcast list
        self.client.force_authenticate(user=self.donor_user_o_neg)
        res_donor = self.client.get("/api/sos/")
        self.assertEqual(res_donor.status_code, status.HTTP_200_OK)
        results_donor = res_donor.data.get("results", res_donor.data)
        self.assertEqual(len(results_donor), 0)


class SOSDonorMatchingTests(EmergencySOSTestsBase):
    """
    Test suite for donor compatibility, eligibility, and exclusion logic.
    """

    def test_donor_matching_logic(self):
        matched = find_eligible_compatible_donors(self.critical_request)
        matched_ids = [d.id for d in matched]

        # O- (Universal donor, eligible) must be matched
        self.assertIn(self.donor_o_neg.id, matched_ids)
        # A+ (Compatible, eligible) must be matched
        self.assertIn(self.donor_a_pos.id, matched_ids)
        # B+ (Incompatible with A+ recipient) must be excluded
        self.assertNotIn(self.donor_b_pos.id, matched_ids)
        # Ineligible A+ (cooldown active) must be excluded
        self.assertNotIn(self.donor_a_pos_ineligible.id, matched_ids)

    def test_inactive_user_donor_excluded(self):
        self.donor_user_a_pos.is_active = False
        self.donor_user_a_pos.save()

        matched = find_eligible_compatible_donors(self.critical_request)
        matched_ids = [d.id for d in matched]

        self.assertNotIn(self.donor_a_pos.id, matched_ids)
        self.assertIn(self.donor_o_neg.id, matched_ids)

    def test_zero_eligible_donors_handled_safely(self):
        # Set all donors to inactive
        User.objects.filter(role=UserRole.DONOR).update(is_active=False)

        broadcast = trigger_sos_broadcast(self.critical_request, self.hospital_staff1)
        self.assertEqual(broadcast.total_donors_targeted, 0)
        self.assertEqual(SOSRecipient.objects.filter(sos_broadcast=broadcast).count(), 0)


class SOSLocationRadiusTests(EmergencySOSTestsBase):
    """
    Test suite for geographical Haversine distance and radius filtering.
    """

    def setUp(self):
        super().setUp()
        # Add a far donor: 150 km north (latitude 42.0628)
        self.donor_user_far = User.objects.create_user(
            username="donor_far_away",
            email="far@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
        )
        self.donor_far = Donor.objects.create(
            user=self.donor_user_far,
            blood_group=BloodGroup.A_POSITIVE,
            date_of_birth=self.today - timedelta(days=22 * 365),
            weight_kg=Decimal("68.0"),
            last_donation_date=None,
            latitude=Decimal("42.062800"),  # ~150 km away
            longitude=Decimal("-74.006000"),
        )

    def test_radius_filter_excludes_distant_donors(self):
        # Request with 25 km radius
        matched_25km = find_eligible_compatible_donors(self.critical_request, radius_km=Decimal("25.0"))
        matched_ids = [d.id for d in matched_25km]

        # Near donors (1-2 km) are included
        self.assertIn(self.donor_o_neg.id, matched_ids)
        self.assertIn(self.donor_a_pos.id, matched_ids)
        # Far donor (150 km) is excluded
        self.assertNotIn(self.donor_far.id, matched_ids)

    def test_no_radius_includes_all_compatible_donors(self):
        matched_all = find_eligible_compatible_donors(self.critical_request, radius_km=None)
        matched_ids = [d.id for d in matched_all]

        self.assertIn(self.donor_o_neg.id, matched_ids)
        self.assertIn(self.donor_a_pos.id, matched_ids)
        self.assertIn(self.donor_far.id, matched_ids)


class SOSNotificationAndEmailAuditTests(EmergencySOSTestsBase):
    """
    Test suite for in-app notification creation, professional email delivery, and audit tracking.
    """

    def test_in_app_notifications_and_emails_created(self):
        broadcast = trigger_sos_broadcast(self.critical_request, self.hospital_staff1)

        # Check in-app notifications
        notifs_o_neg = self.donor_user_o_neg.notifications.filter(notification_type="SOS")
        self.assertEqual(notifs_o_neg.count(), 1)
        notif = notifs_o_neg.first()
        self.assertIn("🚨 EMERGENCY", notif.title)
        self.assertIn("Downtown Metro Blood Bank", notif.message)
        self.assertFalse(notif.is_read)

        notifs_a_pos = self.donor_user_a_pos.notifications.filter(notification_type="SOS")
        self.assertEqual(notifs_a_pos.count(), 1)

        # Ineligible and incompatible donors receive no notification
        self.assertEqual(self.donor_user_b_pos.notifications.count(), 0)
        self.assertEqual(self.donor_user_a_pos_ineligible.notifications.count(), 0)

        # Check SOSRecipient audit records
        recipients = SOSRecipient.objects.filter(sos_broadcast=broadcast)
        self.assertEqual(recipients.count(), 2)
        for recip in recipients:
            self.assertTrue(recip.email_attempted)
            self.assertTrue(recip.email_sent)
            self.assertEqual(recip.delivery_error, "")

        # Check mail outbox (Django test email backend)
        self.assertEqual(len(mail.outbox), 2)
        sent_emails = [m.to[0] for m in mail.outbox]
        self.assertIn("oneg_donor@example.com", sent_emails)
        self.assertIn("apos_donor@example.com", sent_emails)

        # Verify multipart HTML email content
        sent_html = mail.outbox[0].alternatives[0][0]
        self.assertIn("EMERGENCY BLOOD ALERT", sent_html)
        self.assertIn("Downtown Metro Blood Bank", sent_html)

    def test_email_failure_does_not_rollback_sos_broadcast(self):
        # Mock send_notification_email to simulate SMTP connection error
        with patch("apps.emergency_sos.services.send_notification_email", side_effect=Exception("SMTP Server Unreachable")):
            broadcast = trigger_sos_broadcast(self.critical_request, self.hospital_staff1)

            # SOS broadcast still created and active
            self.assertIsNotNone(broadcast.id)
            self.assertEqual(broadcast.status, SOSStatus.ACTIVE)

            # Audit logs capture delivery failure safely
            recipients = SOSRecipient.objects.filter(sos_broadcast=broadcast)
            self.assertEqual(recipients.count(), 2)
            for recip in recipients:
                self.assertTrue(recip.email_attempted)
                self.assertFalse(recip.email_sent)
                self.assertIn("SMTP Server Unreachable", recip.delivery_error)


class SOSCancellationTests(EmergencySOSTestsBase):
    """
    Test suite for cancelling active SOS broadcasts and audit endpoints.
    """

    def setUp(self):
        super().setUp()
        self.broadcast = trigger_sos_broadcast(self.critical_request, self.hospital_staff1)

    def test_cancel_active_broadcast_succeeds(self):
        self.client.force_authenticate(user=self.hospital_staff1)
        response = self.client.post(
            f"/api/sos/{self.broadcast.id}/cancel/",
            {"reason": "Patient received emergency transfer to regional facility."},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "CANCELLED")
        self.assertEqual(response.data["cancellation_reason"], "Patient received emergency transfer to regional facility.")

        self.broadcast.refresh_from_db()
        self.assertEqual(self.broadcast.status, SOSStatus.CANCELLED)
        self.assertEqual(self.broadcast.cancelled_by, self.hospital_staff1)
        self.assertIsNotNone(self.broadcast.cancelled_at)

    def test_cancel_without_reason_rejected(self):
        self.client.force_authenticate(user=self.hospital_staff1)
        response = self.client.post(
            f"/api/sos/{self.broadcast.id}/cancel/",
            {"reason": "   "},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reason", response.data)

    def test_cancel_already_cancelled_broadcast_rejected(self):
        cancel_sos_broadcast(self.broadcast, self.hospital_staff1, "Initial reason.")

        self.client.force_authenticate(user=self.hospital_staff1)
        response = self.client.post(
            f"/api/sos/{self.broadcast.id}/cancel/",
            {"reason": "Second cancel attempt."},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_user_cannot_cancel(self):
        self.client.force_authenticate(user=self.hospital_staff2)  # Different hospital staff
        response = self.client.post(
            f"/api/sos/{self.broadcast.id}/cancel/",
            {"reason": "Unauthorized attempt."},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sos_recipients_audit_endpoint(self):
        self.client.force_authenticate(user=self.hospital_staff1)
        response = self.client.get(f"/api/sos/{self.broadcast.id}/recipients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)
        donor_usernames = [r["donor_username"] for r in results]
        self.assertIn("donor_one_oneg", donor_usernames)
        self.assertIn("donor_two_apos", donor_usernames)
