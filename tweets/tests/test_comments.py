from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tweets.models import Tweet, Comment
from accounts.models import User


class TestCommentEndpoints(APITestCase):
    """Test comment endpoints (create, list, detail, delete)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(user=self.user, content="Test tweet")
        self.list_url = reverse("comments", kwargs={"pk": self.tweet.pk})

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def test_create_comment_success(self):
        """User can comment on a tweet"""
        self.authenticate()
        data = {"content": "Great tweet!"}
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Comment.objects.filter(user=self.user, tweet=self.tweet).exists()
        )

    def test_create_comment_unauthenticated(self):
        """Unauthenticated user cannot comment"""
        response = self.client.post(self.list_url, {"content": "Comment"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_comment_on_nonexistent_tweet(self):
        """Cannot comment on tweet that doesn't exist"""
        self.authenticate()
        url = reverse("comments", kwargs={"pk": 99999})
        response = self.client.post(url, {"content": "Comment"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Reply to Comment Tests
    def test_reply_to_comment_success(self):
        """User can reply to a comment"""
        self.authenticate()
        parent_comment = Comment.objects.create(
            user=self.user, tweet=self.tweet, content="Parent comment"
        )

        data = {"content": "This is a reply", "parent": parent_comment.pk}
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Comment.objects.filter(
                user=self.user, tweet=self.tweet, parent=parent_comment
            ).exists()
        )
        self.assertEqual(response.data["parent"], parent_comment.pk)

    def test_reply_to_comment_from_different_tweet_fails(self):
        """Cannot reply to comment from a different tweet"""
        self.authenticate()
        other_tweet = Tweet.objects.create(user=self.user, content="Other tweet")
        other_comment = Comment.objects.create(
            user=self.user, tweet=other_tweet, content="Other comment"
        )

        data = {"content": "Invalid reply", "parent": other_comment.pk}
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"][0], "invalid_parent")

    # GET - List Comments Tests
    def test_list_comments_success(self):
        """Can list top-level comments on a tweet"""
        self.authenticate()
        Comment.objects.create(user=self.user, tweet=self.tweet, content="First")
        Comment.objects.create(user=self.other_user, tweet=self.tweet, content="Second")

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_comments_unauthenticated(self):
        """Unauthenticated user cannot list comments"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestCommentDetailEndpoints(APITestCase):
    """Test suite for individual comment detail endpoint (view full thread, delete)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@gmail.com", password="user1234"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@gmail.com", password="user1234"
        )
        self.tweet = Tweet.objects.create(user=self.user, content="Test tweet")
        self.comment = Comment.objects.create(
            user=self.user, tweet=self.tweet, content="Test comment"
        )
        self.detail_url = reverse(
            "comment-details",
            kwargs={"pk": self.tweet.pk, "comment_id": self.comment.pk},
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def test_view_comment_detail_success(self):
        self.authenticate(self.other_user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.comment.pk)
        self.assertEqual(response.data["content"], "Test comment")

    def test_view_comment_with_full_nested_replies(self):
        self.authenticate()

        reply1 = Comment.objects.create(
            user=self.other_user,
            tweet=self.tweet,
            content="Reply 1",
            parent=self.comment,
        )
        reply2 = Comment.objects.create(
            user=self.user, tweet=self.tweet, content="Reply 2", parent=reply1
        )
        reply3 = Comment.objects.create(
            user=self.other_user, tweet=self.tweet, content="Reply 3", parent=reply2
        )

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify full depth recursion
        self.assertEqual(len(response.data["replies"]), 1)
        level1 = response.data["replies"][0]
        self.assertEqual(level1["content"], "Reply 1")

        self.assertEqual(len(level1["replies"]), 1)
        level2 = level1["replies"][0]
        self.assertEqual(level2["content"], "Reply 2")

        self.assertEqual(len(level2["replies"]), 1)
        level3 = level2["replies"][0]
        self.assertEqual(level3["content"], "Reply 3")

    def test_view_comment_unauthenticated(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_view_nonexistent_comment(self):
        self.authenticate()
        url = reverse(
            "comment-details", kwargs={"pk": self.tweet.pk, "comment_id": 99999}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_comment_from_wrong_tweet(self):
        self.authenticate()
        other_tweet = Tweet.objects.create(user=self.user, content="Other")
        url = reverse(
            "comment-details",
            kwargs={"pk": other_tweet.pk, "comment_id": self.comment.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # DELETE - Delete Comment Tests
    def test_delete_comment_as_owner(self):
        self.authenticate(self.user)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_delete_comment_not_owner(self):
        """Non-owner cannot delete comment"""
        self.authenticate(self.other_user)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_delete_comment_unauthenticated(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_comment_cascade_deletes_replies(self):
        self.authenticate()
        reply = Comment.objects.create(
            user=self.other_user, tweet=self.tweet, content="Reply", parent=self.comment
        )

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())
        self.assertFalse(Comment.objects.filter(pk=reply.pk).exists())  # Cascade delete
