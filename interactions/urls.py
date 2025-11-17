from django.urls import path
from .views import (
    ListUserMentionsAPIView,
    ListNotificationAPIView,
    MarkNotificationAsReadAPIView,
    UnreadNotificationsAPIView,
    NotificationsCountAPIView,
)

urlpatterns = [
    path("mentions/", ListUserMentionsAPIView.as_view(), name="mentions"),
    path(
        "notifications/unread/",
        UnreadNotificationsAPIView.as_view(),
        name="unread-notifications",
    ),
    path(
        "notifications/count/",
        NotificationsCountAPIView.as_view(),
        name="notifications-count",
    ),
    path(
        "notifications/<int:pk>/read/",
        MarkNotificationAsReadAPIView.as_view(),
        name="read-notification",
    ),
    path("notifications/", ListNotificationAPIView.as_view(), name="notifications"),
]
