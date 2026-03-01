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

    @patch("accounts.views.Util.send_email")
    def test_deactivate_success(self, mock_email):
        self.authenticate()
        response = self.client.post(self.url, {"password": "user1234"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("deactivated", response.data["detail"].lower())

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(self.user.profile.status, "deactive")

    @patch("accounts.views.Util.send_email")
    def test_deactivate_sends_email(self, mock_email):
        self.authenticate()
        self.client.post(self.url, {"password": "user1234"})

        mock_email.assert_called_once()
        call_args = mock_email.call_args[0][0]
        self.assertEqual(call_args["to_email"], self.user.email)

    @patch("accounts.views.Util.send_email")
    def test_deactivate_creates_notification(self, mock_email):
        self.authenticate()
        self.client.post(self.url, {"password": "user1234"})

        self.assertTrue(
            Notification.objects.filter(
                receiver=self.user, verb="deactivated"
            ).exists()
        )

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

    @patch("accounts.views.Util.send_email")
    def test_deactivate_already_deactivated(self, mock_email):
        self.authenticate()
        self.user.profile.status = "deactive"
        self.user.is_active = False
        self.user.save()
        self.user.profile.save()

        response = self.client.post(self.url, {"password": "user1234"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("already deactivated", response.data["detail"].lower())
        mock_email.assert_not_called()

    # --- Unauthenticated ---

    def test_deactivate_unauthenticated(self):
        response = self.client.post(self.url, {"password": "user1234"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
