from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
from rest_framework import status
from interactions.models import Notification
from tweets.models import Tweet

User = get_user_model()


class TestDeleteNotification(APITestCase):
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
            content_type=tweet_ct,
            content_id=tweet.id,
        )
        self.url = reverse("delete-notification", kwargs={"pk": self.notification.pk})

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def test_delete_notification_success(self):
        self.authenticate()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Notification.objects.filter(pk=self.notification.pk).exists())

    def test_delete_notification_not_receiver(self):
        self.authenticate(self.other_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Notification.objects.filter(pk=self.notification.pk).exists())

    def test_delete_notification_unauthenticated(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Notification.objects.filter(pk=self.notification.pk).exists())

    def test_delete_nonexistent_notification(self):
        self.authenticate()
        url = reverse("delete-notification", kwargs={"pk": 99999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
