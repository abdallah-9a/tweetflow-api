from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet, Like
from accounts.models import User


class TestUnlikeTweet(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(content="tweet", user=self.user)
        self.url = reverse("unlike-tweet", kwargs={"pk": self.tweet.pk})

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def like_tweet(self):
        self.client.post(reverse("like-tweet", kwargs={"pk": self.tweet.pk}))

    def test_unlike_tweet_success(self):
        self.authenticate()
        self.like_tweet()

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Like.objects.filter(user=self.user, tweet=self.tweet).exists())

    def test_unlike_tweet_not_liked_before(self):
        self.authenticate()

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unlike_tweet_unauthenticated(self):
        self.like_tweet()

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
