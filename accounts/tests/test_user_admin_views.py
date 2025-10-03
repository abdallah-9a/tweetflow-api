from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class UsersListAPITestCase(APITestCase):
    def setUp(self):
        self.url = reverse("users-list")
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@gmail.com", password="admin1234"
        )
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )

    def authenticate(self, admin=False):
        if admin:
            self.client.force_authenticate(user=self.admin)
        else:
            self.client.force_authenticate(user=self.user)

    def test_admin_can_list_users(self):
        self.authenticate(True)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admin_cant_list_users(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_list_users(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
