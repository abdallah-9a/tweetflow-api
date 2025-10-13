from django.urls import path
from .views import ListUserMentionsAPIView

urlpatterns = [
    path("mentions/", ListUserMentionsAPIView.as_view(), name="mentions"),
]
