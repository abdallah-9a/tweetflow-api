from django.shortcuts import render
from django.db.models import Count
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Mention, Notification
from .serializers import ListUserMentionsSerializer, ListNotificationsSerializer
from .permissions import IsNotificationReceiver

# Create your views here.


class ListUserMentionsAPIView(generics.ListAPIView):
    serializer_class = ListUserMentionsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["=content_type__model", "actor__username"]

    def get_queryset(self):
        return (
            Mention.objects.filter(mentioned_user=self.request.user)
            .select_related("actor", "content_type")
            .order_by("-created_at")
        )


class ListNotificationAPIView(generics.ListAPIView):
    serializer_class = ListNotificationsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Notification.objects.filter(receiver=self.request.user)
            .select_related("sender", "sender__profile", "content_type")
            .order_by("-created_at")
        )


class MarkNotificationAsReadAPIView(generics.UpdateAPIView):
    queryset = Notification.objects.all()
    permission_classes = [IsAuthenticated, IsNotificationReceiver]
    lookup_field = "pk"

    def patch(self, request, *args, **kwargs):
        notification = self.get_object()

        notification.is_read = True
        notification.save()

        return Response({"detail": "Notification marked as read"})


class NotificationsCountAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(receiver=self.request.user, is_read=False)

    def get(self, request):
        unread_count = self.get_queryset().count()

        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)


class UnreadNotificationsAPIView(generics.ListAPIView):
    serializer_class = ListNotificationsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Notification.objects.filter(receiver=self.request.user, is_read=False)
            .select_related("sender", "sender__profile", "content_type")
            .order_by("-created_at")
        )
