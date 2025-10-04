from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet
from accounts.models import User

class TestCreateTweet(APITestCase):
    def setUp(self):
        self.url = reverse("feed")
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.data = {"content": "tweet-content"}

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_create_tweet_success(self):
        self.authenticate()
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_tweet_unauthenticated(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_tweet_without_data(self):
        self.authenticate()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
