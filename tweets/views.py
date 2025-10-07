from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    CreateTweetSerializer,
    RetrieveTweetSerializer,
    ListLikesSerializer,
    LikeTweetSerializer,
    UnlikTweetSerializer,
    CommentOnTweetSerializer,
    ListCommentSerializer,
)
from .models import Tweet, Like, Comment
from .permissions import IsAuthorOrReadOnly, IsTweetAuthor

# Create your views here.


class ListCreateTweetAPIView(generics.ListCreateAPIView):
    queryset = Tweet.objects.all()
    serializer_class = CreateTweetSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RetrieveDeleteTweetAPIView(generics.RetrieveDestroyAPIView):
    queryset = Tweet.objects.all()
    serializer_class = RetrieveTweetSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]


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
