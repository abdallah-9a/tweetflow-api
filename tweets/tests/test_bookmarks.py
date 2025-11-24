from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from tweets.models import Tweet, Bookmark


class TestBookmarkEndpoints(APITestCase):
    """Tests for bookmark add/remove endpoint (POST/DELETE)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(content="Test tweet", user=self.other_user)
        self.url = reverse("bookmark", kwargs={"pk": self.tweet.pk})

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    # POST - Add Bookmark Tweet
    def test_bookmark_tweet_success(self):
        self.authenticate()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Bookmark.objects.filter(user=self.user, tweet=self.tweet).exists()
        )
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Tweet added to your bookmarks")

    def test_bookmark_tweet_duplicate_prevented(self):
        self.authenticate()
        self.client.post(self.url)
        response = self.client.post(self.url)  # second bookmark
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "already_bookmarked")

    def test_bookmark_tweet_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bookmark_nonexistent_tweet(self):
        self.authenticate()
        url = reverse("bookmark", kwargs={"pk": 999999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # DELETE - Remove Bookmark
    def test_remove_bookmark_success(self):
        self.authenticate()
        Bookmark.objects.create(user=self.user, tweet=self.tweet)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Bookmark.objects.filter(user=self.user, tweet=self.tweet).exists()
        )
        self.assertEqual(response.data["detail"], "Tweet removed from your bookmarks")

    def test_remove_bookmark_not_exists(self):
        self.authenticate()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_bookmark_unauthenticated(self):
        Bookmark.objects.create(user=self.user, tweet=self.tweet)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
