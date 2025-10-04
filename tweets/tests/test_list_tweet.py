from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet
from accounts.models import User


class TestListTweet(APITestCase):
    def setUp(self):
        self.url = reverse("feed")
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_list_tweet_success(self):
        self.authenticate()
        Tweet.objects.create(user=self.user, content="First tweet")
        Tweet.objects.create(user=self.user, content="Second tweet")
        Tweet.objects.create(user=self.user, content="Third tweet")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_tweet_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_pagination(self):
        self.authenticate()

        # Create tweets to test pagination
        for i in range(15):
            Tweet.objects.create(user=self.user, content=f"Tweet {i}")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(response.data["count"], 15)
        self.assertIsInstance(response.data["results"], list)

    def test_list_tweet_empty_list(self):
        self.authenticate()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["results"]), 0)
