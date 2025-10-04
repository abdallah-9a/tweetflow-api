from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet
from accounts.models import User

# Create your tests here.


class TestDeleteTweet(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@gmail.com", password="user222"
        )
        self.tweet = Tweet.objects.create(content="Tweet 1", user=self.user)
        self.url = reverse("tweet-detail", kwargs={"pk": self.tweet.pk})

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_delete_tweet_success(self):
        self.authenticate(self.user)

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_tweet_not_found(self):
        self.authenticate(self.user)
        url = reverse("tweet-detail", kwargs={"pk": 10})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_tweet_not_author(self):
        self.authenticate(self.user2)

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_tweet_unauthenticated(self):

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
