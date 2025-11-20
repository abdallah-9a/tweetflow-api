from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
from rest_framework import status
from interactions.models import Notification
from tweets.models import Tweet
from relationships.models import Follow

User = get_user_model()


class TestMarkAllNotificationsRead(APITestCase):
    def setUp(self):
        self.url = reverse("mark-all-read")
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.sender = User.objects.create_user(
            username="sender", email="sender@gmail.com", password="user1234"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@gmail.com", password="user1234"
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_mark_all_notifications_read_success(self):
        self.authenticate()
        tweet1 = Tweet.objects.create(user=self.user, content="Test tweet 1")
        tweet_ct = ContentType.objects.get_for_model(Tweet)
        notif1 = Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="liked",
            is_read=False,
            content_type=tweet_ct,
            content_id=tweet1.id,
        )
        tweet2 = Tweet.objects.create(user=self.user, content="Test tweet 2")
        notif2 = Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="commented",
            is_read=False,
            content_type=tweet_ct,
            content_id=tweet2.id,
        )
        tweet3 = Tweet.objects.create(user=self.user, content="Test tweet 3")
        notif3 = Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="retweeted",
            is_read=False,
            content_type=tweet_ct,
            content_id=tweet3.id,
        )

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("updated_count", response.data)
        # 4 = 1 welcome notification (auto-created) + 3 test notifications
        self.assertEqual(response.data["updated_count"], 4)

        # all are now read
        notif1.refresh_from_db()
        notif2.refresh_from_db()
        notif3.refresh_from_db()
        self.assertTrue(notif1.is_read)
        self.assertTrue(notif2.is_read)
        self.assertTrue(notif3.is_read)

    def test_mark_all_notifications_read_mixed_status(self):
        self.authenticate()
        # Create some read and some unread
        tweet1 = Tweet.objects.create(user=self.user, content="Test tweet 1")
        tweet_ct = ContentType.objects.get_for_model(Tweet)
        notif1 = Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="liked",
            is_read=True,
            content_type=tweet_ct,
            content_id=tweet1.id,
        )
        tweet2 = Tweet.objects.create(user=self.user, content="Test tweet 2")
        notif2 = Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="commented",
            is_read=False,
            content_type=tweet_ct,
            content_id=tweet2.id,
        )
        tweet3 = Tweet.objects.create(user=self.user, content="Test tweet 3")
        notif3 = Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="retweeted",
            is_read=False,
            content_type=tweet_ct,
            content_id=tweet3.id,
        )

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 3 = 1 welcome notification (auto-created) + 2 unread test notifications
        self.assertEqual(response.data["updated_count"], 3)

    def test_mark_all_notifications_read_no_unread(self):
        self.authenticate()
        tweet = Tweet.objects.create(user=self.user, content="Test tweet")
        tweet_ct = ContentType.objects.get_for_model(Tweet)
        Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="liked",
            is_read=True,
            content_type=tweet_ct,
            content_id=tweet.id,
        )

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 1 = welcome notification (auto-created and unread)
        self.assertEqual(response.data["updated_count"], 1)

    def test_mark_all_notifications_read_only_affects_own_notifications(self):
        self.authenticate()
        # Create notifications for current user
        tweet1 = Tweet.objects.create(user=self.user, content="Test tweet 1")
        tweet_ct = ContentType.objects.get_for_model(Tweet)
        notif1 = Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="liked",
            is_read=False,
            content_type=tweet_ct,
            content_id=tweet1.id,
        )
        # Create notification for other user
        tweet2 = Tweet.objects.create(user=self.other_user, content="Test tweet 2")
        notif2 = Notification.objects.create(
            sender=self.sender,
            receiver=self.other_user,
            verb="liked",
            is_read=False,
            content_type=tweet_ct,
            content_id=tweet2.id,
        )

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 2 = 1 welcome notification (auto-created) + 1 test notification
        self.assertEqual(response.data["updated_count"], 2)

        # Verify only user's notification was updated
        notif1.refresh_from_db()
        notif2.refresh_from_db()
        self.assertTrue(notif1.is_read)
        self.assertFalse(notif2.is_read)  # Other user's notification unchanged

    def test_mark_all_notifications_read_empty(self):
        self.authenticate()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 1 = welcome notification (auto-created on user registration)
        self.assertEqual(response.data["updated_count"], 1)

    def test_mark_all_notifications_read_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
