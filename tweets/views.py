from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.db.models import Prefetch, Count, Exists, OuterRef, Q
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import generics, filters, mixins, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from .cache_utils import invalidate_feed_cache, get_feed_cache_key, invalidate_user_posts_cache, get_user_posts_cache_key,get_tweet_cache_key, invalidate_tweet_cache
from .serializers import (
    TweetSerializer,
    FeedSerializer,
    RetrieveTweetSerializer,
    RetweetSerializer,
    LikeTweetSerializer,
    CommentOnTweetSerializer,
    CommentSerializer,
    PostSerializer,
    BookmarkSerializer,
    BookmarkedTweetSerializer,
)
from .models import Tweet, Like, Comment, Retweet, Bookmark
from .permissions import IsAuthorOrReadOnly, IsTweetAuthor, IsCommentOwner, CanEdit
from config.throttles import ContentCreationRateThrottle, InteractionRateThrottle

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


class CreateTweetAPIView(generics.CreateAPIView):
    queryset = Tweet.objects.all()
    serializer_class = TweetSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ContentCreationRateThrottle]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        invalidate_feed_cache(self.request.user.id)
        invalidate_user_posts_cache(self.request.user.id)


class FeedAPIView(generics.ListAPIView):
    """
    API endpoint that returns a personalized feed of tweets and retweets from followed users
    and the current user, sorted by creation date in descending order.
    """

    serializer_class = FeedSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__username", "user__profile__name", "content"]

    def list(self, request, *args, **kwargs):
        page = request.query_params.get("page", "1")
        search = request.query_params.get("search", "")
        cache_key = get_feed_cache_key(request.user.id, page, search)
        cached = cache.get(cache_key)

        if cached is not None:
            return Response(cached)

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            cache.set(cache_key, response.data, timeout=120)
            return response

        serializer = self.get_serializer(queryset, many=True)
        cache.set(cache_key, serializer.data, timeout=120)
        return Response(serializer.data)

    def get_queryset(self):
        from django.db.models import Count, Exists, OuterRef, Q

        current_user = self.request.user
        following_users = User.objects.filter(followers__follower=current_user)
        tweets = (
            Tweet.objects.filter(Q(user__in=following_users) | Q(user=current_user))
            .select_related("user", "user__profile")
            .annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count(
                    "comments", filter=Q(comments__parent=None), distinct=True
                ),
                retweets_count=Count("retweets", distinct=True),
                is_liked=Exists(
                    Like.objects.filter(user=current_user, tweet=OuterRef("pk"))
                ),
                is_retweeted=Exists(
                    Retweet.objects.filter(user=current_user, tweet=OuterRef("pk"))
                ),
                is_bookmarked=Exists(
                    Bookmark.objects.filter(user=current_user, tweet=OuterRef("pk"))
                ),
            )
        )

        retweets = (
            Retweet.objects.filter(Q(user__in=following_users) | Q(user=current_user))
            .select_related(
                "user", "user__profile", "tweet", "tweet__user", "tweet__user__profile"
            )
            .annotate(
                tweet_likes_count=Count("tweet__likes", distinct=True),
                tweet_comments_count=Count(
                    "tweet__comments",
                    filter=Q(tweet__comments__parent=None),
                    distinct=True,
                ),
                tweet_retweets_count=Count("tweet__retweets", distinct=True),
                tweet_is_liked=Exists(
                    Like.objects.filter(user=current_user, tweet=OuterRef("tweet"))
                ),
                tweet_is_retweeted=Exists(
                    Retweet.objects.filter(user=current_user, tweet=OuterRef("tweet"))
                ),
                tweet_is_bookmarked=Exists(
                    Bookmark.objects.filter(user=current_user, tweet=OuterRef("tweet"))
                ),
            )
        )

        posts = sorted(
            list(tweets) + list(retweets), key=lambda x: x.created_at, reverse=True
        )

        search_query = self.request.query_params.get("search", "").lower()
        if search_query:
            posts = [
                p for p in posts 
                if search_query in getattr(p, 'content', '').lower() or 
                   search_query in p.user.username.lower() or
                   search_query in getattr(p, 'quote', '').lower()
            ]

        return posts


class UserPostsAPIView(generics.ListAPIView):
    """
    API endpoint that returns a paginated list of a user's posts (tweets and retweets)
    sorted by creation date in descending order.

    Returns rich nested data including:
    - Author details (name, username, profile image)
    - Engagement metrics (likes, comments counts)
    - Current user interaction status (is_liked)
    - Full original tweet for retweets
    """

    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

        
    def get_queryset(self):

        user = get_object_or_404(User, username=self.kwargs["username"])
        current_user = self.request.user
        
        tweets = (
            Tweet.objects.filter(user=user)
            .select_related("user", "user__profile")
            .annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count(
                    "comments", filter=Q(comments__parent=None), distinct=True
                ),
                retweets_count=Count("retweets", distinct=True),
                is_liked=Exists(
                    Like.objects.filter(user=current_user, tweet=OuterRef("pk"))
                ),
                is_retweeted=Exists(
                    Retweet.objects.filter(user=current_user, tweet=OuterRef("pk"))
                ),
                is_bookmarked=Exists(
                    Bookmark.objects.filter(user=current_user, tweet=OuterRef("pk"))
                ),
            )
        )

        retweets = (
            Retweet.objects.filter(user=user)
            .select_related(
                "user", "user__profile", "tweet", "tweet__user", "tweet__user__profile"
            )
            .annotate(
                tweet_likes_count=Count("tweet__likes", distinct=True),
                tweet_comments_count=Count(
                    "tweet__comments",
                    filter=Q(tweet__comments__parent=None),
                    distinct=True,
                ),
                tweet_retweets_count=Count("tweet__retweets", distinct=True),
                tweet_is_liked=Exists(
                    Like.objects.filter(user=current_user, tweet=OuterRef("tweet"))
                ),
                tweet_is_retweeted=Exists(
                    Retweet.objects.filter(user=current_user, tweet=OuterRef("tweet"))
                ),
                tweet_is_bookmarked=Exists(
                    Bookmark.objects.filter(user=current_user, tweet=OuterRef("tweet"))
                ),
            )
        )

        posts = sorted(
            list(tweets) + list(retweets), key=lambda x: x.created_at, reverse=True
        )

        return posts


    def list(self, request, *args, **kwargs):
            user = get_object_or_404(User, username=self.kwargs["username"])
            viewer = request.user
            page = request.query_params.get("page", "1")

            cache_key = get_user_posts_cache_key(user.id, viewer.id,page)
            cached = cache.get(cache_key)

            if cached is not None:
                return Response(cached)
            
            response = super().list(request, *args, **kwargs)
            cache.set(cache_key, response.data, timeout=300) # 5 minutes
            return response


class TweetAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly, CanEdit]

    def get_queryset(self):
        return (
            Tweet.objects.all()
            .select_related("user", "user__profile")
            .prefetch_related(prefetch_top_level_comments())
            .annotate(likes_count=Count("likes", distinct=True))
        )

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return TweetSerializer

        return RetrieveTweetSerializer
    
    def retrieve(self, request, *args, **kwargs):
        viewer = request.user
        tweet_id = self.kwargs["pk"]

        cache_key = get_tweet_cache_key(tweet_id,viewer.id)
        cached = cache.get(cache_key)

        if cached is not None:
            return Response(cached)
        
        tweet = self.get_object()
        serializer = self.get_serializer(tweet)
        cache.set(cache_key, serializer.data, timeout=300) # 5 minutes
        return Response(serializer.data)

    def perform_update(self, serializer):
        tweet = serializer.save()
        invalidate_feed_cache(self.request.user.id)
        invalidate_user_posts_cache(self.request.user.id)
        invalidate_tweet_cache(tweet.id)

    def perform_destroy(self, instance):
        user_id = instance.user.id
        tweet_id = instance.id
        instance.delete()
        invalidate_feed_cache(user_id)
        invalidate_user_posts_cache(user_id)
        invalidate_tweet_cache(tweet_id)


class RetweetAPIView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    serializer_class = RetweetSerializer
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        # Rate-limit retweet creation only; listing/removing retweets should stay unrestricted.
        if self.request.method == "POST":
            return [InteractionRateThrottle()]

        return super().get_throttles()

    def get_tweet(self):
        return get_object_or_404(Tweet, pk=self.kwargs["pk"])

    def get_queryset(self):
        return (
            Retweet.objects.filter(tweet=self.get_tweet())
            .select_related(
                "user", "user__profile", "tweet", "tweet__user", "tweet__user__profile"
            )
            .annotate(
                tweet_likes_count=Count("tweet__likes", distinct=True),
                tweet_comments_count=Count(
                    "tweet__comments",
                    filter=Q(tweet__comments__parent=None),
                    distinct=True,
                ),
                tweet_retweets_count=Count("tweet__retweets", distinct=True),
                tweet_is_liked=Exists(
                    Like.objects.filter(user=self.request.user, tweet=self.get_tweet())
                ),
                tweet_is_retweeted=Exists(
                    Retweet.objects.filter(
                        user=self.request.user, tweet=self.get_tweet()
                    )
                ),
                tweet_is_bookmarked=Exists(
                    Bookmark.objects.filter(
                        user=self.request.user, tweet=self.get_tweet()
                    )
                ),
            )
        )

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = {
            **self.get_serializer_context(),
            "user": self.request.user,
            "tweet": self.get_tweet(),
        }

        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user, tweet=self.get_tweet())
        except IntegrityError:
            raise ValidationError(
                {
                    "error": "already_retweeted",
                    "detail": "You have already retweeted this tweet. Use DELETE to unretweet.",
                }
            )

    def post(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            instance = self.get_queryset().get(pk=response.data["id"])
            serializer = self.get_serializer(instance)
            invalidate_feed_cache(request.user.id)
            invalidate_user_posts_cache(request.user.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return response

    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        instance = get_object_or_404(Retweet, tweet=self.get_tweet(), user=request.user)
        self.perform_destroy(instance)
        invalidate_feed_cache(request.user.id)
        invalidate_user_posts_cache(request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LikeTweetAPIView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):

    serializer_class = LikeTweetSerializer
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        # Rate-limit like creation only; listing/removing likes should stay unrestricted.
        if self.request.method == "POST":
            return [InteractionRateThrottle()]

        return super().get_throttles()

    def get_queryset(self):
        return Like.objects.filter(tweet=self.get_tweet()).select_related(
            "user", "user__profile"
        )

    def get_tweet(self):
        return get_object_or_404(Tweet, pk=self.kwargs["pk"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["tweet"] = self.get_tweet()
        return context

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsTweetAuthor()]

        return super().get_permissions()

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user, tweet=self.get_tweet())
        except IntegrityError:
            raise ValidationError(
                {
                    "error": "already_liked",
                    "detail": "You have already liked this tweet. Use DELETE to unlike.",
                }
            )

    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            instance = self.get_queryset().get(pk=response.data["id"])
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return response

    def delete(self, request, *args, **kwargs):
        instance = get_object_or_404(Like, user=request.user, tweet=self.get_tweet())
        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentOnTweetAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_tweet(self):
        return get_object_or_404(Tweet, pk=self.kwargs["pk"])

    def get_queryset(self):
        return (
            Comment.objects.filter(tweet=self.get_tweet(), parent=None)
            .select_related("user", "user__profile", "tweet")
            .prefetch_related(
                Prefetch(
                    "replies",
                    queryset=Comment.objects.select_related("user", "user__profile"),
                )
            )
            .annotate(replies_count=Count("replies", distinct=True))
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CommentSerializer
        return CommentOnTweetSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["tweet_id"] = self.kwargs["pk"]
        return context

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, tweet=self.get_tweet())


class CommentDetailAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        return Comment.objects.select_related(
            "user", "user__profile", "tweet"
        ).prefetch_related(
            Prefetch(
                "replies",
                queryset=Comment.objects.select_related(
                    "user", "user__profile"
                ).prefetch_related(
                    Prefetch(
                        "replies",
                        queryset=Comment.objects.select_related(
                            "user", "user__profile"
                        ),
                    )
                ),
            )
        )

    def get_object(self):
        tweet = get_object_or_404(Tweet, pk=self.kwargs["pk"])
        obj = get_object_or_404(
            self.get_queryset(), pk=self.kwargs["comment_id"], tweet=tweet
        )
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsCommentOwner()]
        return [IsAuthenticated()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["full_depth"] = True  # Full recusrsion
        return context


class BookmarkAPIView(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Bookmark.objects.filter(user=self.request.user)
            .select_related("user", "user__profile", "tweet")
            .prefetch_related("tweet__comments")
        )

    def get_tweet(self):
        return get_object_or_404(Tweet, pk=self.kwargs["pk"])

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user, tweet=self.get_tweet())
        except IntegrityError:
            raise ValidationError(
                {
                    "error": "already_bookmarked",
                    "detail": "You have already bookmarked this tweet. Use DELETE to remove.",
                }
            )

    def post(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            return Response(
                {"detail": "Tweet added to your bookmarks"},
                status=status.HTTP_201_CREATED,
            )
        return response

    def delete(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Bookmark, tweet=self.get_tweet(), user=request.user
        )
        self.perform_destroy(instance)
        return Response(
            {"detail": "Tweet removed from your bookmarks"}, status=status.HTTP_200_OK
        )


class UserBookmarksAPIView(generics.ListAPIView):
    serializer_class = BookmarkedTweetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Bookmark.objects.filter(user=self.request.user)
            .select_related("tweet", "tweet__user", "tweet__user__profile")
            .annotate(
                likes_count=Count("tweet__likes", distinct=True),
                comments_count=Count(
                    "tweet__comments",
                    filter=Q(tweet__comments__parent=None),
                    distinct=True,
                ),
                retweets_count=Count("tweet__retweets", distinct=True),
                is_liked=Exists(
                    Like.objects.filter(user=self.request.user, tweet=OuterRef("tweet"))
                ),
                is_retweeted=Exists(
                    Retweet.objects.filter(
                        user=self.request.user, tweet=OuterRef("tweet")
                    )
                ),
            )
        ).order_by("-created_at")
