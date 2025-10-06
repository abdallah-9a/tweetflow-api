from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from relationships.models import Follow

User = get_user_model()


class TestUnfollow(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="test1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="test1234"
        )

        self.follow_url_user2 = reverse("follow", kwargs={"pk": self.user2.pk})
        self.unfollow_url_user2 = reverse("unfollow", kwargs={"pk": self.user2.pk})

    def authenticate_user1(self):
        self.client.force_authenticate(user=self.user1)

    def test_unfollow_success(self):
        self.authenticate_user1()
        # follow
        self.client.post(self.follow_url_user2)
        self.assertTrue(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

        # Then unfollow
        response = self.client.delete(self.unfollow_url_user2)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_unfollow_not_followed(self):
        self.authenticate_user1()

        response = self.client.delete(self.unfollow_url_user2)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unfollow_not_found_user(self):
        self.authenticate_user1()
        url = reverse("unfollow", kwargs={"pk": 999999})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unfollow_unauthenticated(self):
        response = self.client.delete(self.unfollow_url_user2)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
