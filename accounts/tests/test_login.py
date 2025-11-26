from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class UserLoginAPITestCase(APITestCase):
    def setUp(self):
        self.url = reverse("login")
        self.data = {"username": "user", "password": "user1234"}
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )

    def test_successful_login(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("detail", response.data)

    def test_login_with_wrong_password(self):
        data = self.data.copy()
        data["password"] = "user1111"

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_missing_username_field(self):
        data = {"password": "user1234"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_missing_password_field(self):
        data = {"username": "user"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
