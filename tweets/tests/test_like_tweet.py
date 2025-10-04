from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet, Like
from accounts.models import User


class TestLikeTweet(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(content="tweet", user=self.user)
        self.url = reverse("like-tweet", kwargs={"pk": self.tweet.pk})

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_like_tweet_success(self):
        self.authenticate()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Like.objects.filter(user=self.user, tweet=self.tweet).exists())

    def test_like_same_tweet_twice(self):
        self.authenticate()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Twice
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_like_tweet_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
