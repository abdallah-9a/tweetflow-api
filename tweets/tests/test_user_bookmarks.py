from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from tweets.models import Tweet, Bookmark, Like, Retweet


class TestUserBookmarksEndpoint(APITestCase):
    """Tests for GET /bookmarks/ endpoint to list user's bookmarked tweets"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@gmail.com", password="user1234"
        )
        self.tweet1 = Tweet.objects.create(content="First tweet", user=self.other_user)
        self.tweet2 = Tweet.objects.create(content="Second tweet", user=self.other_user)
        self.tweet3 = Tweet.objects.create(content="Third tweet", user=self.user)
        self.url = reverse("user-bookmarks")

    def authenticate(self, user=None):
        self.client.force_authenticate(user=self.user)

    def test_list_bookmarks_empty(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_list_bookmarks_success(self):
        self.authenticate()
        Bookmark.objects.create(user=self.user, tweet=self.tweet1)
        Bookmark.objects.create(user=self.user, tweet=self.tweet2)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # Verify structure of first bookmark
        first_bookmark = response.data["results"][0]
        self.assertIn("id", first_bookmark)
        self.assertIn("author", first_bookmark)
        self.assertIn("content", first_bookmark)
        self.assertIn("likes_count", first_bookmark)
        self.assertIn("comments_count", first_bookmark)
        self.assertIn("retweets_count", first_bookmark)
        self.assertIn("is_liked", first_bookmark)
        self.assertIn("is_retweeted", first_bookmark)
        self.assertIn("is_bookmarked", first_bookmark)
        self.assertIn("bookmarked_at", first_bookmark)
        self.assertTrue(first_bookmark["is_bookmarked"])

    def test_list_bookmarks_ordered_by_most_recent(self):
        """Bookmarks are ordered by most recently bookmarked first"""
        self.authenticate()
        bookmark1 = Bookmark.objects.create(user=self.user, tweet=self.tweet1)
        bookmark2 = Bookmark.objects.create(user=self.user, tweet=self.tweet2)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        # Most recent bookmark should be first
        self.assertEqual(results[0]["id"], self.tweet2.id)
        self.assertEqual(results[1]["id"], self.tweet1.id)

    def test_list_bookmarks_only_own_bookmarks(self):
        self.authenticate()
        Bookmark.objects.create(user=self.user, tweet=self.tweet1)
        Bookmark.objects.create(user=self.other_user, tweet=self.tweet2)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.tweet1.id)

    def test_list_bookmarks_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_bookmarks_pagination(self):
        self.authenticate()
        # Create 15 bookmarks (default page size is 10)
        for i in range(15):
            tweet = Tweet.objects.create(content=f"Tweet {i}", user=self.other_user)
            Bookmark.objects.create(user=self.user, tweet=tweet)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(response.data["count"], 15)
        self.assertIsNotNone(response.data["next"])
