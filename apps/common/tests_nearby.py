from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import UserRole
from apps.blood_requests.models import Hospital
from apps.donors.models import BloodGroup, Donor
from apps.emergency_sos.compatibility import calculate_haversine_distance_km
from apps.inventory.models import BloodBank

User = get_user_model()


class NearbyDistanceCalculationTest(TestCase):
    """
    Tests Haversine distance calculations and boundary conditions.
    """
    def test_haversine_known_distance(self):
        # Chennai (13.0827, 80.2707) to Bengaluru (12.9716, 77.5946) ~ 290 km
        dist = calculate_haversine_distance_km(13.0827, 80.2707, 12.9716, 77.5946)
        self.assertIsNotNone(dist)
        self.assertAlmostEqual(dist, 290.0, delta=15.0)

    def test_haversine_zero_distance_same_point(self):
        dist = calculate_haversine_distance_km(13.0827, 80.2707, 13.0827, 80.2707)
        self.assertIsNotNone(dist)
        self.assertAlmostEqual(dist, 0.0, places=4)

    def test_haversine_missing_coordinates(self):
        self.assertIsNone(calculate_haversine_distance_km(None, 80.27, 13.08, 80.27))
        self.assertIsNone(calculate_haversine_distance_km(13.08, None, 13.08, 80.27))
        self.assertIsNone(calculate_haversine_distance_km(13.08, 80.27, None, 80.27))
        self.assertIsNone(calculate_haversine_distance_km(13.08, 80.27, 13.08, None))


class NearbyAPITests(APITestCase):
    """
    Comprehensive API tests for /api/nearby/ proximity search.
    """
    def setUp(self):
        # Super Admin
        self.super_admin = User.objects.create_superuser(
            username="admin_nearby",
            email="admin_nearby@test.com",
            password="AdminPassword123!",
            role=UserRole.SUPER_ADMIN,
        )

        # Hospital Staff
        self.hospital_staff = User.objects.create_user(
            username="staff_nearby",
            email="staff_nearby@test.com",
            password="StaffPassword123!",
            role=UserRole.HOSPITAL_STAFF,
            latitude=Decimal("13.082700"),
            longitude=Decimal("80.270700"),
        )

        # Blood Bank Admin
        self.bank_admin = User.objects.create_user(
            username="bankadmin_nearby",
            email="bankadmin_nearby@test.com",
            password="BankPassword123!",
            role=UserRole.BLOOD_BANK_ADMIN,
        )

        # Regular Donor User
        self.donor_user1 = User.objects.create_user(
            username="donor1_nearby",
            email="donor1_nearby@test.com",
            password="DonorPassword123!",
            role=UserRole.DONOR,
            latitude=Decimal("13.085000"),
            longitude=Decimal("80.275000"),
        )
        self.donor1 = Donor.objects.create(
            user=self.donor_user1,
            blood_group=BloodGroup.O_POSITIVE,
            date_of_birth=timezone.now().date() - timezone.timedelta(days=25 * 365),
            weight_kg=Decimal("68.00"),
            latitude=Decimal("13.085000"),
            longitude=Decimal("80.275000"),
        )

        # Second Donor (Farther away: ~30km)
        self.donor_user2 = User.objects.create_user(
            username="donor2_far",
            email="donor2_far@test.com",
            password="DonorPassword123!",
            role=UserRole.DONOR,
            latitude=Decimal("13.350000"),
            longitude=Decimal("80.270000"),
        )
        self.donor2 = Donor.objects.create(
            user=self.donor_user2,
            blood_group=BloodGroup.A_POSITIVE,
            date_of_birth=timezone.now().date() - timezone.timedelta(days=30 * 365),
            weight_kg=Decimal("72.00"),
            latitude=Decimal("13.350000"),
            longitude=Decimal("80.270000"),
        )

        # Donor without coordinates
        self.donor_user_no_coords = User.objects.create_user(
            username="donor_no_coords",
            email="donor_no_coords@test.com",
            password="DonorPassword123!",
            role=UserRole.DONOR,
        )
        self.donor_no_coords = Donor.objects.create(
            user=self.donor_user_no_coords,
            blood_group=BloodGroup.B_POSITIVE,
            date_of_birth=timezone.now().date() - timezone.timedelta(days=28 * 365),
            weight_kg=Decimal("60.00"),
            latitude=None,
            longitude=None,
        )

        # Blood Bank Facility
        self.blood_bank = BloodBank.objects.create(
            name="City Central Blood Bank",
            city="Chennai",
            state="Tamil Nadu",
            address="10 Hospital Road",
            contact_number="+91 44 2800 0001",
            email="bank@cityhospital.org",
            capacity=200,
            latitude=Decimal("13.084000"),
            longitude=Decimal("80.272000"),
            admin=self.bank_admin,
        )

        # Hospital Facility
        self.hospital = Hospital.objects.create(
            name="Apollo General Hospital",
            city="Chennai",
            state="Tamil Nadu",
            address="21 Greams Lane",
            contact_number="+91 44 2829 0200",
            email="apollo@hospital.org",
            beds=500,
            latitude=Decimal("13.060000"),
            longitude=Decimal("80.250000"),
        )

    def test_unauthenticated_request_rejected(self):
        """1. Unauthorized access returns 401."""
        res = self.client.get("/api/nearby/?lat=13.08&lng=80.27&radius=10")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_latitude_validation(self):
        """2. Validates latitude range (-90 to 90)."""
        self.client.force_authenticate(user=self.hospital_staff)
        res_invalid_lat = self.client.get("/api/nearby/?lat=95.0&lng=80.27&radius=10")
        self.assertEqual(res_invalid_lat.status_code, status.HTTP_400_BAD_REQUEST)

    def test_longitude_validation(self):
        """3. Validates longitude range (-180 to 180)."""
        self.client.force_authenticate(user=self.hospital_staff)
        res_invalid_lng = self.client.get("/api/nearby/?lat=13.08&lng=190.0&radius=10")
        self.assertEqual(res_invalid_lng.status_code, status.HTTP_400_BAD_REQUEST)

    def test_radius_validation(self):
        """4. Validates radius boundary (> 0 and <= 100)."""
        self.client.force_authenticate(user=self.hospital_staff)
        res_zero = self.client.get("/api/nearby/?lat=13.08&lng=80.27&radius=0")
        self.assertEqual(res_zero.status_code, status.HTTP_400_BAD_REQUEST)

        res_huge = self.client.get("/api/nearby/?lat=13.08&lng=80.27&radius=500")
        self.assertEqual(res_huge.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nearby_search_as_hospital_staff(self):
        """5. Hospital staff discovers nearby donors, blood banks, and hospitals."""
        self.client.force_authenticate(user=self.hospital_staff)
        res = self.client.get("/api/nearby/?lat=13.0827&lng=80.2707&radius=10")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data
        self.assertIn("results", data)
        self.assertIn("donors", data["results"])
        self.assertIn("blood_banks", data["results"])
        self.assertIn("hospitals", data["results"])

        # Donor 1 (~0.5 km) is within 10 km
        donor_ids = [d["donor_id"] for d in data["results"]["donors"]]
        self.assertIn(self.donor1.id, donor_ids)
        # Donor 2 (~30 km) is NOT within 10 km
        self.assertNotIn(self.donor2.id, donor_ids)
        # Donor with no coordinates is NOT included
        self.assertNotIn(self.donor_no_coords.id, donor_ids)

        # Blood Bank is within 10 km
        bank_ids = [b["id"] for b in data["results"]["blood_banks"]]
        self.assertIn(self.blood_bank.id, bank_ids)

        # Hospital is within 10 km
        hosp_ids = [h["id"] for h in data["results"]["hospitals"]]
        self.assertIn(self.hospital.id, hosp_ids)

    def test_radius_filtering_expansion(self):
        """6. Expanding search radius to 50 km includes distant donor."""
        self.client.force_authenticate(user=self.hospital_staff)
        res = self.client.get("/api/nearby/?lat=13.0827&lng=80.2707&radius=50")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        donor_ids = [d["donor_id"] for d in res.data["results"]["donors"]]
        self.assertIn(self.donor1.id, donor_ids)
        self.assertIn(self.donor2.id, donor_ids)

    def test_blood_group_filtering(self):
        """7. Blood group filter narrows donor search."""
        self.client.force_authenticate(user=self.hospital_staff)
        res_o = self.client.get("/api/nearby/?lat=13.0827&lng=80.2707&radius=50&blood_group=O%2B")
        self.assertEqual(res_o.status_code, status.HTTP_200_OK)
        donor_ids = [d["donor_id"] for d in res_o.data["results"]["donors"]]
        self.assertIn(self.donor1.id, donor_ids)
        self.assertNotIn(self.donor2.id, donor_ids)

    def test_donor_privacy_protection(self):
        """8. Donor exact coordinates, addresses, and passwords are not exposed."""
        self.client.force_authenticate(user=self.hospital_staff)
        res = self.client.get("/api/nearby/?lat=13.0827&lng=80.2707&radius=10")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        donors = res.data["results"]["donors"]
        self.assertTrue(len(donors) > 0)
        donor_res = donors[0]

        # Ensure approximate coordinates are fuzzed to 2 decimal places
        self.assertIn("approximate_latitude", donor_res)
        self.assertIn("approximate_longitude", donor_res)
        self.assertEqual(donor_res["approximate_latitude"], 13.09) # 13.085 -> rounded 13.09
        self.assertEqual(donor_res["approximate_longitude"], 80.28) # 80.275 -> rounded 80.28

        # Ensure sensitive fields are absent
        self.assertNotIn("password", donor_res)
        self.assertNotIn("email", donor_res)
        self.assertNotIn("phone", donor_res)
        self.assertNotIn("address", donor_res)

    def test_donor_role_cannot_discover_other_donors(self):
        """9. Regular DONOR users cannot query other donors' locations."""
        self.client.force_authenticate(user=self.donor_user1)

        # Asking for only donors returns 403 Forbidden
        res_explicit = self.client.get("/api/nearby/?lat=13.08&lng=80.27&radius=10&type=donors")
        self.assertEqual(res_explicit.status_code, status.HTTP_403_FORBIDDEN)

        # Asking for all returns blood banks and hospitals, but donors array is empty
        res_all = self.client.get("/api/nearby/?lat=13.08&lng=80.27&radius=10&type=all")
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_all.data["results"]["donors"], [])
        self.assertIn("donor_access_note", res_all.data)
        self.assertTrue(len(res_all.data["results"]["blood_banks"]) > 0)
        self.assertTrue(len(res_all.data["results"]["hospitals"]) > 0)

    def test_profile_location_update_and_sync(self):
        """10. User profile coordinates update and sync bidirectionally."""
        self.client.force_authenticate(user=self.donor_user1)
        patch_data = {
            "latitude": "12.971600",
            "longitude": "77.594600",
            "address": "Koramangala, Bengaluru",
        }
        res = self.client.patch("/api/profile/", patch_data, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.donor_user1.refresh_from_db()
        self.assertEqual(self.donor_user1.latitude, Decimal("12.971600"))
        self.assertEqual(self.donor_user1.longitude, Decimal("77.594600"))
        self.assertEqual(self.donor_user1.address, "Koramangala, Bengaluru")

        # Synchronized to donor profile
        self.donor1.refresh_from_db()
        self.assertEqual(self.donor1.latitude, Decimal("12.971600"))
        self.assertEqual(self.donor1.longitude, Decimal("77.594600"))
