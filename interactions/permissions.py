from rest_framework import permissions


class IsNotificationReceiver(permissions.BasePermission):
    message = "Forbidden"

    def has_object_permission(self, request, view, obj):
        return obj.receiver == request.user
