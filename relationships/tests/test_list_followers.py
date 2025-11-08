from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from relationships.models import Follow

User = get_user_model()


class TestListFollowers(APITestCase):
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

        self.url_user1_followers = reverse("followers", kwargs={"username": self.user1.username})

    def authenticate_user1(self):
        self.client.force_authenticate(user=self.user1)

    def test_list_followers_success(self):
        Follow.objects.create(follower=self.user2, following=self.user1)
        Follow.objects.create(follower=self.user3, following=self.user1)

        self.authenticate_user1()
        response = self.client.get(self.url_user1_followers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_followers_not_found_user(self):
        self.authenticate_user1()
        url = reverse("followers", kwargs={"username": "nonexistent_user"})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_followers_unauthenticated(self):
        response = self.client.get(self.url_user1_followers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
