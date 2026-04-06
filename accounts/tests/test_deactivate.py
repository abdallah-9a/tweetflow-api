from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from interactions.models import Notification


class TestDeactivateAccount(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.url = reverse("deactivate")

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    # --- Success ---

    @patch("accounts.views.send_email_task.delay")
    def test_deactivate_success(self, mock_delay):
        self.authenticate()
        response = self.client.post(self.url, {"password": "user1234"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("deactivated", response.data["detail"].lower())

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(self.user.profile.status, "deactive")
        mock_delay.assert_called_once()

    @patch("accounts.views.send_email_task.delay")
    def test_deactivate_sends_email(self, mock_delay):
        self.authenticate()
        self.client.post(self.url, {"password": "user1234"})

        mock_delay.assert_called_once()
        call_args = mock_delay.call_args.args[0]
        self.assertEqual(call_args["to_email"], self.user.email)

    @patch("accounts.views.send_email_task.delay")
    def test_deactivate_creates_notification(self, mock_delay):
        self.authenticate()
        self.client.post(self.url, {"password": "user1234"})

        self.assertTrue(
            Notification.objects.filter(
                receiver=self.user, verb="deactivated"
            ).exists()
        )
        mock_delay.assert_called_once()

    # --- Invalid password ---

    def test_deactivate_wrong_password(self):
        self.authenticate()
        response = self.client.post(self.url, {"password": "wrongpass"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.profile.status, "active")

    def test_deactivate_missing_password(self):
        self.authenticate()
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Already deactivated ---

    @patch("accounts.views.send_email_task.delay")
    def test_deactivate_already_deactivated(self, mock_delay):
        self.authenticate()
        self.user.profile.status = "deactive"
        self.user.is_active = False
        self.user.save()
        self.user.profile.save()

        response = self.client.post(self.url, {"password": "user1234"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("already deactivated", response.data["detail"].lower())
        mock_delay.assert_not_called()

    # --- Unauthenticated ---

    def test_deactivate_unauthenticated(self):
        response = self.client.post(self.url, {"password": "user1234"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
