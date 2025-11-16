from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet, Like, Comment, Retweet
from accounts.models import User


class TestDeleteTweet(APITestCase):
    """Test suite for tweet deletion endpoint"""

    def setUp(self):
        self.author = User.objects.create_user(
            username="author", email="author@gmail.com", password="user1234"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(user=self.author, content="Test tweet")
        self.url = reverse("tweet-detail", kwargs={"pk": self.tweet.pk})

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.author)

    def test_delete_own_tweet_success(self):
        self.authenticate(self.author)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tweet.objects.filter(pk=self.tweet.pk).exists())

    def test_delete_others_tweet_forbidden(self):
        self.authenticate(self.other_user)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Tweet.objects.filter(pk=self.tweet.pk).exists())

    def test_delete_tweet_unauthenticated(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Tweet.objects.filter(pk=self.tweet.pk).exists())

    def test_delete_nonexistent_tweet(self):
        self.authenticate()
        url = reverse("tweet-detail", kwargs={"pk": 99999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_cascades_to_comments(self):
        self.authenticate(self.author)
        comment = Comment.objects.create(
            user=self.other_user, tweet=self.tweet, content="Comment"
        )

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tweet.objects.filter(pk=self.tweet.pk).exists())
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_delete_cascades_to_likes(self):
        self.authenticate(self.author)
        like = Like.objects.create(user=self.other_user, tweet=self.tweet)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tweet.objects.filter(pk=self.tweet.pk).exists())
        self.assertFalse(Like.objects.filter(pk=like.pk).exists())

    def test_delete_cascades_to_retweets(self):
        self.authenticate(self.author)
        retweet = Retweet.objects.create(user=self.other_user, tweet=self.tweet)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tweet.objects.filter(pk=self.tweet.pk).exists())
        self.assertFalse(Retweet.objects.filter(pk=retweet.pk).exists())
