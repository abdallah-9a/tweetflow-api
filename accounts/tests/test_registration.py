from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class UserRegistrationAPITestCase(APITestCase):
    def setUp(self):
        self.url = reverse("register")
        self.data = {
            "username": "User",
            "email": "user@gmail.com",
            "password": "user1234",
            "password2": "user1234",
        }

    def test_successful_registration(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username=self.data["username"]).exists())
        self.assertIn("detail", response.data)
        self.assertIn("token", response.data)

    def test_auto_create_profile_post_user(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username=self.data["username"])
        self.assertEqual(user.profile.name, self.data["username"])
        self.assertEqual(user.profile.user, user)

    def test_registration_with_duplicate_username(self):
        data = self.data.copy()
        data["email"] = "user2@gmail.com"
        self.client.post(self.url, self.data)

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_with_duplicate_email(self):
        data = self.data.copy()
        data["username"] = "user2"
        self.client.post(self.url, self.data)

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_with_invalid_email(self):
        data = self.data.copy()
        data["email"] = "not-an-email"
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_with_insenstive_email(self):
        data = self.data.copy()
        data["email"] = "USER@GMAIL.COM"

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registration_with_mismatch_passwords(self):
        data = self.data.copy()
        data["password2"] = "1234user"

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_incase_missing_fields(self):
        data = [
            {
                "username": "User",
                "password": "user1234",
                "password2": "user1234",
            },
            {
                "email": "user@gmail.com",
                "password": "user1234",
                "password2": "user1234",
            },
            {
                "username": "User",
                "email": "user@gmail.com",
                "password2": "user1234",
            },
            {
                "username": "User",
                "email": "user@gmail.com",
                "password": "user1234",
            },
        ]

        for d in data:
            response = self.client.post(self.url, d)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
