from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
from rest_framework import status
from interactions.models import Notification
from tweets.models import Tweet

User = get_user_model()


class TestMarkOneNotificationRead(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.sender = User.objects.create_user(
            username="sender", email="sender@gmail.com", password="user1234"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@gmail.com", password="user1234"
        )
        tweet = Tweet.objects.create(user=self.user, content="Test tweet")
        tweet_ct = ContentType.objects.get_for_model(Tweet)
        self.notification = Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="liked",
            is_read=False,
            content_type=tweet_ct,
            content_id=tweet.id,
        )
        self.url = reverse("read-notification", kwargs={"pk": self.notification.pk})

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def test_mark_notification_read_success(self):
        self.authenticate()
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_already_read_notification(self):
        self.authenticate()
        # Mark it read first
        self.notification.is_read = True
        self.notification.save()

        # mark it read again
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_notification_read_not_receiver(self):
        self.authenticate(self.other_user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # still unread
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)

    def test_mark_notification_read_unauthenticated(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # still unread
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)

    def test_mark_nonexistent_notification_read(self):
        self.authenticate()
        url = reverse("read-notification", kwargs={"pk": 99999})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
