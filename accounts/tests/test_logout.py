from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class UserLogoutAPITestCase(APITestCase):
    def setUp(self):
        self.url = reverse("logout")
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )

    def authenticate(self):
        data = {"username": "user", "password": "user1234"}
        response = self.client.post(reverse("login"), data)
        tokens = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        return tokens

    def test_sucessful_logout(self):
        tokens = self.authenticate()

        response = self.client.post(self.url, {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("msg", response.data)

    def test_logout_without_authentication(self):
        response = self.client.post(self.url, {"refresh": "refresh-token"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_token(self):
        tokens = self.authenticate()

        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_with_invalid_refresh_token(self):
        tokens = self.authenticate()

        response = self.client.post(self.url, {"refresh": "invalid-token"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_with_already_blacklisted_token(self):
        tokens = self.authenticate()

        # Sucess 1st time
        response = self.client.post(self.url, {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Fail when reuse it
        response = self.client.post(self.url, {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
