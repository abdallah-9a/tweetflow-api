from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet
from accounts.models import User

# Create your tests here.


class TestRetrieveTweet(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(content="Tweet 1", user=self.user)
        self.url = reverse("tweet-detail", kwargs={"pk": self.tweet.pk})

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tweet_success(self):
        self.authenticate()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_test_not_found(self):
        self.authenticate()
        url = reverse("tweet-detail", kwargs={"pk": 10})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_tweet_unauthenticated(self):

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
