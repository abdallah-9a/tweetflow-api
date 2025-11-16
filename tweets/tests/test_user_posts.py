from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet, Retweet
from accounts.models import User


class TestUserPosts(APITestCase):
    """Test suite for user posts endpoint (tweets + retweets)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="user@gmail.com", password="user1234"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@gmail.com", password="user1234"
        )
        self.url = reverse("user-posts", kwargs={"username": self.user.username})

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def test_get_user_posts_success(self):
        self.authenticate()
        # Create tweets
        Tweet.objects.create(user=self.user, content="First tweet")
        Tweet.objects.create(user=self.user, content="Second tweet")

        # Create retweet
        other_tweet = Tweet.objects.create(user=self.other_user, content="Other tweet")
        Retweet.objects.create(user=self.user, tweet=other_tweet)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 3)

    def test_user_posts_includes_engagement_metrics(self):
        self.authenticate()
        tweet = Tweet.objects.create(user=self.user, content="Tweet")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tweet_data = response.data["results"][0]

        self.assertEqual(tweet_data["likes_count"], 0)
        self.assertEqual(tweet_data["comments_count"], 0)
        self.assertEqual(tweet_data["retweets_count"], 0)
        self.assertFalse(tweet_data["is_liked"])
        self.assertFalse(tweet_data["is_retweeted"])

    def test_user_posts_pagination(self):
        """Pagination works correctly"""
        self.authenticate()
        # Create 15 tweets
        for i in range(15):
            Tweet.objects.create(user=self.user, content=f"Tweet {i}")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 15)
        self.assertEqual(len(response.data["results"]), 10)  # PAGE_SIZE=10

    def test_user_posts_nonexistent_user(self):
        self.authenticate()
        url = reverse("user-posts", kwargs={"username": "nonexistent"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_posts_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_posts_empty_list(self):
        self.authenticate()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_user_posts_sorted_by_created_at(self):
        self.authenticate()
        tweet1 = Tweet.objects.create(user=self.user, content="First")
        tweet2 = Tweet.objects.create(user=self.user, content="Second")
        tweet3 = Tweet.objects.create(user=self.user, content="Third")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        # Newest first
        self.assertEqual(results[0]["id"], tweet3.pk)
        self.assertEqual(results[1]["id"], tweet2.pk)
        self.assertEqual(results[2]["id"], tweet1.pk)
