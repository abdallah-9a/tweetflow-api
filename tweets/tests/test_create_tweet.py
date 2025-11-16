from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet
from accounts.models import User


class TestCreateTweet(APITestCase):
    """Test suite for tweet creation endpoint"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.url = reverse("create-tweet")

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_create_tweet_with_content_success(self):
        self.authenticate()
        data = {"content": "This is a test tweet"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Tweet.objects.filter(
                user=self.user, content="This is a test tweet"
            ).exists()
        )
        self.assertIn("id", response.data)
        self.assertEqual(response.data["content"], "This is a test tweet")

    def test_create_tweet_empty_content_and_no_image_fails(self):
        self.authenticate()
        data = {"content": ""}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Can be either Django's default error or custom validation error
        self.assertTrue("error" in response.data or "content" in response.data)
        self.assertFalse(Tweet.objects.filter(user=self.user).exists())

    def test_create_tweet_no_data_fails(self):
        self.authenticate()
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Can be either Django's default error or custom validation error
        self.assertTrue("error" in response.data or "content" in response.data)
        self.assertFalse(Tweet.objects.filter(user=self.user).exists())

    def test_create_tweet_content_exceeds_max_length(self):
        self.authenticate()
        long_content = "a" * 1001  # 1001 characters
        data = {"content": long_content}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Tweet.objects.filter(user=self.user).exists())

    def test_create_tweet_content_exactly_1000_chars_success(self):
        self.authenticate()
        content = "a" * 1000  # Exactly 1000 characters
        data = {"content": content}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Tweet.objects.filter(user=self.user, content=content).exists())

    def test_create_tweet_whitespace_only_fails(self):
        self.authenticate()
        data = {"content": "   "}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Can be either Django's default error or custom validation error
        self.assertTrue("error" in response.data or "content" in response.data)

    def test_create_tweet_unauthenticated(self):
        data = {"content": "Test tweet"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Tweet.objects.exists())

    def test_create_tweet_response_structure(self):
        self.authenticate()
        data = {"content": "Test tweet"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("content", response.data)
        self.assertIn("image", response.data)
        self.assertEqual(response.data["content"], "Test tweet")
        self.assertIsNone(response.data["image"])
