from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet, Retweet
from accounts.models import User


class TestRetweetEndpoints(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(
            content="Original tweet", user=self.other_user
        )
        self.url = reverse("retweet", kwargs={"pk": self.tweet.pk})

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    # POST - Create Retweet Tests
    def test_retweet_success(self):
        """User can retweet a tweet"""
        self.authenticate()
        response = self.client.post(self.url, {"quote": "Great post!"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Retweet.objects.filter(user=self.user, tweet=self.tweet).exists()
        )

    def test_retweet_without_quote(self):
        self.authenticate()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["quote"])

    def test_retweet_duplicate_prevented(self):
        self.authenticate()
        self.client.post(self.url)  # First retweet

        response = self.client.post(self.url)  # Second retweet
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        # Error can be a list or string depending on serializer
        error_value = response.data["error"]
        if isinstance(error_value, list):
            self.assertEqual(error_value[0], "already_retweeted")
        else:
            self.assertEqual(error_value, "already_retweeted")
        self.assertEqual(
            Retweet.objects.filter(user=self.user, tweet=self.tweet).count(), 1
        )

    def test_retweet_own_tweet(self):
        self.authenticate()
        own_tweet = Tweet.objects.create(content="My tweet", user=self.user)
        url = reverse("retweet", kwargs={"pk": own_tweet.pk})

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retweet_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retweet_nonexistent_tweet(self):
        self.authenticate()
        url = reverse("retweet", kwargs={"pk": 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # DELETE - Unretweet Tests
    def test_unretweet_success(self):
        self.authenticate()
        Retweet.objects.create(user=self.user, tweet=self.tweet)

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Retweet.objects.filter(user=self.user, tweet=self.tweet).exists()
        )

    def test_unretweet_not_retweeted(self):
        self.authenticate()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unretweet_unauthenticated(self):
        Retweet.objects.create(user=self.user, tweet=self.tweet)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # GET - List Retweets Tests
    def test_list_retweets(self):
        # Create retweets from multiple users
        Retweet.objects.create(user=self.user, tweet=self.tweet, quote="Nice!")
        Retweet.objects.create(user=self.other_user, tweet=self.tweet)

        self.authenticate()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_retweets_empty(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_list_retweets_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
