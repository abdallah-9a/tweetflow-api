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

    @patch("accounts.views.Util.send_email")
    def test_activate_success(self, mock_email):
        response = self.client.post(
            self.url, {"username": "user", "password": "user1234"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("reactivated", response.data["detail"].lower())

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.profile.status, "active")

    @patch("accounts.views.Util.send_email")
    def test_activate_sends_email(self, mock_email):
        self.client.post(self.url, {"username": "user", "password": "user1234"})

        mock_email.assert_called_once()
        call_args = mock_email.call_args[0][0]
        self.assertEqual(call_args["to_email"], self.user.email)

    @patch("accounts.views.Util.send_email")
    def test_activate_creates_notification(self, mock_email):
        self.client.post(self.url, {"username": "user", "password": "user1234"})

        self.assertTrue(
            Notification.objects.filter(
                receiver=self.user, verb="reactivated"
            ).exists()
        )

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

    @patch("accounts.views.Util.send_email")
    def test_activate_already_active(self, mock_email):
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
        mock_email.assert_not_called()

    # --- No auth required ---

    @patch("accounts.views.Util.send_email")
    def test_activate_requires_no_authentication(self, mock_email):
        """Activate endpoint should be accessible without JWT since the user is deactivated."""
        response = self.client.post(
            self.url, {"username": "user", "password": "user1234"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
