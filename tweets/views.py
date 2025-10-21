from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from django.contrib.auth import get_user_model
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    CreateTweetSerializer,
    RetrieveTweetSerializer,
    RetweetSerializer,
    ListLikesSerializer,
    LikeTweetSerializer,
    UnlikTweetSerializer,
    CommentOnTweetSerializer,
    ListCommentSerializer,
    PostSerializer,
)
from .models import Tweet, Like, Comment, Retweet
from .permissions import IsAuthorOrReadOnly, IsTweetAuthor
from relationships.models import Follow

# Create your views here.
User = get_user_model()


def prefetch_top_level_comments(path: str = "comments"):
    replies_qs = Comment.objects.select_related("user", "user__profile")

    top_level_comments_qs = (
        Comment.objects.filter(parent=None)
        .select_related("user", "user__profile")
        .prefetch_related(Prefetch("replies", queryset=replies_qs))
    )

    return Prefetch(path, queryset=top_level_comments_qs)


class ListCreateTweetAPIView(generics.ListCreateAPIView):
    serializer_class = CreateTweetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__profile__name", "content"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """
        Returns a queryset of tweets for the user's feed, including tweets from users
        that the current user follows as well as their own tweets. The tweets are
        ordered by creation date in descending order (most recent first).
        """
        followings = Follow.objects.filter(follower=self.request.user).values_list(
            "following", flat=True
        )
        followings_ids = list(followings) + [self.request.user.id]
        tweets = (
            Tweet.objects.filter(user_id__in=followings_ids)
            .select_related("user", "user__profile")
            .prefetch_related(prefetch_top_level_comments())
            .order_by("-created_at")
        )

        return tweets


class UserPostsAPIView(generics.ListAPIView):
    """
    API endpoint that returns a paginated list of a user's posts (tweets and retweets)
    sorted by creation date in descending order.
    """

    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        tweets = (
            Tweet.objects.filter(user=user)
            .select_related("user", "user__profile")
            .prefetch_related(prefetch_top_level_comments())
        )
        retweets = (
            Retweet.objects.filter(user=user)
            .select_related("user", "user__profile", "tweet")
            .prefetch_related(prefetch_top_level_comments("tweet__comments"))
        )
        from itertools import chain
        from operator import attrgetter

        posts = sorted(
            chain(tweets, retweets),
            key=attrgetter("created_at"),
            reverse=True,
        )

        return posts


class RetrieveDeleteTweetAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = RetrieveTweetSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    def get_queryset(self):
        return (
            Tweet.objects.all()
            .select_related("user", "user__profile")
            .prefetch_related(prefetch_top_level_comments())
        )


class RetweetAPIView(generics.CreateAPIView):
    queryset = Retweet.objects.all()
    serializer_class = RetweetSerializer
    permission_classes = [IsAuthenticated]

    def get_tweet(self):
        return get_object_or_404(Tweet, pk=self.kwargs["pk"])

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, tweet=self.get_tweet())


class ListRetweetsAPIView(generics.ListAPIView):
    serializer_class = RetweetSerializer
    permission_classes = [IsAuthenticated]

    def get_tweet(self):
        return get_object_or_404(Tweet, pk=self.kwargs["pk"])

    def get_queryset(self):
        return (
            Retweet.objects.filter(tweet=self.get_tweet())
            .select_related(
                "user", "user__profile", "tweet", "tweet__user", "tweet__user__profile"
            )
            .prefetch_related(prefetch_top_level_comments("tweet__comments"))
        )


class LikeTweetAPIView(generics.CreateAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeTweetSerializer
    permission_classes = [IsAuthenticated]

    def get_tweet(self):
        return get_object_or_404(Tweet, pk=self.kwargs["pk"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["tweet"] = self.get_tweet()
        return context

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, tweet=self.get_tweet())


class UnlikeTweetAPIView(generics.DestroyAPIView):
    queryset = Like.objects.all()
    serializer_class = UnlikTweetSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        tweet = get_object_or_404(Tweet, pk=self.kwargs["pk"])
        return get_object_or_404(Like, user=self.request.user, tweet=tweet)


class ListLikesAPIView(generics.ListAPIView):
    serializer_class = ListLikesSerializer
    permission_classes = [IsAuthenticated, IsTweetAuthor]

    def get_tweet(self):
        return get_object_or_404(Tweet, pk=self.kwargs["pk"])

    def get_queryset(self):
        tweet = self.get_tweet()
        return Like.objects.filter(tweet=tweet).select_related("user", "user__profile")


class CommentOnTweetAPIView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentOnTweetSerializer
    permission_classes = [IsAuthenticated]

    def get_tweet(self):
        return get_object_or_404(Tweet, pk=self.kwargs["pk"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["tweet"] = self.get_tweet()
        return context

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, tweet=self.get_tweet())


class ListCommentAPIView(generics.ListAPIView):
    serializer_class = ListCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_tweet(self):
        return get_object_or_404(Tweet, pk=self.kwargs["pk"])

    def get_queryset(self):
        replies = Comment.objects.select_related("user", "user__profile")
        return (
            self.get_tweet()
            .comments.filter(parent=None)
            .select_related("user", "user__profile", "parent")
            .prefetch_related(Prefetch("replies", queryset=replies))
        )
