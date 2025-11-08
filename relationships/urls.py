from django.urls import path
from .views import (
    FollowUserAPIView,
    UnFollowUserAPIView,
    ListFollowersAPIView,
    ListFollowingAPIView,
)

urlpatterns = [
    path("<str:username>/follow/", FollowUserAPIView.as_view(), name="follow"),
    path("<str:username>/unfollow/", UnFollowUserAPIView.as_view(), name="unfollow"),
    path("<str:username>/followers/", ListFollowersAPIView.as_view(), name="followers"),
    path("<str:username>/following/", ListFollowingAPIView.as_view(), name="following"),
]
