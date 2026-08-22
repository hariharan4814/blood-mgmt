from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import UserRole

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_standard_user(self):
        user = User.objects.create_user(
            username="johndoe",
            email="john@example.com",
            password="SecurePassword123!",
            phone="+1122334455"
        )
        self.assertEqual(user.username, "johndoe")
        self.assertEqual(user.email, "john@example.com")
        self.assertEqual(user.role, UserRole.DONOR)
        self.assertFalse(user.is_verified)
        self.assertTrue(user.is_donor)
        self.assertFalse(user.is_super_admin)
        self.assertIn("Donor", str(user))

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            username="superadmin",
            email="admin@example.com",
            password="SuperAdminPassword123!",
            role=UserRole.SUPER_ADMIN,
            is_verified=True
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_super_admin)
        self.assertTrue(admin.is_verified)


class AuthenticationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPassword123!",
            role=UserRole.DONOR,
            phone="+1234567890",
            is_verified=True
        )
        self.login_url = reverse("accounts:token_obtain_pair")
        self.refresh_url = reverse("accounts:token_refresh")
        self.register_url = reverse("accounts:register")
        self.me_url = reverse("accounts:current_user")

    def test_public_registration_donor_success(self):
        payload = {
            "username": "newdonor",
            "email": "newdonor@example.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "role": UserRole.DONOR,
            "phone": "+1999888777"
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["message"], "Registration successful")
        self.assertIn("user", data)
        self.assertEqual(data["user"]["username"], "newdonor")
        self.assertEqual(data["user"]["email"], "newdonor@example.com")
        self.assertEqual(data["user"]["role"], UserRole.DONOR)
        self.assertEqual(data["user"]["phone"], "+1999888777")
        self.assertFalse(data["user"]["is_verified"])
        self.assertNotIn("password", data["user"])

    def test_public_registration_hospital_staff_success(self):
        payload = {
            "username": "hospitalstaff1",
            "email": "staff1@hospital.local",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "role": UserRole.HOSPITAL_STAFF,
            "phone": "+1555666777"
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["user"]["role"], UserRole.HOSPITAL_STAFF)

    def test_public_registration_super_admin_rejected(self):
        payload = {
            "username": "fakeadmin",
            "email": "fakeadmin@example.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "role": UserRole.SUPER_ADMIN,
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.json())

    def test_public_registration_blood_bank_admin_rejected(self):
        payload = {
            "username": "fakebbadmin",
            "email": "fakebbadmin@example.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "role": UserRole.BLOOD_BANK_ADMIN,
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.json())

    def test_public_registration_lab_technician_rejected(self):
        payload = {
            "username": "fakelabtech",
            "email": "fakelabtech@example.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "role": UserRole.LAB_TECHNICIAN,
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.json())

    def test_registration_password_mismatch(self):
        payload = {
            "username": "mismatchuser",
            "email": "mismatch@example.com",
            "password": "SecurePassword123!",
            "password_confirm": "DifferentPassword123!",
            "role": UserRole.DONOR,
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.json())

    def test_registration_duplicate_username(self):
        payload = {
            "username": "testuser",
            "email": "unique@example.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "role": UserRole.DONOR,
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.json())

    def test_registration_duplicate_email(self):
        payload = {
            "username": "uniqueuser",
            "email": "testuser@example.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "role": UserRole.DONOR,
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.json())

    def test_login_successful(self):
        payload = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["username"], "testuser")
        self.assertEqual(data["user"]["email"], "testuser@example.com")
        self.assertEqual(data["user"]["role"], UserRole.DONOR)
        self.assertEqual(data["user"]["phone"], "+1234567890")
        self.assertTrue(data["user"]["is_verified"])
        self.assertNotIn("password", data["user"])

    def test_login_with_email_successful(self):
        payload = {
            "username": "testuser@example.com",
            "password": "StrongPassword123!"
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("access", data)
        self.assertEqual(data["user"]["username"], "testuser")
        self.assertEqual(data["user"]["email"], "testuser@example.com")

    def test_login_invalid_credentials(self):
        payload = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        login_response = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "StrongPassword123!"},
            format="json"
        )
        refresh_token = login_response.json()["refresh"]

        refresh_response = self.client.post(
            self.refresh_url,
            {"refresh": refresh_token},
            format="json"
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.json())

    def test_current_user_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["id"], self.user.id)
        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["email"], "testuser@example.com")
        self.assertEqual(data["role"], UserRole.DONOR)
        self.assertNotIn("password", data)

    def test_current_user_unauthenticated(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserManagementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="AdminPassword123!",
            role=UserRole.SUPER_ADMIN,
            is_verified=True
        )
        self.donor = User.objects.create_user(
            username="donoruser",
            email="donor@example.com",
            password="DonorPassword123!",
            role=UserRole.DONOR,
            phone="+1112223333",
            is_verified=False
        )
        self.hospital_staff = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="StaffPassword123!",
            role=UserRole.HOSPITAL_STAFF,
            phone="+1112224444",
            is_verified=True
        )
        self.users_url = reverse("user_management:user_list")
        self.donor_detail_url = reverse("user_management:user_detail", kwargs={"pk": self.donor.id})
        self.admin_detail_url = reverse("user_management:user_detail", kwargs={"pk": self.admin.id})

    def test_super_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        self.assertIn("count", data)
        self.assertEqual(data["count"], 3)

    def test_non_super_admin_cannot_list_users(self):
        self.client.force_authenticate(user=self.donor)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.hospital_staff)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_list_users(self):
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_super_admin_can_retrieve_user_detail(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.donor_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["username"], "donoruser")
        self.assertEqual(data["role"], UserRole.DONOR)
        self.assertNotIn("password", data)

    def test_non_super_admin_cannot_retrieve_user_detail(self):
        self.client.force_authenticate(user=self.donor)
        response = self.client.get(self.donor_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_admin_can_update_user_patch(self):
        self.client.force_authenticate(user=self.admin)
        patch_payload = {
            "role": UserRole.LAB_TECHNICIAN,
            "is_verified": True,
            "phone": "+1999000111"
        }
        response = self.client.patch(self.donor_detail_url, patch_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["role"], UserRole.LAB_TECHNICIAN)
        self.assertTrue(data["is_verified"])
        self.assertEqual(data["phone"], "+1999000111")

        self.donor.refresh_from_db()
        self.assertEqual(self.donor.role, UserRole.LAB_TECHNICIAN)
        self.assertTrue(self.donor.is_verified)

    def test_non_super_admin_cannot_update_user(self):
        self.client.force_authenticate(user=self.hospital_staff)
        patch_payload = {"role": UserRole.SUPER_ADMIN}
        response = self.client.patch(self.donor_detail_url, patch_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_admin_can_delete_other_user(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.donor_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.donor.id).exists())

    def test_super_admin_self_deletion_safeguard(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.admin_detail_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(id=self.admin.id).exists())

    def test_super_admin_can_provision_user_post(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "username": "new_lab_tech",
            "email": "labtech@example.com",
            "password": "SecurePassword123!",
            "role": UserRole.LAB_TECHNICIAN,
            "first_name": "Lab",
            "last_name": "Tech",
            "phone": "+1999888777",
            "is_active": True,
        }
        response = self.client.post(self.users_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["username"], "new_lab_tech")
        self.assertEqual(data["role"], UserRole.LAB_TECHNICIAN)
        self.assertTrue(User.objects.filter(username="new_lab_tech").exists())

    def test_non_super_admin_cannot_provision_user(self):
        self.client.force_authenticate(user=self.hospital_staff)
        payload = {
            "username": "unauthorized_user",
            "email": "unauth@example.com",
            "password": "SecurePassword123!",
            "role": UserRole.BLOOD_BANK_ADMIN,
        }
        response = self.client.post(self.users_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

