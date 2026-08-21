from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import UserRole
from apps.donors.models import BloodGroup, Donor
from apps.inventory.models import BloodBank, BloodUnit, BloodUnitStatus
from apps.testing_qc.models import TestResult, ScreeningResult
from apps.testing_qc.services import evaluate_and_update_blood_unit_status

from .models import (
    DonationCamp,
    DonationCampRegistration,
    Donation,
    CampStatus,
    CampRegistrationStatus,
)
from .services import record_donation

User = get_user_model()


class DonationCampModelTest(TestCase):
    """
    Unit tests for DonationCamp model validation.
    """
    def setUp(self):
        self.bank_admin = User.objects.create_user(
            username="admin_alice",
            email="alice@bank.org",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.bank = BloodBank.objects.create(
            name="Metro Blood Bank",
            city="Metropolis",
            state="NY",
            contact_number="+1-555-0100",
            email="metro@test.org",
            capacity=1000,
            admin=self.bank_admin,
        )

    def test_01_camp_creation_success(self):
        """Test 1: Camp creation with valid fields."""
        camp = DonationCamp.objects.create(
            blood_bank=self.bank,
            name="Downtown Community Blood Drive",
            location="City Hall Aud",
            camp_date=timezone.now().date() + timedelta(days=7),
            organizer="Rotary Club",
            target_units=100,
            created_by=self.bank_admin,
        )
        self.assertEqual(camp.status, CampStatus.UPCOMING)
        self.assertEqual(camp.target_units, 100)
        self.assertIn("Downtown Community Blood Drive", str(camp))

    def test_05_target_units_must_be_positive(self):
        """Test 5: target_units <= 0 is rejected."""
        camp = DonationCamp(
            blood_bank=self.bank,
            name="Invalid Target Camp",
            location="Somewhere",
            camp_date=timezone.now().date() + timedelta(days=5),
            organizer="NGO",
            target_units=0,
            created_by=self.bank_admin,
        )
        with self.assertRaises(ValidationError):
            camp.clean()


class DonationCampRegistrationModelTest(TestCase):
    """
    Unit tests for DonationCampRegistration model and constraints.
    """
    def setUp(self):
        self.bank_admin = User.objects.create_user(
            username="admin_bob",
            email="bob@bank.org",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.bank = BloodBank.objects.create(
            name="Central Blood Center",
            city="Metropolis",
            state="NY",
            contact_number="+1-555-0101",
            email="central@test.org",
            capacity=1000,
            admin=self.bank_admin,
        )
        self.camp = DonationCamp.objects.create(
            blood_bank=self.bank,
            name="University Drive",
            location="Campus Quad",
            camp_date=timezone.now().date() + timedelta(days=3),
            organizer="Red Cross Student Chapter",
            target_units=50,
            created_by=self.bank_admin,
        )
        self.donor_user = User.objects.create_user(
            username="donor_john",
            email="john@donor.org",
            password="Password123!",
            role=UserRole.DONOR,
        )
        self.donor = Donor.objects.create(
            user=self.donor_user,
            blood_group=BloodGroup.O_POSITIVE,
            date_of_birth=date(1995, 5, 10),
            weight_kg=Decimal("70.00"),
        )

    def test_10_registration_success(self):
        """Test 10 & 11: Donor can register for a camp."""
        reg = DonationCampRegistration.objects.create(
            donor=self.donor,
            camp=self.camp,
            status=CampRegistrationStatus.REGISTERED,
        )
        self.assertEqual(reg.donor, self.donor)
        self.assertEqual(reg.camp, self.camp)
        self.assertEqual(reg.status, CampRegistrationStatus.REGISTERED)
        self.assertIn("donor_john", str(reg))

    def test_13_duplicate_registration_db_constraint(self):
        """Test 13 & 14: Duplicate registration is prevented at database level."""
        DonationCampRegistration.objects.create(
            donor=self.donor,
            camp=self.camp,
            status=CampRegistrationStatus.REGISTERED,
        )
        with self.assertRaises(IntegrityError):
            DonationCampRegistration.objects.create(
                donor=self.donor,
                camp=self.camp,
                status=CampRegistrationStatus.REGISTERED,
            )

    def test_registration_on_cancelled_camp_rejected(self):
        """Registration on CANCELLED camp raises validation error."""
        self.camp.status = CampStatus.CANCELLED
        self.camp.save()
        reg = DonationCampRegistration(
            donor=self.donor,
            camp=self.camp,
            status=CampRegistrationStatus.REGISTERED,
        )
        with self.assertRaises(ValidationError):
            reg.clean()


class DonationServiceAndAtomicityTest(TestCase):
    """
    Unit tests for atomic recording of donations, BloodUnit creation, and eligibility integration.
    """
    def setUp(self):
        self.bank_admin = User.objects.create_user(
            username="admin_charlie",
            email="charlie@bank.org",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.bank1 = BloodBank.objects.create(
            name="Bank One",
            city="Metropolis",
            state="NY",
            contact_number="+1-555-0201",
            email="bank1@test.org",
            capacity=1000,
            admin=self.bank_admin,
        )
        self.bank2 = BloodBank.objects.create(
            name="Bank Two",
            city="Gotham",
            state="NJ",
            contact_number="+1-555-0202",
            email="bank2@test.org",
            capacity=500,
        )
        self.camp = DonationCamp.objects.create(
            blood_bank=self.bank1,
            name="Bank One Drive",
            location="Plaza",
            camp_date=timezone.now().date(),
            organizer="City Services",
            target_units=40,
            created_by=self.bank_admin,
        )
        self.donor_user = User.objects.create_user(
            username="donor_emma",
            email="emma@donor.org",
            password="Password123!",
            role=UserRole.DONOR,
        )
        self.donor = Donor.objects.create(
            user=self.donor_user,
            blood_group=BloodGroup.A_POSITIVE,
            date_of_birth=date(1998, 3, 15),
            weight_kg=Decimal("62.00"),
            last_donation_date=None,
        )

    def test_21_valid_walk_in_donation(self):
        """Test 21 & 23: Authorized admin can record a valid walk-in donation (camp=None)."""
        today = timezone.now().date()
        donation = record_donation(
            donor=self.donor,
            blood_bank=self.bank1,
            camp=None,
            donation_date=today,
            created_by=self.bank_admin,
        )
        self.assertIsNotNone(donation)
        self.assertIsNone(donation.camp)
        self.assertEqual(donation.donor, self.donor)
        self.assertEqual(donation.blood_bank, self.bank1)
        self.assertEqual(donation.created_by, self.bank_admin)

        # BloodUnit checks
        blood_unit = donation.blood_unit
        self.assertIsNotNone(blood_unit)
        self.assertEqual(blood_unit.blood_bank, self.bank1)
        self.assertEqual(blood_unit.blood_group, "A+")
        self.assertEqual(blood_unit.collection_date, today)
        self.assertEqual(blood_unit.expiry_date, today + timedelta(days=42))
        self.assertEqual(blood_unit.status, BloodUnitStatus.TESTING)

        # Donor last donation date updated
        self.donor.refresh_from_db()
        self.assertEqual(self.donor.last_donation_date, today)

    def test_22_valid_camp_donation(self):
        """Test 22 & 24: Valid camp donation links correctly and marks registration ATTENDED."""
        # Create registration
        reg = DonationCampRegistration.objects.create(
            donor=self.donor,
            camp=self.camp,
            status=CampRegistrationStatus.REGISTERED,
        )
        today = timezone.now().date()
        donation = record_donation(
            donor=self.donor,
            blood_bank=self.bank1,
            camp=self.camp,
            donation_date=today,
            created_by=self.bank_admin,
        )
        self.assertEqual(donation.camp, self.camp)
        reg.refresh_from_db()
        self.assertEqual(reg.status, CampRegistrationStatus.ATTENDED)

    def test_25_cross_bank_camp_rejected(self):
        """Test 25: Cross-bank camp donation is rejected."""
        camp_other = DonationCamp.objects.create(
            blood_bank=self.bank2,
            name="Bank Two Drive",
            location="Gotham Mall",
            camp_date=timezone.now().date(),
            organizer="Gotham Org",
            target_units=30,
        )
        with self.assertRaises(ValidationError):
            record_donation(
                donor=self.donor,
                blood_bank=self.bank1,
                camp=camp_other,
            )

    def test_26_cancelled_camp_donation_rejected(self):
        """Test 26: CANCELLED camp donation is rejected."""
        self.camp.status = CampStatus.CANCELLED
        self.camp.save()
        with self.assertRaises(ValidationError):
            record_donation(
                donor=self.donor,
                blood_bank=self.bank1,
                camp=self.camp,
            )

    def test_35_ineligible_donor_underweight_rejected(self):
        """Test 35, 36, 37: Underweight donor (<50kg) cannot donate."""
        self.donor.weight_kg = Decimal("45.00")
        self.donor.save()

        initial_unit_count = BloodUnit.objects.count()
        initial_donation_count = Donation.objects.count()

        with self.assertRaises(ValidationError):
            record_donation(
                donor=self.donor,
                blood_bank=self.bank1,
            )

        self.assertEqual(BloodUnit.objects.count(), initial_unit_count)
        self.assertEqual(Donation.objects.count(), initial_donation_count)
        self.donor.refresh_from_db()
        self.assertIsNone(self.donor.last_donation_date)

    def test_38_39_donor_cooldown_90_days_enforced(self):
        """Test 38 & 39: Donor with donation within 90 days is ineligible."""
        today = timezone.now().date()
        self.donor.last_donation_date = today - timedelta(days=30)
        self.donor.save()

        with self.assertRaises(ValidationError) as cm:
            record_donation(
                donor=self.donor,
                blood_bank=self.bank1,
                donation_date=today,
            )
        self.assertIn("Must wait at least 90 days", str(cm.exception))


class DonationCampAPITest(APITestCase):
    """
    API tests for Donation Camp management endpoints.
    """
    def setUp(self):
        self.super_admin = User.objects.create_user(
            username="super_admin",
            email="super@admin.org",
            password="Password123!",
            role=UserRole.SUPER_ADMIN,
        )
        self.bank_admin_1 = User.objects.create_user(
            username="bank_admin_1",
            email="admin1@bank.org",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.bank_admin_2 = User.objects.create_user(
            username="bank_admin_2",
            email="admin2@bank.org",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.donor_user = User.objects.create_user(
            username="donor_dave",
            email="dave@donor.org",
            password="Password123!",
            role=UserRole.DONOR,
        )
        self.donor = Donor.objects.create(
            user=self.donor_user,
            blood_group=BloodGroup.B_POSITIVE,
            date_of_birth=date(1992, 7, 20),
            weight_kg=Decimal("75.00"),
        )
        self.hospital_staff = User.objects.create_user(
            username="staff_helen",
            email="helen@hospital.org",
            password="Password123!",
            role=UserRole.HOSPITAL_STAFF,
        )
        self.lab_tech = User.objects.create_user(
            username="tech_lucas",
            email="lucas@lab.org",
            password="Password123!",
            role=UserRole.LAB_TECHNICIAN,
        )

        self.bank1 = BloodBank.objects.create(
            name="Bank Alpha",
            city="Metropolis",
            state="NY",
            contact_number="+1-555-0301",
            email="alpha@test.org",
            capacity=1000,
            admin=self.bank_admin_1,
        )
        self.bank2 = BloodBank.objects.create(
            name="Bank Beta",
            city="Gotham",
            state="NJ",
            contact_number="+1-555-0302",
            email="beta@test.org",
            capacity=800,
            admin=self.bank_admin_2,
        )

    def test_01_bank_admin_can_create_camp(self):
        """Test 1, 2, 3: Bank admin creates camp; server controls created_by."""
        self.client.force_authenticate(user=self.bank_admin_1)
        url = "/api/donation-camps/"
        payload = {
            "blood_bank": self.bank1.id,
            "name": "Alpha Blood Drive",
            "location": "Alpha HQ",
            "camp_date": str(timezone.now().date() + timedelta(days=10)),
            "organizer": "Alpha Corp",
            "target_units": 80,
            "description": "Annual drive",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["blood_bank_id"], self.bank1.id)
        self.assertEqual(res.data["created_by_id"], self.bank_admin_1.id)
        self.assertEqual(res.data["status"], "UPCOMING")

    def test_04_client_cannot_spoof_created_by(self):
        """Test 4: Client spoofing created_by is ignored; server sets authenticated user."""
        self.client.force_authenticate(user=self.bank_admin_1)
        url = "/api/donation-camps/"
        payload = {
            "blood_bank": self.bank1.id,
            "name": "Spoof Attempt Camp",
            "location": "Venue",
            "camp_date": str(timezone.now().date() + timedelta(days=5)),
            "organizer": "Org",
            "target_units": 50,
            "created_by": self.super_admin.id,
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["created_by_id"], self.bank_admin_1.id)

    def test_07_cross_bank_camp_creation_rejected(self):
        """Test 7: Bank admin 1 cannot create camp for Bank 2."""
        self.client.force_authenticate(user=self.bank_admin_1)
        url = "/api/donation-camps/"
        payload = {
            "blood_bank": self.bank2.id,
            "name": "Unauthorized Camp",
            "location": "Venue",
            "camp_date": str(timezone.now().date() + timedelta(days=5)),
            "organizer": "Org",
            "target_units": 50,
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_08_cross_bank_camp_update_rejected(self):
        """Test 8: Bank admin 2 cannot update Bank 1's camp."""
        camp = DonationCamp.objects.create(
            blood_bank=self.bank1,
            name="Bank 1 Camp",
            location="Venue",
            camp_date=timezone.now().date() + timedelta(days=5),
            organizer="Org",
            target_units=50,
            created_by=self.bank_admin_1,
        )
        self.client.force_authenticate(user=self.bank_admin_2)
        url = f"/api/donation-camps/{camp.id}/"
        res = self.client.patch(url, {"name": "Hacked Name"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_09_47_49_unauthorized_roles_cannot_create_camp(self):
        """Test 9, 47, 49: Donors, Hospital Staff, Lab Techs cannot create camps."""
        for unauthorized_user in [self.donor_user, self.hospital_staff, self.lab_tech]:
            self.client.force_authenticate(user=unauthorized_user)
            res = self.client.post("/api/donation-camps/", {"blood_bank": self.bank1.id}, format="json")
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_50_unauthenticated_rejected(self):
        """Test 50: Unauthenticated requests are rejected."""
        self.client.logout()
        res = self.client.get("/api/donation-camps/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class DonationCampRegistrationAPITest(APITestCase):
    """
    API tests for camp registrations and data isolation.
    """
    def setUp(self):
        self.bank_admin = User.objects.create_user(
            username="admin_dan",
            email="dan@bank.org",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.bank = BloodBank.objects.create(
            name="Dan Blood Bank",
            city="Metropolis",
            state="NY",
            contact_number="+1-555-0401",
            email="dan@test.org",
            capacity=1000,
            admin=self.bank_admin,
        )
        self.camp = DonationCamp.objects.create(
            blood_bank=self.bank,
            name="Spring Blood Drive",
            location="Civic Center",
            camp_date=timezone.now().date() + timedelta(days=4),
            organizer="Community Foundation",
            target_units=60,
            created_by=self.bank_admin,
        )
        self.donor1_user = User.objects.create_user(
            username="donor_one",
            email="donor1@test.org",
            password="Password123!",
            role=UserRole.DONOR,
        )
        self.donor1 = Donor.objects.create(
            user=self.donor1_user,
            blood_group=BloodGroup.O_NEGATIVE,
            date_of_birth=date(1990, 1, 1),
            weight_kg=Decimal("72.00"),
        )
        self.donor2_user = User.objects.create_user(
            username="donor_two",
            email="donor2@test.org",
            password="Password123!",
            role=UserRole.DONOR,
        )
        self.donor2 = Donor.objects.create(
            user=self.donor2_user,
            blood_group=BloodGroup.AB_POSITIVE,
            date_of_birth=date(1994, 6, 12),
            weight_kg=Decimal("68.00"),
        )

    def test_10_11_donor_registers_for_camp(self):
        """Test 10 & 11: Authenticated donor registers for camp."""
        self.client.force_authenticate(user=self.donor1_user)
        url = f"/api/donation-camps/{self.camp.id}/register/"
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["donor_id"], self.donor1.id)
        self.assertEqual(res.data["camp_id"], self.camp.id)
        self.assertEqual(res.data["status"], "REGISTERED")

        # Confirm no Donation or BloodUnit was created
        self.assertEqual(Donation.objects.count(), 0)
        self.assertEqual(BloodUnit.objects.count(), 0)

    def test_13_duplicate_registration_api_rejected(self):
        """Test 13: Duplicate registration returns 400 error."""
        self.client.force_authenticate(user=self.donor1_user)
        url = f"/api/donation-camps/{self.camp.id}/register/"
        res1 = self.client.post(url, {}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        res2 = self.client.post(url, {}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already registered", res2.data["detail"])

    def test_15_16_donor_sees_only_own_registrations(self):
        """Test 15 & 16: Donor sees only their own registrations."""
        DonationCampRegistration.objects.create(donor=self.donor1, camp=self.camp)
        DonationCampRegistration.objects.create(donor=self.donor2, camp=self.camp)

        self.client.force_authenticate(user=self.donor1_user)
        res = self.client.get("/api/donation-camp-registrations/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Results may be paginated or list
        results = res.data["results"] if "results" in res.data else res.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["donor_id"], self.donor1.id)

    def test_17_18_bank_admin_registration_isolation(self):
        """Test 17 & 18: Bank admin sees registrations for their bank's camps only."""
        DonationCampRegistration.objects.create(donor=self.donor1, camp=self.camp)

        self.client.force_authenticate(user=self.bank_admin)
        res = self.client.get("/api/donation-camp-registrations/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data["results"] if "results" in res.data else res.data
        self.assertEqual(len(results), 1)

    def test_donor_can_cancel_registration(self):
        """Test: Donor can cancel their own camp registration."""
        reg = DonationCampRegistration.objects.create(donor=self.donor1, camp=self.camp)
        self.client.force_authenticate(user=self.donor1_user)
        url = f"/api/donation-camp-registrations/{reg.id}/cancel/"
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "CANCELLED")


class DonationAPITest(APITestCase):
    """
    API tests for recording donations and viewing donation history.
    """
    def setUp(self):
        self.bank_admin = User.objects.create_user(
            username="admin_victor",
            email="victor@bank.org",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.bank = BloodBank.objects.create(
            name="Victor Blood Center",
            city="Metropolis",
            state="NY",
            contact_number="+1-555-0501",
            email="victor@test.org",
            capacity=1000,
            admin=self.bank_admin,
        )
        self.camp = DonationCamp.objects.create(
            blood_bank=self.bank,
            name="Victor Camp",
            location="Community Center",
            camp_date=timezone.now().date(),
            organizer="Lions Club",
            target_units=50,
            created_by=self.bank_admin,
        )
        self.donor_user = User.objects.create_user(
            username="donor_george",
            email="george@donor.org",
            password="Password123!",
            role=UserRole.DONOR,
        )
        self.donor = Donor.objects.create(
            user=self.donor_user,
            blood_group=BloodGroup.B_NEGATIVE,
            date_of_birth=date(1991, 11, 23),
            weight_kg=Decimal("78.00"),
            last_donation_date=None,
        )

    def test_21_record_walk_in_donation_via_api(self):
        """Test 21, 27-34: Recording walk-in donation creates BloodUnit in TESTING status."""
        self.client.force_authenticate(user=self.bank_admin)
        url = "/api/donations/"
        payload = {
            "donor": self.donor.id,
            "blood_bank": self.bank.id,
            "camp": None,
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["donor_id"], self.donor.id)
        self.assertEqual(res.data["blood_bank_id"], self.bank.id)
        self.assertIsNone(res.data["camp_id"])

        # Check created BloodUnit
        unit_data = res.data["blood_unit"]
        self.assertEqual(unit_data["blood_group"], "B-")
        self.assertEqual(unit_data["status"], "TESTING")

        # Check donor last donation date
        self.donor.refresh_from_db()
        self.assertEqual(self.donor.last_donation_date, timezone.now().date())

    def test_22_record_camp_donation_via_api(self):
        """Test 22: Recording camp donation creates linked record."""
        self.client.force_authenticate(user=self.bank_admin)
        url = "/api/donations/"
        payload = {
            "donor": self.donor.id,
            "blood_bank": self.bank.id,
            "camp": self.camp.id,
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["camp_id"], self.camp.id)

    def test_45_46_donor_cannot_record_donation(self):
        """Test 45 & 46: Donor cannot record donations."""
        self.client.force_authenticate(user=self.donor_user)
        url = "/api/donations/"
        payload = {
            "donor": self.donor.id,
            "blood_bank": self.bank.id,
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_donor_sees_only_own_donation_history(self):
        """Test: Donor sees only their own donation history."""
        # Create donation for donor
        donation = record_donation(
            donor=self.donor,
            blood_bank=self.bank,
            created_by=self.bank_admin,
        )

        self.client.force_authenticate(user=self.donor_user)
        res = self.client.get("/api/donations/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data["results"] if "results" in res.data else res.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], donation.id)


class TestingQCIntegrationTest(TestCase):
    """
    Integration tests verifying newly collected units enter TESTING and follow Testing / QC workflow.
    """
    def setUp(self):
        self.bank_admin = User.objects.create_user(
            username="admin_frank",
            email="frank@bank.org",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.lab_tech = User.objects.create_user(
            username="tech_tina",
            email="tina@lab.org",
            password="Password123!",
            role=UserRole.LAB_TECHNICIAN,
        )
        self.bank = BloodBank.objects.create(
            name="Frank Blood Center",
            city="Metropolis",
            state="NY",
            contact_number="+1-555-0601",
            email="frank@test.org",
            capacity=1000,
            admin=self.bank_admin,
        )
        self.donor_user = User.objects.create_user(
            username="donor_grace",
            email="grace@donor.org",
            password="Password123!",
            role=UserRole.DONOR,
        )
        self.donor = Donor.objects.create(
            user=self.donor_user,
            blood_group=BloodGroup.O_POSITIVE,
            date_of_birth=date(1996, 4, 18),
            weight_kg=Decimal("65.00"),
        )

    def test_51_52_53_unit_becomes_available_after_negative_tests(self):
        """Test 51, 52, 53: BloodUnit enters TESTING, and after all NEGATIVE tests becomes AVAILABLE."""
        donation = record_donation(
            donor=self.donor,
            blood_bank=self.bank,
            created_by=self.bank_admin,
        )
        blood_unit = donation.blood_unit
        self.assertEqual(blood_unit.status, BloodUnitStatus.TESTING)

        # Lab tech screens unit: all negative
        test_result = TestResult.objects.create(
            blood_unit=blood_unit,
            hiv_result=ScreeningResult.NEGATIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.NEGATIVE,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        new_status = evaluate_and_update_blood_unit_status(test_result)
        self.assertEqual(new_status, BloodUnitStatus.AVAILABLE)
        blood_unit.refresh_from_db()
        self.assertEqual(blood_unit.status, BloodUnitStatus.AVAILABLE)

    def test_54_unit_becomes_discarded_if_positive_test(self):
        """Test 54: BloodUnit becomes DISCARDED if any test is POSITIVE."""
        donation = record_donation(
            donor=self.donor,
            blood_bank=self.bank,
            created_by=self.bank_admin,
        )
        blood_unit = donation.blood_unit
        self.assertEqual(blood_unit.status, BloodUnitStatus.TESTING)

        # Lab tech screens unit: HIV positive
        test_result = TestResult.objects.create(
            blood_unit=blood_unit,
            hiv_result=ScreeningResult.POSITIVE,
            hepatitis_b_result=ScreeningResult.NEGATIVE,
            hepatitis_c_result=ScreeningResult.NEGATIVE,
            syphilis_result=ScreeningResult.NEGATIVE,
            malaria_result=ScreeningResult.NEGATIVE,
            tested_by=self.lab_tech,
        )
        new_status = evaluate_and_update_blood_unit_status(test_result)
        self.assertEqual(new_status, BloodUnitStatus.DISCARDED)
        blood_unit.refresh_from_db()
        self.assertEqual(blood_unit.status, BloodUnitStatus.DISCARDED)


class AdditionalEligibilityAndPermissionTests(APITestCase):
    """
    Additional tests for age restrictions, hospital staff restrictions, and atomicity verification.
    """
    def setUp(self):
        self.super_admin = User.objects.create_user(
            username="super_sam",
            email="sam@super.org",
            password="Password123!",
            role=UserRole.SUPER_ADMIN,
        )
        self.bank_admin = User.objects.create_user(
            username="admin_oliver",
            email="oliver@bank.org",
            password="Password123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )
        self.hospital_staff = User.objects.create_user(
            username="nurse_nancy",
            email="nancy@hospital.org",
            password="Password123!",
            role=UserRole.HOSPITAL_STAFF,
        )
        self.bank = BloodBank.objects.create(
            name="Oliver Blood Center",
            city="Metropolis",
            state="NY",
            contact_number="+1-555-0701",
            email="oliver@test.org",
            capacity=1000,
            admin=self.bank_admin,
        )
        self.underage_user = User.objects.create_user(
            username="donor_teen",
            email="teen@donor.org",
            password="Password123!",
            role=UserRole.DONOR,
        )
        self.underage_donor = Donor.objects.create(
            user=self.underage_user,
            blood_group=BloodGroup.O_POSITIVE,
            date_of_birth=timezone.now().date() - timedelta(days=16 * 365),
            weight_kg=Decimal("60.00"),
        )
        self.overage_user = User.objects.create_user(
            username="donor_senior",
            email="senior@donor.org",
            password="Password123!",
            role=UserRole.DONOR,
        )
        self.overage_donor = Donor.objects.create(
            user=self.overage_user,
            blood_group=BloodGroup.A_NEGATIVE,
            date_of_birth=timezone.now().date() - timedelta(days=70 * 365),
            weight_kg=Decimal("70.00"),
        )

    def test_underage_donor_rejected(self):
        """Underage donor (<18) cannot donate."""
        with self.assertRaises(ValidationError):
            record_donation(
                donor=self.underage_donor,
                blood_bank=self.bank,
            )

    def test_overage_donor_rejected(self):
        """Overage donor (>65) cannot donate."""
        with self.assertRaises(ValidationError):
            record_donation(
                donor=self.overage_donor,
                blood_bank=self.bank,
            )

    def test_hospital_staff_cannot_record_donation(self):
        """Hospital staff cannot record donations via API."""
        self.client.force_authenticate(user=self.hospital_staff)
        res = self.client.post("/api/donations/", {"donor": self.underage_donor.id, "blood_bank": self.bank.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_admin_can_record_donation(self):
        """Super Admin can record valid donations."""
        valid_user = User.objects.create_user(
            username="donor_valid",
            email="valid@donor.org",
            password="Password123!",
            role=UserRole.DONOR,
        )
        valid_donor = Donor.objects.create(
            user=valid_user,
            blood_group=BloodGroup.O_POSITIVE,
            date_of_birth=date(1993, 8, 10),
            weight_kg=Decimal("68.00"),
        )
        self.client.force_authenticate(user=self.super_admin)
        payload = {
            "donor": valid_donor.id,
            "blood_bank": self.bank.id,
        }
        res = self.client.post("/api/donations/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

