from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet
from accounts.models import User


class TestListTweet(APITestCase):
    def setUp(self):
        cache.clear()
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

    def test_feed_search(self):
        self.authenticate()
        Tweet.objects.create(user=self.user, content="Python is great")
        Tweet.objects.create(user=self.user, content="Django is awesome")
        
        response = self.client.get(self.url, {"search": "Python"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["content"], "Python is great")

    def test_feed_cache_invalidation(self):
        self.authenticate()
        Tweet.objects.create(user=self.user, content="Old Tweet")
        self.client.get(self.url)
        self.client.post(reverse("create-tweet"), {"content": "New Tweet"})
        
        response = self.client.get(self.url)
        self.assertEqual(response.data["results"][0]["content"], "New Tweet")
