from django.urls import path
from .views import (
    CreateTweetAPIView,
    FeedAPIView,
    UserPostsAPIView,
    TweetAPIView,
    RetweetAPIView,
    LikeTweetAPIView,
    CommentOnTweetAPIView,
    CommentDetailAPIView,
)

urlpatterns = [
    path("", CreateTweetAPIView.as_view(), name="create-tweet"),
    path("feed/", FeedAPIView.as_view(), name="feed"),
    path("<int:pk>/", TweetAPIView.as_view(), name="tweet-detail"),
    path("<int:pk>/retweets/", RetweetAPIView.as_view(), name="retweet"),
    path("<int:pk>/likes/", LikeTweetAPIView.as_view(), name="like-tweet"),
    path("<int:pk>/comments/", CommentOnTweetAPIView.as_view(), name="comments"),
    path(
        "<int:pk>/comments/<int:comment_id>/",
        CommentDetailAPIView.as_view(),
        name="comment-details",
    ),
    path("user/<str:username>/", UserPostsAPIView.as_view(), name="user-posts"),
]
