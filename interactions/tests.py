from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Mention
from tweets.models import Tweet


# Create your tests here.
User = get_user_model()


class TestListMentions(APITestCase):
    def setUp(self):
        self.url = reverse("mentions")
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@gmail.com", password="user1234"
        )
        unique_content = f"This is a tweet mentioning @user"
        self.tweet = Tweet.objects.create(user=self.user2, content=unique_content)
        tweet_content_type = ContentType.objects.get_for_model(Tweet)
        self.mention, created = Mention.objects.get_or_create(
            actor=self.user2,
            mentioned_user=self.user,
            content_type=tweet_content_type,
            content_id=self.tweet.id,
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_list_mentions_success(self):
        self.authenticate()
        response = self.client.get(self.url)
        mention_data = response.data["results"][0]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mention_data["actor"], self.user2.username)

    def test_list_mentions_with_search(self):
        self.authenticate()

        # Test search by username
        response = self.client.get(f"{self.url}?search={self.user2.username}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["actor"], self.user2.username)

        # Test search by content_type
        response = self.client.get(f"{self.url}?search=tweet")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["content_object"], "tweet")

        # Test search with no results
        response = self.client.get(f"{self.url}?search=No-Thing")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
