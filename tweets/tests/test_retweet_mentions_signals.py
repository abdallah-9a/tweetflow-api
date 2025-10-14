from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from tweets.models import Retweet, Tweet
from interactions.models import Mention


User = get_user_model()


class TestRetweetMentions(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@gmail.com", password="user1234"
        )

    def test_mention_success(self):
        tweet = Tweet.objects.create(user=self.user, content="Original tweet")
        retweet = Retweet.objects.create(
            user=self.user, tweet=tweet, quote="Hello @user2"
        )
        self.assertTrue(
            Mention.objects.filter(
                mentioned_user=self.user2, content_id=retweet.id
            ).exists()
        )

    def test_mention_multiple_users(self):
        user3 = User.objects.create_user(
            username="user3", email="user3@gmail.com", password="user1234"
        )
        tweet = Tweet.objects.create(user=self.user, content="Original tweet")
        retweet = Retweet.objects.create(
            user=self.user, tweet=tweet, quote="Hello @user2 and @user3"
        )

        self.assertTrue(
            Mention.objects.filter(
                mentioned_user=self.user2, content_id=retweet.id
            ).exists()
        )
        self.assertTrue(
            Mention.objects.filter(mentioned_user=user3, content_id=retweet.id).exists()
        )
        self.assertEqual(Mention.objects.filter(content_id=retweet.id).count(), 2)

    def test_mention_nonexistent_user(self):
        tweet = Tweet.objects.create(user=self.user, content="Original tweet")
        retweet = Retweet.objects.create(
            user=self.user, tweet=tweet, quote="Hello @no-user"
        )
        self.assertEqual(Mention.objects.filter(content_id=retweet.id).count(), 0)

    def test_mention_case_insensitivity(self):
        tweet = Tweet.objects.create(user=self.user, content="Original tweet")
        retweet = Retweet.objects.create(
            user=self.user, tweet=tweet, quote="Hello @USER2"
        )
        self.assertFalse(Mention.objects.filter(mentioned_user=self.user2).exists())

    def test_mention_self(self):
        tweet = Tweet.objects.create(user=self.user, content="Original tweet")
        retweet = Retweet.objects.create(
            user=self.user, tweet=tweet, quote="I'm mentioning myself @user"
        )
        self.assertFalse(
            Mention.objects.filter(
                mentioned_user=self.user, content_id=retweet.id
            ).exists()
        )
