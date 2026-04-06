from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from interactions.models import Notification


class TestActivateAccount(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.url = reverse("activate")
        # Pre-deactivate the user for most tests
        self.user.is_active = False
        self.user.profile.status = "deactive"
        self.user.save()
        self.user.profile.save()

    # --- Success ---

    @patch("accounts.views.send_email_task.delay")
    def test_activate_success(self, mock_delay):
        response = self.client.post(
            self.url, {"username": "user", "password": "user1234"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("reactivated", response.data["detail"].lower())

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.profile.status, "active")
        mock_delay.assert_called_once()

    @patch("accounts.views.send_email_task.delay")
    def test_activate_sends_email(self, mock_delay):
        self.client.post(self.url, {"username": "user", "password": "user1234"})

        mock_delay.assert_called_once()
        call_args = mock_delay.call_args.args[0]
        self.assertEqual(call_args["to_email"], self.user.email)

    @patch("accounts.views.send_email_task.delay")
    def test_activate_creates_notification(self, mock_delay):
        self.client.post(self.url, {"username": "user", "password": "user1234"})

        self.assertTrue(
            Notification.objects.filter(
                receiver=self.user, verb="reactivated"
            ).exists()
        )
        mock_delay.assert_called_once()

    # --- Invalid credentials ---

    def test_activate_wrong_password(self):
        response = self.client.post(
            self.url, {"username": "user", "password": "wrongpass"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_activate_nonexistent_user(self):
        response = self.client.post(
            self.url, {"username": "ghost", "password": "user1234"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_activate_missing_username(self):
        response = self.client.post(self.url, {"password": "user1234"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activate_missing_password(self):
        response = self.client.post(self.url, {"username": "user"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Already active ---

    @patch("accounts.views.send_email_task.delay")
    def test_activate_already_active(self, mock_delay):
        # Re-activate user first
        self.user.is_active = True
        self.user.profile.status = "active"
        self.user.save()
        self.user.profile.save()

        response = self.client.post(
            self.url, {"username": "user", "password": "user1234"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("already active", response.data["detail"].lower())
        mock_delay.assert_not_called()

    # --- No auth required ---

    @patch("accounts.views.send_email_task.delay")
    def test_activate_requires_no_authentication(self, mock_delay):
        """Activate endpoint should be accessible without JWT since the user is deactivated."""
        response = self.client.post(
            self.url, {"username": "user", "password": "user1234"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_delay.assert_called_once()
