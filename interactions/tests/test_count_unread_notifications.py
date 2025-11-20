from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from interactions.models import Notification

User = get_user_model()


class TestCountUnreadNotifications(APITestCase):
    def setUp(self):
        self.url = reverse("notifications-count")
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.sender = User.objects.create_user(
            username="sender", email="sender@gmail.com", password="user1234"
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_count_unread_notifications_success(self):
        self.authenticate()
        # Create some unread notifications
        Notification.objects.create(
            sender=self.sender, receiver=self.user, verb="followed", is_read=False
        )
        Notification.objects.create(
            sender=self.sender, receiver=self.user, verb="liked", is_read=False
        )
        # Create a read notification
        Notification.objects.create(
            sender=self.sender, receiver=self.user, verb="commented", is_read=True
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("unread_count", response.data)
        # 3 = 1 welcome notification (auto-created on user registration) + 2 test notifications
        self.assertEqual(response.data["unread_count"], 3)

    def test_count_unread_notifications_zero(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 1 = welcome notification (auto-created on user registration)
        self.assertEqual(response.data["unread_count"], 1)

    def test_count_unread_notifications_only_own_notifications(self):
        self.authenticate()
        other_user = User.objects.create_user(
            username="other", email="other@gmail.com", password="user1234"
        )
        # Create notification for current user
        Notification.objects.create(
            sender=self.sender, receiver=self.user, verb="followed", is_read=False
        )
        # Create notification for other user
        Notification.objects.create(
            sender=self.sender, receiver=other_user, verb="followed", is_read=False
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 2 = 1 welcome notification (auto-created on user registration) + 1 test notification
        self.assertEqual(response.data["unread_count"], 2)

    def test_count_unread_notifications_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
