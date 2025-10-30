from django.shortcuts import render
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Mention, Notification
from .serializers import ListUserMentionsSerializer, ListNotificationsSerializer

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
        return Notification.objects.filter(receiver=self.request.user)


class MarkNotificationAsReadAPIView(generics.UpdateAPIView):
    queryset = Notification.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def patch(self, request, *args, **kwargs):
        Notification = self.get_object()
        if Notification.receiver != request.user:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        Notification.is_read = True
        Notification.save()

        return Response({"msg": "Notification marked as read"})
