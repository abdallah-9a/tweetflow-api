from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class TestDeleteAccount(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.url = reverse("delete-account")

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    # --- Success ---

    def test_delete_account_success(self):
        self.authenticate()
        response = self.client.delete(self.url, {"password": "user1234"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("permanently deleted", response.data["detail"].lower())
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_account_removes_profile(self):
        self.authenticate()
        profile_pk = self.user.profile.pk
        self.client.delete(self.url, {"password": "user1234"})

        from accounts.models import Profile

        self.assertFalse(Profile.objects.filter(pk=profile_pk).exists())

    def test_delete_account_removes_related_data(self):
        """Deleting a user should cascade-delete their tweets."""
        from tweets.models import Tweet

        self.authenticate()
        tweet = Tweet.objects.create(user=self.user, content="will be deleted")
        tweet_pk = tweet.pk

        self.client.delete(self.url, {"password": "user1234"})

        self.assertFalse(Tweet.objects.filter(pk=tweet_pk).exists())

    # --- Invalid password ---

    def test_delete_account_wrong_password(self):
        self.authenticate()
        response = self.client.delete(self.url, {"password": "wrongpass"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_account_missing_password(self):
        self.authenticate()
        response = self.client.delete(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    # --- Unauthenticated ---

    def test_delete_account_unauthenticated(self):
        response = self.client.delete(self.url, {"password": "user1234"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
