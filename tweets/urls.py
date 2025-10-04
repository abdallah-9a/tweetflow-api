from django.urls import path
from .views import ListCreateTweetAPIView, RetrieveDeleteTweetAPIView

urlpatterns = [
    path("", ListCreateTweetAPIView.as_view(), name="feed"),
    path("<int:pk>/", RetrieveDeleteTweetAPIView.as_view(), name="tweet-detail"),
]
