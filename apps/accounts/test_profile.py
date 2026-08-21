import io
import os
import shutil
import tempfile
from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import UserRole
from apps.accounts.validators import validate_phone_number

User = get_user_model()

# Create a temporary directory for media during tests
MEDIA_ROOT_TMP = tempfile.mkdtemp()


def create_test_image(format="JPEG", size=(100, 100), color=(255, 0, 0)):
    """
    Creates an in-memory image for upload testing.
    """
    file_obj = io.BytesIO()
    image = Image.new("RGB", size=size, color=color)
    image.save(file_obj, format=format)
    file_obj.seek(0)
    ext = format.lower()
    if ext == "jpeg":
        ext = "jpg"
    mime = f"image/{ext if ext != 'jpg' else 'jpeg'}"
    return SimpleUploadedFile(f"test_avatar.{ext}", file_obj.read(), content_type=mime)


@override_settings(MEDIA_ROOT=MEDIA_ROOT_TMP)
class ProfileManagementTests(TestCase):
    """
    Comprehensive test suite for the Profile Management module.
    """

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up temporary media directory
        if os.path.exists(MEDIA_ROOT_TMP):
            shutil.rmtree(MEDIA_ROOT_TMP, ignore_errors=True)

    def setUp(self):
        self.client = APIClient()

        self.donor_user = User.objects.create_user(
            username="test_donor",
            email="donor@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            first_name="Jane",
            last_name="Doe",
            phone="+1-555-0199",
        )

        self.admin_user = User.objects.create_user(
            username="test_admin",
            email="admin@example.com",
            password="StrongPassword123!",
            role=UserRole.SUPER_ADMIN,
            first_name="Admin",
            last_name="User",
        )

        self.other_user = User.objects.create_user(
            username="other_user",
            email="other@example.com",
            password="StrongPassword123!",
            role=UserRole.HOSPITAL_STAFF,
            first_name="Doctor",
            last_name="Smith",
        )

    # =========================================================================
    # 1. PROFILE RETRIEVAL TESTS
    # =========================================================================

    def test_unauthenticated_user_denied_profile_access(self):
        response = self.client.get("/api/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_retrieve_own_profile(self):
        self.client.force_authenticate(user=self.donor_user)
        response = self.client.get("/api/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data["id"], self.donor_user.id)
        self.assertEqual(data["username"], "test_donor")
        self.assertEqual(data["email"], "donor@example.com")
        self.assertEqual(data["first_name"], "Jane")
        self.assertEqual(data["last_name"], "Doe")
        self.assertEqual(data["full_name"], "Jane Doe")
        self.assertEqual(data["role"], UserRole.DONOR)
        self.assertEqual(data["phone"], "+1-555-0199")
        self.assertIsNone(data["profile_image"])
        self.assertFalse(data["is_verified"])
        self.assertTrue(data["is_active"])
        self.assertIn("date_joined", data)

    def test_full_name_fallback_to_username(self):
        user = User.objects.create_user(
            username="anonymous_user",
            email="anon@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
        )
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], "anonymous_user")

    # =========================================================================
    # 2. PROFILE UPDATE TESTS
    # =========================================================================

    def test_partial_update_names_and_phone(self):
        self.client.force_authenticate(user=self.donor_user)
        response = self.client.patch(
            "/api/profile/",
            {
                "first_name": "Janet",
                "last_name": "Williams",
                "phone": "+1 (555) 987-6543",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Janet")
        self.assertEqual(response.data["last_name"], "Williams")
        self.assertEqual(response.data["full_name"], "Janet Williams")
        self.assertEqual(response.data["phone"], "+1 (555) 987-6543")

        self.donor_user.refresh_from_db()
        self.assertEqual(self.donor_user.first_name, "Janet")
        self.assertEqual(self.donor_user.last_name, "Williams")
        self.assertEqual(self.donor_user.phone, "+1 (555) 987-6543")

    def test_full_update_put(self):
        self.client.force_authenticate(user=self.donor_user)
        response = self.client.put(
            "/api/profile/",
            {
                "first_name": "Alice",
                "last_name": "Cooper",
                "email": "alice.cooper@example.com",
                "phone": "+1-800-555-0100",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Alice")
        self.assertEqual(response.data["email"], "alice.cooper@example.com")

        self.donor_user.refresh_from_db()
        self.assertEqual(self.donor_user.email, "alice.cooper@example.com")

    def test_whitespace_trimmed_on_update(self):
        self.client.force_authenticate(user=self.donor_user)
        response = self.client.patch(
            "/api/profile/",
            {
                "first_name": "  TrimmedName  ",
                "last_name": "  TrimmedLast  ",
                "email": "  NEWEMAIL@EXAMPLE.COM  ",
                "phone": "  +1-555-4321  ",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "TrimmedName")
        self.assertEqual(response.data["last_name"], "TrimmedLast")
        self.assertEqual(response.data["email"], "newemail@example.com")
        self.assertEqual(response.data["phone"], "+1-555-4321")

    # =========================================================================
    # 3. SECURITY & PRIVILEGE PROTECTION TESTS
    # =========================================================================

    def test_role_cannot_be_changed_via_profile_api(self):
        self.client.force_authenticate(user=self.donor_user)
        self.assertEqual(self.donor_user.role, UserRole.DONOR)

        # Attempt privilege escalation to SUPER_ADMIN
        response = self.client.patch(
            "/api/profile/",
            {"role": UserRole.SUPER_ADMIN},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], UserRole.DONOR)

        self.donor_user.refresh_from_db()
        self.assertEqual(self.donor_user.role, UserRole.DONOR)

    def test_administrative_and_staff_flags_cannot_be_changed(self):
        self.client.force_authenticate(user=self.donor_user)
        self.assertFalse(self.donor_user.is_staff)
        self.assertFalse(self.donor_user.is_superuser)

        response = self.client.patch(
            "/api/profile/",
            {"is_staff": True, "is_superuser": True},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.donor_user.refresh_from_db()
        self.assertFalse(self.donor_user.is_staff)
        self.assertFalse(self.donor_user.is_superuser)

    def test_is_verified_cannot_be_changed(self):
        self.client.force_authenticate(user=self.donor_user)
        self.assertFalse(self.donor_user.is_verified)

        response = self.client.patch(
            "/api/profile/",
            {"is_verified": True},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.donor_user.refresh_from_db()
        self.assertFalse(self.donor_user.is_verified)

    def test_password_cannot_be_changed_via_profile_api(self):
        self.client.force_authenticate(user=self.donor_user)
        original_hash = self.donor_user.password

        response = self.client.patch(
            "/api/profile/",
            {"password": "CompromisedNewPassword123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.donor_user.refresh_from_db()
        self.assertEqual(self.donor_user.password, original_hash)
        self.assertTrue(self.donor_user.check_password("StrongPassword123!"))

    # =========================================================================
    # 4. EMAIL VALIDATION TESTS
    # =========================================================================

    def test_valid_email_accepted_and_lowercased(self):
        self.client.force_authenticate(user=self.donor_user)
        response = self.client.patch(
            "/api/profile/",
            {"email": "Updated.Email@Domain.COM"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "updated.email@domain.com")

        self.donor_user.refresh_from_db()
        self.assertEqual(self.donor_user.email, "updated.email@domain.com")

    def test_blank_email_rejected(self):
        self.client.force_authenticate(user=self.donor_user)
        response = self.client.patch(
            "/api/profile/",
            {"email": "   "},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_invalid_email_syntax_rejected(self):
        self.client.force_authenticate(user=self.donor_user)
        response = self.client.patch(
            "/api/profile/",
            {"email": "not-an-email"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_duplicate_email_of_another_user_rejected(self):
        self.client.force_authenticate(user=self.donor_user)
        # Attempt to steal other_user's email address
        response = self.client.patch(
            "/api/profile/",
            {"email": "other@example.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_retaining_existing_email_succeeds(self):
        self.client.force_authenticate(user=self.donor_user)
        response = self.client.patch(
            "/api/profile/",
            {
                "email": "donor@example.com",
                "first_name": "UpdatedName",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "UpdatedName")

    # =========================================================================
    # 5. PHONE VALIDATION TESTS
    # =========================================================================

    def test_valid_phone_formats_accepted(self):
        valid_numbers = [
            "+1 555 123 4567",
            "+91 9876543210",
            "(555) 123-4567",
            "555-123-4567",
            "+44 20 7946 0958",
            "9876543210",
        ]
        self.client.force_authenticate(user=self.donor_user)
        for phone_num in valid_numbers:
            response = self.client.patch("/api/profile/", {"phone": phone_num})
            self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed for {phone_num}")

    def test_malformed_phone_rejected(self):
        malformed_numbers = [
            "abc",
            "123",  # Too short (< 7 digits)
            "12345678901234567890",  # Too long (> 15 digits)
            "phone#1234",
            "+1-555-ABC-DEFG",
        ]
        self.client.force_authenticate(user=self.donor_user)
        for bad_phone in malformed_numbers:
            response = self.client.patch("/api/profile/", {"phone": bad_phone})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, f"Allowed bad phone: {bad_phone}")
            self.assertIn("phone", response.data)

    def test_clearing_phone_number_succeeds(self):
        self.client.force_authenticate(user=self.donor_user)
        self.assertIsNotNone(self.donor_user.phone)

        response = self.client.patch("/api/profile/", {"phone": ""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["phone"])

        self.donor_user.refresh_from_db()
        self.assertIsNone(self.donor_user.phone)

    # =========================================================================
    # 6. PROFILE IMAGE UPLOAD & REMOVAL TESTS
    # =========================================================================

    def test_valid_jpeg_upload_succeeds(self):
        self.client.force_authenticate(user=self.donor_user)
        image = create_test_image(format="JPEG")

        response = self.client.post(
            "/api/profile/image/",
            {"profile_image": image},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIsNotNone(response.data["user"]["profile_image"])

        self.donor_user.refresh_from_db()
        self.assertTrue(bool(self.donor_user.profile_image))
        self.assertTrue(os.path.exists(self.donor_user.profile_image.path))

    def test_valid_png_upload_succeeds(self):
        self.client.force_authenticate(user=self.donor_user)
        image = create_test_image(format="PNG")

        response = self.client.post(
            "/api/profile/image/",
            {"profile_image": image},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.donor_user.refresh_from_db()
        self.assertTrue(bool(self.donor_user.profile_image))

    def test_valid_webp_upload_succeeds(self):
        self.client.force_authenticate(user=self.donor_user)
        image = create_test_image(format="WEBP")

        response = self.client.post(
            "/api/profile/image/",
            {"profile_image": image},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.donor_user.refresh_from_db()
        self.assertTrue(bool(self.donor_user.profile_image))

    def test_non_image_file_rejected(self):
        self.client.force_authenticate(user=self.donor_user)
        fake_file = SimpleUploadedFile(
            "document.txt",
            b"This is plain text and not an image.",
            content_type="text/plain",
        )

        response = self.client.post(
            "/api/profile/image/",
            {"profile_image": fake_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile_image", response.data)

    def test_corrupted_fake_image_rejected(self):
        self.client.force_authenticate(user=self.donor_user)
        fake_image = SimpleUploadedFile(
            "fake.jpg",
            b"Not an actual JPEG binary data stream.",
            content_type="image/jpeg",
        )

        response = self.client.post(
            "/api/profile/image/",
            {"profile_image": fake_image},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile_image", response.data)

    def test_oversized_image_rejected(self):
        self.client.force_authenticate(user=self.donor_user)
        # Create a large image (> 2MB)
        large_file = SimpleUploadedFile(
            "large_avatar.jpg",
            b"\xFF\xD8\xFF" + b"0" * (2 * 1024 * 1024 + 1024),
            content_type="image/jpeg",
        )

        response = self.client.post(
            "/api/profile/image/",
            {"profile_image": large_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile_image", response.data)

    def test_replace_profile_image_cleans_up_old_file(self):
        self.client.force_authenticate(user=self.donor_user)
        image1 = create_test_image(format="JPEG")
        self.client.post("/api/profile/image/", {"profile_image": image1}, format="multipart")
        self.donor_user.refresh_from_db()
        old_path = self.donor_user.profile_image.path
        self.assertTrue(os.path.exists(old_path))

        # Upload replacement image
        image2 = create_test_image(format="PNG", color=(0, 255, 0))
        self.client.post("/api/profile/image/", {"profile_image": image2}, format="multipart")
        self.donor_user.refresh_from_db()
        new_path = self.donor_user.profile_image.path

        self.assertNotEqual(old_path, new_path)
        self.assertTrue(os.path.exists(new_path))
        self.assertFalse(os.path.exists(old_path))

    def test_delete_profile_image_removes_file_and_clears_field(self):
        self.client.force_authenticate(user=self.donor_user)
        image = create_test_image(format="JPEG")
        self.client.post("/api/profile/image/", {"profile_image": image}, format="multipart")
        self.donor_user.refresh_from_db()
        image_path = self.donor_user.profile_image.path
        self.assertTrue(os.path.exists(image_path))

        # Delete image
        response = self.client.delete("/api/profile/image/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["profile_image"])

        self.donor_user.refresh_from_db()
        self.assertFalse(bool(self.donor_user.profile_image))
        self.assertFalse(os.path.exists(image_path))

    def test_delete_profile_image_when_none_exists(self):
        self.client.force_authenticate(user=self.donor_user)
        self.assertFalse(bool(self.donor_user.profile_image))

        response = self.client.delete("/api/profile/image/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_image_operations_denied(self):
        response_post = self.client.post("/api/profile/image/", {})
        self.assertEqual(response_post.status_code, status.HTTP_401_UNAUTHORIZED)

        response_delete = self.client.delete("/api/profile/image/")
        self.assertEqual(response_delete.status_code, status.HTTP_401_UNAUTHORIZED)

    # =========================================================================
    # 7. ROLE COVERAGE TESTS
    # =========================================================================

    def test_profile_management_across_all_roles(self):
        roles = [
            (UserRole.SUPER_ADMIN, "super_usr"),
            (UserRole.BLOOD_BANK_ADMIN, "bb_admin_usr"),
            (UserRole.HOSPITAL_STAFF, "hosp_usr"),
            (UserRole.LAB_TECHNICIAN, "lab_usr"),
            (UserRole.DONOR, "donor_cov_usr"),
        ]

        for role_val, username in roles:
            user = User.objects.create_user(
                username=username,
                email=f"{username}@healthcare.org",
                password="Password123!",
                role=role_val,
                first_name="RoleFirst",
                last_name="RoleLast",
            )
            self.client.force_authenticate(user=user)

            # Retrieve profile
            get_res = self.client.get("/api/profile/")
            self.assertEqual(get_res.status_code, status.HTTP_200_OK)
            self.assertEqual(get_res.data["role"], role_val)

            # Update safe fields
            patch_res = self.client.patch(
                "/api/profile/",
                {"first_name": f"{role_val}_Updated"},
            )
            self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
            self.assertEqual(patch_res.data["first_name"], f"{role_val}_Updated")

            user.refresh_from_db()
            self.assertEqual(user.first_name, f"{role_val}_Updated")
            self.assertEqual(user.role, role_val)  # Role remains strictly intact
