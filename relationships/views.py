from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    FollowUserSerializer,
    UnFollowUserSerializer,
    ListFollowersSerializer,
    ListFollowingSerializer,
)
from .models import Follow

# Create your views here.
User = get_user_model()


class FollowUserAPIView(generics.CreateAPIView):
    queryset = Follow.objects.all()
    serializer_class = FollowUserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["follower"] = self.request.user
        context["following"] = self.get_following()
        return context

    def get_following(self):
        return get_object_or_404(User, pk=self.kwargs["pk"])

    def perform_create(self, serializer):
        serializer.save(follower=self.request.user, following=self.get_following())


class UnFollowUserAPIView(generics.DestroyAPIView):
    queryset = Follow.objects.all()
    serializer_class = UnFollowUserSerializer
    permission_classes = [IsAuthenticated]

    def get_following(self):
        return get_object_or_404(User, pk=self.kwargs["pk"])

    def get_object(self):
        return get_object_or_404(
            Follow, follower=self.request.user, following=self.get_following()
        )


class ListFollowersAPIView(generics.ListAPIView):
    serializer_class = ListFollowersSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.kwargs["pk"])
        return User.objects.filter(pk=user.pk).select_related("profile")


class ListFollowingAPIView(generics.ListAPIView):
    serializer_class = ListFollowingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.kwargs["pk"])
        return User.objects.filter(pk=user.pk).select_related("profile")
