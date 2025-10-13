from django.shortcuts import render
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from .models import Mention
from .serializers import ListUserMentionsSerializer

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
