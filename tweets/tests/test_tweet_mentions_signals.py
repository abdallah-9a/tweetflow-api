from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from django.test import override_settings
from tweets.models import Tweet
from interactions.models import Mention


User = get_user_model()

@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class TestTweetMentions(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@gmail.com", password="user1234"
        )

    def test_mention_success(self):
        with self.captureOnCommitCallbacks(execute=True):
            tweet = Tweet.objects.create(user=self.user, content="Hello @user2")
        self.assertTrue(
            Mention.objects.filter(
                mentioned_user=self.user2, content_id=tweet.id
            ).exists()
        )

    def test_mention_multiple_users(self):
        user3 = User.objects.create_user(
            username="user3", email="user3@gmail.com", password="user1234"
        )
        with self.captureOnCommitCallbacks(execute=True):
            tweet = Tweet.objects.create(user=self.user, content="Hello @user2 and @user3")

        self.assertTrue(
            Mention.objects.filter(
                mentioned_user=self.user2, content_id=tweet.id
            ).exists()
        )
        self.assertTrue(
            Mention.objects.filter(mentioned_user=user3, content_id=tweet.id).exists()
        )
        self.assertEqual(Mention.objects.filter(content_id=tweet.id).count(), 2)

    def test_mention_nonexistent_user(self):
        with self.captureOnCommitCallbacks(execute=True):
            tweet = Tweet.objects.create(user=self.user, content="Hello @no-user")
        self.assertEqual(Mention.objects.filter(content_id=tweet.id).count(), 0)

    def test_mention_case_insensitivity(self):
        with self.captureOnCommitCallbacks(execute=True):
            tweet = Tweet.objects.create(user=self.user, content="Hello @USER2")
        self.assertFalse(Mention.objects.filter(mentioned_user=self.user2).exists())

    def test_mention_self(self):
        with self.captureOnCommitCallbacks(execute=True):
            tweet = Tweet.objects.create(
                user=self.user, content="I'm mentioning myself @user"
            )
        self.assertFalse(
            Mention.objects.filter(
                mentioned_user=self.user, content_id=tweet.id
            ).exists()
        )
