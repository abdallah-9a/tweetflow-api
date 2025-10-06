from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from relationships.models import Follow

User = get_user_model()


class TestFollow(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="test1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="test1234"
        )

        self.follow_url_user2 = reverse("follow", kwargs={"pk": self.user2.pk})

    def authenticate_user1(self):
        self.client.force_authenticate(user=self.user1)

    def test_follow_success(self):
        self.authenticate_user1()

        response = self.client.post(self.follow_url_user2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_follow_twice(self):
        self.authenticate_user1()
        response = self.client.post(self.follow_url_user2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Second follow
        response = self.client.post(self.follow_url_user2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data.get("error")[0], "already_following")

    def test_follow_unknown_user(self):
        self.authenticate_user1()
        url = reverse("follow", kwargs={"pk": 999999})

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_self_follow(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse("follow", kwargs={"pk": self.user1.pk})

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data.get("error")[0], "self_follow")

    def test_follow_unauthenticated(self):
        response = self.client.post(self.follow_url_user2)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
