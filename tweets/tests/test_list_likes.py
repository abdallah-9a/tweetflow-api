from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet, Like
from accounts.models import User


class TestUnlikeTweet(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(content="tweet", user=self.user)
        self.url = reverse("tweet-likes", kwargs={"pk": self.tweet.pk})

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def likes(self):
        for i in range(3):
            user = User.objects.create_user(
                username=f"user{i}", email=f"user{i}@gmail.com", password="user1234"
            )
            self.authenticate(user)
            self.client.post(reverse("like-tweet", kwargs={"pk": self.tweet.pk}))

    def test_list_list_for_tweet(self):
        self.likes()
        self.authenticate(self.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_likes_unauthenticated(self):
        self.likes()
        self.client.force_authenticate()  # Unauthenticated

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_likes_not_author(self):
        self.likes()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
