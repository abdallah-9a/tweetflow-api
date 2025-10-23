from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet, Comment
from accounts.models import User


class TestListComment(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(user=self.user, content="Tweet")
        self.url = reverse("comments", kwargs={"pk": self.tweet.pk})

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_list_comments_success(self):
        self.authenticate()
        Comment.objects.create(user=self.user, tweet=self.tweet, content="First")
        Comment.objects.create(user=self.user, tweet=self.tweet, content="Second")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_comments_empty(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_list_comments_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_comments_missing_tweet(self):
        self.authenticate()
        missing_url = reverse("comments", kwargs={"pk": 999999})
        response = self.client.get(missing_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
