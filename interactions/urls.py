from django.urls import path
from .views import (
    ListUserMentionsAPIView,
    ListNotificationAPIView,
    MarkNotificationAsReadAPIView,
)

urlpatterns = [
    path("mentions/", ListUserMentionsAPIView.as_view(), name="mentions"),
    path("notifications/", ListNotificationAPIView.as_view(), name="notifications"),
    path(
        "notifications/<int:pk>/read/",
        MarkNotificationAsReadAPIView.as_view(),
        name="read-notification",
    ),
]
