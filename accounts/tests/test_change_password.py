from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class ChangePasswordAPITestCase(APITestCase):
    def setUp(self):
        self.url = reverse("change-password")
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.data = {
            "old_password": "user1234",
            "password": "USER99",
            "password2": "USER99",
        }

    def authenticate(self):
        response = self.client.post(
            reverse("login"), {"username": "user", "password": "user1234"}
        )
        tokens = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def test_successful_change_password(self):
        self.authenticate()

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_with_wrong_old_password(self):
        self.authenticate()
        data = self.data.copy()
        data["old_password"] = "wrong-password"

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_with_missing_fields(self):
        self.authenticate()
        data = [
            {
                "password": "USER99",
                "password2": "USER99",
            },
            {
                "old_password": "user1234",
                "password2": "USER99",
            },
            {
                "old_password": "user1234",
                "password": "USER99",
            },
        ]
        for d in data:
            response = self.client.post(self.url, d)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_with_mismatch_new_passwords(self):
        self.authenticate()
        data = self.data.copy()
        data["password2"] = "mismatch-password"

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_without_authentication(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
