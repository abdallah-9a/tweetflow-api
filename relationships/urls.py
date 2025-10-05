from django.urls import path
from .views import (
    FollowUserAPIView,
    UnFollowUserAPIView,
    ListFollowersAPIView,
    ListFollowingAPIView,
)

urlpatterns = [
    path("<int:pk>/follow/", FollowUserAPIView.as_view(), name="follow"),
    path("<int:pk>/unfollow/", UnFollowUserAPIView.as_view(), name="unfollow"),
    path("<int:pk>/followers/", ListFollowersAPIView.as_view(), name="followers"),
    path("<int:pk>/following/", ListFollowingAPIView.as_view(), name="following"),
]
