from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet, Like
from accounts.models import User


class TestLikeEndpoints(APITestCase):
    """Test like endpoints (GET/POST/DELETE on single URL)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(content="Test tweet", user=self.user)
        self.url = reverse("like-tweet", kwargs={"pk": self.tweet.pk})

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    # POST - Like Tweet Tests
    def test_like_tweet_success(self):
        """User can like a tweet"""
        self.authenticate()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Like.objects.filter(user=self.user, tweet=self.tweet).exists())

    def test_like_tweet_duplicate_prevented(self):
        self.authenticate()
        self.client.post(self.url)  # First like

        response = self.client.post(self.url)  # Second like
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        error_value = response.data["error"]
        self.assertEqual(error_value[0], "already_liked")

    def test_like_tweet_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_like_nonexistent_tweet(self):
        self.authenticate()
        url = reverse("like-tweet", kwargs={"pk": 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # DELETE - Unlike Tweet Tests
    def test_unlike_tweet_success(self):
        self.authenticate()
        Like.objects.create(user=self.user, tweet=self.tweet)

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Like.objects.filter(user=self.user, tweet=self.tweet).exists())

    def test_unlike_tweet_not_liked(self):
        self.authenticate()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unlike_tweet_unauthenticated(self):
        Like.objects.create(user=self.user, tweet=self.tweet)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # GET - List Likes Tests (Author Only)
    def test_list_likes_as_author(self):
        # Create likes from multiple users
        Like.objects.create(user=self.other_user, tweet=self.tweet)
        Like.objects.create(user=self.user, tweet=self.tweet)

        self.authenticate(self.user)  # Authenticate as tweet author
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_likes_not_author(self):
        Like.objects.create(user=self.user, tweet=self.tweet)

        self.authenticate(self.other_user)  # Authenticate as different user
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)

    def test_list_likes_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
