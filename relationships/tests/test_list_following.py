from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from relationships.models import Follow

User = get_user_model()


class TestListFollowing(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="test1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="test1234"
        )
        self.user3 = User.objects.create_user(
            username="user3", email="user3@test.com", password="test1234"
        )

        self.url_user1_following = reverse("following", kwargs={"pk": self.user1.pk})

    def authenticate_user1(self):
        self.client.force_authenticate(user=self.user1)

    def test_list_following_success(self):
        Follow.objects.create(follower=self.user1, following=self.user2)
        Follow.objects.create(follower=self.user1, following=self.user3)

        self.authenticate_user1()
        response = self.client.get(self.url_user1_following)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results'][0]['following']), 2)

    def test_list_following_not_found_user(self):
        self.authenticate_user1()
        url = reverse("following", kwargs={"pk": 999999})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_following_unauthenticated(self):
        response = self.client.get(self.url_user1_following)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
