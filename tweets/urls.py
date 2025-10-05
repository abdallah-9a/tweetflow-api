from django.urls import path
from .views import (
    ListCreateTweetAPIView,
    RetrieveDeleteTweetAPIView,
    ListLikesAPIView,
    LikeTweetAPIView,
    UnlikeTweetAPIView,
    CommentOnTweetAPIView,
    ListCommentAPIView,
)

urlpatterns = [
    path("", ListCreateTweetAPIView.as_view(), name="feed"),
    path("<int:pk>/", RetrieveDeleteTweetAPIView.as_view(), name="tweet-detail"),
    path("<int:pk>/like/", LikeTweetAPIView.as_view(), name="like-tweet"),
    path("<int:pk>/unlike/", UnlikeTweetAPIView.as_view(), name="unlike-tweet"),
    path("<int:pk>/likes/", ListLikesAPIView.as_view(), name="tweet-likes"),
    path("<int:pk>/comment/", CommentOnTweetAPIView.as_view(), name="comment"),
    path("<int:pk>/comments/", ListCommentAPIView.as_view(), name="comments"),
]
