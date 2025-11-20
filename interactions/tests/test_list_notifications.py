from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
from rest_framework import status
from interactions.models import Notification
from tweets.models import Tweet
from relationships.models import Follow

User = get_user_model()


class TestListNotifications(APITestCase):
    def setUp(self):
        self.url = reverse("notifications")
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

    def test_list_notifications_success(self):
        self.authenticate()
        tweet1 = Tweet.objects.create(user=self.user, content="Test tweet 1")
        tweet_ct = ContentType.objects.get_for_model(Tweet)
        Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="liked",
            content_type=tweet_ct,
            content_id=tweet1.id,
        )
        tweet2 = Tweet.objects.create(user=self.user, content="Test tweet 2")
        Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="commented",
            content_type=tweet_ct,
            content_id=tweet2.id,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        # 3 = 1 welcome notification (auto-created) + 2 test notifications
        self.assertEqual(len(response.data["results"]), 3)

    def test_list_notifications_empty(self):
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 1 = welcome notification (auto-created on user registration)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_notifications_only_own_notifications(self):
        self.authenticate()
        # Notification for current user
        tweet1 = Tweet.objects.create(user=self.user, content="Test tweet 1")
        tweet_ct = ContentType.objects.get_for_model(Tweet)
        Notification.objects.create(
            sender=self.sender,
            receiver=self.user,
            verb="liked",
            content_type=tweet_ct,
            content_id=tweet1.id,
        )
        # Notification for other user (should not appear)
        tweet2 = Tweet.objects.create(user=self.other_user, content="Test tweet 2")
        Notification.objects.create(
            sender=self.sender,
            receiver=self.other_user,
            verb="liked",
            content_type=tweet_ct,
            content_id=tweet2.id,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 2 = 1 welcome notification (auto-created) + 1 test notification
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_notifications_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
