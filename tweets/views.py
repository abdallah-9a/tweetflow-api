from django.shortcuts import get_object_or_404
from rest_framework import generics
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
)
from .models import Tweet, Like, Comment, Retweet
from .permissions import IsAuthorOrReadOnly, IsTweetAuthor
from relationships.models import Follow

# Create your views here.


class ListCreateTweetAPIView(generics.ListCreateAPIView):
    serializer_class = CreateTweetSerializer
    permission_classes = [IsAuthenticated]

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
        tweets = Tweet.objects.filter(user_id__in=followings_ids).order_by(
            "-created_at"
        )
        return tweets


class RetrieveDeleteTweetAPIView(generics.RetrieveDestroyAPIView):
    queryset = Tweet.objects.all()
    serializer_class = RetrieveTweetSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]


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
        return Retweet.objects.filter(tweet=self.get_tweet()).all()


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
        return (
            self.get_tweet()
            .comments.filter(parent=None)
            .select_related("user", "user__profile", "parent")
            .prefetch_related("replies")
        )
