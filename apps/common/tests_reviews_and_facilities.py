from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.blood_requests.models import Hospital
from apps.common.models import Review, ReviewStatus
from apps.inventory.models import BloodBank

User = get_user_model()


class HospitalManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin_test",
            email="admin_test@example.com",
            password="adminpassword123",
            role="SUPER_ADMIN"
        )
        self.donor = User.objects.create_user(
            username="donor_test",
            email="donor_test@example.com",
            password="donorpassword123",
            role="DONOR"
        )
        self.hospital_staff = User.objects.create_user(
            username="staff_test",
            email="staff_test@example.com",
            password="staffpassword123",
            role="HOSPITAL_STAFF"
        )

    def test_super_admin_can_create_hospital(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "Apollo Care Hospital",
            "address": "123 Greams Road",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "contact_number": "+91 9876543210",
            "email": "apollo@example.com",
            "beds": 250,
            "latitude": 13.0600,
            "longitude": 80.2500,
            "is_active": True,
        }
        response = self.client.post("/api/hospitals/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Hospital.objects.filter(name="Apollo Care Hospital").count(), 1)
        hospital = Hospital.objects.get(name="Apollo Care Hospital")
        self.assertEqual(hospital.city, "Chennai")
        self.assertTrue(hospital.is_active)

    def test_super_admin_can_edit_hospital(self):
        hospital = Hospital.objects.create(
            name="City Clinic",
            address="45 Main St",
            city="Chennai",
            contact_number="1234567890",
            beds=50,
            is_active=True,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/hospitals/{hospital.id}/",
            {"beds": 80, "name": "City General Hospital"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        hospital.refresh_from_db()
        self.assertEqual(hospital.beds, 80)
        self.assertEqual(hospital.name, "City General Hospital")

    def test_super_admin_can_deactivate_hospital(self):
        hospital = Hospital.objects.create(
            name="Metro Hospital",
            city="Chennai",
            contact_number="1234567890",
            is_active=True,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/hospitals/{hospital.id}/",
            {"is_active": False},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        hospital.refresh_from_db()
        self.assertFalse(hospital.is_active)

    def test_unauthorized_users_cannot_administer_hospitals(self):
        # Anonymous cannot create
        data = {"name": "Unauthorized Hosp", "city": "Chennai"}
        response = self.client.post("/api/hospitals/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Donor cannot create
        self.client.force_authenticate(user=self.donor)
        response = self.client.post("/api/hospitals/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Donor cannot delete or edit
        hospital = Hospital.objects.create(name="Existing Hosp", city="Chennai", is_active=True)
        response = self.client.delete(f"/api/hospitals/{hospital.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.patch(f"/api/hospitals/{hospital.id}/", {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_hospital_coordinates_validate_correctly(self):
        self.client.force_authenticate(user=self.admin)
        invalid_data = {
            "name": "Invalid Coord Hospital",
            "city": "Chennai",
            "latitude": 95.0,  # Invalid latitude (> 90)
            "longitude": 80.0,
        }
        response = self.client.post("/api/hospitals/", invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_hospitals_excluded_from_nearby_active_resources(self):
        active_hosp = Hospital.objects.create(
            name="Active Hosp",
            city="Chennai",
            latitude=13.0827,
            longitude=80.2707,
            is_active=True,
        )
        inactive_hosp = Hospital.objects.create(
            name="Inactive Hosp",
            city="Chennai",
            latitude=13.0828,
            longitude=80.2708,
            is_active=False,
        )
        self.client.force_authenticate(user=self.donor)
        response = self.client.get(
            "/api/nearby/?lat=13.0827&lng=80.2707&radius=10&types=hospitals"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        hospitals_returned = response.json()["results"]["hospitals"]
        hosp_ids = [h["id"] for h in hospitals_returned]
        self.assertIn(active_hosp.id, hosp_ids)
        self.assertNotIn(inactive_hosp.id, hosp_ids)


class BloodBankManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="bb_admin_test",
            email="bb_admin@example.com",
            password="adminpassword123",
            role="SUPER_ADMIN"
        )
        self.donor = User.objects.create_user(
            username="bb_donor_test",
            email="bb_donor@example.com",
            password="donorpassword123",
            role="DONOR"
        )
        self.bank_manager = User.objects.create_user(
            username="bb_manager",
            email="bb_manager@example.com",
            password="managerpassword123",
            role="BLOOD_BANK_ADMIN"
        )

    def test_super_admin_can_create_blood_bank(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "name": "Central Blood Repository",
            "address": "50 Red Cross Road",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "contact_number": "+91 9444123456",
            "email": "centralbb@example.com",
            "capacity": 1000,
            "latitude": 13.0850,
            "longitude": 80.2800,
            "is_active": True,
        }
        response = self.client.post("/api/blood-banks/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BloodBank.objects.filter(name="Central Blood Repository").count(), 1)

    def test_super_admin_can_edit_and_deactivate_blood_bank(self):
        bank = BloodBank.objects.create(
            name="Life Blood Bank",
            city="Chennai",
            capacity=500,
            is_active=True,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/blood-banks/{bank.id}/",
            {"capacity": 750, "is_active": False},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bank.refresh_from_db()
        self.assertEqual(bank.capacity, 750)
        self.assertFalse(bank.is_active)

    def test_unauthorized_users_cannot_manage_blood_banks(self):
        self.client.force_authenticate(user=self.donor)
        data = {"name": "Unauthorized Bank", "city": "Chennai"}
        response = self.client.post("/api/blood-banks/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        bank = BloodBank.objects.create(name="Existing Bank", city="Chennai", is_active=True)
        response = self.client.delete(f"/api/blood-banks/{bank.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReviewSystemTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="rev_admin",
            email="rev_admin@example.com",
            password="adminpassword123",
            role="SUPER_ADMIN"
        )
        self.donor1 = User.objects.create_user(
            username="rev_donor1",
            email="donor1@example.com",
            password="donorpassword123",
            role="DONOR"
        )
        self.donor2 = User.objects.create_user(
            username="rev_donor2",
            email="donor2@example.com",
            password="donorpassword123",
            role="DONOR"
        )
        self.hospital_staff = User.objects.create_user(
            username="rev_staff",
            email="staff@example.com",
            password="staffpassword123",
            role="HOSPITAL_STAFF"
        )
        self.bank_admin = User.objects.create_user(
            username="rev_bank_admin",
            email="bankadmin@example.com",
            password="bankpassword123",
            role="BLOOD_BANK_ADMIN"
        )
        self.lab_tech = User.objects.create_user(
            username="rev_lab_tech",
            email="labtech@example.com",
            password="labpassword123",
            role="LAB_TECHNICIAN"
        )
        self.hospital = Hospital.objects.create(
            name="Apex General Hospital",
            city="Chennai",
            is_active=True
        )
        self.blood_bank = BloodBank.objects.create(
            name="Apex Blood Bank",
            city="Chennai",
            is_active=True
        )

    def test_anonymous_user_cannot_submit_review(self):
        response = self.client.post(
            "/api/reviews/",
            {"hospital": self.hospital.id, "rating": 5, "comment": "Excellent service"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_submit_valid_review(self):
        self.client.force_authenticate(user=self.donor1)
        response = self.client.post(
            "/api/reviews/",
            {"hospital": self.hospital.id, "rating": 5, "comment": "Great doctors and clean premises."},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["status"], "PENDING")
        self.assertEqual(response.json()["reviewer"]["username"], "rev_donor1")
        self.assertEqual(response.json()["target_type"], "HOSPITAL")

    def test_rating_validation(self):
        self.client.force_authenticate(user=self.donor1)
        # Rating 0 rejected
        r0 = self.client.post(
            "/api/reviews/",
            {"hospital": self.hospital.id, "rating": 0, "comment": "Very bad"},
            format="json"
        )
        self.assertEqual(r0.status_code, status.HTTP_400_BAD_REQUEST)

        # Rating 6 rejected
        r6 = self.client.post(
            "/api/reviews/",
            {"hospital": self.hospital.id, "rating": 6, "comment": "Too good"},
            format="json"
        )
        self.assertEqual(r6.status_code, status.HTTP_400_BAD_REQUEST)

        # Rating -1 rejected
        rn = self.client.post(
            "/api/reviews/",
            {"hospital": self.hospital.id, "rating": -1, "comment": "Negative rating"},
            format="json"
        )
        self.assertEqual(rn.status_code, status.HTTP_400_BAD_REQUEST)

        # Rating 1-5 accepted
        for valid_rating in [1, 2, 3, 4, 5]:
            r_valid = self.client.post(
                "/api/reviews/",
                {"blood_bank": self.blood_bank.id, "rating": valid_rating, "comment": f"Rating {valid_rating} test review"},
                format="json"
            )
            self.assertIn(r_valid.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_empty_or_whitespace_review_rejected(self):
        self.client.force_authenticate(user=self.donor1)
        response = self.client.post(
            "/api/reviews/",
            {"hospital": self.hospital.id, "rating": 4, "comment": "   "},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_target_both_or_neither_hospital_and_blood_bank(self):
        self.client.force_authenticate(user=self.donor1)
        # Both
        r_both = self.client.post(
            "/api/reviews/",
            {
                "hospital": self.hospital.id,
                "blood_bank": self.blood_bank.id,
                "rating": 4,
                "comment": "Targeting both",
            },
            format="json"
        )
        self.assertEqual(r_both.status_code, status.HTTP_400_BAD_REQUEST)

        # Neither
        r_none = self.client.post(
            "/api/reviews/",
            {"rating": 4, "comment": "Targeting neither"},
            format="json"
        )
        self.assertEqual(r_none.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reviewer_always_authenticated_user_cannot_impersonate(self):
        self.client.force_authenticate(user=self.donor1)
        # Attempt to pass donor2's ID as reviewer
        response = self.client.post(
            "/api/reviews/",
            {
                "hospital": self.hospital.id,
                "reviewer": self.donor2.id,
                "rating": 5,
                "comment": "Trying to impersonate donor 2",
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verify review is credited strictly to donor1
        review = Review.objects.get(id=response.json()["id"])
        self.assertEqual(review.reviewer, self.donor1)

    def test_duplicate_review_updates_existing_and_resets_to_pending(self):
        self.client.force_authenticate(user=self.donor1)
        # First submission
        r1 = self.client.post(
            "/api/reviews/",
            {"hospital": self.hospital.id, "rating": 4, "comment": "First review"},
            format="json"
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        rev_id = r1.json()["id"]

        # Admin approves it
        review = Review.objects.get(id=rev_id)
        review.status = ReviewStatus.APPROVED
        review.save()

        # User submits updated review for same hospital
        r2 = self.client.post(
            "/api/reviews/",
            {"hospital": self.hospital.id, "rating": 5, "comment": "Updated review - much better!"},
            format="json"
        )
        self.assertIn(r2.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(r2.json()["id"], rev_id)

        # Total review count for this user & hospital remains 1
        self.assertEqual(Review.objects.filter(reviewer=self.donor1, hospital=self.hospital).count(), 1)
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Updated review - much better!")
        # Must be reset to PENDING
        self.assertEqual(review.status, ReviewStatus.PENDING)


class ReviewModerationAndVisibilityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="mod_admin",
            email="mod_admin@example.com",
            password="adminpassword123",
            role="SUPER_ADMIN"
        )
        self.donor = User.objects.create_user(
            username="mod_donor",
            email="mod_donor@example.com",
            password="donorpassword123",
            role="DONOR"
        )
        self.hospital_staff = User.objects.create_user(
            username="mod_staff",
            email="mod_staff@example.com",
            password="staffpassword123",
            role="HOSPITAL_STAFF"
        )
        self.blood_bank_admin = User.objects.create_user(
            username="mod_bb_admin",
            email="mod_bb_admin@example.com",
            password="bbpassword123",
            role="BLOOD_BANK_ADMIN"
        )
        self.lab_technician = User.objects.create_user(
            username="mod_lab_tech",
            email="mod_lab_tech@example.com",
            password="labpassword123",
            role="LAB_TECHNICIAN"
        )
        self.hospital = Hospital.objects.create(name="St. Jude Hospital", city="Chennai", is_active=True)
        self.review = Review.objects.create(
            reviewer=self.donor,
            hospital=self.hospital,
            rating=5,
            comment="Wonderful care and compassion.",
            status=ReviewStatus.PENDING,
        )

    def test_pending_and_rejected_reviews_not_public(self):
        # Unauthenticated query for hospital reviews
        response = self.client.get(f"/api/reviews/?hospital={self.hospital.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Pending review must not appear
        self.assertEqual(len(response.json()), 0)

        # Reject the review
        self.review.status = ReviewStatus.REJECTED
        self.review.save()
        response = self.client.get(f"/api/reviews/?hospital={self.hospital.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_super_admin_can_approve(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f"/api/reviews/{self.review.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "APPROVED")

        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.APPROVED)
        self.assertEqual(self.review.reviewed_by, self.admin)
        self.assertIsNotNone(self.review.reviewed_at)

        # Now public
        self.client.logout()
        response = self.client.get(f"/api/reviews/?hospital={self.hospital.id}")
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["id"], self.review.id)

    def test_super_admin_can_reject(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/reviews/{self.review.id}/reject/",
            {"rejection_reason": "Inappropriate language"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "REJECTED")

        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.REJECTED)
        self.assertEqual(self.review.rejection_reason, "Inappropriate language")
        self.assertEqual(self.review.reviewed_by, self.admin)

    def test_non_super_admins_cannot_approve_or_reject(self):
        non_admins = [
            self.donor,
            self.hospital_staff,
            self.blood_bank_admin,
            self.lab_technician,
        ]
        for user in non_admins:
            self.client.force_authenticate(user=user)
            r_app = self.client.post(f"/api/reviews/{self.review.id}/approve/")
            self.assertEqual(r_app.status_code, status.HTTP_403_FORBIDDEN)
            r_rej = self.client.post(f"/api/reviews/{self.review.id}/reject/", {"rejection_reason": "test"}, format="json")
            self.assertEqual(r_rej.status_code, status.HTTP_403_FORBIDDEN)

    def test_ratings_calculation_only_includes_approved_reviews(self):
        self.client.force_authenticate(user=self.donor)
        # Initially pending: rating is None, count is 0
        hosp_resp = self.client.get(f"/api/hospitals/{self.hospital.id}/")
        self.assertIsNone(hosp_resp.json()["average_rating"])
        self.assertEqual(hosp_resp.json()["review_count"], 0)

        # Approve review (5 stars)
        self.client.force_authenticate(user=self.admin)
        self.client.post(f"/api/reviews/{self.review.id}/approve/")

        hosp_resp = self.client.get(f"/api/hospitals/{self.hospital.id}/")
        self.assertEqual(hosp_resp.json()["average_rating"], 5.0)
        self.assertEqual(hosp_resp.json()["review_count"], 1)

        # Add a 3 star review from another user that remains pending
        rev2 = Review.objects.create(
            reviewer=self.hospital_staff,
            hospital=self.hospital,
            rating=3,
            comment="Pending 3 star review",
            status=ReviewStatus.PENDING,
        )

        hosp_resp = self.client.get(f"/api/hospitals/{self.hospital.id}/")
        # Average is still 5.0 and count is still 1
        self.assertEqual(hosp_resp.json()["average_rating"], 5.0)
        self.assertEqual(hosp_resp.json()["review_count"], 1)

        # Approve rev2 -> Average becomes (5 + 3) / 2 = 4.0, count becomes 2
        self.client.post(f"/api/reviews/{rev2.id}/approve/")
        hosp_resp = self.client.get(f"/api/hospitals/{self.hospital.id}/")
        self.assertEqual(hosp_resp.json()["average_rating"], 4.0)
        self.assertEqual(hosp_resp.json()["review_count"], 2)
