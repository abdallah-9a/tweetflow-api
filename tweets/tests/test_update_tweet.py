from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet
from accounts.models import User
from unittest.mock import patch


class TestUpdateTweet(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="author", email="author@example.com", password="pass1234"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="pass1234"
        )

        self.tweet = Tweet.objects.create(content="This is a tweet", user=self.author)
        self.url = reverse("tweet-detail", kwargs={"pk": self.tweet.id})

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_update_tweet_success_within_window(self):
        self.authenticate(self.author)
        data = {"content": "Updated Tweet"}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("content"), "Updated Tweet")

    def test_update_tweet_forbidden_outside_window(self):
        self.authenticate(self.author)

        Tweet.objects.filter(pk=self.tweet.pk).update(
            created_at=timezone.now() - timezone.timedelta(minutes=16)
        )

        data = {"content": "Late Update"}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_tweet_unauthenticated(self):
        payload = {"content": "Updated Tweet"}
        response = self.client.patch(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_tweet_not_author(self):
        self.authenticate(self.other)
        data = {"content": "Hacked Update"}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_tweet_validation_empty_payload(self):
        self.authenticate(self.author)
        response = self.client.patch(self.url, {})
        self.assertIn(
            response.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST)
        )
