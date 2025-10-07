from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet, Comment
from accounts.models import User


class TestCreateComment(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(user=self.user, content="Tweet")
        self.url = reverse("comment", kwargs={"pk": self.tweet.pk})
        self.data = {"content": "Comment"}

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_create_comment_success(self):
        self.authenticate()
        response = self.client.post(self.url, {"content": "comment"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Comment.objects.filter(user=self.user, tweet=self.tweet).exists()
        )

    def test_create_comment_without_data(self):
        self.authenticate()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_comment_unauthenticated(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_comment_with_not_found_tweet(self):
        self.authenticate()
        url = reverse("comment", kwargs={"pk": 10})
        response = self.client.post(url, self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reply_to_comment_success(self):
        self.authenticate()
        parent_comment = Comment.objects.create(
            user=self.user, tweet=self.tweet, content="Parent"
        )

        response = self.client.post(
            self.url, {"content": "Reply", "parent": parent_comment.pk}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Comment.objects.filter(
                user=self.user, tweet=self.tweet, parent=parent_comment
            ).exists()
        )

    def test_reply_to_comment_from_other_tweet_fails(self):
        self.authenticate()
        other_tweet = Tweet.objects.create(user=self.user, content="Other tweet")
        other_comment = Comment.objects.create(
            user=self.user, tweet=other_tweet, content="Other comment"
        )

        response = self.client.post(
            self.url,
            {"content": "Reply", "parent": other_comment.pk},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("error")[0], "invalid_parent")
