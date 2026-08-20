from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import UserRole
from apps.donors.models import Donor, BloodGroup
from apps.donors.services import calculate_donor_eligibility

User = get_user_model()


class DonorModelAndEligibilityUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="donor_unit_test",
            email="donor_unit@test.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone="+1234567890",
            is_verified=True,
        )
        self.today = timezone.now().date()

    def get_dob_for_age(self, age):
        try:
            return date(self.today.year - age, self.today.month, self.today.day)
        except ValueError:
            # Leap year Feb 29 fallback
            return date(self.today.year - age, self.today.month, self.today.day - 1)

    def test_donor_profile_creation_success(self):
        dob = self.get_dob_for_age(25)
        donor = Donor.objects.create(
            user=self.user,
            blood_group=BloodGroup.O_POSITIVE,
            date_of_birth=dob,
            weight_kg=Decimal("68.50"),
            latitude=Decimal("12.971598"),
            longitude=Decimal("77.594566"),
            last_donation_date=self.today - timedelta(days=120),
        )
        self.assertEqual(donor.user, self.user)
        self.assertEqual(donor.blood_group, "O+")
        self.assertEqual(donor.age, 25)
        self.assertTrue(donor.is_eligible)
        self.assertIn("donor_unit_test (O+)", str(donor))

    def test_one_to_one_relationship_enforced(self):
        dob = self.get_dob_for_age(25)
        Donor.objects.create(
            user=self.user,
            blood_group=BloodGroup.A_POSITIVE,
            date_of_birth=dob,
            weight_kg=Decimal("60.00"),
        )
        with self.assertRaises(Exception):
            Donor.objects.create(
                user=self.user,
                blood_group=BloodGroup.B_POSITIVE,
                date_of_birth=dob,
                weight_kg=Decimal("65.00"),
            )

    def test_all_valid_blood_groups(self):
        valid_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for idx, bg in enumerate(valid_groups):
            u = User.objects.create_user(
                username=f"donor_bg_{idx}",
                email=f"donor_bg_{idx}@test.com",
                password="SecurePassword123!",
                role=UserRole.DONOR,
            )
            donor = Donor.objects.create(
                user=u,
                blood_group=bg,
                date_of_birth=self.get_dob_for_age(20),
                weight_kg=Decimal("55.00"),
            )
            self.assertEqual(donor.blood_group, bg)

    def test_future_date_of_birth_rejection(self):
        donor = Donor(
            user=self.user,
            blood_group=BloodGroup.O_POSITIVE,
            date_of_birth=self.today + timedelta(days=10),
            weight_kg=Decimal("60.00"),
        )
        with self.assertRaises(ValidationError):
            donor.clean()

    def test_future_last_donation_date_rejection(self):
        donor = Donor(
            user=self.user,
            blood_group=BloodGroup.O_POSITIVE,
            date_of_birth=self.get_dob_for_age(25),
            weight_kg=Decimal("60.00"),
            last_donation_date=self.today + timedelta(days=5),
        )
        with self.assertRaises(ValidationError):
            donor.clean()

    def test_invalid_weight_rejection(self):
        donor = Donor(
            user=self.user,
            blood_group=BloodGroup.O_POSITIVE,
            date_of_birth=self.get_dob_for_age(25),
            weight_kg=Decimal("0.00"),
        )
        with self.assertRaises(ValidationError):
            donor.clean()

    def test_eligibility_logic_eligible_donor(self):
        dob = self.get_dob_for_age(30)
        res = calculate_donor_eligibility(
            date_of_birth=dob,
            weight_kg=Decimal("70.00"),
            last_donation_date=self.today - timedelta(days=100),
            reference_date=self.today,
        )
        self.assertTrue(res["is_eligible"])
        self.assertEqual(len(res["reasons"]), 0)
        self.assertTrue(res["criteria"]["age"]["passed"])
        self.assertTrue(res["criteria"]["weight"]["passed"])
        self.assertTrue(res["criteria"]["donation_interval"]["passed"])

    def test_eligibility_logic_underage_donor(self):
        dob = self.get_dob_for_age(17)
        res = calculate_donor_eligibility(
            date_of_birth=dob,
            weight_kg=Decimal("60.00"),
            reference_date=self.today,
        )
        self.assertFalse(res["is_eligible"])
        self.assertFalse(res["criteria"]["age"]["passed"])
        self.assertIn("at least 18 years old", res["reasons"][0])

    def test_eligibility_logic_over_age_donor(self):
        dob = self.get_dob_for_age(66)
        res = calculate_donor_eligibility(
            date_of_birth=dob,
            weight_kg=Decimal("65.00"),
            reference_date=self.today,
        )
        self.assertFalse(res["is_eligible"])
        self.assertFalse(res["criteria"]["age"]["passed"])
        self.assertIn("at most 65 years old", res["reasons"][0])

    def test_eligibility_logic_underweight_donor(self):
        dob = self.get_dob_for_age(22)
        res = calculate_donor_eligibility(
            date_of_birth=dob,
            weight_kg=Decimal("48.50"),
            reference_date=self.today,
        )
        self.assertFalse(res["is_eligible"])
        self.assertFalse(res["criteria"]["weight"]["passed"])
        self.assertIn("at least 50.0 kg", res["reasons"][0])

    def test_eligibility_logic_within_90_day_cooldown(self):
        dob = self.get_dob_for_age(25)
        res = calculate_donor_eligibility(
            date_of_birth=dob,
            weight_kg=Decimal("65.00"),
            last_donation_date=self.today - timedelta(days=45),
            reference_date=self.today,
        )
        self.assertFalse(res["is_eligible"])
        self.assertFalse(res["criteria"]["donation_interval"]["passed"])
        self.assertEqual(res["criteria"]["donation_interval"]["days_since_last_donation"], 45)
        self.assertEqual(res["criteria"]["donation_interval"]["days_until_next_eligible"], 45)
        self.assertIn("wait at least 90 days", res["reasons"][0])

    def test_eligibility_logic_first_time_donor_null_donation_date(self):
        dob = self.get_dob_for_age(22)
        res = calculate_donor_eligibility(
            date_of_birth=dob,
            weight_kg=Decimal("55.00"),
            last_donation_date=None,
            reference_date=self.today,
        )
        self.assertTrue(res["is_eligible"])
        self.assertTrue(res["criteria"]["donation_interval"]["passed"])
        self.assertIsNone(res["criteria"]["donation_interval"]["days_since_last_donation"])


class DonorAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = timezone.now().date()

        # Donor 1
        self.donor_user = User.objects.create_user(
            username="donor_api_1",
            email="donor1@example.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone="+1112223333",
            is_verified=True,
        )

        # Donor 2
        self.donor_user_2 = User.objects.create_user(
            username="donor_api_2",
            email="donor2@example.com",
            password="SecurePassword123!",
            role=UserRole.DONOR,
            phone="+1112224444",
            is_verified=True,
        )

        # Hospital Staff
        self.staff_user = User.objects.create_user(
            username="hospital_staff_user",
            email="staff@example.com",
            password="SecurePassword123!",
            role=UserRole.HOSPITAL_STAFF,
            phone="+1112225555",
            is_verified=True,
        )

        # Super Admin
        self.admin_user = User.objects.create_superuser(
            username="super_admin_user",
            email="admin@example.com",
            password="AdminPassword123!",
            role=UserRole.SUPER_ADMIN,
            is_verified=True,
        )

        self.me_url = reverse("donors:donor_me")
        self.eligibility_url = reverse("donors:donor_me_eligibility")
        self.admin_list_url = reverse("donors:donor_list")

    def get_dob_for_age(self, age):
        try:
            return date(self.today.year - age, self.today.month, self.today.day)
        except ValueError:
            return date(self.today.year - age, self.today.month, self.today.day - 1)

    def test_unauthenticated_requests_rejected(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(self.eligibility_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(self.admin_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_donor_role_cannot_access_donor_me_endpoints(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(self.eligibility_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_donor_get_profile_before_creation_returns_404(self):
        self.client.force_authenticate(user=self.donor_user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Donor profile not found", response.json()["detail"])

    def test_donor_create_profile_via_post_and_put(self):
        self.client.force_authenticate(user=self.donor_user)
        dob = self.get_dob_for_age(24).isoformat()
        payload = {
            "blood_group": "O+",
            "date_of_birth": dob,
            "weight_kg": "65.50",
            "latitude": "12.971598",
            "longitude": "77.594566",
            "last_donation_date": None,
        }
        # Create via PUT
        response = self.client.put(self.me_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["username"], "donor_api_1")
        self.assertEqual(data["blood_group"], "O+")
        self.assertEqual(data["weight_kg"], "65.50")
        self.assertEqual(data["age"], 24)
        self.assertTrue(data["is_eligible"])

    def test_donor_update_profile_patch(self):
        # Create profile first
        dob = self.get_dob_for_age(28)
        donor = Donor.objects.create(
            user=self.donor_user,
            blood_group=BloodGroup.A_POSITIVE,
            date_of_birth=dob,
            weight_kg=Decimal("72.00"),
        )
        self.client.force_authenticate(user=self.donor_user)

        patch_payload = {
            "weight_kg": "75.00",
            "blood_group": "A-",
            "latitude": "13.082680",
            "longitude": "80.270721",
        }
        response = self.client.patch(self.me_url, patch_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["weight_kg"], "75.00")
        self.assertEqual(data["blood_group"], "A-")
        self.assertEqual(data["latitude"], "13.082680")

        donor.refresh_from_db()
        self.assertEqual(donor.blood_group, "A-")
        self.assertEqual(donor.weight_kg, Decimal("75.00"))

    def test_donor_get_eligibility_endpoint(self):
        dob = self.get_dob_for_age(22)
        Donor.objects.create(
            user=self.donor_user,
            blood_group=BloodGroup.B_POSITIVE,
            date_of_birth=dob,
            weight_kg=Decimal("58.00"),
            last_donation_date=self.today - timedelta(days=120),
        )
        self.client.force_authenticate(user=self.donor_user)
        response = self.client.get(self.eligibility_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["is_eligible"])
        self.assertEqual(data["criteria"]["age"]["value"], 22)
        self.assertEqual(data["criteria"]["weight"]["value_kg"], 58.0)
        self.assertEqual(data["criteria"]["donation_interval"]["days_since_last_donation"], 120)

    def test_donor_cannot_access_other_donor_profile(self):
        dob = self.get_dob_for_age(30)
        donor2 = Donor.objects.create(
            user=self.donor_user_2,
            blood_group=BloodGroup.AB_POSITIVE,
            date_of_birth=dob,
            weight_kg=Decimal("80.00"),
        )
        # Donor 1 logs in and hits /me/
        self.client.force_authenticate(user=self.donor_user)
        response = self.client.get(self.me_url)
        # Donor 1 has no profile yet -> 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Donor 1 cannot access admin donor detail endpoint
        admin_detail_url = reverse("donors:donor_detail", kwargs={"pk": donor2.id})
        response = self.client.get(admin_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_serializer_validation_invalid_latitude_longitude(self):
        self.client.force_authenticate(user=self.donor_user)
        payload = {
            "blood_group": "O+",
            "date_of_birth": self.get_dob_for_age(20).isoformat(),
            "weight_kg": "60.00",
            "latitude": "95.000000",  # > 90
            "longitude": "200.000000",  # > 180
        }
        response = self.client.put(self.me_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("latitude", response.json())
        self.assertIn("longitude", response.json())

    def test_serializer_validation_invalid_blood_group(self):
        self.client.force_authenticate(user=self.donor_user)
        payload = {
            "blood_group": "INVALID_BG",
            "date_of_birth": self.get_dob_for_age(20).isoformat(),
            "weight_kg": "60.00",
        }
        response = self.client.put(self.me_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blood_group", response.json())

    def test_super_admin_can_list_and_view_donors(self):
        dob = self.get_dob_for_age(25)
        d1 = Donor.objects.create(
            user=self.donor_user,
            blood_group=BloodGroup.A_POSITIVE,
            date_of_birth=dob,
            weight_kg=Decimal("60.00"),
        )
        d2 = Donor.objects.create(
            user=self.donor_user_2,
            blood_group=BloodGroup.O_NEGATIVE,
            date_of_birth=dob,
            weight_kg=Decimal("70.00"),
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.admin_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 2)

        # Test filtering by blood_group
        response = self.client.get(f"{self.admin_list_url}?blood_group=O-")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["blood_group"], "O-")

        # Test detail view
        detail_url = reverse("donors:donor_detail", kwargs={"pk": d1.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["username"], "donor_api_1")
