from rest_framework import permissions
from django.shortcuts import get_object_or_404
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
