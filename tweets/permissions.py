from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Tweet


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsTweetAuthor(permissions.BasePermission):
    message = "You must be the author of this tweet to view its likes."

    def has_permission(self, request, view):
        tweet_pk = view.kwargs.get("pk")
        tweet = get_object_or_404(Tweet, pk=tweet_pk)
        return tweet.user == request.user


class CanEdit(permissions.BasePermission):
    message = "Edit Option expired (15 minutes after posting)"

    def has_object_permission(self, request, view, obj):
        if request.method in ("PUT", "PATCH"):
            period = 15
            age_seconds = (timezone.now() - obj.created_at).total_seconds()
            if age_seconds > period * 60:
                return False

        return True
