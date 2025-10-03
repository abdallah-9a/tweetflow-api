from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class SendResetEmailAPITestCase(APITestCase):
    def setUp(self):
        self.url = reverse("send-reset-password-email")
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )

    def test_request_password_reset_success_send_email(self):
        data = {"email": "user@gmail.com"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_request_password_reset_with_missing_email_field(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_password_reset_with_invalid_email_field(self):
        email = {"email": "invalid-email"}
        response = self.client.post(self.url, email)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResetPasswordAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.data = {"password": "NewPassword123", "password2": "NewPassword123"}

    def test_password_reset_confirm_success_changes_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse("reset-password", kwargs={"uid": uid, "token": token})

        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_confirm_with_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = reverse("reset-password", kwargs={"uid": uid, "token": "invalid-token"})
        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_with_invalid_uid(self):
        token = default_token_generator.make_token(self.user)
        url = reverse("reset-password", kwargs={"uid": "invalid-uid", "token": token})
        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_with_mismatched_passwords(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse("reset-password", kwargs={"uid": uid, "token": token})

        data = {"password": "NewPassword123", "password2": "DifferentPassword456"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_with_expired_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        # Change password to invalidate the token
        self.user.set_password("changed_password")
        self.user.save()

        url = reverse("reset-password", kwargs={"uid": uid, "token": token})
        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
