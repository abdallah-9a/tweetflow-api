from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class UserProfileAPITestCase(APITestCase):
    def setUp(self):
        self.url = reverse("profile")
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_get_profile_sucess(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.user.username)

    def test_get_profile_without_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UpdateProfileAPITestCase(APITestCase):
    def setUp(self):
        self.url = reverse("update-profile")
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.data = {"name": "user_10", "bio": "no rist no fun"}

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_update_profile_success(self):
        self.authenticate()

        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_profile_without_authentication(self):
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_with_empty_data(self):
        self.authenticate()
        response = self.client.put(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

