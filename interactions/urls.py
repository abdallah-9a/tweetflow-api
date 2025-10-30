from django.urls import path
from .views import ListUserMentionsAPIView, ListNotificationAPIView

urlpatterns = [
    path("mentions/", ListUserMentionsAPIView.as_view(), name="mentions"),
    path("notifications/", ListNotificationAPIView.as_view(), name="notifications"),
]
